"""
ScrapyUI Rich Progress Extension

Scrapyスパイダーにrichライブラリを使用した美しい進捗バーを追加する拡張機能
"""

import os
import sys
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
            'total_urls': 0
        }
        
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
        import time
        self.stats['start_time'] = time.time()
        
        # start_urlsの数を取得
        if hasattr(spider, 'start_urls'):
            self.stats['total_urls'] = len(spider.start_urls)
        
        # Rich進捗バーを初期化
        self._initialize_progress(spider)
        
        spider.logger.info(f"🎨 Rich進捗バー開始: {spider.name}")
    
    def spider_closed(self, spider: Spider, reason: str):
        """スパイダー終了時の処理"""
        if self.live:
            self.live.stop()
        
        if self.progress:
            self.progress.stop()
        
        # 最終統計を表示
        self._show_final_stats(spider, reason)
        
        spider.logger.info(f"🎨 Rich進捗バー終了: {spider.name} (理由: {reason})")
    
    def request_scheduled(self, request: Request, spider: Spider):
        """リクエスト送信時の処理"""
        self.stats['requests_count'] += 1
        self._update_progress()
    
    def response_received(self, response: Response, request: Request, spider: Spider):
        """レスポンス受信時の処理"""
        self.stats['responses_count'] += 1
        self._update_progress()
    
    def item_scraped(self, item: Dict[str, Any], response: Response, spider: Spider):
        """アイテム取得時の処理"""
        self.stats['items_count'] += 1
        self._update_progress()
    
    def spider_error(self, failure, response: Response, spider: Spider):
        """エラー発生時の処理"""
        self.stats['errors_count'] += 1
        self._update_progress()
    
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
            # WebSocket通知の実装（ScrapyUIのWebSocketマネージャーと連携）
            progress_data = {
                'type': 'progress_update',
                'stats': self.stats.copy(),
                'progress_percentage': self._calculate_progress_percentage()
            }
            
            # ここでWebSocketマネージャーに送信
            # websocket_manager.broadcast(progress_data)
            
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
