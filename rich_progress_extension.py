from scrapy import signals
from scrapy.extensions import telnet
from rich.console import Console
from rich.progress import Progress, TaskID, BarColumn, TextColumn, TimeRemainingColumn, SpinnerColumn
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
import threading
import time


class RichProgressExtension:
    """
    Scrapy Extension for Rich Progress Bar
    """
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.console = Console()
        self.progress = None
        self.live = None
        self.task_id = None
        self.stats = crawler.stats
        
        # カウンター
        self.items_scraped = 0
        self.requests_made = 0
        self.responses_received = 0
        self.errors_count = 0
        
        # 設定
        self.item_limit = crawler.settings.getint('CLOSESPIDER_ITEMCOUNT', 0)
        self.spider_name = ""
        
        # スレッドロック
        self.lock = threading.Lock()
        
    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(crawler)
        
        # シグナル接続
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(ext.request_scheduled, signal=signals.request_scheduled)
        crawler.signals.connect(ext.response_received, signal=signals.response_received)
        crawler.signals.connect(ext.spider_error, signal=signals.spider_error)
        
        return ext
    
    def spider_opened(self, spider):
        """スパイダー開始時"""
        self.spider_name = spider.name
        
        # Rich Progress設定
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TextColumn("[green]Items: {task.fields[items]}"),
            TextColumn("•"),
            TextColumn("[blue]Requests: {task.fields[requests]}"),
            TextColumn("•"),
            TextColumn("[red]Errors: {task.fields[errors]}"),
            TimeRemainingColumn(),
            console=self.console,
            transient=False
        )
        
        # タスク追加
        total = self.item_limit if self.item_limit > 0 else 100
        self.task_id = self.progress.add_task(
            f"🕷️  Scraping {self.spider_name}",
            total=total,
            items=0,
            requests=0,
            errors=0
        )
        
        # Live表示開始
        self.live = Live(self._create_layout(), console=self.console, refresh_per_second=2)
        self.live.start()
        
        self.console.print(f"\n🚀 [bold green]Starting spider: {self.spider_name}[/bold green]\n")
    
    def spider_closed(self, spider, reason):
        """スパイダー終了時"""
        if self.live:
            self.live.stop()
        
        # 最終統計表示
        self._show_final_stats(reason)
    
    def item_scraped(self, item, response, spider):
        """アイテム取得時"""
        with self.lock:
            self.items_scraped += 1
            self._update_progress()
    
    def request_scheduled(self, request, spider):
        """リクエスト送信時"""
        with self.lock:
            self.requests_made += 1
            self._update_progress()
    
    def response_received(self, response, request, spider):
        """レスポンス受信時"""
        with self.lock:
            self.responses_received += 1
            self._update_progress()
    
    def spider_error(self, failure, response, spider):
        """エラー発生時"""
        with self.lock:
            self.errors_count += 1
            self._update_progress()
    
    def _update_progress(self):
        """プログレス更新"""
        if self.progress and self.task_id is not None:
            # 進捗計算
            if self.item_limit > 0:
                completed = min(self.items_scraped, self.item_limit)
            else:
                completed = self.items_scraped
            
            self.progress.update(
                self.task_id,
                completed=completed,
                items=self.items_scraped,
                requests=self.requests_made,
                errors=self.errors_count
            )
    
    def _create_layout(self):
        """レイアウト作成"""
        # 統計テーブル
        stats_table = Table(title="📊 Real-time Statistics", show_header=True, header_style="bold magenta")
        stats_table.add_column("Metric", style="cyan", width=15)
        stats_table.add_column("Count", style="green", width=10)
        stats_table.add_column("Rate", style="yellow", width=15)
        
        # プログレスバーとテーブルを組み合わせ
        return Panel(
            self.progress,
            title=f"🕷️ Scrapy Progress - {self.spider_name}",
            border_style="blue"
        )
    
    def _show_final_stats(self, reason):
        """最終統計表示"""
        # 最終結果テーブル
        final_table = Table(title="🎯 Final Results", show_header=True, header_style="bold green")
        final_table.add_column("Metric", style="cyan")
        final_table.add_column("Value", style="green")
        
        final_table.add_row("Spider Name", self.spider_name)
        final_table.add_row("Completion Reason", reason)
        final_table.add_row("Items Scraped", str(self.items_scraped))
        final_table.add_row("Requests Made", str(self.requests_made))
        final_table.add_row("Responses Received", str(self.responses_received))
        final_table.add_row("Errors", str(self.errors_count))
        
        # 成功率計算
        if self.requests_made > 0:
            success_rate = (self.responses_received / self.requests_made) * 100
            final_table.add_row("Success Rate", f"{success_rate:.1f}%")
        
        self.console.print("\n")
        self.console.print(final_table)
        self.console.print(f"\n✅ [bold green]Spider completed: {reason}[/bold green]\n")
