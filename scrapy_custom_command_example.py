#!/usr/bin/env python3
"""
Scrapyカスタムコマンドでwatchdog監視を自動開始する例
プロジェクトの management/commands/ ディレクトリに配置
"""
import asyncio
import threading
import time
from scrapy.commands import ScrapyCommand
from scrapy.utils.conf import arglist_to_dict
from scrapy.exceptions import UsageError

class Command(ScrapyCommand):
    """watchdog監視付きcrawlコマンド"""
    
    requires_project = True
    default_settings = {'LOG_LEVEL': 'INFO'}

    def syntax(self):
        return "<spider> [options]"

    def short_desc(self):
        return "Run a spider with watchdog monitoring"

    def add_options(self, parser):
        ScrapyCommand.add_options(self, parser)
        parser.add_option("-o", "--output", dest="output",
                         help="dump scraped items to FILE (use - for stdout)")
        parser.add_option("-t", "--output-format", dest="output_format",
                         help="format to use for dumping items")
        parser.add_option("--task-id", dest="task_id",
                         help="task ID for monitoring")
        parser.add_option("--db-path", dest="db_path", 
                         default="backend/database/scrapy_ui.db",
                         help="database path for storing results")

    def process_options(self, args, opts):
        ScrapyCommand.process_options(self, args, opts)
        try:
            opts.spargs, opts.spkwargs = arglist_to_dict(args[1:])
        except ValueError:
            raise UsageError("Invalid -a value, use -a NAME=VALUE", print_help=False)

    def run(self, args, opts):
        if len(args) < 1:
            raise UsageError()

        spider_name = args[0]
        task_id = opts.task_id or f"custom_{int(time.time())}"
        
        print(f"🚀 Starting spider with watchdog monitoring: {spider_name}")
        print(f"📋 Task ID: {task_id}")
        
        # watchdog監視を別スレッドで開始
        monitor_thread = threading.Thread(
            target=self._start_watchdog_monitoring,
            args=(task_id, opts.output, opts.db_path),
            daemon=True
        )
        monitor_thread.start()
        
        # 通常のScrapyクローラーを実行
        self.crawler_process.crawl(spider_name, **opts.spkwargs)
        self.crawler_process.start()

    def _start_watchdog_monitoring(self, task_id, output_file, db_path):
        """watchdog監視を開始"""
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'app', 'services'))
            
            from scrapy_watchdog_monitor import ScrapyWatchdogMonitor
            
            # 監視クラスを作成
            monitor = ScrapyWatchdogMonitor(
                task_id=task_id,
                project_path=os.getcwd(),
                spider_name="unknown",  # スパイダー名は後で設定
                db_path=db_path
            )
            
            # 非同期監視を開始
            asyncio.run(monitor._start_jsonl_monitoring(output_file))
            
        except Exception as e:
            print(f"❌ Watchdog monitoring error: {e}")


# 使用例:
# scrapy crawlwithwatchdog spider_name -o results.jsonl --task-id=test_123
