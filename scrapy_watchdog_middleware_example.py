#!/usr/bin/env python3
"""
Scrapyミドルウェアでwatchdog監視を自動開始する例
settings.pyのDOWNLOADER_MIDDLEWARESに追加
"""
import asyncio
import threading
import os
import sys
from pathlib import Path
from scrapy import signals
from scrapy.exceptions import NotConfigured

class WatchdogMonitoringMiddleware:
    """watchdog監視を自動開始するミドルウェア"""
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.settings = crawler.settings
        self.monitor = None
        self.monitor_thread = None
        
        # 監視設定を取得
        self.enable_watchdog = self.settings.getbool('WATCHDOG_MONITORING_ENABLED', False)
        self.task_id = self.settings.get('WATCHDOG_TASK_ID', f"auto_{int(time.time())}")
        self.db_path = self.settings.get('WATCHDOG_DB_PATH', 'backend/database/scrapy_ui.db')
        self.output_file = self.settings.get('FEED_URI', None)
        
        if not self.enable_watchdog:
            raise NotConfigured('Watchdog monitoring is disabled')
        
        if not self.output_file:
            raise NotConfigured('FEED_URI must be set for watchdog monitoring')
        
        print(f"🔍 Watchdog monitoring middleware initialized")
        print(f"   Task ID: {self.task_id}")
        print(f"   Output file: {self.output_file}")
        print(f"   DB path: {self.db_path}")

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def spider_opened(self, spider):
        """スパイダー開始時にwatchdog監視を開始"""
        print(f"🚀 Starting watchdog monitoring for spider: {spider.name}")
        
        try:
            # watchdog監視を別スレッドで開始
            self.monitor_thread = threading.Thread(
                target=self._start_monitoring_thread,
                args=(spider.name,),
                daemon=True
            )
            self.monitor_thread.start()
            
            print(f"✅ Watchdog monitoring thread started")
            
        except Exception as e:
            print(f"❌ Failed to start watchdog monitoring: {e}")

    def spider_closed(self, spider):
        """スパイダー終了時に監視を停止"""
        print(f"🛑 Stopping watchdog monitoring for spider: {spider.name}")
        
        if self.monitor:
            self.monitor.stop_monitoring()

    def _start_monitoring_thread(self, spider_name):
        """監視スレッドを開始"""
        try:
            # watchdog監視クラスをインポート
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'app', 'services'))
            from scrapy_watchdog_monitor import ScrapyWatchdogMonitor
            
            # 監視クラスを作成
            self.monitor = ScrapyWatchdogMonitor(
                task_id=self.task_id,
                project_path=os.getcwd(),
                spider_name=spider_name,
                db_path=self.db_path
            )
            
            # 非同期監視を開始
            asyncio.run(self.monitor._start_jsonl_monitoring(self.output_file))
            
        except Exception as e:
            print(f"❌ Watchdog monitoring thread error: {e}")


# settings.pyに追加する設定例:
"""
# Watchdog監視を有効化
WATCHDOG_MONITORING_ENABLED = True
WATCHDOG_TASK_ID = 'custom_task_123'
WATCHDOG_DB_PATH = 'backend/database/scrapy_ui.db'

# ミドルウェアを追加
DOWNLOADER_MIDDLEWARES = {
    'myproject.middlewares.WatchdogMonitoringMiddleware': 543,
}

# JSONLファイル出力を設定
FEED_URI = 'results_%(time)s.jsonl'
FEED_FORMAT = 'jsonlines'
"""
