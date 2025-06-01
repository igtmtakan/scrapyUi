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
        """ファイル変更の処理（重複防止のためDB挿入無効化）"""
        try:
            print(f"📝 ファイル変更を検出しました")
            print(f"ℹ️ DB挿入はcrawlwithwatchdogコマンドが処理するため、watchdog監視では実行しません")

            # ファイルサイズのみ更新（DB挿入は行わない）
            if self.monitor.jsonl_file_path.exists():
                current_size = self.monitor.jsonl_file_path.stat().st_size
                print(f"📊 ファイルサイズ更新: {self.monitor.last_file_size} → {current_size}")
                self.monitor.last_file_size = current_size

                # 行数をカウント
                with open(self.monitor.jsonl_file_path, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
                    self.monitor.processed_lines = len(lines)
                    print(f"📊 現在の行数: {len(lines)}行")

                # WebSocket通知のみ送信（DB挿入なし）
                if self.monitor.websocket_callback:
                    try:
                        import requests
                        response = requests.post(
                            'http://localhost:8000/api/tasks/internal/websocket-notify',
                            json={
                                'type': 'file_update',
                                'task_id': self.monitor.task_id,
                                'file_lines': len(lines),
                                'message': 'ファイル更新検出（DB挿入はcrawlwithwatchdogが処理）'
                            },
                            timeout=5
                        )
                        if response.status_code == 200:
                            print(f"📡 WebSocket通知送信完了")
                    except Exception as ws_error:
                        print(f"📡 WebSocket通知エラー: {ws_error}")

        except Exception as e:
            print(f"❌ ファイル変更処理エラー: {e}")
            import traceback
            print(f"❌ ファイル変更処理エラー詳細: {traceback.format_exc()}")


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

            # 最終的な成功判定：プロセス成功 OR データ取得成功
            final_success = scrapy_result['success'] or (self.processed_lines > 0)

            return {
                'success': final_success,
                'process_success': scrapy_result.get('process_success', scrapy_result['success']),
                'data_success': self.processed_lines > 0,
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
        """scrapy crawlwithwatchdogコマンドを実行（DB挿入機能付き）"""
        try:
            # コマンドを構築（crawlwithwatchdogを使用）
            cmd = [
                sys.executable, "-m", "scrapy", "crawlwithwatchdog", self.spider_name,
                "-o", str(self.jsonl_file_path),  # JSONLファイル出力
                "--task-id", self.task_id,        # タスクIDを指定
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

            # 結果を解析（改善版：データ取得状況も考慮）
            process_success = self.scrapy_process.returncode == 0
            data_success = self.processed_lines > 0

            # 最終的な成功判定：プロセス成功 OR データ取得成功
            success = process_success or data_success

            result = {
                'success': success,
                'process_success': process_success,
                'data_success': data_success,
                'return_code': self.scrapy_process.returncode,
                'processed_lines': self.processed_lines,
                'stdout': stdout.decode('utf-8', errors='ignore'),
                'stderr': stderr.decode('utf-8', errors='ignore')
            }

            if success:
                if process_success and data_success:
                    print(f"✅ Scrapyプロセス完了（プロセス成功 + データ取得: {self.processed_lines}件）")
                elif data_success:
                    print(f"✅ Scrapyプロセス完了（データ取得成功: {self.processed_lines}件、プロセスコード: {self.scrapy_process.returncode}）")
                    print(f"🔍 プロセス失敗原因調査 - stderr: {result['stderr'][:500]}")
                    print(f"🔍 プロセス失敗原因調査 - stdout: {result['stdout'][-500:]}")
                else:
                    print(f"✅ Scrapyプロセス完了（プロセス成功、データ: {self.processed_lines}件）")
            else:
                print(f"❌ Scrapyプロセス失敗 (code: {self.scrapy_process.returncode}, データ: {self.processed_lines}件)")
                print(f"🔍 完全失敗 - stderr: {result['stderr']}")
                print(f"🔍 完全失敗 - stdout: {result['stdout']}")

                # 失敗原因の詳細分析
                self._analyze_failure_cause(result)

            return result

        except Exception as e:
            print(f"❌ Scrapyプロセス実行エラー: {e}")
            raise

    def _analyze_failure_cause(self, result: Dict[str, Any]):
        """Scrapyプロセス失敗原因を分析"""
        try:
            print(f"🔍 === Scrapyプロセス失敗原因分析開始 ===")
            print(f"リターンコード: {result['return_code']}")

            stderr = result['stderr']
            stdout = result['stdout']

            # 一般的な失敗パターンを分析
            failure_patterns = {
                'ImportError': 'モジュールのインポートエラー',
                'ModuleNotFoundError': 'モジュールが見つからない',
                'AttributeError': '属性エラー',
                'SyntaxError': 'シンタックスエラー',
                'IndentationError': 'インデントエラー',
                'NameError': '名前エラー',
                'TypeError': '型エラー',
                'ValueError': '値エラー',
                'ConnectionError': '接続エラー',
                'TimeoutError': 'タイムアウトエラー',
                'PermissionError': '権限エラー',
                'FileNotFoundError': 'ファイルが見つからない',
                'twisted.internet.error': 'Twistedエラー',
                'scrapy.exceptions': 'Scrapyエラー',
                'playwright': 'Playwrightエラー',
                'ERROR': '一般的なエラー',
                'CRITICAL': '重大なエラー',
                'Traceback': 'Python例外',
                'Exception': '例外発生'
            }

            detected_issues = []
            for pattern, description in failure_patterns.items():
                if pattern in stderr or pattern in stdout:
                    detected_issues.append(f"{description} ({pattern})")

            if detected_issues:
                print(f"🔍 検出された問題:")
                for issue in detected_issues:
                    print(f"   - {issue}")
            else:
                print(f"🔍 既知のパターンに該当しない失敗")

            # リターンコード別の分析
            return_code_meanings = {
                1: "一般的なエラー",
                2: "シェルの誤用",
                126: "実行権限なし",
                127: "コマンドが見つからない",
                128: "無効な終了引数",
                130: "Ctrl+Cによる中断",
                137: "SIGKILL (強制終了)",
                139: "セグメンテーション違反"
            }

            if result['return_code'] in return_code_meanings:
                print(f"🔍 リターンコード {result['return_code']}: {return_code_meanings[result['return_code']]}")

            print(f"🔍 === 失敗原因分析完了 ===")

        except Exception as e:
            print(f"❌ 失敗原因分析エラー: {e}")

    def _process_new_lines_threading(self):
        """新しい行を処理（threading版・asyncio完全回避）"""
        import threading
        print(f"🧵 _process_new_lines_threading開始: {threading.current_thread().name}")
        try:
            if not self.jsonl_file_path.exists():
                print(f"❌ ファイルが存在しません: {self.jsonl_file_path}")
                return

            # ファイルサイズをチェック
            current_size = self.jsonl_file_path.stat().st_size
            print(f"🔍 ファイルサイズ: 現在={current_size}, 前回={self.last_file_size}")
            if current_size <= self.last_file_size:
                print(f"🔍 新しいデータなし")
                return

            # 新しい部分のみ読み取り
            print(f"🔍 新しい内容を読み取り中...")
            with open(self.jsonl_file_path, 'r', encoding='utf-8') as f:
                f.seek(self.last_file_size)
                new_content = f.read()

            # 新しい行を処理
            new_lines = [line.strip() for line in new_content.split('\n') if line.strip()]
            print(f"🔍 新しい行数: {len(new_lines)}")

            if new_lines:
                print(f"📝 新しい行を検出: {len(new_lines)}件")

                # 直接DB挿入処理（threading版・asyncio完全回避）
                successful_inserts = 0
                print(f"🔍 直接DB挿入処理開始: {len(new_lines)}件の新しい行")

                for i, line in enumerate(new_lines):
                    print(f"🔍 処理中 {i+1}/{len(new_lines)}: {line[:50]}...")
                    try:
                        # JSON解析
                        item_data = json.loads(line.strip())
                        print(f"🔍 JSON解析成功: {item_data.get('title', 'N/A')[:30]}...")

                        # 直接DB挿入（threading版）
                        print(f"🔍 DB挿入開始...")
                        insert_result = self._sync_insert_item_threading(item_data)
                        if insert_result:
                            successful_inserts += 1
                            print(f"✅ DB挿入成功: {successful_inserts}件目")
                        else:
                            print(f"❌ DB挿入失敗: {successful_inserts}件目")

                        self.processed_lines += 1

                    except json.JSONDecodeError as e:
                        print(f"❌ JSON解析エラー: {e} - Line: {line[:100]}...")
                    except Exception as e:
                        print(f"❌ 行処理エラー: {e}")
                        import traceback
                        print(f"❌ 行処理エラー詳細: {traceback.format_exc()}")

                print(f"✅ 直接DB挿入完了: {successful_inserts}/{len(new_lines)}件")

                # WebSocket通知（threading版・同期的）
                print(f"🔍 WebSocket通知開始...")
                try:
                    if self.websocket_callback and successful_inserts > 0:
                        print(f"🔍 WebSocket通知実行中...")
                        # 同期的にWebSocket通知を送信
                        self._safe_websocket_notify_threading({
                            'type': 'items_update',
                            'task_id': self.task_id,
                            'new_items': successful_inserts,
                            'total_items': self.processed_lines
                        })
                        print(f"✅ WebSocket通知完了")
                    else:
                        print(f"🔍 WebSocket通知スキップ: callback={self.websocket_callback is not None}, inserts={successful_inserts}")
                except Exception as ws_error:
                    print(f"📡 WebSocket通知エラー: {ws_error}")
                    import traceback
                    print(f"📡 WebSocket通知エラー詳細: {traceback.format_exc()}")

            # ファイルサイズを更新
            print(f"🔍 ファイルサイズ更新: {current_size}")
            self.last_file_size = current_size
            print(f"✅ _process_new_lines_threading完了")

        except Exception as e:
            print(f"❌ 新しい行処理エラー: {e}")
            import traceback
            print(f"❌ エラー詳細: {traceback.format_exc()}")

    async def _process_new_lines(self):
        """新しい行を処理（完全同期版）"""
        # asyncラッパーを削除し、直接同期処理を実行
        print(f"🔍 _process_new_lines開始（完全同期版）")
        try:
            if not self.jsonl_file_path.exists():
                print(f"❌ ファイルが存在しません: {self.jsonl_file_path}")
                return

            # ファイルサイズをチェック
            current_size = self.jsonl_file_path.stat().st_size
            print(f"🔍 ファイルサイズ: 現在={current_size}, 前回={self.last_file_size}")
            if current_size <= self.last_file_size:
                print(f"🔍 新しいデータなし")
                return

            # 新しい部分のみ読み取り
            print(f"🔍 新しい内容を読み取り中...")
            with open(self.jsonl_file_path, 'r', encoding='utf-8') as f:
                f.seek(self.last_file_size)
                new_content = f.read()

            # 新しい行を処理
            new_lines = [line.strip() for line in new_content.split('\n') if line.strip()]
            print(f"🔍 新しい行数: {len(new_lines)}")

            if new_lines:
                print(f"📝 新しい行を検出: {len(new_lines)}件")

                # 直接DB挿入処理（Celeryタスクを使わない）
                successful_inserts = 0
                print(f"🔍 直接DB挿入処理開始: {len(new_lines)}件の新しい行")

                for i, line in enumerate(new_lines):
                    print(f"🔍 処理中 {i+1}/{len(new_lines)}: {line[:50]}...")
                    try:
                        # JSON解析
                        item_data = json.loads(line.strip())
                        print(f"🔍 JSON解析成功: {item_data.get('title', 'N/A')[:30]}...")

                        # 直接DB挿入
                        print(f"🔍 DB挿入開始...")
                        insert_result = self._sync_insert_item(item_data)
                        if insert_result:
                            successful_inserts += 1
                            print(f"✅ DB挿入成功: {successful_inserts}件目")
                        else:
                            print(f"❌ DB挿入失敗: {successful_inserts}件目")

                        self.processed_lines += 1

                    except json.JSONDecodeError as e:
                        print(f"❌ JSON解析エラー: {e} - Line: {line[:100]}...")
                    except Exception as e:
                        print(f"❌ 行処理エラー: {e}")
                        import traceback
                        print(f"❌ 行処理エラー詳細: {traceback.format_exc()}")

                print(f"✅ 直接DB挿入完了: {successful_inserts}/{len(new_lines)}件")

                # WebSocket通知（同期的に）
                print(f"🔍 WebSocket通知開始...")
                try:
                    if self.websocket_callback and successful_inserts > 0:
                        print(f"🔍 WebSocket通知実行中...")
                        # 同期的にWebSocket通知を送信
                        self._safe_websocket_notify({
                            'type': 'items_update',
                            'task_id': self.task_id,
                            'new_items': successful_inserts,
                            'total_items': self.processed_lines
                        })
                        print(f"✅ WebSocket通知完了")
                    else:
                        print(f"🔍 WebSocket通知スキップ: callback={self.websocket_callback is not None}, inserts={successful_inserts}")
                except Exception as ws_error:
                    print(f"📡 WebSocket通知エラー: {ws_error}")
                    import traceback
                    print(f"📡 WebSocket通知エラー詳細: {traceback.format_exc()}")

            # ファイルサイズを更新
            print(f"🔍 ファイルサイズ更新: {current_size}")
            self.last_file_size = current_size
            print(f"✅ _process_new_lines完了（完全同期版）")

        except Exception as e:
            print(f"❌ 新しい行処理エラー: {e}")
            import traceback
            print(f"❌ エラー詳細: {traceback.format_exc()}")

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

                # 未処理の行を同期的に処理
                successful_inserts = 0
                for i in range(self.processed_lines, total_lines):
                    if i < len(all_lines):
                        line = all_lines[i].strip()
                        if line:
                            try:
                                # JSON解析
                                item_data = json.loads(line)

                                # 同期的にDBインサート
                                self._sync_insert_item(item_data)
                                successful_inserts += 1
                                self.processed_lines += 1

                            except json.JSONDecodeError as e:
                                print(f"❌ JSON解析エラー: {e} - Line: {line[:100]}...")
                            except Exception as e:
                                print(f"❌ 行処理エラー: {e}")

                print(f"✅ 残り行DB挿入完了: {successful_inserts}/{remaining_lines}件")

            print(f"✅ 最終処理完了: 総処理行数 {self.processed_lines}")

        except Exception as e:
            print(f"❌ 残り行処理エラー: {e}")

    def _sync_insert_item_threading(self, item_data: Dict[str, Any]):
        """同期的にDBインサート（threading版・asyncio完全回避）"""
        import threading
        max_retries = 3
        retry_count = 0

        print(f"🧵 DB挿入開始: {threading.current_thread().name}")

        while retry_count < max_retries:
            try:
                # SQLAlchemyを使用してDBインサート
                from ..database import SessionLocal, Result

                db = SessionLocal()
                try:
                    # resultsテーブルにインサート
                    result_id = str(uuid.uuid4())
                    db_result = Result(
                        id=result_id,
                        task_id=self.task_id,
                        data=item_data,
                        item_acquired_datetime=datetime.now(),
                        created_at=datetime.now()
                    )

                    db.add(db_result)
                    db.commit()

                    print(f"✅ DBインサート成功: {result_id[:8]}... (試行: {retry_count + 1}) - Thread: {threading.current_thread().name}")

                    # タスク統計を更新（threading版）
                    self._update_task_statistics_threading()

                    return True  # 成功

                except Exception as e:
                    db.rollback()
                    retry_count += 1
                    print(f"❌ DBインサートエラー (試行 {retry_count}/{max_retries}): {e}")

                    if retry_count >= max_retries:
                        raise
                    else:
                        # 短時間待機してリトライ
                        import time
                        time.sleep(0.1 * retry_count)

                finally:
                    db.close()

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"❌ DBインサート最終失敗: {e}")
                    return False

        return False

    def _sync_insert_item(self, item_data: Dict[str, Any]):
        """同期的にDBインサート（強化版）"""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # SQLAlchemyを使用してDBインサート
                from ..database import SessionLocal, Result

                db = SessionLocal()
                try:
                    # resultsテーブルにインサート
                    result_id = str(uuid.uuid4())
                    db_result = Result(
                        id=result_id,
                        task_id=self.task_id,
                        data=item_data,
                        item_acquired_datetime=datetime.now(),
                        created_at=datetime.now()
                    )

                    db.add(db_result)
                    db.commit()

                    print(f"✅ DBインサート成功: {result_id[:8]}... (試行: {retry_count + 1})")

                    # タスク統計を更新（別のトランザクションで）
                    self._update_task_statistics_safe()

                    return True  # 成功

                except Exception as e:
                    db.rollback()
                    retry_count += 1
                    print(f"❌ DBインサートエラー (試行 {retry_count}/{max_retries}): {e}")

                    if retry_count >= max_retries:
                        raise
                    else:
                        # 短時間待機してリトライ
                        import time
                        time.sleep(0.1 * retry_count)

                finally:
                    db.close()

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"❌ DBインサート最終失敗: {e}")
                    return False

        return False

    def _update_task_statistics(self, db):
        """タスク統計を更新"""
        try:
            from ..database import Task, Result

            # タスクを取得
            task = db.query(Task).filter(Task.id == self.task_id).first()
            if task:
                # 結果数を取得
                result_count = db.query(Result).filter(Result.task_id == self.task_id).count()

                # タスク統計を更新
                task.items_count = result_count
                task.updated_at = datetime.now()

                db.commit()
                print(f"📊 タスク統計更新: {self.task_id} - アイテム数: {result_count}")

        except Exception as e:
            print(f"❌ タスク統計更新エラー: {e}")

    def _update_task_statistics_threading(self):
        """安全なタスク統計更新（threading版）"""
        import threading
        try:
            from ..database import SessionLocal, Task, Result

            print(f"🧵 タスク統計更新開始: {threading.current_thread().name}")
            db = SessionLocal()
            try:
                # タスクを取得
                task = db.query(Task).filter(Task.id == self.task_id).first()
                if task:
                    # 結果数を取得
                    result_count = db.query(Result).filter(Result.task_id == self.task_id).count()

                    # タスク統計を更新
                    task.items_count = result_count
                    task.updated_at = datetime.now()

                    db.commit()
                    print(f"📊 タスク統計更新: {self.task_id[:8]}... - アイテム数: {result_count} - Thread: {threading.current_thread().name}")

            except Exception as e:
                db.rollback()
                print(f"❌ タスク統計更新エラー: {e}")
            finally:
                db.close()

        except Exception as e:
            print(f"❌ タスク統計更新エラー: {e}")

    def _update_task_statistics_safe(self):
        """安全なタスク統計更新（別のセッションで）"""
        try:
            from ..database import SessionLocal, Task, Result

            db = SessionLocal()
            try:
                # タスクを取得
                task = db.query(Task).filter(Task.id == self.task_id).first()
                if task:
                    # 結果数を取得
                    result_count = db.query(Result).filter(Result.task_id == self.task_id).count()

                    # タスク統計を更新
                    task.items_count = result_count
                    task.updated_at = datetime.now()

                    db.commit()
                    print(f"📊 タスク統計更新: {self.task_id[:8]}... - アイテム数: {result_count}")

            except Exception as e:
                db.rollback()
                print(f"❌ タスク統計更新エラー: {e}")
            finally:
                db.close()

        except Exception as e:
            print(f"❌ タスク統計更新エラー: {e}")

    def _safe_websocket_notify_threading(self, data: Dict[str, Any]):
        """安全なWebSocket通知（threading版）"""
        import threading
        try:
            if not self.websocket_callback:
                return

            print(f"🧵 WebSocket通知開始: {threading.current_thread().name}")

            # HTTPリクエストでWebSocket通知を送信
            import requests

            # バックエンドのWebSocket通知エンドポイントを呼び出し
            response = requests.post(
                'http://localhost:8000/api/tasks/internal/websocket-notify',
                json=data,
                timeout=5
            )

            if response.status_code == 200:
                print(f"📡 WebSocket notification sent: Task {data.get('task_id', 'unknown')[:8]}... - {data.get('type', 'unknown')} - Thread: {threading.current_thread().name}")
            else:
                print(f"📡 WebSocket notification failed: {response.status_code}")

        except Exception as e:
            print(f"📡 WebSocket通知エラー: {e}")

    def _safe_websocket_notify(self, data: Dict[str, Any]):
        """安全なWebSocket通知（同期的）"""
        try:
            if not self.websocket_callback:
                return

            # HTTPリクエストでWebSocket通知を送信
            import requests

            # バックエンドのWebSocket通知エンドポイントを呼び出し
            response = requests.post(
                'http://localhost:8000/api/tasks/internal/websocket-notify',
                json=data,
                timeout=5
            )

            if response.status_code == 200:
                print(f"📡 WebSocket notification sent: Task {data.get('task_id', 'unknown')[:8]}... - {data.get('type', 'unknown')}")
            else:
                print(f"📡 WebSocket notification failed: {response.status_code}")

        except Exception as e:
            print(f"📡 WebSocket通知エラー: {e}")


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
