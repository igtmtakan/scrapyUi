#!/usr/bin/env python3
"""
scrapy crawlコマンド + watchdog監視の実装
backend/app/services/scrapy_watchdog_monitor.py
"""
import asyncio
import subprocess
import json
import sqlite3
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
import uuid
import os
import sys

# watchdogライブラリ
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("⚠️ watchdogライブラリが必要です: pip install watchdog")


class JSONLWatchdogHandler(FileSystemEventHandler):
    """JSONLファイル専用のwatchdogイベントハンドラー"""

    def __init__(self, monitor):
        self.monitor = monitor
        self.last_size = 0

    def on_modified(self, event):
        """ファイル変更時の処理"""
        if event.is_directory:
            return

        # 監視対象のJSONLファイルかチェック
        if event.src_path == str(self.monitor.jsonl_file_path):
            # 非同期処理をスレッドセーフに実行
            threading.Thread(
                target=self._handle_file_change,
                daemon=True
            ).start()

    def _handle_file_change(self):
        """ファイル変更の処理（スレッドで実行）"""
        try:
            # asyncioループで実行
            if self.monitor.loop and not self.monitor.loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    self.monitor._process_new_lines(),
                    self.monitor.loop
                )
        except Exception as e:
            print(f"❌ ファイル変更処理エラー: {e}")


class ScrapyWatchdogMonitor:
    """scrapy crawl + watchdog監視クラス"""

    def __init__(self,
                 task_id: str,
                 project_path: str,
                 spider_name: str,
                 db_path: str = "backend/database/scrapy_ui.db",
                 websocket_callback: Optional[Callable] = None):
        self.task_id = task_id
        self.project_path = Path(project_path)
        self.spider_name = spider_name
        self.db_path = db_path
        self.websocket_callback = websocket_callback

        # 監視状態
        self.is_monitoring = False
        self.observer = None
        self.loop = None
        self.processed_lines = 0
        self.last_file_size = 0

        # JSONLファイルパス
        self.jsonl_file_path = self.project_path / f"results_{task_id}.jsonl"

        # Scrapyプロセス
        self.scrapy_process = None

    async def execute_spider_with_monitoring(self,
                                           settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """watchdog監視付きでscrapy crawlを実行"""
        try:
            print(f"🚀 watchdog監視付きスパイダー実行開始: {self.spider_name}")

            # 現在のイベントループを保存
            self.loop = asyncio.get_event_loop()

            # 1. watchdog監視を開始
            await self._start_watchdog_monitoring()

            # 2. scrapy crawlコマンドを実行
            scrapy_task = asyncio.create_task(
                self._execute_scrapy_crawl(settings)
            )

            # 3. プロセス完了まで待機
            scrapy_result = await scrapy_task

            # 4. 少し待ってから監視停止（最後のファイル変更を確実に処理）
            await asyncio.sleep(2)
            self._stop_watchdog_monitoring()

            # 5. 最終的な結果処理
            await self._process_remaining_lines()

            return {
                'success': scrapy_result['success'],
                'task_id': self.task_id,
                'items_processed': self.processed_lines,
                'scrapy_result': scrapy_result,
                'jsonl_file': str(self.jsonl_file_path)
            }

        except Exception as e:
            self._stop_watchdog_monitoring()
            return {
                'success': False,
                'task_id': self.task_id,
                'error': str(e)
            }

    async def _start_watchdog_monitoring(self):
        """watchdog監視を開始"""
        if not WATCHDOG_AVAILABLE:
            raise Exception("watchdogライブラリが利用できません")

        self.is_monitoring = True

        # JSONLファイルのディレクトリを監視
        watch_directory = self.jsonl_file_path.parent

        # イベントハンドラーを作成
        event_handler = JSONLWatchdogHandler(self)

        # Observerを作成して監視開始
        self.observer = Observer()
        self.observer.schedule(event_handler, str(watch_directory), recursive=False)
        self.observer.start()

        print(f"🔍 watchdog監視開始: {watch_directory}")
        print(f"📄 監視対象ファイル: {self.jsonl_file_path}")

    def _stop_watchdog_monitoring(self):
        """watchdog監視を停止"""
        self.is_monitoring = False

        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

        print(f"🛑 watchdog監視停止: 処理済み行数 {self.processed_lines}")

    async def _execute_scrapy_crawl(self, settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """scrapy crawlコマンドを実行"""
        try:
            # コマンドを構築
            cmd = [
                sys.executable, "-m", "scrapy", "crawl", self.spider_name,
                "-o", str(self.jsonl_file_path),  # JSONLファイル出力
                "-s", "FEED_FORMAT=jsonlines",    # JSONL形式指定
                "-s", "LOG_LEVEL=INFO"
            ]

            # 追加設定があれば適用
            if settings:
                for key, value in settings.items():
                    cmd.extend(["-s", f"{key}={value}"])

            print(f"📋 実行コマンド: {' '.join(cmd)}")
            print(f"📁 実行ディレクトリ: {self.project_path}")

            # 環境変数を設定
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.project_path)

            # プロセスを開始
            self.scrapy_process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            print(f"✅ Scrapyプロセス開始: PID {self.scrapy_process.pid}")

            # プロセス完了を待機
            stdout, stderr = await self.scrapy_process.communicate()

            # 結果を解析
            success = self.scrapy_process.returncode == 0

            result = {
                'success': success,
                'return_code': self.scrapy_process.returncode,
                'stdout': stdout.decode('utf-8', errors='ignore'),
                'stderr': stderr.decode('utf-8', errors='ignore')
            }

            if success:
                print(f"✅ Scrapyプロセス完了")
            else:
                print(f"❌ Scrapyプロセスエラー (code: {self.scrapy_process.returncode})")
                print(f"   stderr: {result['stderr'][:200]}...")

            return result

        except Exception as e:
            print(f"❌ Scrapyプロセス実行エラー: {e}")
            raise

    async def _process_new_lines(self):
        """新しい行を処理（watchdogイベントから呼ばれる）"""
        try:
            if not self.jsonl_file_path.exists():
                return

            # ファイルサイズをチェック
            current_size = self.jsonl_file_path.stat().st_size
            if current_size <= self.last_file_size:
                return

            # 新しい部分のみ読み取り
            with open(self.jsonl_file_path, 'r', encoding='utf-8') as f:
                f.seek(self.last_file_size)
                new_content = f.read()

            # 新しい行を処理
            new_lines = [line.strip() for line in new_content.split('\n') if line.strip()]

            if new_lines:
                print(f"📝 新しい行を検出: {len(new_lines)}件")

                for line in new_lines:
                    await self._process_single_line(line)
                    self.processed_lines += 1

                # WebSocket通知
                if self.websocket_callback:
                    await self.websocket_callback({
                        'type': 'items_update',
                        'task_id': self.task_id,
                        'new_items': len(new_lines),
                        'total_items': self.processed_lines
                    })

            # ファイルサイズを更新
            self.last_file_size = current_size

        except Exception as e:
            print(f"❌ 新しい行処理エラー: {e}")

    async def _process_remaining_lines(self):
        """残りの行を処理（最終処理）"""
        try:
            if not self.jsonl_file_path.exists():
                return

            # ファイル全体を読み直して未処理の行があるかチェック
            with open(self.jsonl_file_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()

            total_lines = len([line for line in all_lines if line.strip()])
            remaining_lines = total_lines - self.processed_lines

            if remaining_lines > 0:
                print(f"📝 残りの行を処理: {remaining_lines}件")

                # 未処理の行を処理
                for i in range(self.processed_lines, total_lines):
                    if i < len(all_lines):
                        line = all_lines[i].strip()
                        if line:
                            await self._process_single_line(line)
                            self.processed_lines += 1

            print(f"✅ 最終処理完了: 総処理行数 {self.processed_lines}")

        except Exception as e:
            print(f"❌ 残り行処理エラー: {e}")

    async def _process_single_line(self, json_line: str):
        """単一の行を処理してDBにインサート"""
        try:
            # JSON解析
            item_data = json.loads(json_line)

            # 非同期でDBインサート
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._sync_insert_item, item_data)

        except json.JSONDecodeError as e:
            print(f"❌ JSON解析エラー: {e} - Line: {json_line[:100]}...")
        except Exception as e:
            print(f"❌ 行処理エラー: {e}")

    def _sync_insert_item(self, item_data: Dict[str, Any]):
        """同期的にDBインサート"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # scraped_itemsテーブルにインサート
            item_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO scraped_items
                (id, task_id, project_id, spider_name, data, scraped_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                self.task_id,
                str(self.project_path.name),  # プロジェクト名をproject_idとして使用
                self.spider_name,
                json.dumps(item_data, ensure_ascii=False),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"❌ DBインサートエラー: {e}")
            raise


# 使用例とテスト
async def test_scrapy_watchdog_monitor():
    """テスト実行"""

    print("🎯 scrapy crawl + watchdog監視テスト")

    # WebSocketコールバック例
    async def websocket_callback(data):
        print(f"📡 WebSocket通知: {data}")

    # 監視クラスを作成
    monitor = ScrapyWatchdogMonitor(
        task_id="test_task_123",
        project_path="scrapy_projects/test_project",  # 実際のプロジェクトパスに変更
        spider_name="test_spider",  # 実際のスパイダー名に変更
        websocket_callback=websocket_callback
    )

    # 実行
    result = await monitor.execute_spider_with_monitoring(
        settings={
            'LOG_LEVEL': 'INFO',
            'ROBOTSTXT_OBEY': False
        }
    )

    print(f"🎉 実行結果: {result}")


if __name__ == "__main__":
    if WATCHDOG_AVAILABLE:
        asyncio.run(test_scrapy_watchdog_monitor())
    else:
        print("❌ watchdogライブラリをインストールしてください: pip install watchdog")
