"""
ScrapyUI Rich Progress Extension

Scrapyスパイダーにrichライブラリを使用した美しい進捗バーを追加する拡張機能
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from scrapy import signals
from scrapy.crawler import Crawler
from scrapy.spiders import Spider
from scrapy.http import Request, Response
from scrapy.exceptions import NotConfigured
import pytz
from datetime import datetime

# 動的パス追加（根本対応）
def _setup_dynamic_imports():
    """Rich Progress Extension用の動的インポート設定"""
    try:
        # 環境変数からパスを取得
        scrapyui_root = os.environ.get('SCRAPYUI_ROOT')
        scrapyui_backend = os.environ.get('SCRAPYUI_BACKEND')

        if scrapyui_root and scrapyui_root not in sys.path:
            sys.path.insert(0, scrapyui_root)
            print(f"🔧 [RICH] Added SCRAPYUI_ROOT to sys.path: {scrapyui_root}")

        if scrapyui_backend and scrapyui_backend not in sys.path:
            sys.path.insert(0, scrapyui_backend)
            print(f"🔧 [RICH] Added SCRAPYUI_BACKEND to sys.path: {scrapyui_backend}")

        # 現在のディレクトリから推測
        current_file = Path(__file__).absolute()
        backend_path = current_file.parent.parent.parent  # backend/app/scrapy_extensions/../../../ = backend
        scrapyui_path = backend_path.parent  # backend/../ = scrapyui root

        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))
            print(f"🔧 [RICH] Added backend path to sys.path: {backend_path}")

        if str(scrapyui_path) not in sys.path:
            sys.path.insert(0, str(scrapyui_path))
            print(f"🔧 [RICH] Added scrapyui path to sys.path: {scrapyui_path}")

        print(f"🔧 [RICH] Current sys.path: {sys.path[:5]}...")  # 最初の5つだけ表示

    except Exception as e:
        print(f"⚠️ [RICH] Dynamic import setup error: {e}")

# 動的インポート設定を実行
_setup_dynamic_imports()

# タイムゾーン設定
TIMEZONE = pytz.timezone('Asia/Tokyo')

try:
    from rich.progress import Progress, TaskID, BarColumn, TextColumn, TimeRemainingColumn, SpinnerColumn
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class RichProgressExtension:
    """
    Scrapyスパイダー用Rich進捗バー拡張機能
    
    Features:
    - 美しい進捗バー表示
    - リアルタイム統計情報
    - カスタマイズ可能な表示形式
    - WebSocket経由での進捗通知（オプション）
    """
    
    def __init__(self, crawler: Crawler):
        if not RICH_AVAILABLE:
            raise NotConfigured("Rich library is not installed. Run: pip install rich")

        self.crawler = crawler
        self.settings = crawler.settings

        # Rich進捗バー設定
        self.console = Console()
        self.progress = None
        self.live = None
        self.task_id: Optional[TaskID] = None

        # 統計情報
        self.stats = {
            'requests_count': 0,
            'responses_count': 0,
            'items_count': 0,
            'errors_count': 0,
            'start_time': None,
            'finish_time': None,
            'total_urls': 0
        }

        # 統計ファイルパス
        self.stats_file = None
        self.task_id_str = None

        # 設定
        self.enabled = self.settings.getbool('RICH_PROGRESS_ENABLED', True)
        self.show_stats = self.settings.getbool('RICH_PROGRESS_SHOW_STATS', True)
        self.update_interval = self.settings.getfloat('RICH_PROGRESS_UPDATE_INTERVAL', 2.0)  # 2秒間隔に緩和
        self.websocket_enabled = self.settings.getbool('RICH_PROGRESS_WEBSOCKET', False)

        if not self.enabled:
            raise NotConfigured("Rich progress bar is disabled")
    
    @classmethod
    def from_crawler(cls, crawler: Crawler):
        """Crawlerからインスタンスを作成"""
        # Rich Progress WebSocketが無効化されている場合はNoneを返す
        if not crawler.settings.getbool('RICH_PROGRESS_WEBSOCKET', True):
            return None

        extension = cls(crawler)

        # シグナルを接続（根本修正版）
        try:
            # 基本シグナルを接続
            crawler.signals.connect(extension.spider_opened, signal=signals.spider_opened)
            crawler.signals.connect(extension.spider_closed, signal=signals.spider_closed)
            crawler.signals.connect(extension.request_scheduled, signal=signals.request_scheduled)
            crawler.signals.connect(extension.response_received, signal=signals.response_received)
            crawler.signals.connect(extension.item_scraped, signal=signals.item_scraped)
            crawler.signals.connect(extension.spider_error, signal=signals.spider_error)

            # 統計更新用の追加シグナルも接続
            try:
                crawler.signals.connect(extension.request_reached_downloader, signal=signals.request_reached_downloader)
                crawler.signals.connect(extension.response_downloaded, signal=signals.response_downloaded)
            except AttributeError:
                # 一部のシグナルが存在しない場合は無視
                pass

            print("🔧 Rich Progress Extension signals connected successfully")
        except Exception as e:
            print(f"❌ Failed to connect Rich Progress Extension signals: {e}")

        return extension
    
    def spider_opened(self, spider: Spider):
        """スパイダー開始時の処理"""
        self.stats['start_time'] = time.time()

        # タスクIDを取得（複数の方法で試行）
        self.task_id_str = (
            os.environ.get('SCRAPY_TASK_ID') or
            getattr(self.crawler, 'task_id', None) or
            getattr(spider, 'task_id', None) or
            f"task_{int(time.time())}"
        )

        # スパイダーにtask_idを設定（確実に利用可能にする）
        if not hasattr(spider, 'task_id'):
            spider.task_id = self.task_id_str

        # プロジェクトパスを設定（複数の方法で試行）
        project_path = (
            os.environ.get('SCRAPY_PROJECT_PATH') or
            getattr(spider, 'project_path', None) or
            str(Path.cwd())
        )

        # スパイダーにproject_pathを設定
        if not hasattr(spider, 'project_path'):
            spider.project_path = project_path

        # 統計ファイルパスを設定
        project_dir = Path(project_path)
        self.stats_file = project_dir / f"stats_{self.task_id_str}.json"

        # start_urlsの数を取得
        if hasattr(spider, 'start_urls'):
            self.stats['total_urls'] = len(spider.start_urls)

        # 初期統計ファイルを作成
        self._save_stats()

        # Rich進捗バーを初期化
        self._initialize_progress(spider)

        spider.logger.info(f"🎨 Rich進捗バー開始: {spider.name}")
        spider.logger.info(f"📊 統計ファイル: {self.stats_file}")
        spider.logger.info(f"🔧 Task ID: {self.task_id_str}")
        spider.logger.info(f"📁 Project path: {project_path}")
    
    def spider_closed(self, spider: Spider, reason: str):
        """スパイダー終了時の処理"""
        print(f"🔥 [RICH PROGRESS] spider_closed called with reason: {reason}")
        spider.logger.info(f"🔥 [RICH PROGRESS] spider_closed called with reason: {reason}")

        # 終了時刻を記録
        self.stats['finish_time'] = time.time()

        # Scrapyの統計情報と同期
        self._sync_with_scrapy_stats()

        # 最終統計ファイルを保存
        self._save_stats()

        # タスクIDを確実に取得（複数の方法で試行）
        task_id = (
            getattr(spider, 'task_id', None) or
            self.task_id_str or
            os.environ.get('SCRAPY_TASK_ID')
        )

        print(f"🔥 [RICH PROGRESS] Task ID found: {task_id}")
        spider.logger.info(f"🎯 Spider closed with reason '{reason}' - Task ID: {task_id}")

        # 完了通知とバルクインサート発動（理由に関係なく実行）
        if task_id:
            print(f"🔥 [RICH PROGRESS] Starting bulk insert for task: {task_id}")
            spider.logger.info(f"🚀 Triggering Rich progress completion for task {task_id}")

            # スパイダーにtask_idを設定（念のため）
            if not hasattr(spider, 'task_id'):
                spider.task_id = task_id

            # Rich progress完了通知でバルクインサートを発動
            try:
                self._trigger_bulk_insert_on_completion(spider)
                print(f"🔥 [RICH PROGRESS] Bulk insert completed for task: {task_id}")
            except Exception as e:
                print(f"🔥 [RICH PROGRESS] Bulk insert error: {e}")
                spider.logger.error(f"❌ Rich progress bulk insert error: {e}")
        else:
            print(f"🔥 [RICH PROGRESS] No task ID found - skipping bulk insert")
            spider.logger.warning("🔍 Task ID not found - skipping Rich progress completion")
            spider.logger.warning(f"🔍 Debug info: spider.task_id={getattr(spider, 'task_id', None)}, self.task_id_str={self.task_id_str}, env={os.environ.get('SCRAPY_TASK_ID')}")

        if self.live:
            self.live.stop()

        if self.progress:
            self.progress.stop()

        # 最終統計を表示
        self._show_final_stats(spider, reason)
        print(f"🔥 [RICH PROGRESS] spider_closed completed")

    def _trigger_bulk_insert_on_completion(self, spider):
        """Rich progress完了通知でバルクインサートを発動"""
        try:
            print(f"🔥 [RICH PROGRESS] _trigger_bulk_insert_on_completion started")

            task_id = getattr(spider, 'task_id', None)
            if not task_id:
                print(f"🔥 [RICH PROGRESS] Task ID not found - skipping bulk insert")
                spider.logger.warning("🔍 Task ID not found - skipping bulk insert")
                return

            print(f"🔥 [RICH PROGRESS] Task ID found: {task_id}")
            spider.logger.info(f"🚀 Rich progress completion triggered - starting bulk insert for task {task_id}")

            # プロジェクトパスを取得
            project_path = getattr(spider, 'project_path', None)
            if not project_path:
                # 現在のディレクトリから推測
                import os
                project_path = os.getcwd()

            print(f"🔥 [RICH PROGRESS] Project path: {project_path}")
            spider.logger.info(f"📁 Project path: {project_path}")

            # JSONLファイルパスを構築（複数のパターンを試行）
            from pathlib import Path

            # 可能なファイル名パターン（resultsディレクトリ内を優先）
            possible_files = [
                # 新しい形式（results/ディレクトリ内）
                f"results/{task_id}.jsonl",
                f"results/{task_id}.json",
                f"results/results_{task_id}.jsonl",
                # 従来の形式（プロジェクトルート）
                f"results_{task_id}.jsonl",
                f"{task_id}.jsonl",
                f"ranking_results.jsonl",
                f"{spider.name}_results.jsonl"
            ]

            print(f"🔥 [RICH PROGRESS] Checking possible files: {possible_files}")

            jsonl_file_path = None
            for filename in possible_files:
                file_path = Path(project_path) / filename
                print(f"🔥 [RICH PROGRESS] Checking: {file_path} (exists: {file_path.exists()})")
                if file_path.exists():
                    jsonl_file_path = file_path
                    print(f"🔥 [RICH PROGRESS] ✅ Found result file: {file_path}")
                    break

            if not jsonl_file_path:
                print(f"🔥 [RICH PROGRESS] No JSONL file found in any pattern")
                spider.logger.warning(f"📄 No JSONL file found for task {task_id}")
                return

            print(f"🔥 [RICH PROGRESS] Found JSONL file: {jsonl_file_path}")
            spider.logger.info(f"📄 Found JSONL file: {jsonl_file_path}")

            # ファイルサイズと行数を確認
            file_size = jsonl_file_path.stat().st_size
            with open(jsonl_file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]

            print(f"🔥 [RICH PROGRESS] File size: {file_size} bytes, Lines: {len(lines)}")
            spider.logger.info(f"📊 File size: {file_size} bytes, Lines: {len(lines)}")

            if len(lines) == 0:
                print(f"🔥 [RICH PROGRESS] No data lines found in JSONL file")
                spider.logger.warning("📄 No data lines found in JSONL file")
                return

            # バルクインサート実行
            print(f"🔥 [RICH PROGRESS] Starting _execute_bulk_insert")
            self._execute_bulk_insert(task_id, lines, spider)
            print(f"🔥 [RICH PROGRESS] _execute_bulk_insert completed")

        except Exception as e:
            print(f"🔥 [RICH PROGRESS] Error in _trigger_bulk_insert_on_completion: {e}")
            spider.logger.error(f"❌ Bulk insert trigger error: {e}")
            import traceback
            print(f"🔥 [RICH PROGRESS] Traceback: {traceback.format_exc()}")
            spider.logger.error(f"❌ Traceback: {traceback.format_exc()}")

    def _execute_bulk_insert(self, task_id: str, lines: list, spider):
        """JSONLファイル全体をバルクインサート（根本対応版）"""
        try:
            spider.logger.info(f"🔄 Starting JSONL bulk insert for {len(lines)} lines")

            # タスクの存在確認と作成（根本対応）
            task_id = self._ensure_task_exists(task_id, spider)

            # 直接バルクインサートを実行
            inserted_count = self._bulk_insert_from_jsonl_lines(task_id, lines, spider)

            spider.logger.info(f"✅ JSONL bulk insert completed: {inserted_count}/{len(lines)} items inserted")

            # 念のため重複クリーンアップを実行
            spider.logger.info(f"🧹 Starting post-insert duplicate cleanup for task {task_id}")
            cleanup_result = self._cleanup_duplicate_records(task_id, spider)

            # WebSocket通知を送信
            self._send_completion_websocket_notification(task_id, inserted_count, spider, cleanup_result)

        except Exception as e:
            spider.logger.error(f"❌ JSONL bulk insert execution error: {e}")
            import traceback
            spider.logger.error(f"❌ Traceback: {traceback.format_exc()}")

    def _bulk_insert_from_jsonl_lines(self, task_id: str, lines: list, spider) -> int:
        """JSONLファイルの行からバルクインサート（重複チェック付き）"""
        try:
            from ..database import SessionLocal, Result
            import json
            import uuid
            import hashlib
            from datetime import datetime

            spider.logger.info(f"📊 Processing {len(lines)} JSONL lines for bulk insert")

            # JSONLファイルの行を解析
            items_data = []
            for line_num, line in enumerate(lines, 1):
                try:
                    if line.strip():
                        item_data = json.loads(line.strip())
                        items_data.append(item_data)
                except json.JSONDecodeError as e:
                    spider.logger.warning(f"⚠️ JSON decode error at line {line_num}: {e}")

            if not items_data:
                spider.logger.warning(f"⚠️ No valid items found in JSONL lines")
                return 0

            spider.logger.info(f"📦 Found {len(items_data)} valid items in JSONL lines")

            # バルクインサート実行（重複チェック付き）
            db = SessionLocal()
            try:
                bulk_data = []
                skipped_count = 0

                for item_data in items_data:
                    # データハッシュを生成
                    data_hash = self._generate_data_hash(item_data)

                    # 重複チェック（同一タスク内）
                    existing = db.query(Result).filter(
                        Result.task_id == task_id,
                        Result.data_hash == data_hash
                    ).first()

                    if existing:
                        skipped_count += 1
                        spider.logger.debug(f"⚠️ Duplicate data skipped: {data_hash[:8]}...")
                        continue

                    result_id = str(uuid.uuid4())
                    bulk_data.append({
                        'id': result_id,
                        'task_id': task_id,
                        'data': item_data,
                        'data_hash': data_hash,
                        'item_acquired_datetime': datetime.now(TIMEZONE),
                        'created_at': datetime.now(TIMEZONE)
                    })

                # バルクインサート実行
                inserted_count = 0
                if bulk_data:
                    db.bulk_insert_mappings(Result, bulk_data)
                    db.commit()
                    inserted_count = len(bulk_data)
                    spider.logger.info(f"✅ Bulk insert completed: {inserted_count} items inserted, {skipped_count} duplicates skipped")
                else:
                    spider.logger.info(f"⚠️ No new data to insert, {skipped_count} duplicates skipped")

                # タスクのアイテム数を更新
                self._update_task_item_count(task_id, db, spider)

                return inserted_count

            except Exception as e:
                db.rollback()
                spider.logger.error(f"❌ Bulk insert error: {e}")
                raise
            finally:
                db.close()

        except Exception as e:
            spider.logger.error(f"❌ Bulk insert from JSONL lines error: {e}")
            return 0

    def _generate_data_hash(self, item_data: dict) -> str:
        """データハッシュを生成"""
        try:
            import json
            import hashlib

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
            else:
                # その他の場合は全データを使用
                hash_data = item_data.copy()

            # 辞書をソートしてJSON文字列に変換
            hash_string = json.dumps(hash_data, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(hash_string.encode('utf-8')).hexdigest()
        except Exception as e:
            # フォールバック：データ全体のハッシュ
            data_str = json.dumps(item_data, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(data_str.encode('utf-8')).hexdigest()

    def _update_task_item_count(self, task_id: str, db, spider):
        """タスクのアイテム数を更新"""
        try:
            from ..database import Task, Result
            from datetime import datetime

            # タスクを取得
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                # 結果数を取得
                result_count = db.query(Result).filter(Result.task_id == task_id).count()

                # タスクのアイテム数を更新
                task.items_count = result_count
                task.updated_at = datetime.now(TIMEZONE)

                db.commit()
                spider.logger.info(f"📊 Task item count updated: {result_count} items")

        except Exception as e:
            spider.logger.error(f"❌ Task item count update error: {e}")

    def _cleanup_duplicate_records(self, task_id: str, spider):
        """重複レコードのクリーンアップを実行"""
        try:
            spider.logger.info(f"🧹 Starting duplicate cleanup for task {task_id}")

            from ..database import get_db, Result as DBResult
            from sqlalchemy import func

            # データベース接続
            db_gen = get_db()
            db = next(db_gen)

            try:
                # クリーンアップ前の件数を確認
                before_count = db.query(DBResult).filter(DBResult.task_id == task_id).count()
                spider.logger.info(f"📊 Before cleanup: {before_count} records")

                # 重複レコードを特定（data_hashが同じものを検索）
                duplicate_subquery = (
                    db.query(DBResult.data_hash)
                    .filter(DBResult.task_id == task_id)
                    .group_by(DBResult.data_hash)
                    .having(func.count(DBResult.data_hash) > 1)
                    .subquery()
                )

                # 重複グループごとに最新のレコード以外を削除
                duplicates_to_delete = []
                duplicate_hashes = db.query(duplicate_subquery.c.data_hash).all()

                spider.logger.info(f"🔍 Found {len(duplicate_hashes)} duplicate hash groups")

                for (hash_value,) in duplicate_hashes:
                    # 同じハッシュを持つレコードを取得（作成日時順）
                    duplicate_records = (
                        db.query(DBResult)
                        .filter(DBResult.task_id == task_id)
                        .filter(DBResult.data_hash == hash_value)
                        .order_by(DBResult.created_at.desc())
                        .all()
                    )

                    # 最新のレコード以外を削除対象に追加
                    if len(duplicate_records) > 1:
                        records_to_delete = duplicate_records[1:]  # 最新以外
                        duplicates_to_delete.extend(records_to_delete)

                        spider.logger.info(f"🗑️ Hash {hash_value[:8]}...: keeping 1, deleting {len(records_to_delete)} duplicates")

                # 重複レコードを削除
                deleted_count = 0
                if duplicates_to_delete:
                    for record in duplicates_to_delete:
                        db.delete(record)
                        deleted_count += 1

                    db.commit()
                    spider.logger.info(f"✅ Deleted {deleted_count} duplicate records")
                else:
                    spider.logger.info(f"✅ No duplicate records found to delete")

                # クリーンアップ後の件数を確認
                after_count = db.query(DBResult).filter(DBResult.task_id == task_id).count()
                spider.logger.info(f"📊 After cleanup: {after_count} records")

                # 結果をまとめる
                cleanup_result = {
                    'before_count': before_count,
                    'after_count': after_count,
                    'deleted_count': deleted_count,
                    'duplicate_groups': len(duplicate_hashes)
                }

                spider.logger.info(f"🧹 Cleanup completed: {before_count} → {after_count} (-{deleted_count})")

                return cleanup_result

            finally:
                db.close()

        except Exception as e:
            spider.logger.error(f"❌ Duplicate cleanup error: {e}")
            import traceback
            spider.logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return {
                'before_count': 0,
                'after_count': 0,
                'deleted_count': 0,
                'duplicate_groups': 0,
                'error': str(e)
            }

    def _send_completion_websocket_notification(self, task_id: str, items_inserted: int, spider, cleanup_result=None):
        """完了通知のWebSocket送信"""
        try:
            # WebSocket通知データを作成
            completion_data = {
                'taskId': task_id,
                'status': 'completed',
                'itemsScraped': items_inserted,
                'requestsCount': self.stats['requests_count'],
                'errorCount': self.stats['errors_count'],
                'elapsedTime': int(self.stats.get('finish_time', time.time()) - self.stats.get('start_time', time.time())),
                'progressPercentage': 100.0,
                'message': f'Rich progress completed - {items_inserted} items bulk inserted',
                'bulkInsertCompleted': True
            }

            # クリーンアップ結果を追加
            if cleanup_result:
                completion_data.update({
                    'cleanupCompleted': True,
                    'cleanupResult': cleanup_result,
                    'finalItemCount': cleanup_result.get('after_count', items_inserted),
                    'duplicatesRemoved': cleanup_result.get('deleted_count', 0)
                })

                # メッセージを更新
                deleted_count = cleanup_result.get('deleted_count', 0)
                if deleted_count > 0:
                    completion_data['message'] = f'Rich progress completed - {items_inserted} items inserted, {deleted_count} duplicates removed'
                else:
                    completion_data['message'] = f'Rich progress completed - {items_inserted} items inserted, no duplicates found'

            spider.logger.info(f"📡 Sending completion WebSocket notification: {completion_data}")

            # WebSocket送信（非同期）
            import asyncio
            from ..api.websocket_progress import broadcast_rich_progress_update

            try:
                # 非同期でWebSocket送信
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(
                        broadcast_rich_progress_update(task_id, completion_data)
                    )
                else:
                    loop.run_until_complete(
                        broadcast_rich_progress_update(task_id, completion_data)
                    )
                spider.logger.info("📡 Completion WebSocket notification sent successfully")
            except Exception as ws_error:
                spider.logger.warning(f"📡 WebSocket notification failed: {ws_error}")

        except Exception as e:
            spider.logger.error(f"❌ Completion notification error: {e}")

    def _ensure_task_exists(self, task_id: str, spider) -> str:
        """タスクの存在確認と作成（根本対応）"""
        try:
            from ..database import SessionLocal, Task
            from datetime import datetime

            db = SessionLocal()
            try:
                # タスクの存在確認
                existing_task = db.query(Task).filter(Task.id == task_id).first()

                if existing_task:
                    spider.logger.info(f"✅ Task {task_id} already exists")
                    return task_id

                # タスクが存在しない場合は作成
                spider.logger.warning(f"⚠️ Task {task_id} not found, creating new task")

                new_task = Task(
                    id=task_id,
                    spider_name=spider.name,
                    project_name=getattr(spider, 'project_name', 'unknown'),
                    status='RUNNING',
                    items_count=0,
                    requests_count=0,
                    errors_count=0,
                    created_at=datetime.now(TIMEZONE),
                    started_at=datetime.now(TIMEZONE),
                    updated_at=datetime.now(TIMEZONE)
                )

                db.add(new_task)
                db.commit()

                spider.logger.info(f"✅ Created new task: {task_id}")
                return task_id

            finally:
                db.close()

        except Exception as e:
            spider.logger.error(f"❌ Task creation error: {e}")
            # フォールバック：元のタスクIDを返す
            return task_id

    def request_scheduled(self, request, spider):
        """リクエスト送信時の処理（根本修正版）"""
        try:
            # 統計を直接更新
            self.stats['requests_count'] += 1
            spider.logger.debug(f"📤 Request scheduled: {self.stats['requests_count']}")

            # Scrapyの統計システムから実際の値を取得して同期
            self._sync_with_scrapy_stats()
            self._update_progress()
            self._save_stats()
        except Exception as e:
            spider.logger.error(f"❌ Error in request_scheduled: {e}")

    def request_reached_downloader(self, request, spider):
        """リクエストがダウンローダーに到達した時の処理（追加シグナル）"""
        try:
            spider.logger.debug(f"🔄 Request reached downloader: {request.url}")
            self._sync_with_scrapy_stats()
            self._update_progress()
        except Exception as e:
            spider.logger.error(f"❌ Error in request_reached_downloader: {e}")

    def response_received(self, response, request, spider):
        """レスポンス受信時の処理（根本修正版）"""
        try:
            # 統計を直接更新
            self.stats['responses_count'] += 1
            spider.logger.debug(f"📥 Response received: {self.stats['responses_count']}")

            # Scrapyの統計システムから実際の値を取得して同期
            self._sync_with_scrapy_stats()
            self._update_progress()
            self._save_stats()
        except Exception as e:
            spider.logger.error(f"❌ Error in response_received: {e}")

    def response_downloaded(self, response, request, spider):
        """レスポンスダウンロード完了時の処理（追加シグナル）"""
        try:
            spider.logger.debug(f"✅ Response downloaded: {response.url}")
            self._sync_with_scrapy_stats()
            self._update_progress()
        except Exception as e:
            spider.logger.error(f"❌ Error in response_downloaded: {e}")

    def item_scraped(self, item, response, spider):
        """アイテム取得時の処理（根本修正版）"""
        try:
            # 統計を直接更新
            self.stats['items_count'] += 1
            spider.logger.debug(f"📦 Item scraped: {self.stats['items_count']}")

            # Scrapyの統計システムから実際の値を取得して同期
            self._sync_with_scrapy_stats()
            self._update_progress()
            self._save_stats()
        except Exception as e:
            spider.logger.error(f"❌ Error in item_scraped: {e}")

    def spider_error(self, failure, response, spider):
        """エラー発生時の処理（根本修正版）"""
        try:
            # 統計を直接更新
            self.stats['errors_count'] += 1
            spider.logger.debug(f"❌ Error occurred: {self.stats['errors_count']}")

            # Scrapyの統計システムから実際の値を取得して同期
            self._sync_with_scrapy_stats()
            self._update_progress()
            self._save_stats()
        except Exception as e:
            spider.logger.error(f"❌ Error in spider_error: {e}")

    def _sync_with_scrapy_stats(self):
        """Scrapyの統計システムと同期（根本修正版）"""
        try:
            if hasattr(self, 'crawler') and hasattr(self.crawler, 'stats'):
                scrapy_stats = self.crawler.stats.get_stats()

                # Scrapyの統計から実際の値を取得
                scrapy_requests = scrapy_stats.get('downloader/request_count', 0)
                scrapy_responses = scrapy_stats.get('downloader/response_count', 0)
                scrapy_items = scrapy_stats.get('item_scraped_count', 0)
                scrapy_errors = scrapy_stats.get('spider_exceptions', 0)

                # 統計を同期（Scrapyの値を優先）
                if scrapy_requests > 0:
                    self.stats['requests_count'] = scrapy_requests
                if scrapy_responses > 0:
                    self.stats['responses_count'] = scrapy_responses
                if scrapy_items > 0:
                    self.stats['items_count'] = scrapy_items
                if scrapy_errors > 0:
                    self.stats['errors_count'] = scrapy_errors

                print(f"🔄 Stats synced - R:{scrapy_requests}, Res:{scrapy_responses}, I:{scrapy_items}, E:{scrapy_errors}")

        except Exception as e:
            print(f"❌ Error syncing with Scrapy stats: {e}")
    
    def _initialize_progress(self, spider: Spider):
        """Rich進捗バーを初期化"""
        # カスタム進捗バーカラム
        columns = [
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TextColumn("[bold green]{task.completed}/{task.total}"),
            TextColumn("•"),
            TimeRemainingColumn(),
        ]
        
        self.progress = Progress(*columns, console=self.console)
        
        # タスクを追加
        total = max(self.stats['total_urls'], 1)  # 最低1に設定
        self.task_id = self.progress.add_task(
            f"🕷️ {spider.name}",
            total=total
        )
        
        if self.show_stats:
            # ライブ表示でテーブルと進捗バーを組み合わせ（リフレッシュレートを緩和）
            self.live = Live(self._create_layout(), console=self.console, refresh_per_second=2)
            self.live.start()
        else:
            self.progress.start()
    
    def _create_layout(self):
        """表示レイアウトを作成"""
        # 統計テーブル
        stats_table = Table(title="📊 スクレイピング統計", show_header=True, header_style="bold magenta")
        stats_table.add_column("項目", style="cyan", width=15)
        stats_table.add_column("値", style="green", width=10)
        
        # 経過時間を計算
        elapsed_time = 0
        if self.stats['start_time']:
            import time
            elapsed_time = time.time() - self.stats['start_time']
        
        # 統計データを追加
        stats_table.add_row("📤 リクエスト", str(self.stats['requests_count']))
        stats_table.add_row("📥 レスポンス", str(self.stats['responses_count']))
        stats_table.add_row("📦 アイテム", str(self.stats['items_count']))
        stats_table.add_row("❌ エラー", str(self.stats['errors_count']))
        stats_table.add_row("⏱️ 経過時間", f"{elapsed_time:.1f}秒")
        
        # 速度計算
        if elapsed_time > 0:
            items_per_sec = self.stats['items_count'] / elapsed_time
            stats_table.add_row("🚀 処理速度", f"{items_per_sec:.2f} items/sec")
        
        # レイアウトを組み合わせ
        layout = Table.grid()
        layout.add_row(Panel(self.progress, title="🎯 進捗状況", border_style="blue"))
        layout.add_row(Panel(stats_table, title="📈 詳細統計", border_style="green"))
        
        return layout
    
    def _update_progress(self):
        """進捗バーを更新"""
        if not self.progress or not self.task_id:
            return
        
        # 進捗を更新（アイテム数ベース）
        completed = self.stats['items_count']
        
        # 動的に総数を調整（リクエスト数が初期予想を超えた場合）
        if self.stats['requests_count'] > self.stats['total_urls']:
            total = max(self.stats['requests_count'], self.stats['total_urls'])
            self.progress.update(self.task_id, total=total)
        
        self.progress.update(self.task_id, completed=completed)
        
        # WebSocket通知（オプション）
        if self.websocket_enabled:
            self._send_websocket_update()
    
    def _send_websocket_update(self):
        """WebSocket経由で進捗を通知"""
        try:
            # 経過時間を計算
            elapsed_time = 0
            if self.stats['start_time']:
                import time
                elapsed_time = time.time() - self.stats['start_time']

            # 速度計算
            items_per_second = 0
            requests_per_second = 0
            if elapsed_time > 0:
                items_per_second = self.stats['items_count'] / elapsed_time
                requests_per_second = self.stats['requests_count'] / elapsed_time

            # WebSocket通知データを作成
            progress_data = {
                'taskId': getattr(self.crawler, 'task_id', 'unknown'),
                'status': 'running',
                'itemsScraped': self.stats['items_count'],
                'requestsCount': self.stats['requests_count'],
                'errorCount': self.stats['errors_count'],
                'elapsedTime': int(elapsed_time),
                'progressPercentage': self._calculate_progress_percentage(),
                'itemsPerSecond': round(items_per_second, 2),
                'requestsPerSecond': round(requests_per_second, 2),
                'totalPages': self.stats['total_urls'],
                'currentPage': self.stats['responses_count']
            }

            # ScrapyUIのWebSocketマネージャーに送信
            try:
                import asyncio
                from ..api.websocket_progress import broadcast_rich_progress_update

                # 非同期でWebSocket送信
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(
                        broadcast_rich_progress_update(
                            progress_data['taskId'],
                            progress_data
                        )
                    )
                else:
                    loop.run_until_complete(
                        broadcast_rich_progress_update(
                            progress_data['taskId'],
                            progress_data
                        )
                    )
            except Exception as ws_error:
                # WebSocket送信エラーは無視（進捗バー表示に影響しないように）
                pass

        except Exception as e:
            # WebSocket送信エラーは無視（進捗バー表示に影響しないように）
            pass
    
    def _calculate_progress_percentage(self) -> float:
        """進捗率を計算"""
        if self.stats['total_urls'] == 0:
            return 0.0
        
        # アイテム数ベースで計算
        return min(100.0, (self.stats['items_count'] / self.stats['total_urls']) * 100)
    
    def _show_final_stats(self, spider: Spider, reason: str):
        """最終統計を表示"""
        import time
        
        elapsed_time = 0
        if self.stats['start_time']:
            elapsed_time = time.time() - self.stats['start_time']
        
        # 最終レポート
        final_table = Table(title=f"🏁 {spider.name} 完了レポート", show_header=True, header_style="bold yellow")
        final_table.add_column("項目", style="cyan", width=20)
        final_table.add_column("値", style="green", width=15)
        
        final_table.add_row("📤 総リクエスト数", str(self.stats['requests_count']))
        final_table.add_row("📥 総レスポンス数", str(self.stats['responses_count']))
        final_table.add_row("📦 総アイテム数", str(self.stats['items_count']))
        final_table.add_row("❌ エラー数", str(self.stats['errors_count']))
        final_table.add_row("⏱️ 総実行時間", f"{elapsed_time:.2f}秒")
        final_table.add_row("🏁 終了理由", reason)
        
        if elapsed_time > 0:
            items_per_sec = self.stats['items_count'] / elapsed_time
            final_table.add_row("🚀 平均処理速度", f"{items_per_sec:.2f} items/sec")
        
        self.console.print(Panel(final_table, title="📊 スクレイピング完了", border_style="yellow"))

    def _save_stats(self):
        """統計情報をファイルに保存"""
        if not self.stats_file:
            return

        try:
            # 経過時間を計算
            elapsed_time = 0
            if self.stats['start_time']:
                current_time = self.stats['finish_time'] or time.time()
                elapsed_time = current_time - self.stats['start_time']

            # 速度計算
            items_per_second = 0
            requests_per_second = 0
            items_per_minute = 0
            if elapsed_time > 0:
                items_per_second = self.stats['items_count'] / elapsed_time
                requests_per_second = self.stats['requests_count'] / elapsed_time
                items_per_minute = items_per_second * 60

            # 成功率・エラー率計算
            total_responses = self.stats['responses_count']
            success_rate = 0
            error_rate = 0
            if total_responses > 0:
                success_rate = ((total_responses - self.stats['errors_count']) / total_responses) * 100
                error_rate = (self.stats['errors_count'] / total_responses) * 100

            # Scrapy標準形式の統計情報を作成
            scrapy_stats = {
                # 基本統計
                'item_scraped_count': self.stats['items_count'],
                'downloader/request_count': self.stats['requests_count'],
                'response_received_count': self.stats['responses_count'],
                'spider_exceptions': self.stats['errors_count'],

                # 時間情報
                'elapsed_time_seconds': elapsed_time,
                'start_time': self.stats['start_time'],
                'finish_time': self.stats['finish_time'],

                # 速度メトリクス
                'items_per_second': items_per_second,
                'requests_per_second': requests_per_second,
                'items_per_minute': items_per_minute,

                # 成功率・エラー率
                'success_rate': success_rate,
                'error_rate': error_rate,

                # HTTPステータス統計（デフォルト値）
                'downloader/response_status_count/200': max(0, self.stats['responses_count'] - self.stats['errors_count']),
                'downloader/response_status_count/404': 0,
                'downloader/response_status_count/500': self.stats['errors_count'],

                # ログレベル統計（デフォルト値）
                'log_count/DEBUG': 0,
                'log_count/INFO': self.stats['items_count'],
                'log_count/WARNING': 0,
                'log_count/ERROR': self.stats['errors_count'],
                'log_count/CRITICAL': 0,

                # Rich progress拡張統計
                'rich_progress_enabled': True,
                'rich_progress_version': '1.0.0'
            }

            # ファイルに保存
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(scrapy_stats, f, indent=2, ensure_ascii=False)

        except Exception as e:
            # 統計ファイル保存エラーは無視（進捗バー表示に影響しないように）
            pass

    def _sync_with_scrapy_stats(self):
        """Scrapyの統計情報と同期（強化版）"""
        try:
            if hasattr(self.crawler, 'stats'):
                scrapy_stats = self.crawler.stats

                # Scrapyの統計情報を常に優先（実際のHTTPリクエスト数と一致させる）
                items_count = scrapy_stats.get_value('item_scraped_count', 0)
                requests_count = scrapy_stats.get_value('downloader/request_count', 0)
                responses_count = scrapy_stats.get_value('response_received_count', 0)
                errors_count = scrapy_stats.get_value('spider_exceptions', 0)

                # 統計が更新された場合のみ反映
                if items_count > 0:
                    self.stats['items_count'] = items_count
                if requests_count > 0:
                    self.stats['requests_count'] = requests_count
                if responses_count > 0:
                    self.stats['responses_count'] = responses_count
                if errors_count > 0:
                    self.stats['errors_count'] = errors_count

                # デバッグ情報
                if items_count > 0 or requests_count > 0:
                    print(f"📊 Stats sync: items={items_count}, requests={requests_count}, responses={responses_count}")

        except Exception as e:
            # 同期エラーは無視
            print(f"⚠️ Stats sync error: {e}")
            pass




# 設定例をコメントで記載
"""
# settings.pyに追加する設定例

# Rich進捗バーを有効化
RICH_PROGRESS_ENABLED = True

# 詳細統計を表示
RICH_PROGRESS_SHOW_STATS = True

# 更新間隔（秒）- 大幅に緩和
RICH_PROGRESS_UPDATE_INTERVAL = 2.0

# WebSocket通知を有効化
RICH_PROGRESS_WEBSOCKET = True

# 拡張機能を登録
EXTENSIONS = {
    'app.scrapy_extensions.rich_progress_extension.RichProgressExtension': 500,
}
"""
