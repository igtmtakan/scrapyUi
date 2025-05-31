#!/usr/bin/env python3
"""
JSONLファイル監視によるDB自動インサート実装例
"""
import json
import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import uuid

# 方法1: watchdogライブラリ使用（ファイルシステム監視）
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("⚠️ watchdogライブラリがインストールされていません")
    print("   インストール: pip install watchdog")

class JSONLFileMonitor:
    """JSONLファイルを監視してDBに自動インサートするクラス"""
    
    def __init__(self, 
                 db_path: str,
                 task_id: str,
                 project_id: str,
                 spider_name: str,
                 websocket_callback: Optional[Callable] = None):
        self.db_path = db_path
        self.task_id = task_id
        self.project_id = project_id
        self.spider_name = spider_name
        self.websocket_callback = websocket_callback
        self.processed_lines = 0
        self.is_monitoring = False
        self.observer = None
        
    async def start_monitoring(self, jsonl_file_path: str):
        """JSONLファイルの監視を開始"""
        self.jsonl_file_path = Path(jsonl_file_path)
        self.is_monitoring = True
        
        print(f"🔍 JSONLファイル監視開始: {self.jsonl_file_path}")
        
        if WATCHDOG_AVAILABLE:
            await self._start_watchdog_monitoring()
        else:
            await self._start_polling_monitoring()
    
    async def _start_watchdog_monitoring(self):
        """watchdogライブラリを使用した監視"""
        
        class JSONLEventHandler(FileSystemEventHandler):
            def __init__(self, monitor):
                self.monitor = monitor
                
            def on_modified(self, event):
                if not event.is_directory and event.src_path == str(self.monitor.jsonl_file_path):
                    asyncio.create_task(self.monitor._process_new_lines())
        
        event_handler = JSONLEventHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.jsonl_file_path.parent), recursive=False)
        self.observer.start()
        
        print(f"✅ watchdog監視開始: {self.jsonl_file_path.parent}")
        
        try:
            while self.is_monitoring:
                await asyncio.sleep(1)
        finally:
            self.observer.stop()
            self.observer.join()
    
    async def _start_polling_monitoring(self):
        """ポーリング方式の監視（フォールバック）"""
        print(f"🔄 ポーリング監視開始（1秒間隔）")
        
        while self.is_monitoring:
            await self._process_new_lines()
            await asyncio.sleep(1)
    
    async def _process_new_lines(self):
        """新しい行を処理してDBにインサート"""
        try:
            if not self.jsonl_file_path.exists():
                return
            
            with open(self.jsonl_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 新しい行のみ処理
            new_lines = lines[self.processed_lines:]
            
            if new_lines:
                print(f"📝 新しい行を検出: {len(new_lines)}件")
                
                for line in new_lines:
                    line = line.strip()
                    if line:
                        await self._insert_item_to_db(line)
                        self.processed_lines += 1
                
                # WebSocket通知
                if self.websocket_callback:
                    await self.websocket_callback({
                        'type': 'items_update',
                        'task_id': self.task_id,
                        'new_items': len(new_lines),
                        'total_items': self.processed_lines
                    })
        
        except Exception as e:
            print(f"❌ 行処理エラー: {e}")
    
    async def _insert_item_to_db(self, json_line: str):
        """単一アイテムをDBにインサート"""
        try:
            # JSON解析
            item_data = json.loads(json_line)
            
            # データベース接続
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # アイテムテーブルにインサート
            item_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO scraped_items 
                (id, task_id, project_id, spider_name, data, scraped_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                self.task_id,
                self.project_id,
                self.spider_name,
                json.dumps(item_data, ensure_ascii=False),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ DBインサート成功: {item_id}")
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析エラー: {e} - Line: {json_line[:100]}...")
        except Exception as e:
            print(f"❌ DBインサートエラー: {e}")
    
    def stop_monitoring(self):
        """監視を停止"""
        self.is_monitoring = False
        if self.observer:
            self.observer.stop()
        print(f"🛑 監視停止: 処理済み行数 {self.processed_lines}")


# 方法2: tail -f 方式（Linuxライク）
class TailFollowMonitor:
    """tail -f方式でJSONLファイルを監視"""
    
    def __init__(self, db_path: str, task_id: str, project_id: str, spider_name: str):
        self.db_path = db_path
        self.task_id = task_id
        self.project_id = project_id
        self.spider_name = spider_name
        self.is_monitoring = False
    
    async def follow_file(self, file_path: str):
        """ファイルの末尾を追跡"""
        file_path = Path(file_path)
        
        print(f"🔍 tail -f方式監視開始: {file_path}")
        
        # ファイルが存在するまで待機
        while not file_path.exists() and self.is_monitoring:
            await asyncio.sleep(0.1)
        
        if not self.is_monitoring:
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            # ファイルの末尾に移動
            f.seek(0, 2)
            
            while self.is_monitoring:
                line = f.readline()
                if line:
                    line = line.strip()
                    if line:
                        await self._process_line(line)
                else:
                    await asyncio.sleep(0.1)
    
    async def _process_line(self, line: str):
        """行を処理してDBにインサート"""
        try:
            item_data = json.loads(line)
            
            # DBインサート処理（JSONLFileMonitorと同じ）
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            item_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO scraped_items 
                (id, task_id, project_id, spider_name, data, scraped_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                self.task_id,
                self.project_id,
                self.spider_name,
                json.dumps(item_data, ensure_ascii=False),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ tail方式DBインサート成功: {item_id}")
            
        except Exception as e:
            print(f"❌ tail方式処理エラー: {e}")
    
    def start_monitoring(self, file_path: str):
        """監視開始"""
        self.is_monitoring = True
        return asyncio.create_task(self.follow_file(file_path))
    
    def stop_monitoring(self):
        """監視停止"""
        self.is_monitoring = False


# 方法3: 非同期バッチ処理
class BatchJSONLProcessor:
    """バッチ処理でJSONLファイルを定期的に処理"""
    
    def __init__(self, db_path: str, task_id: str, project_id: str, spider_name: str):
        self.db_path = db_path
        self.task_id = task_id
        self.project_id = project_id
        self.spider_name = spider_name
        self.last_processed_size = 0
        self.is_processing = False
    
    async def start_batch_processing(self, file_path: str, interval: int = 5):
        """バッチ処理開始"""
        file_path = Path(file_path)
        self.is_processing = True
        
        print(f"🔄 バッチ処理開始: {file_path} (間隔: {interval}秒)")
        
        while self.is_processing:
            await self._process_batch(file_path)
            await asyncio.sleep(interval)
    
    async def _process_batch(self, file_path: Path):
        """バッチでファイルを処理"""
        try:
            if not file_path.exists():
                return
            
            current_size = file_path.stat().st_size
            
            if current_size > self.last_processed_size:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.seek(self.last_processed_size)
                    new_content = f.read()
                
                new_lines = [line.strip() for line in new_content.split('\n') if line.strip()]
                
                if new_lines:
                    await self._batch_insert(new_lines)
                    print(f"📦 バッチ処理完了: {len(new_lines)}件")
                
                self.last_processed_size = current_size
        
        except Exception as e:
            print(f"❌ バッチ処理エラー: {e}")
    
    async def _batch_insert(self, lines: list):
        """複数行を一括でDBにインサート"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            insert_data = []
            for line in lines:
                try:
                    item_data = json.loads(line)
                    item_id = str(uuid.uuid4())
                    insert_data.append((
                        item_id,
                        self.task_id,
                        self.project_id,
                        self.spider_name,
                        json.dumps(item_data, ensure_ascii=False),
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                except json.JSONDecodeError:
                    continue
            
            if insert_data:
                cursor.executemany("""
                    INSERT INTO scraped_items 
                    (id, task_id, project_id, spider_name, data, scraped_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, insert_data)
                
                conn.commit()
                print(f"✅ バッチインサート成功: {len(insert_data)}件")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ バッチインサートエラー: {e}")
    
    def stop_processing(self):
        """処理停止"""
        self.is_processing = False


# 使用例
async def example_usage():
    """使用例"""
    
    # データベースパス
    db_path = "backend/database/scrapy_ui.db"
    
    # タスク情報
    task_id = "test_task_123"
    project_id = "test_project"
    spider_name = "test_spider"
    jsonl_file = "scrapy_projects/test_project/results_test_task_123.jsonl"
    
    print("🎯 JSONLファイル監視によるDB自動インサート例")
    
    # 方法1: watchdog監視
    if WATCHDOG_AVAILABLE:
        print("\n📋 方法1: watchdog監視")
        monitor = JSONLFileMonitor(db_path, task_id, project_id, spider_name)
        # await monitor.start_monitoring(jsonl_file)
    
    # 方法2: tail -f方式
    print("\n📋 方法2: tail -f方式")
    tail_monitor = TailFollowMonitor(db_path, task_id, project_id, spider_name)
    # task = tail_monitor.start_monitoring(jsonl_file)
    
    # 方法3: バッチ処理
    print("\n📋 方法3: バッチ処理")
    batch_processor = BatchJSONLProcessor(db_path, task_id, project_id, spider_name)
    # await batch_processor.start_batch_processing(jsonl_file, interval=3)

if __name__ == "__main__":
    asyncio.run(example_usage())
