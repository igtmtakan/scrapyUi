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
import hashlib
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
        self.last_update_time = 0
        self.update_interval = 10.0  # 10秒間隔に緩和

    def on_modified(self, event):
        """ファイル変更時の処理（間隔制限付き）"""
        if event.is_directory:
            return

        # 監視対象のJSONLファイルかチェック
        if event.src_path == str(self.monitor.jsonl_file_path):
            # 更新間隔をチェック（10秒以内の連続更新を制限）
            current_time = time.time()
            if current_time - self.last_update_time < self.update_interval:
                return

            self.last_update_time = current_time

            # 非同期処理をスレッドセーフに実行
            threading.Thread(
                target=self._handle_file_change,
                daemon=True
            ).start()

    def _handle_file_change(self):
        """ファイル変更の処理（進捗表示のみ、DBインサートなし）"""
        try:
            print(f"📝 ファイル変更を検出しました（10秒間隔制限）")
            print(f"📊 watchdog監視で進捗表示を更新します")

            # 新しい行を進捗表示のみ（DBインサートなし）
            if self.monitor.jsonl_file_path.exists():
                current_size = self.monitor.jsonl_file_path.stat().st_size
                print(f"📊 ファイルサイズ更新: {self.monitor.last_file_size} → {current_size}")

                # 新しい部分のみ読み取り
                if current_size > self.monitor.last_file_size:
                    with open(self.monitor.jsonl_file_path, 'r', encoding='utf-8') as f:
                        f.seek(self.monitor.last_file_size)
                        new_content = f.read()

                    # 新しい行を検出（進捗表示のみ）
                    new_lines = [line.strip() for line in new_content.split('\n') if line.strip()]
                    print(f"📝 新しい行を検出: {len(new_lines)}件（進捗表示のみ）")

                    if new_lines:
                        # 進捗カウンターのみ更新（DBインサートなし）
                        self.monitor.processed_lines += len(new_lines)
                        print(f"📊 総処理済みアイテム数: {self.monitor.processed_lines}（進捗表示のみ）")

                self.monitor.last_file_size = current_size

                # WebSocket通知を送信（進捗表示用・頻度制限付き）
                current_time = time.time()
                if (self.monitor.websocket_callback and
                    current_time - self.monitor.last_websocket_time >= self.monitor.websocket_interval):
                    try:
                        import requests
                        response = requests.post(
                            'http://localhost:8000/api/tasks/internal/websocket-notify',
                            json={
                                'type': 'progress_update',
                                'task_id': self.monitor.task_id,
                                'file_lines': self.monitor.processed_lines,
                                'message': 'ファイル更新検出・進捗表示更新'
                            },
                            timeout=5
                        )
                        if response.status_code == 200:
                            self.monitor.last_websocket_time = current_time
                            print(f"📡 WebSocket進捗通知送信完了（15秒間隔制限）")
                    except Exception as ws_error:
                        print(f"📡 WebSocket通知エラー: {ws_error}")
                else:
                    print(f"🔍 WebSocket通知スキップ（15秒間隔制限）")

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

        # WebSocket通知の頻度制限
        self.last_websocket_time = 0
        self.websocket_interval = 15.0  # 15秒間隔に制限
        self.processed_lines = 0
        self.last_file_size = 0

        # JSONLファイルパス
        self.jsonl_file_path = self.project_path / f"results_{task_id}.jsonl"

        # Scrapyプロセス
        self.scrapy_process = None

        # 根本対応: richprogressと同じタスク事前作成
        self._ensure_task_exists_like_richprogress()

    def _generate_data_hash_improved(self, item_data: dict) -> str:
        """item_typeを考慮した改善されたハッシュ生成（全フィールド対応）"""
        try:
            # item_typeに応じて適切なフィールドを選択
            item_type = item_data.get('item_type', 'unknown')

            if item_type == 'ranking_product':
                # ランキング商品の場合
                hash_data = {
                    'item_type': item_type,
                    'ranking_position': item_data.get('ranking_position'),
                    'page_number': item_data.get('page_number'),
                    'title': item_data.get('title'),
                    'product_url': item_data.get('product_url'),
                    'source_url': item_data.get('source_url')
                }
            elif item_type == 'ranking_product_detail':
                # 商品詳細の場合
                hash_data = {
                    'item_type': item_type,
                    'title': item_data.get('title'),
                    'product_url': item_data.get('product_url'),
                    'description': item_data.get('description'),
                    'detail_scraped_at': item_data.get('detail_scraped_at')
                }
            elif item_type == 'test_product':
                # テスト商品の場合
                hash_data = {
                    'item_type': item_type,
                    'title': item_data.get('title'),
                    'price': item_data.get('price'),
                    'test_id': item_data.get('test_id')
                }
            elif item_type == 'test_product_detail':
                # テスト商品詳細の場合
                hash_data = {
                    'item_type': item_type,
                    'title': item_data.get('title'),
                    'description': item_data.get('description'),
                    'test_id': item_data.get('test_id')
                }
            else:
                # その他の場合は全データを使用
                hash_data = item_data.copy()

            # 辞書をソートしてJSON文字列に変換
            hash_string = json.dumps(hash_data, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(hash_string.encode('utf-8')).hexdigest()
        except Exception as e:
            print(f"⚠️ ハッシュ生成エラー: {e}")
            # フォールバック：データ全体のハッシュ
            data_str = json.dumps(item_data, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(data_str.encode('utf-8')).hexdigest()

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
        # watchdog無効化チェック
        if self._is_watchdog_disabled():
            print(f"🛑 Watchdog monitoring is disabled for task {self.task_id}")
            return

        if not WATCHDOG_AVAILABLE:
            raise Exception("watchdogライブラリが利用できません")

        self.is_monitoring = True

        # JSONLファイルのディレクトリを監視
        watch_directory = self.jsonl_file_path.parent

        print(f"🔍 デバッグ情報:")
        print(f"   - プロジェクトパス: {self.project_path}")
        print(f"   - JSONLファイルパス: {self.jsonl_file_path}")
        print(f"   - 監視対象ディレクトリ: {watch_directory}")
        print(f"   - 監視対象ディレクトリ存在: {watch_directory.exists()}")

        # 監視対象ディレクトリが存在するかチェック
        if not watch_directory.exists():
            print(f"⚠️ 監視対象ディレクトリが存在しません: {watch_directory}")
            print(f"📁 ディレクトリを作成します...")
            watch_directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ ディレクトリ作成完了: {watch_directory}")

        # イベントハンドラーを作成
        event_handler = JSONLWatchdogHandler(self)

        # Observerを作成して監視開始
        self.observer = Observer()
        self.observer.schedule(event_handler, str(watch_directory), recursive=False)
        self.observer.start()

        print(f"🔍 watchdog監視開始: {watch_directory}")
        print(f"📄 監視対象ファイル: {self.jsonl_file_path}")

    def _is_watchdog_disabled(self):
        """watchdog監視が無効化されているかチェック"""
        import os

        # 環境変数チェック
        if os.environ.get('SCRAPY_WATCHDOG_DISABLED') == 'true':
            return True

        if os.environ.get(f'SCRAPY_WATCHDOG_DISABLED_{self.task_id}') == 'true':
            return True

        # プロジェクト設定チェック
        try:
            project_dir = Path(self.project_path)
            settings_file = project_dir / 'settings.py'

            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 設定値をチェック
                if 'WATCHDOG_MONITORING_ENABLED = False' in content:
                    return True

                if 'SCRAPY_WATCHDOG_DISABLED = True' in content:
                    return True

        except Exception:
            pass

        return False

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

            # 環境変数を設定（Playwright対応強化）
            env = os.environ.copy()
            env['SCRAPY_TASK_ID'] = self.task_id
            env['SCRAPY_PROJECT_PATH'] = str(self.project_path)
            env['PYTHONPATH'] = str(self.project_path)

            # Playwright環境変数を追加
            env['PLAYWRIGHT_BROWSERS_PATH'] = '0'  # システムブラウザを使用
            env['PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD'] = '1'
            env['DISPLAY'] = ':99'  # 仮想ディスプレイ（必要に応じて）

            # Node.js環境変数（Playwrightに必要）
            env['NODE_OPTIONS'] = '--max-old-space-size=4096'

            # デバッグ用環境変数
            env['DEBUG'] = 'pw:api'  # Playwrightデバッグ有効化

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

            # 推奨対応: richprogressと同じ結果ファイル→DB保存に完全依存
            print(f"🔧 推奨対応: richprogressと同じ結果ファイル→DB保存を実行")
            self._store_results_to_db_like_richprogress()

            # 根本対応: プロセス完了時のタスクステータス更新
            self._update_task_status_on_completion(success, process_success, data_success, result)

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

    def _update_task_status_on_completion(self, success: bool, process_success: bool, data_success: bool, result: Dict[str, Any]):
        """プロセス完了時のタスクステータス更新（根本対応）"""
        try:
            from ..database import SessionLocal, Task, TaskStatus, Result
            from datetime import datetime

            db = SessionLocal()
            try:
                task = db.query(Task).filter(Task.id == self.task_id).first()
                if not task:
                    print(f"⚠️ タスクが見つかりません: {self.task_id}")
                    return

                # 完全統計同期（根本対応）
                actual_db_items = db.query(Result).filter(Result.task_id == self.task_id).count()

                # 結果ファイルからも統計を取得
                file_items_count = 0
                if self.jsonl_file_path and self.jsonl_file_path.exists():
                    try:
                        with open(self.jsonl_file_path, 'r', encoding='utf-8') as f:
                            file_items_count = len([line for line in f if line.strip()])
                    except Exception as file_error:
                        print(f"⚠️ Error reading result file: {file_error}")

                # より多い方を実際のアイテム数とする（完全同期）
                final_items_count = max(actual_db_items, file_items_count, result.get('items_count', 0))
                final_requests_count = max(final_items_count + 5, result.get('requests_count', 1))

                # 完了時刻を設定
                task.finished_at = datetime.now()

                # 根本対応: 正確なステータス判定（完全統計同期版）
                if success and data_success and final_items_count > 0:
                    # データ取得成功 → FINISHED
                    task.status = TaskStatus.FINISHED
                    task.items_count = final_items_count
                    task.requests_count = final_requests_count
                    task.error_count = 0
                    task.error_message = None
                    print(f"🔧 タスクステータス更新: {self.task_id[:8]}... → FINISHED")
                    print(f"   Items: {final_items_count} (DB: {actual_db_items}, File: {file_items_count})")
                    print(f"   Requests: {final_requests_count}")

                elif success and process_success and final_items_count == 0:
                    # 根本対応強化: アイテム数0件は必ずFAILED状態にする
                    task.status = TaskStatus.FAILED
                    task.items_count = 0
                    task.requests_count = 1
                    task.error_count = (task.error_count or 0) + 1
                    task.error_message = "Process completed but no items were collected - marked as FAILED (lightprogress complete sync fix)"
                    print(f"🔧 タスクステータス更新: {self.task_id[:8]}... → FAILED (no items collected - complete sync fix)")

                else:
                    # 失敗 → FAILED
                    task.status = TaskStatus.FAILED
                    task.items_count = final_items_count
                    task.requests_count = final_requests_count
                    task.error_count = (task.error_count or 0) + 1

                    # エラーメッセージを生成
                    error_details = []
                    if not process_success:
                        error_details.append(f"Process failed (code: {result.get('return_code', 'unknown')})")
                    if not data_success:
                        error_details.append("No data collected")
                    if result.get('stderr'):
                        error_details.append(f"Error: {result['stderr'][:200]}")

                    task.error_message = "; ".join(error_details)
                    print(f"🔧 タスクステータス更新: {self.task_id[:8]}... → FAILED ({'; '.join(error_details)})")
                    print(f"   Items: {final_items_count} (DB: {actual_db_items}, File: {file_items_count})")
                    print(f"   Requests: {final_requests_count}")

                task.updated_at = datetime.now()
                db.commit()

            except Exception as e:
                db.rollback()
                print(f"❌ タスクステータス更新エラー: {e}")
            finally:
                db.close()

        except Exception as e:
            print(f"❌ タスクステータス更新エラー: {e}")

    def _store_results_to_db_like_richprogress(self):
        """richprogressと同じ方法で結果ファイルをDBに保存（根本対応）"""
        try:
            import json
            from pathlib import Path
            from ..database import SessionLocal, Result as DBResult
            import uuid
            import hashlib
            from datetime import datetime

            print(f"📁 Starting richprogress-style result storage for task {self.task_id}")

            # 結果ファイルを検索（richprogressと同じパターン）
            possible_paths = []

            # 1. JSONLファイル（最優先）
            if self.jsonl_file_path and self.jsonl_file_path.exists():
                possible_paths.append(self.jsonl_file_path)

            # 2. プロジェクトディレクトリ内の結果ファイルを検索（推奨対応: 拡張パターン）
            project_path = Path(self.project_path)
            patterns = [
                f"results/{self.task_id}.jsonl",
                f"results/{self.task_id}.json",
                f"results/results_{self.task_id}.jsonl",
                f"results_{self.task_id}.jsonl",
                f"results_{self.task_id}.json",
                f"*{self.task_id}*.json",
                f"*{self.task_id}*.jsonl",
                # 推奨対応: Scrapyデフォルト出力ファイルも検索
                "ranking_results.jsonl",
                "items.jsonl",
                "output.jsonl",
                "*.jsonl",
                "*.json"
            ]

            for pattern in patterns:
                files = list(project_path.glob(pattern))
                if files:
                    latest_file = max(files, key=lambda f: f.stat().st_mtime)
                    possible_paths.append(latest_file)
                    break

            # 存在するファイルを見つける
            result_path = None
            for path in possible_paths:
                if path and path.exists() and path.stat().st_size > 0:
                    result_path = path
                    break

            if not result_path:
                print(f"📁 No valid result file found for task {self.task_id}")
                print(f"   Searched paths: {[str(p) for p in possible_paths if p]}")
                return

            print(f"📁 Found result file for task {self.task_id}: {result_path}")

            db = SessionLocal()
            try:
                # 既存のデータをチェック（重複防止）
                existing_count = db.query(DBResult).filter(DBResult.task_id == self.task_id).count()
                if existing_count > 0:
                    print(f"⚠️ Task {self.task_id} already has {existing_count} results in database, skipping to prevent duplicates")
                    return

                with open(result_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                if not content:
                    print(f"📁 Empty result file for task {self.task_id}")
                    return

                stored_count = 0

                # JSONLファイルとして処理（推奨対応: エラー耐性強化）
                if content.count('\n') > 0 or result_path.suffix == '.jsonl':
                    items = content.strip().split('\n')

                    for line_num, line in enumerate(items, 1):
                        line = line.strip()
                        if line:
                            try:
                                item_data = json.loads(line)

                                # データハッシュを生成（richprogressと同じ方法）
                                data_hash = None
                                if isinstance(item_data, dict):
                                    product_url = item_data.get('product_url', '')
                                    ranking_position = item_data.get('ranking_position', '')

                                    if product_url:
                                        data_hash = hashlib.md5(product_url.encode('utf-8')).hexdigest()
                                    elif ranking_position:
                                        data_hash = hashlib.md5(f"pos_{ranking_position}".encode('utf-8')).hexdigest()

                                # 日時フィールドを処理
                                crawl_start_datetime = None
                                item_acquired_datetime = None

                                if isinstance(item_data, dict):
                                    if 'crawl_start_datetime' in item_data:
                                        try:
                                            crawl_start_datetime = datetime.fromisoformat(item_data['crawl_start_datetime'].replace('Z', '+00:00'))
                                        except (ValueError, TypeError):
                                            crawl_start_datetime = datetime.now()

                                    if 'item_acquired_datetime' in item_data:
                                        try:
                                            item_acquired_datetime = datetime.fromisoformat(item_data['item_acquired_datetime'].replace('Z', '+00:00'))
                                        except (ValueError, TypeError):
                                            item_acquired_datetime = datetime.now()

                                # DBに保存（richprogressと同じ方法）
                                db_result = DBResult(
                                    id=str(uuid.uuid4()),
                                    task_id=self.task_id,
                                    data=item_data,
                                    data_hash=data_hash,
                                    created_at=datetime.now(),
                                    crawl_start_datetime=crawl_start_datetime,
                                    item_acquired_datetime=item_acquired_datetime
                                )
                                db.add(db_result)
                                stored_count += 1

                            except json.JSONDecodeError as e:
                                print(f"⚠️ Invalid JSON in result line: {line[:100]}... Error: {e}")
                                continue

                    db.commit()
                    print(f"✅ Stored {stored_count} items (JSONL format) to DB for task {self.task_id} using richprogress method")

                else:
                    # 単一JSONオブジェクトの場合
                    try:
                        data = json.loads(content)

                        if isinstance(data, list):
                            # JSON配列の場合
                            for item in data:
                                # データハッシュを生成
                                data_hash = None
                                if isinstance(item, dict):
                                    product_url = item.get('product_url', '')
                                    if product_url:
                                        data_hash = hashlib.md5(product_url.encode('utf-8')).hexdigest()

                                db_result = DBResult(
                                    id=str(uuid.uuid4()),
                                    task_id=self.task_id,
                                    data=item,
                                    data_hash=data_hash,
                                    created_at=datetime.now(),
                                    item_acquired_datetime=datetime.now()
                                )
                                db.add(db_result)
                                stored_count += 1
                        else:
                            # 単一オブジェクトの場合
                            db_result = DBResult(
                                id=str(uuid.uuid4()),
                                task_id=self.task_id,
                                data=data,
                                created_at=datetime.now(),
                                item_acquired_datetime=datetime.now()
                            )
                            db.add(db_result)
                            stored_count = 1

                        db.commit()
                        print(f"✅ Stored {stored_count} items (JSON format) to DB for task {self.task_id} using richprogress method")

                    except json.JSONDecodeError as e:
                        print(f"❌ Unable to parse result file for task {self.task_id}: {e}")

            finally:
                db.close()

        except Exception as e:
            print(f"❌ Error storing results to DB for task {self.task_id}: {e}")

    def _ensure_task_exists_like_richprogress(self):
        """richprogressと同じ方法でタスクを事前作成（根本対応）"""
        try:
            from ..database import SessionLocal, Task as DBTask, TaskStatus, Project as DBProject, Spider as DBSpider, User as DBUser
            from datetime import datetime
            import pytz

            db = SessionLocal()
            try:
                # タスクの存在確認
                existing_task = db.query(DBTask).filter(DBTask.id == self.task_id).first()

                if existing_task:
                    print(f"✅ Task {self.task_id} already exists")
                    return self.task_id

                print(f"🔧 Creating task like richprogress: {self.task_id}")

                # スパイダーを検索
                spider = db.query(DBSpider).filter(DBSpider.name == self.spider_name).first()
                if not spider:
                    print(f"❌ Spider {self.spider_name} not found in database")
                    return self.task_id

                # プロジェクトを取得
                project = db.query(DBProject).filter(DBProject.id == spider.project_id).first()
                if not project:
                    print(f"❌ Project for spider {self.spider_name} not found")
                    return self.task_id

                # ユーザーを取得（システムユーザー）
                user = db.query(DBUser).first()
                if not user:
                    print(f"❌ No user found in database")
                    return self.task_id

                # タスクを作成（richprogressと同じ方法）
                jst = pytz.timezone('Asia/Tokyo')
                current_time = datetime.now(jst).replace(tzinfo=None)

                new_task = DBTask(
                    id=self.task_id,
                    project_id=project.id,
                    spider_id=spider.id,
                    status=TaskStatus.RUNNING,
                    items_count=0,
                    requests_count=0,
                    error_count=0,
                    created_at=current_time,
                    started_at=current_time,
                    updated_at=current_time,
                    user_id=user.id
                )

                db.add(new_task)
                db.commit()

                print(f"✅ Created task like richprogress: {self.task_id}")
                return self.task_id

            finally:
                db.close()

        except Exception as e:
            print(f"❌ Error creating task like richprogress: {e}")
            return self.task_id

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
                print(f"📝 ファイル変更を検出しました")
                print(f"📊 watchdog監視で進捗表示を更新します")
                print(f"📊 ファイルサイズ更新: {self.last_file_size} → {current_size}")
                print(f"📝 新しい行を検出: {len(new_lines)}件（進捗表示のみ）")

                # 進捗表示のみ（DBインサートは行わない）
                self.processed_lines += len(new_lines)
                print(f"📊 総処理済みアイテム数: {self.processed_lines}（進捗表示のみ）")

                # WebSocket通知（進捗表示のみ・頻度制限付き）
                try:
                    current_time = time.time()
                    if (self.websocket_callback and len(new_lines) > 0 and
                        current_time - self.last_websocket_time >= self.websocket_interval):
                        # 15秒間隔でWebSocket通知を送信
                        self._safe_websocket_notify_threading({
                            'type': 'items_update',
                            'task_id': self.task_id,
                            'new_items': len(new_lines),
                            'total_items': self.processed_lines
                        })
                        self.last_websocket_time = current_time
                        print(f"📡 WebSocket進捗通知送信完了（15秒間隔制限）")
                    else:
                        print(f"🔍 WebSocket通知スキップ: callback={self.websocket_callback is not None}, new_lines={len(new_lines)}, interval_ok={current_time - self.last_websocket_time >= self.websocket_interval}")
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

                # バルクDB挿入処理
                print(f"🔍 バルクDB挿入開始: {len(new_lines)}件")
                successful_inserts = self._bulk_insert_items(new_lines)
                self.processed_lines += successful_inserts
                print(f"✅ バルクDB挿入完了: {successful_inserts}/{len(new_lines)}件")

                print(f"✅ 直接DB挿入完了: {successful_inserts}/{len(new_lines)}件")

                # WebSocket通知（同期的・頻度制限付き）
                print(f"🔍 WebSocket通知開始...")
                try:
                    current_time = time.time()
                    if (self.websocket_callback and successful_inserts > 0 and
                        current_time - self.last_websocket_time >= self.websocket_interval):
                        print(f"🔍 WebSocket通知実行中...")
                        # 15秒間隔でWebSocket通知を送信
                        self._safe_websocket_notify({
                            'type': 'items_update',
                            'task_id': self.task_id,
                            'new_items': successful_inserts,
                            'total_items': self.processed_lines
                        })
                        self.last_websocket_time = current_time
                        print(f"✅ WebSocket通知完了（15秒間隔制限）")
                    else:
                        print(f"🔍 WebSocket通知スキップ: callback={self.websocket_callback is not None}, inserts={successful_inserts}, interval_ok={current_time - self.last_websocket_time >= self.websocket_interval}")
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

                # 未処理の行をバルク処理
                remaining_lines_data = []
                for i in range(self.processed_lines, total_lines):
                    if i < len(all_lines):
                        line = all_lines[i].strip()
                        if line:
                            remaining_lines_data.append(line)

                # バルクDB挿入
                if remaining_lines_data:
                    successful_inserts = self._bulk_insert_items(remaining_lines_data)
                    self.processed_lines += successful_inserts
                    print(f"✅ 残り行バルクDB挿入完了: {successful_inserts}/{len(remaining_lines_data)}件")
                else:
                    successful_inserts = 0

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
                    # データハッシュを生成（改善版：item_type考慮）
                    data_hash = self._generate_data_hash_improved(item_data)

                    # 重複チェック
                    if data_hash:
                        existing = db.query(Result).filter(
                            Result.task_id == self.task_id,
                            Result.data_hash == data_hash
                        ).first()
                        if existing:
                            print(f"⚠️ 重複データをスキップ: {data_hash}")
                            return True  # 重複は成功とみなす

                    # resultsテーブルにインサート
                    result_id = str(uuid.uuid4())
                    db_result = Result(
                        id=result_id,
                        task_id=self.task_id,
                        data=item_data,
                        data_hash=data_hash,  # ハッシュ値を追加
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
                    # データハッシュを生成（改善版：item_type考慮）
                    data_hash = self._generate_data_hash_improved(item_data)

                    # 重複チェック
                    if data_hash:
                        existing = db.query(Result).filter(
                            Result.task_id == self.task_id,
                            Result.data_hash == data_hash
                        ).first()
                        if existing:
                            print(f"⚠️ 重複データをスキップ: {data_hash}")
                            return True  # 重複は成功とみなす

                    # resultsテーブルにインサート
                    result_id = str(uuid.uuid4())
                    db_result = Result(
                        id=result_id,
                        task_id=self.task_id,
                        data=item_data,
                        data_hash=data_hash,  # ハッシュ値を追加
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

    def _realtime_insert_item_threading(self, line: str) -> bool:
        """リアルタイムDB挿入（threading版・1件ずつ処理）"""
        if not line.strip():
            return False

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                from ..database import SessionLocal, Result
                import json
                import uuid
                import hashlib
                from datetime import datetime

                # JSON解析
                try:
                    item_data = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON解析エラー: {e}")
                    return False

                # データハッシュ生成（改善版：item_type考慮）
                data_hash = self._generate_data_hash_improved(item_data)

                db = SessionLocal()
                try:
                    # 重複チェック
                    if data_hash:
                        existing = db.query(Result).filter(
                            Result.task_id == self.task_id,
                            Result.data_hash == data_hash
                        ).first()

                        if existing:
                            print(f"⚠️ 重複データをスキップ: {data_hash[:8]}...")
                            return False

                    # 新しいレコードを作成
                    result_id = str(uuid.uuid4())
                    new_result = Result(
                        id=result_id,
                        task_id=self.task_id,
                        data=item_data,
                        data_hash=data_hash,
                        item_acquired_datetime=datetime.now(),
                        created_at=datetime.now()
                    )

                    db.add(new_result)
                    db.commit()

                    print(f"✅ リアルタイムDB挿入成功: {result_id[:8]}...")
                    return True

                except Exception as e:
                    db.rollback()
                    print(f"❌ リアルタイムDB挿入エラー: {e}")
                    raise
                finally:
                    db.close()

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"❌ リアルタイムDB挿入最終失敗: {e}")
                    return False
                else:
                    import time
                    time.sleep(0.1 * retry_count)

        return False

    def _realtime_insert_item(self, line: str) -> bool:
        """リアルタイムDB挿入（通常版・1件ずつ処理）"""
        if not line.strip():
            return False

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                from ..database import SessionLocal, Result
                import json
                import uuid
                import hashlib
                from datetime import datetime

                # JSON解析
                try:
                    item_data = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON解析エラー: {e}")
                    return False

                # データハッシュ生成（改善版：item_type考慮）
                data_hash = self._generate_data_hash_improved(item_data)

                db = SessionLocal()
                try:
                    # 重複チェック
                    if data_hash:
                        existing = db.query(Result).filter(
                            Result.task_id == self.task_id,
                            Result.data_hash == data_hash
                        ).first()

                        if existing:
                            print(f"⚠️ 重複データをスキップ: {data_hash[:8]}...")
                            return False

                    # 新しいレコードを作成
                    result_id = str(uuid.uuid4())
                    new_result = Result(
                        id=result_id,
                        task_id=self.task_id,
                        data=item_data,
                        data_hash=data_hash,
                        item_acquired_datetime=datetime.now(),
                        created_at=datetime.now()
                    )

                    db.add(new_result)
                    db.commit()

                    print(f"✅ リアルタイムDB挿入成功: {result_id[:8]}...")
                    return True

                except Exception as e:
                    db.rollback()
                    print(f"❌ リアルタイムDB挿入エラー: {e}")
                    raise
                finally:
                    db.close()

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"❌ リアルタイムDB挿入最終失敗: {e}")
                    return False
                else:
                    import time
                    time.sleep(0.1 * retry_count)

        return False

    def _bulk_insert_items_threading(self, lines: List[str]) -> int:
        """バルクDB挿入（threading版）"""
        if not lines:
            return 0

        max_retries = 3
        retry_count = 0
        batch_size = 100  # バッチサイズ

        while retry_count < max_retries:
            try:
                from ..database import SessionLocal, Result

                # JSON解析とデータ準備
                items_data = []
                for line in lines:
                    try:
                        item_data = json.loads(line.strip())
                        items_data.append(item_data)
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON解析エラー: {e} - Line: {line[:50]}...")
                        continue

                if not items_data:
                    print("❌ 有効なJSONデータがありません")
                    return 0

                successful_inserts = 0

                # バッチごとに処理
                for i in range(0, len(items_data), batch_size):
                    batch = items_data[i:i + batch_size]

                    db = SessionLocal()
                    try:
                        # バルクインサート用のデータを準備（軽量重複チェック付き）
                        bulk_data = []

                        for item_data in batch:
                            # データハッシュを生成（改善版：item_type考慮）
                            data_hash = self._generate_data_hash_improved(item_data)

                            if not data_hash:
                                print(f"⚠️ ハッシュ生成失敗: {item_data}")
                                continue

                            # 軽量重複チェック（同一タスク内のみ）
                            existing = db.query(Result).filter(
                                Result.task_id == self.task_id,
                                Result.data_hash == data_hash
                            ).first()

                            if existing:
                                print(f"⚠️ 重複データをスキップ: {data_hash[:8]}...")
                                continue

                            result_id = str(uuid.uuid4())
                            bulk_item = {
                                'id': result_id,
                                'task_id': self.task_id,
                                'data': item_data,
                                'data_hash': data_hash,
                                'item_acquired_datetime': datetime.now(),
                                'created_at': datetime.now()
                            }
                            bulk_data.append(bulk_item)

                        # 高速バルクインサート実行（重複チェック済み）
                        if bulk_data:
                            print(f"🚀 高速バルクインサート実行: {len(bulk_data)}件（重複チェック済み）")

                            for item in bulk_data:
                                try:
                                    db_result = Result(
                                        id=item['id'],
                                        task_id=item['task_id'],
                                        data=item['data'],
                                        data_hash=item['data_hash'],
                                        item_acquired_datetime=item['item_acquired_datetime'],
                                        created_at=item['created_at']
                                    )
                                    db.add(db_result)
                                except Exception as e:
                                    print(f"❌ インサートエラー: {e}")
                                    continue

                            db.commit()
                            print(f"✅ 高速バルクインサート完了: {len(bulk_data)}件（重複チェック済み）")
                        else:
                            print("⚠️ バルクデータが空のためスキップ（重複除外後）")

                        successful_inserts += len(batch)
                        print(f"✅ バルクDBインサート成功: {len(batch)}件 (累計: {successful_inserts}/{len(items_data)}) - Thread: {threading.current_thread().name}")

                    except Exception as e:
                        db.rollback()
                        print(f"❌ バルクDBインサートエラー (バッチ {i//batch_size + 1}): {e}")
                        # バッチが失敗した場合は個別に処理（重複チェックなし）
                        for item_data in batch:
                            try:
                                # データハッシュを生成（改善版：item_type考慮）
                                data_hash = self._generate_data_hash_improved(item_data)

                                result_id = str(uuid.uuid4())
                                db_result = Result(
                                    id=result_id,
                                    task_id=self.task_id,
                                    data=item_data,
                                    data_hash=data_hash,
                                    item_acquired_datetime=datetime.now(),
                                    created_at=datetime.now()
                                )
                                db.add(db_result)
                                db.commit()
                                successful_inserts += 1
                            except Exception as individual_error:
                                db.rollback()
                                print(f"❌ 個別インサートエラー: {individual_error}")
                    finally:
                        db.close()

                # タスク統計を更新
                if successful_inserts > 0:
                    self._update_task_statistics_threading()

                print(f"✅ バルクDBインサート完了: {successful_inserts}/{len(items_data)}件 - Thread: {threading.current_thread().name}")
                return successful_inserts

            except Exception as e:
                retry_count += 1
                print(f"❌ バルクDBインサートエラー (試行 {retry_count}/{max_retries}): {e}")

                if retry_count >= max_retries:
                    print(f"❌ バルクDBインサート最終失敗: {e}")
                    return 0
                else:
                    import time
                    time.sleep(0.1 * retry_count)

        return 0

    def _bulk_insert_items(self, lines: List[str]) -> int:
        """バルクDB挿入（通常版）"""
        if not lines:
            return 0

        max_retries = 3
        retry_count = 0
        batch_size = 100  # バッチサイズ

        while retry_count < max_retries:
            try:
                from ..database import SessionLocal, Result

                # JSON解析とデータ準備
                items_data = []
                for line in lines:
                    try:
                        item_data = json.loads(line.strip())
                        items_data.append(item_data)
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON解析エラー: {e} - Line: {line[:50]}...")
                        continue

                if not items_data:
                    print("❌ 有効なJSONデータがありません")
                    return 0

                successful_inserts = 0

                # バッチごとに処理
                for i in range(0, len(items_data), batch_size):
                    batch = items_data[i:i + batch_size]

                    db = SessionLocal()
                    try:
                        # バルクインサート用のデータを準備（軽量重複チェック付き）
                        bulk_data = []

                        for item_data in batch:
                            # データハッシュを生成（改善版：item_type考慮）
                            data_hash = self._generate_data_hash_improved(item_data)

                            if not data_hash:
                                print(f"⚠️ ハッシュ生成失敗: {item_data}")
                                continue

                            # 軽量重複チェック（同一タスク内のみ）
                            existing = db.query(Result).filter(
                                Result.task_id == self.task_id,
                                Result.data_hash == data_hash
                            ).first()

                            if existing:
                                print(f"⚠️ 重複データをスキップ: {data_hash[:8]}...")
                                continue

                            result_id = str(uuid.uuid4())
                            bulk_data.append({
                                'id': result_id,
                                'task_id': self.task_id,
                                'data': item_data,
                                'data_hash': data_hash,
                                'item_acquired_datetime': datetime.now(),
                                'created_at': datetime.now()
                            })

                        # 高速バルクインサート実行（重複チェック済み）
                        if bulk_data:
                            print(f"🚀 高速バルクインサート実行: {len(bulk_data)}件（重複チェック済み）")

                            db.bulk_insert_mappings(Result, bulk_data)
                            db.commit()
                        else:
                            print("⚠️ バルクデータが空のためスキップ（重複除外後）")

                        successful_inserts += len(batch)
                        print(f"✅ バルクDBインサート成功: {len(batch)}件 (累計: {successful_inserts}/{len(items_data)})")

                    except Exception as e:
                        db.rollback()
                        print(f"❌ バルクDBインサートエラー (バッチ {i//batch_size + 1}): {e}")
                        # バッチが失敗した場合は個別に処理（重複チェックなし）
                        for item_data in batch:
                            try:
                                # データハッシュを生成（改善版：item_type考慮）
                                data_hash = self._generate_data_hash_improved(item_data)

                                result_id = str(uuid.uuid4())
                                db_result = Result(
                                    id=result_id,
                                    task_id=self.task_id,
                                    data=item_data,
                                    data_hash=data_hash,
                                    item_acquired_datetime=datetime.now(),
                                    created_at=datetime.now()
                                )
                                db.add(db_result)
                                db.commit()
                                successful_inserts += 1
                            except Exception as individual_error:
                                db.rollback()
                                print(f"❌ 個別インサートエラー: {individual_error}")
                    finally:
                        db.close()

                # タスク統計を更新
                if successful_inserts > 0:
                    self._update_task_statistics_safe()

                print(f"✅ バルクDBインサート完了: {successful_inserts}/{len(items_data)}件")
                return successful_inserts

            except Exception as e:
                retry_count += 1
                print(f"❌ バルクDBインサートエラー (試行 {retry_count}/{max_retries}): {e}")

                if retry_count >= max_retries:
                    print(f"❌ バルクDBインサート最終失敗: {e}")
                    return 0
                else:
                    import time
                    time.sleep(0.1 * retry_count)

        return 0

    def _update_task_statistics(self, db):
        """タスク統計を更新"""
        try:
            from ..database import Task, Result

            # タスクを取得
            task = db.query(Task).filter(Task.id == self.task_id).first()
            if task:
                # 結果数を取得
                result_count = db.query(Result).filter(Result.task_id == self.task_id).count()

                # タスク統計を更新（リクエスト数の正常化）
                task.items_count = result_count

                # リクエスト数の正常化（異常に大きい値を防止）
                estimated_normal_requests = result_count + 20  # アイテム数 + 初期リクエスト数
                current_requests = task.requests_count or 0

                if current_requests <= estimated_normal_requests * 2:
                    # 現在値が正常範囲内の場合はそのまま
                    pass
                else:
                    # 異常に大きい場合は推定値に修正
                    task.requests_count = estimated_normal_requests
                    print(f"⚠️ Watchdog: Abnormal request count detected for task {self.task_id}, corrected to {estimated_normal_requests}")

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

                    # タスク統計を更新（重複防止：最大値のみ更新）
                    task.items_count = max(result_count, task.items_count or 0)

                    # リクエスト数は推定値と現在値の最大値
                    estimated_requests = result_count + 15
                    task.requests_count = max(estimated_requests, task.requests_count or 0)

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
        """安全なタスク統計更新（強化版）"""
        try:
            from ..database import SessionLocal, Task, Result
            from .task_statistics_validator import task_validator

            db = SessionLocal()
            try:
                # タスクを取得
                task = db.query(Task).filter(Task.id == self.task_id).first()
                if task:
                    # 結果数を取得
                    result_count = db.query(Result).filter(Result.task_id == self.task_id).count()

                    # ファイルベースの統計も確認
                    file_items, file_requests = task_validator._get_file_statistics(task)

                    # より正確な統計を使用
                    final_items = max(result_count, file_items, task.items_count or 0)
                    final_requests = max(file_requests, result_count + 15, task.requests_count or 0)

                    # タスク統計を更新
                    task.items_count = final_items
                    task.requests_count = final_requests

                    # ステータスの自動修正（根本対応版）
                    from ..database import TaskStatus

                    # 正確なステータス判定ロジック
                    if final_items > 0:
                        # データ取得成功 → FINISHED
                        if task.status.name in ['FAILED', 'RUNNING']:
                            task.status = TaskStatus.FINISHED
                            task.error_count = 0
                            print(f"🔧 Status corrected: {self.task_id[:8]}... {task.status.name} → FINISHED (items: {final_items})")
                    else:
                        # データ取得失敗 → FAILED
                        if task.status.name in ['FINISHED', 'RUNNING']:
                            task.status = TaskStatus.FAILED
                            task.error_count = task.error_count + 1 if task.error_count else 1
                            task.error_message = f"No items collected. Requests: {final_requests}, Duration: {(task.finished_at - task.started_at).total_seconds() if task.started_at and task.finished_at else 'unknown'}s"
                            print(f"🔧 Status corrected: {self.task_id[:8]}... {task.status.name} → FAILED (no items collected)")

                    task.updated_at = datetime.now()

                    db.commit()
                    print(f"📊 Enhanced task statistics updated: {self.task_id[:8]}... - Items: {final_items}, Requests: {final_requests}")

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
