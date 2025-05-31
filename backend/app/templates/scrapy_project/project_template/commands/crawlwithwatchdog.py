#!/usr/bin/env python3
"""
Scrapyカスタムコマンド: crawlwithwatchdog
watchdog監視付きでスパイダーを実行

使用例:
scrapy crawlwithwatchdog spider_name -o results.jsonl --task-id=test_123
"""
import asyncio
import threading
import time
import uuid
import json
import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
from scrapy.commands import ScrapyCommand
from scrapy.utils.conf import arglist_to_dict
from scrapy.exceptions import UsageError

# watchdogライブラリ
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


class JSONLWatchdogHandler(FileSystemEventHandler):
    """JSONLファイル専用のwatchdogイベントハンドラー"""
    
    def __init__(self, monitor):
        self.monitor = monitor
        
    def on_modified(self, event):
        """ファイル変更時の処理"""
        if event.is_directory:
            return
            
        # 監視対象のJSONLファイルかチェック
        if event.src_path == str(self.monitor.jsonl_file_path):
            # 非同期処理をスレッドセーフに実行
            threading.Thread(
                target=self.monitor.process_new_lines,
                daemon=True
            ).start()


class JSONLMonitor:
    """JSONLファイル監視クラス"""
    
    def __init__(self, task_id, spider_name, jsonl_file_path, db_path):
        self.task_id = task_id
        self.spider_name = spider_name
        self.jsonl_file_path = Path(jsonl_file_path)
        self.db_path = db_path
        self.processed_lines = 0
        self.last_file_size = 0
        self.is_monitoring = False
        self.observer = None
        
    def start_monitoring(self):
        """watchdog監視を開始"""
        if not WATCHDOG_AVAILABLE:
            print("⚠️ watchdogライブラリが利用できません。ポーリング監視を使用します。")
            self._start_polling_monitoring()
            return
        
        self.is_monitoring = True
        
        # watchdog監視を開始
        event_handler = JSONLWatchdogHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.jsonl_file_path.parent), recursive=False)
        self.observer.start()
        
        print(f"🔍 watchdog監視開始: {self.jsonl_file_path}")
        
    def _start_polling_monitoring(self):
        """ポーリング監視（フォールバック）"""
        self.is_monitoring = True
        
        def polling_loop():
            while self.is_monitoring:
                self.process_new_lines()
                time.sleep(1)
        
        polling_thread = threading.Thread(target=polling_loop, daemon=True)
        polling_thread.start()
        
        print(f"🔄 ポーリング監視開始: {self.jsonl_file_path}")
    
    def stop_monitoring(self):
        """監視を停止"""
        self.is_monitoring = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        
        print(f"🛑 監視停止: 処理済み行数 {self.processed_lines}")
    
    def process_new_lines(self):
        """新しい行を処理"""
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
                    self._process_single_line(line)
                    self.processed_lines += 1
                
                print(f"📊 総処理済みアイテム数: {self.processed_lines}")
            
            # ファイルサイズを更新
            self.last_file_size = current_size
            
        except Exception as e:
            print(f"❌ 新しい行処理エラー: {e}")
    
    def _process_single_line(self, json_line):
        """単一の行を処理してDBにインサート"""
        try:
            # JSON解析
            item_data = json.loads(json_line)
            
            # DBにインサート
            self._insert_item_to_db(item_data)
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析エラー: {e} - Line: {json_line[:100]}...")
        except Exception as e:
            print(f"❌ 行処理エラー: {e}")
    
    def _insert_item_to_db(self, item_data):
        """アイテムをデータベースにインサート"""
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
                "command_project",  # コマンド実行時はプロジェクトIDを固定
                self.spider_name,
                json.dumps(item_data, ensure_ascii=False),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ DBインサート成功: {item_id}")
            
        except Exception as e:
            print(f"❌ DBインサートエラー: {e}")


class Command(ScrapyCommand):
    """watchdog監視付きcrawlコマンド"""
    
    requires_project = True
    default_settings = {'LOG_LEVEL': 'INFO'}

    def syntax(self):
        return "<spider> [options]"

    def short_desc(self):
        return "Run a spider with watchdog monitoring for real-time DB insertion"

    def long_desc(self):
        return """
Run a spider with watchdog monitoring that automatically inserts
scraped items into the database in real-time as they are written
to the JSONL output file.

Examples:
  scrapy crawlwithwatchdog myspider -o results.jsonl --task-id=test_123
  scrapy crawlwithwatchdog myspider -o results.jsonl --db-path=/path/to/db.sqlite
        """

    def add_options(self, parser):
        ScrapyCommand.add_options(self, parser)
        parser.add_option("-o", "--output", dest="output",
                         help="dump scraped items to JSONL file (required for watchdog monitoring)")
        parser.add_option("-t", "--output-format", dest="output_format", default="jsonlines",
                         help="format to use for dumping items (default: jsonlines)")
        parser.add_option("--task-id", dest="task_id",
                         help="task ID for monitoring (auto-generated if not provided)")
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
            raise UsageError("Spider name is required")

        spider_name = args[0]
        
        # 出力ファイルが指定されているかチェック
        if not opts.output:
            raise UsageError("Output file (-o) is required for watchdog monitoring")
        
        # JSONLファイルかチェック
        if not opts.output.endswith('.jsonl'):
            print("⚠️ Warning: Output file should be .jsonl for optimal monitoring")
        
        # タスクIDを生成または取得
        task_id = opts.task_id or f"cmd_{spider_name}_{int(time.time())}"
        
        print(f"🚀 Starting spider with watchdog monitoring")
        print(f"   Spider: {spider_name}")
        print(f"   Task ID: {task_id}")
        print(f"   Output: {opts.output}")
        print(f"   DB Path: {opts.db_path}")
        print(f"   Watchdog Available: {'Yes' if WATCHDOG_AVAILABLE else 'No (using polling)'}")
        
        # watchdog監視を開始
        monitor = JSONLMonitor(
            task_id=task_id,
            spider_name=spider_name,
            jsonl_file_path=opts.output,
            db_path=opts.db_path
        )
        
        monitor.start_monitoring()
        
        try:
            # Scrapyの設定を更新
            self.settings.set('FEED_URI', opts.output)
            self.settings.set('FEED_FORMAT', opts.output_format or 'jsonlines')
            
            # スパイダーを実行
            print(f"🕷️ Starting Scrapy crawler...")
            self.crawler_process.crawl(spider_name, **opts.spkwargs)
            self.crawler_process.start()
            
        except KeyboardInterrupt:
            print(f"\n⚠️ Interrupted by user")
        except Exception as e:
            print(f"❌ Crawler error: {e}")
        finally:
            # 監視を停止
            monitor.stop_monitoring()
            
            # 最終的な統計を表示
            print(f"\n📊 Final Statistics:")
            print(f"   Total items processed: {monitor.processed_lines}")
            print(f"   Output file: {opts.output}")
            print(f"   Database: {opts.db_path}")
            print(f"✅ crawlwithwatchdog completed")
