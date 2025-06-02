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
        self.update_interval = self.settings.getfloat('RICH_PROGRESS_UPDATE_INTERVAL', 0.1)
        self.websocket_enabled = self.settings.getbool('RICH_PROGRESS_WEBSOCKET', False)

        if not self.enabled:
            raise NotConfigured("Rich progress bar is disabled")
    
    @classmethod
    def from_crawler(cls, crawler: Crawler):
        """Crawlerからインスタンスを作成"""
        extension = cls(crawler)
        
        # シグナルを接続
        crawler.signals.connect(extension.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(extension.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(extension.request_scheduled, signal=signals.request_scheduled)
        crawler.signals.connect(extension.response_received, signal=signals.response_received)
        crawler.signals.connect(extension.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(extension.spider_error, signal=signals.spider_error)
        
        return extension
    
    def spider_opened(self, spider: Spider):
        """スパイダー開始時の処理"""
        self.stats['start_time'] = time.time()

        # タスクIDを取得（環境変数またはcrawlerから）
        self.task_id_str = (
            os.environ.get('SCRAPY_TASK_ID') or
            getattr(self.crawler, 'task_id', None) or
            f"task_{int(time.time())}"
        )

        # 統計ファイルパスを設定
        project_dir = Path.cwd()
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
    
    def spider_closed(self, spider: Spider, reason: str):
        """スパイダー終了時の処理"""
        # 終了時刻を記録
        self.stats['finish_time'] = time.time()

        # Scrapyの統計情報と同期
        self._sync_with_scrapy_stats()

        # 最終統計ファイルを保存
        self._save_stats()

        # 完了通知とバルクインサート発動
        if reason == 'finished' and hasattr(spider, 'task_id'):
            spider.logger.info(f"🎯 Spider completed successfully with Rich progress tracking for task {spider.task_id}")

            # Rich progress完了通知でバルクインサートを発動
            self._trigger_bulk_insert_on_completion(spider)

        if self.live:
            self.live.stop()

        if self.progress:
            self.progress.stop()

        # 最終統計を表示
        self._show_final_stats(spider, reason)

    def _trigger_bulk_insert_on_completion(self, spider):
        """Rich progress完了通知でバルクインサートを発動"""
        try:
            task_id = getattr(spider, 'task_id', None)
            if not task_id:
                spider.logger.warning("🔍 Task ID not found - skipping bulk insert")
                return

            spider.logger.info(f"🚀 Rich progress completion triggered - starting bulk insert for task {task_id}")

            # プロジェクトパスを取得
            project_path = getattr(spider, 'project_path', None)
            if not project_path:
                # 現在のディレクトリから推測
                import os
                project_path = os.getcwd()

            spider.logger.info(f"📁 Project path: {project_path}")

            # JSONLファイルパスを構築
            from pathlib import Path
            jsonl_file_path = Path(project_path) / f"results_{task_id}.jsonl"

            if not jsonl_file_path.exists():
                spider.logger.warning(f"📄 JSONL file not found: {jsonl_file_path}")
                return

            spider.logger.info(f"📄 Found JSONL file: {jsonl_file_path}")

            # ファイルサイズと行数を確認
            file_size = jsonl_file_path.stat().st_size
            with open(jsonl_file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]

            spider.logger.info(f"📊 File size: {file_size} bytes, Lines: {len(lines)}")

            if len(lines) == 0:
                spider.logger.warning("📄 No data lines found in JSONL file")
                return

            # バルクインサート実行
            self._execute_bulk_insert(task_id, lines, spider)

        except Exception as e:
            spider.logger.error(f"❌ Bulk insert trigger error: {e}")
            import traceback
            spider.logger.error(f"❌ Traceback: {traceback.format_exc()}")

    def _execute_bulk_insert(self, task_id: str, lines: list, spider):
        """バルクインサートを実行"""
        try:
            spider.logger.info(f"🔄 Starting bulk insert for {len(lines)} lines")

            # ScrapyWatchdogMonitorのバルクインサート機能を使用
            from ..services.scrapy_watchdog_monitor import ScrapyWatchdogMonitor

            # 一時的なモニターインスタンスを作成（バルクインサート専用）
            monitor = ScrapyWatchdogMonitor(
                task_id=task_id,
                project_path=getattr(spider, 'project_path', os.getcwd()),
                spider_name=spider.name
            )

            # バルクインサート実行
            successful_inserts = monitor._bulk_insert_items_threading(lines)

            spider.logger.info(f"✅ Bulk insert completed: {successful_inserts}/{len(lines)} items inserted")

            # 重複クリーンアップを実行
            cleanup_result = self._cleanup_duplicate_records(task_id, spider)

            # WebSocket通知を送信
            self._send_completion_websocket_notification(task_id, successful_inserts, spider, cleanup_result)

        except Exception as e:
            spider.logger.error(f"❌ Bulk insert execution error: {e}")
            import traceback
            spider.logger.error(f"❌ Traceback: {traceback.format_exc()}")

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
    
    def request_scheduled(self, request: Request, spider: Spider):
        """リクエスト送信時の処理"""
        self.stats['requests_count'] += 1
        self._update_progress()
        self._save_stats()

    def response_received(self, response: Response, request: Request, spider: Spider):
        """レスポンス受信時の処理"""
        self.stats['responses_count'] += 1
        self._update_progress()
        self._save_stats()

    def item_scraped(self, item: Dict[str, Any], response: Response, spider: Spider):
        """アイテム取得時の処理"""
        self.stats['items_count'] += 1
        self._update_progress()
        self._save_stats()

    def spider_error(self, failure, response: Response, spider: Spider):
        """エラー発生時の処理"""
        self.stats['errors_count'] += 1
        self._update_progress()
        self._save_stats()
    
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
            # ライブ表示でテーブルと進捗バーを組み合わせ
            self.live = Live(self._create_layout(), console=self.console, refresh_per_second=10)
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
        """Scrapyの統計情報と同期"""
        try:
            if hasattr(self.crawler, 'stats'):
                scrapy_stats = self.crawler.stats

                # Scrapyの統計情報から値を取得
                self.stats['items_count'] = scrapy_stats.get_value('item_scraped_count', self.stats['items_count'])
                self.stats['requests_count'] = scrapy_stats.get_value('downloader/request_count', self.stats['requests_count'])
                self.stats['responses_count'] = scrapy_stats.get_value('response_received_count', self.stats['responses_count'])
                self.stats['errors_count'] = scrapy_stats.get_value('spider_exceptions', self.stats['errors_count'])

        except Exception as e:
            # 同期エラーは無視
            pass




# 設定例をコメントで記載
"""
# settings.pyに追加する設定例

# Rich進捗バーを有効化
RICH_PROGRESS_ENABLED = True

# 詳細統計を表示
RICH_PROGRESS_SHOW_STATS = True

# 更新間隔（秒）
RICH_PROGRESS_UPDATE_INTERVAL = 0.1

# WebSocket通知を有効化
RICH_PROGRESS_WEBSOCKET = True

# 拡張機能を登録
EXTENSIONS = {
    'app.scrapy_extensions.rich_progress_extension.RichProgressExtension': 500,
}
"""
