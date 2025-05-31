#!/usr/bin/env python3
"""
ScrapyTaskManagerにJSONLファイル監視機能を統合した例
"""
import asyncio
import subprocess
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import uuid

class ScrapyTaskManagerWithJSONLMonitor:
    """JSONLファイル監視機能付きScrapyTaskManager"""
    
    def __init__(self, 
                 task_id: str,
                 spider_config: Dict[str, Any],
                 progress_callback: Optional[Callable] = None,
                 websocket_callback: Optional[Callable] = None):
        self.task_id = task_id
        self.spider_config = spider_config
        self.progress_callback = progress_callback
        self.websocket_callback = websocket_callback
        
        # JSONLファイル監視用
        self.jsonl_monitor = None
        self.processed_items = 0
        self.is_monitoring = False
        
        # データベース設定
        self.db_path = "backend/database/scrapy_ui.db"
    
    async def execute(self) -> Dict[str, Any]:
        """スパイダーを実行してJSONLファイルを監視"""
        try:
            print(f"🚀 スパイダー実行開始: {self.spider_config['spider_name']}")
            
            # JSONLファイルパスを設定
            project_path = Path(self.spider_config['project_path'])
            jsonl_file = project_path / f"results_{self.task_id}.jsonl"
            
            # JSONLファイル監視を開始
            monitor_task = asyncio.create_task(
                self._start_jsonl_monitoring(str(jsonl_file))
            )
            
            # Scrapyプロセスを開始
            spider_task = asyncio.create_task(
                self._run_scrapy_process(project_path, jsonl_file)
            )
            
            # 両方のタスクを並行実行
            spider_result, _ = await asyncio.gather(
                spider_task,
                monitor_task,
                return_exceptions=True
            )
            
            # 監視停止
            self.is_monitoring = False
            
            return {
                'success': True,
                'task_id': self.task_id,
                'items_processed': self.processed_items,
                'spider_result': spider_result
            }
            
        except Exception as e:
            self.is_monitoring = False
            return {
                'success': False,
                'task_id': self.task_id,
                'error': str(e)
            }
    
    async def _run_scrapy_process(self, project_path: Path, jsonl_file: Path) -> Dict[str, Any]:
        """Scrapyプロセスを実行"""
        try:
            spider_name = self.spider_config['spider_name']
            
            # Scrapyコマンドを構築
            cmd = [
                'python', '-m', 'scrapy', 'crawl', spider_name,
                '-o', str(jsonl_file),  # JSONLファイル出力
                '-s', 'FEED_FORMAT=jsonlines',  # JSONL形式指定
                '-s', 'LOG_LEVEL=INFO'
            ]
            
            print(f"📋 Scrapyコマンド: {' '.join(cmd)}")
            
            # プロセス実行
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # プロセス完了を待機
            stdout, stderr = await process.communicate()
            
            result = {
                'return_code': process.returncode,
                'stdout': stdout.decode('utf-8'),
                'stderr': stderr.decode('utf-8')
            }
            
            if process.returncode == 0:
                print(f"✅ Scrapyプロセス完了")
            else:
                print(f"❌ Scrapyプロセスエラー: {result['stderr']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Scrapyプロセス実行エラー: {e}")
            raise
    
    async def _start_jsonl_monitoring(self, jsonl_file_path: str):
        """JSONLファイル監視を開始"""
        self.is_monitoring = True
        jsonl_path = Path(jsonl_file_path)
        
        print(f"🔍 JSONLファイル監視開始: {jsonl_path}")
        
        # ファイルが作成されるまで待機
        while not jsonl_path.exists() and self.is_monitoring:
            await asyncio.sleep(0.5)
        
        if not self.is_monitoring:
            return
        
        # tail -f方式でファイルを監視
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            # ファイルの末尾に移動
            f.seek(0, 2)
            
            while self.is_monitoring:
                line = f.readline()
                if line:
                    line = line.strip()
                    if line:
                        await self._process_jsonl_line(line)
                else:
                    await asyncio.sleep(0.1)
        
        print(f"🛑 JSONLファイル監視終了: 処理済みアイテム数 {self.processed_items}")
    
    async def _process_jsonl_line(self, json_line: str):
        """JSONLの1行を処理してDBにインサート"""
        try:
            # JSON解析
            item_data = json.loads(json_line)
            
            # DBにインサート
            await self._insert_item_to_db(item_data)
            
            # カウンター更新
            self.processed_items += 1
            
            # プログレス通知
            if self.progress_callback:
                await self.progress_callback({
                    'task_id': self.task_id,
                    'items_processed': self.processed_items,
                    'latest_item': item_data
                })
            
            # WebSocket通知
            if self.websocket_callback:
                await self.websocket_callback({
                    'type': 'item_scraped',
                    'task_id': self.task_id,
                    'item_count': self.processed_items,
                    'item_data': item_data
                })
            
            print(f"📝 アイテム処理完了: {self.processed_items}件目")
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析エラー: {e}")
        except Exception as e:
            print(f"❌ アイテム処理エラー: {e}")
    
    async def _insert_item_to_db(self, item_data: Dict[str, Any]):
        """アイテムをデータベースにインサート"""
        try:
            # 非同期でDBインサート
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._sync_insert_item, item_data)
            
        except Exception as e:
            print(f"❌ DBインサートエラー: {e}")
            raise
    
    def _sync_insert_item(self, item_data: Dict[str, Any]):
        """同期的にDBインサート（エグゼキューターで実行）"""
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
                self.spider_config.get('project_id', 'unknown'),
                self.spider_config['spider_name'],
                json.dumps(item_data, ensure_ascii=False),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ 同期DBインサートエラー: {e}")
            raise


# ScrapyServiceへの統合例
class ScrapyServiceWithJSONLMonitor:
    """JSONLファイル監視機能付きScrapyService"""
    
    def __init__(self):
        self.base_projects_dir = Path("scrapy_projects")
    
    async def run_spider_with_jsonl_monitor(self, 
                                          project_path: str, 
                                          spider_name: str, 
                                          task_id: str,
                                          settings: Optional[Dict[str, Any]] = None,
                                          websocket_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """JSONLファイル監視付きでスパイダーを実行"""
        
        try:
            print(f"🎯 JSONLファイル監視付きスパイダー実行: {spider_name}")
            
            # スパイダー設定
            spider_config = {
                'project_path': str(self.base_projects_dir / project_path),
                'project_id': project_path,
                'spider_name': spider_name,
                'settings': settings or {}
            }
            
            # プログレスコールバック
            async def progress_callback(progress_data):
                print(f"📊 進行状況: {progress_data}")
                # タスクステータスをDBに更新
                await self._update_task_progress(task_id, progress_data)
            
            # TaskManagerを作成して実行
            task_manager = ScrapyTaskManagerWithJSONLMonitor(
                task_id=task_id,
                spider_config=spider_config,
                progress_callback=progress_callback,
                websocket_callback=websocket_callback
            )
            
            result = await task_manager.execute()
            
            print(f"🎉 スパイダー実行完了: {result}")
            return result
            
        except Exception as e:
            print(f"❌ スパイダー実行エラー: {e}")
            return {
                'success': False,
                'task_id': task_id,
                'error': str(e)
            }
    
    async def _update_task_progress(self, task_id: str, progress_data: Dict[str, Any]):
        """タスクの進行状況をDBに更新"""
        try:
            # 非同期でDB更新
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._sync_update_task, task_id, progress_data)
            
        except Exception as e:
            print(f"❌ タスク進行状況更新エラー: {e}")
    
    def _sync_update_task(self, task_id: str, progress_data: Dict[str, Any]):
        """同期的にタスク進行状況を更新"""
        try:
            conn = sqlite3.connect("backend/database/scrapy_ui.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE tasks 
                SET items_scraped = ?, updated_at = ?
                WHERE id = ?
            """, (
                progress_data.get('items_processed', 0),
                datetime.now().isoformat(),
                task_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ 同期タスク更新エラー: {e}")


# 使用例
async def example_usage():
    """使用例"""
    
    print("🎯 JSONLファイル監視付きScrapyService使用例")
    
    service = ScrapyServiceWithJSONLMonitor()
    
    # WebSocketコールバック例
    async def websocket_callback(data):
        print(f"📡 WebSocket送信: {data}")
    
    # スパイダー実行
    result = await service.run_spider_with_jsonl_monitor(
        project_path="test_project",
        spider_name="test_spider",
        task_id="test_task_123",
        settings={'LOG_LEVEL': 'INFO'},
        websocket_callback=websocket_callback
    )
    
    print(f"🎉 実行結果: {result}")

if __name__ == "__main__":
    asyncio.run(example_usage())
