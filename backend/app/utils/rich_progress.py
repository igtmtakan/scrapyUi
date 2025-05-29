"""
Rich Progress Integration for ScrapyUI
Beautiful progress bars and real-time statistics display
"""

import time
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from rich.progress import (
    Progress, 
    TaskID, 
    BarColumn, 
    TextColumn, 
    TimeRemainingColumn, 
    SpinnerColumn,
    MofNCompleteColumn,
    TimeElapsedColumn,
    FileSizeColumn,
    TransferSpeedColumn
)
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box


class ScrapyProgressTracker:
    """Rich progress tracker for Scrapy spiders"""
    
    def __init__(self):
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=self.console,
            expand=True
        )
        self.tasks: Dict[str, TaskID] = {}
        self.task_stats: Dict[str, Dict[str, Any]] = {}
        self.live: Optional[Live] = None
        self.start_time = datetime.now()
        
    def start_tracking(self):
        """Start the live progress display"""
        layout = self._create_layout()
        self.live = Live(layout, console=self.console, refresh_per_second=2)
        self.live.start()
        
    def stop_tracking(self):
        """Stop the live progress display"""
        if self.live:
            self.live.stop()
            
    def add_spider_task(self, task_id: str, spider_name: str, total_pages: int = 100):
        """Add a new spider task to track"""
        if not self.live:
            self.start_tracking()
            
        description = f"🕷️ {spider_name}"
        progress_task = self.progress.add_task(description, total=total_pages)
        self.tasks[task_id] = progress_task
        self.task_stats[task_id] = {
            'spider_name': spider_name,
            'start_time': datetime.now(),
            'items_scraped': 0,
            'requests_made': 0,
            'errors': 0,
            'pages_visited': 0,
            'current_url': '',
            'status': 'RUNNING'
        }
        
    def update_progress(self, task_id: str, **kwargs):
        """Update progress for a specific task"""
        if task_id not in self.tasks:
            return
            
        progress_task = self.tasks[task_id]
        stats = self.task_stats[task_id]
        
        # Update statistics
        if 'items_scraped' in kwargs:
            stats['items_scraped'] = kwargs['items_scraped']
        if 'requests_made' in kwargs:
            stats['requests_made'] = kwargs['requests_made']
        if 'errors' in kwargs:
            stats['errors'] = kwargs['errors']
        if 'pages_visited' in kwargs:
            stats['pages_visited'] = kwargs['pages_visited']
            # Update progress bar
            self.progress.update(progress_task, completed=stats['pages_visited'])
        if 'current_url' in kwargs:
            stats['current_url'] = kwargs['current_url']
        if 'status' in kwargs:
            stats['status'] = kwargs['status']
            
        # Update task description with current stats
        description = f"🕷️ {stats['spider_name']} | Items: {stats['items_scraped']} | Requests: {stats['requests_made']}"
        if stats['errors'] > 0:
            description += f" | ❌ Errors: {stats['errors']}"
            
        self.progress.update(progress_task, description=description)
        
    def complete_task(self, task_id: str, status: str = 'COMPLETED'):
        """Mark a task as completed"""
        if task_id not in self.tasks:
            return
            
        progress_task = self.tasks[task_id]
        stats = self.task_stats[task_id]
        stats['status'] = status
        stats['end_time'] = datetime.now()
        
        # Update final description
        if status == 'COMPLETED':
            description = f"✅ {stats['spider_name']} | Items: {stats['items_scraped']} | Requests: {stats['requests_made']}"
        else:
            description = f"❌ {stats['spider_name']} | {status}"
            
        self.progress.update(progress_task, description=description, completed=100)
        
    def _create_layout(self) -> Layout:
        """Create the rich layout for display"""
        layout = Layout()
        
        layout.split_column(
            Layout(self._create_header(), size=3),
            Layout(self.progress, name="progress"),
            Layout(self._create_stats_table(), size=10)
        )
        
        return layout
        
    def _create_header(self) -> Panel:
        """Create header panel"""
        elapsed = datetime.now() - self.start_time
        header_text = Text()
        header_text.append("🚀 ScrapyUI Progress Monitor", style="bold magenta")
        header_text.append(f" | Elapsed: {str(elapsed).split('.')[0]}", style="cyan")
        header_text.append(f" | Active Tasks: {len([t for t in self.task_stats.values() if t['status'] == 'RUNNING'])}", style="green")
        
        return Panel(header_text, box=box.ROUNDED)
        
    def _create_stats_table(self) -> Table:
        """Create statistics table"""
        table = Table(title="📊 Task Statistics", box=box.MINIMAL_DOUBLE_HEAD)
        
        table.add_column("Spider", style="cyan", no_wrap=True)
        table.add_column("Status", style="magenta")
        table.add_column("Items", style="green", justify="right")
        table.add_column("Requests", style="blue", justify="right")
        table.add_column("Errors", style="red", justify="right")
        table.add_column("Duration", style="yellow")
        table.add_column("Rate", style="bright_green", justify="right")
        
        for task_id, stats in self.task_stats.items():
            # Calculate duration
            start_time = stats['start_time']
            end_time = stats.get('end_time', datetime.now())
            duration = end_time - start_time
            duration_str = str(duration).split('.')[0]
            
            # Calculate rate (items per minute)
            minutes = duration.total_seconds() / 60
            rate = f"{stats['items_scraped'] / max(minutes, 0.1):.1f}/min" if minutes > 0 else "0/min"
            
            # Status emoji
            status_emoji = {
                'RUNNING': '🔄',
                'COMPLETED': '✅',
                'FAILED': '❌',
                'CANCELLED': '⏹️'
            }.get(stats['status'], '❓')
            
            table.add_row(
                stats['spider_name'][:15],
                f"{status_emoji} {stats['status']}",
                str(stats['items_scraped']),
                str(stats['requests_made']),
                str(stats['errors']),
                duration_str,
                rate
            )
            
        return table


class RichSpiderMonitor:
    """Simplified rich monitor for single spider execution"""
    
    def __init__(self, spider_name: str):
        self.spider_name = spider_name
        self.console = Console()
        self.start_time = datetime.now()
        self.stats = {
            'items': 0,
            'requests': 0,
            'errors': 0,
            'pages': 0,
            'current_url': ''
        }
        
    def show_progress(self, **kwargs):
        """Show current progress"""
        # Update stats
        self.stats.update(kwargs)
        
        # Calculate elapsed time
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]
        
        # Calculate rate
        minutes = elapsed.total_seconds() / 60
        rate = f"{self.stats['items'] / max(minutes, 0.1):.1f}" if minutes > 0 else "0"
        
        # Create progress display
        self.console.clear()
        
        # Header
        header = Panel(
            f"🕷️ [bold cyan]{self.spider_name}[/bold cyan] | "
            f"⏱️ {elapsed_str} | "
            f"📈 {rate} items/min",
            title="ScrapyUI Spider Monitor",
            box=box.ROUNDED
        )
        self.console.print(header)
        
        # Stats table
        table = Table(box=box.MINIMAL)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        table.add_row("📦 Items Scraped", str(self.stats['items']))
        table.add_row("🌐 Requests Made", str(self.stats['requests']))
        table.add_row("📄 Pages Visited", str(self.stats['pages']))
        table.add_row("❌ Errors", str(self.stats['errors']))
        
        if self.stats['current_url']:
            table.add_row("🔗 Current URL", self.stats['current_url'][:50] + "..." if len(self.stats['current_url']) > 50 else self.stats['current_url'])
            
        self.console.print(table)
        
        # Progress bar
        if self.stats['pages'] > 0:
            progress_text = f"Processing page {self.stats['pages']}..."
            self.console.print(f"\n[yellow]{progress_text}[/yellow]")
            
    def show_completion(self, status: str = "COMPLETED"):
        """Show completion status"""
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]
        
        if status == "COMPLETED":
            emoji = "🎉"
            color = "green"
        else:
            emoji = "❌"
            color = "red"
            
        completion_panel = Panel(
            f"{emoji} [bold {color}]{status}[/bold {color}]\n"
            f"📦 Total Items: {self.stats['items']}\n"
            f"🌐 Total Requests: {self.stats['requests']}\n"
            f"⏱️ Duration: {elapsed_str}",
            title=f"Spider {self.spider_name} Finished",
            box=box.DOUBLE
        )
        
        self.console.print(completion_panel)
