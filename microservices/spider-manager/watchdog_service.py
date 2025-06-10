#!/usr/bin/env python3
"""
ScrapyUI Spider Manager - Watchdog Service
scrapy crawlwithwatchdog のマイクロサービス版実装
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable

import aiofiles
import aioredis
import asyncpg
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WatchdogTask(BaseModel):
    task_id: str
    project_id: str
    spider_id: str
    project_path: str
    spider_name: str
    output_file: str
    settings: Dict = {}
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    status: str = "PENDING"
    items_count: int = 0
    requests_count: int = 0
    error_message: Optional[str] = None

class WatchdogMonitor:
    """ファイル監視とリアルタイムデータベース挿入"""
    
    def __init__(self, task: WatchdogTask, db_pool: asyncpg.Pool, 
                 redis: aioredis.Redis, websocket_callback: Optional[Callable] = None):
        self.task = task
        self.db_pool = db_pool
        self.redis = redis
        self.websocket_callback = websocket_callback
        
        self.is_monitoring = False
        self.processed_lines = 0
        self.last_file_size = 0
        self.last_websocket_time = 0
        self.websocket_interval = 15.0  # 15秒間隔
        
    async def start_monitoring(self):
        """ファイル監視開始"""
        self.is_monitoring = True
        output_file = Path(self.task.output_file)
        
        logger.info(f"🔍 Starting file monitoring: {output_file}")
        
        # ファイルが作成されるまで待機
        max_wait = 30  # 30秒待機
        wait_count = 0
        
        while not output_file.exists() and wait_count < max_wait:
            await asyncio.sleep(1)
            wait_count += 1
        
        if not output_file.exists():
            logger.warning(f"⚠️ Output file not created within {max_wait}s: {output_file}")
            return
        
        # ファイル監視ループ
        while self.is_monitoring:
            try:
                await self._check_file_changes(output_file)
                await asyncio.sleep(2)  # 2秒間隔でチェック
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def _check_file_changes(self, file_path: Path):
        """ファイル変更をチェックして新しい行を処理"""
        try:
            current_size = file_path.stat().st_size
            
            if current_size > self.last_file_size:
                # ファイルサイズが増加した場合、新しい行を読み取り
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    await f.seek(self.last_file_size)
                    new_content = await f.read()
                
                if new_content.strip():
                    lines = new_content.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            await self._process_new_line(line.strip())
                
                self.last_file_size = current_size
                
        except Exception as e:
            logger.error(f"❌ File check error: {e}")
    
    async def _process_new_line(self, line: str):
        """新しい行を処理してデータベースに挿入"""
        try:
            # JSON行をパース
            data = json.loads(line)
            self.processed_lines += 1
            
            # データベースに挿入
            await self._insert_result_to_db(data)
            
            # タスク統計更新
            await self._update_task_stats()
            
            # WebSocket通知（頻度制限あり）
            await self._send_websocket_notification()
            
        except json.JSONDecodeError:
            logger.warning(f"⚠️ Invalid JSON line: {line[:100]}...")
        except Exception as e:
            logger.error(f"❌ Line processing error: {e}")
    
    async def _insert_result_to_db(self, data: Dict):
        """結果をデータベースに挿入"""
        try:
            async with self.db_pool.acquire() as conn:
                # 重複チェック用ハッシュ計算
                import hashlib
                data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
                data_hash = hashlib.md5(data_str.encode('utf-8')).hexdigest()
                
                # 結果挿入
                await conn.execute("""
                    INSERT INTO results (id, task_id, data, hash, created_at)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (hash) DO NOTHING
                """, 
                f"{self.task.task_id}_{self.processed_lines}",
                self.task.task_id,
                json.dumps(data),
                data_hash,
                datetime.now()
                )
                
        except Exception as e:
            logger.error(f"❌ Database insert error: {e}")
    
    async def _update_task_stats(self):
        """タスク統計を更新"""
        try:
            # Redis経由でタスク統計更新
            await self.redis.hset(f"task:{self.task.task_id}", mapping={
                "items_count": self.processed_lines,
                "status": "RUNNING",
                "updated_at": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Stats update error: {e}")
    
    async def _send_websocket_notification(self):
        """WebSocket通知送信（頻度制限あり）"""
        try:
            current_time = time.time()
            
            if current_time - self.last_websocket_time >= self.websocket_interval:
                if self.websocket_callback:
                    notification_data = {
                        "task_id": self.task.task_id,
                        "type": "progress_update",
                        "items_processed": self.processed_lines,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await self.websocket_callback(notification_data)
                    self.last_websocket_time = current_time
                
                # Redis経由でWebSocket通知
                await self.redis.publish("events:spider_progress", json.dumps({
                    "task_id": self.task.task_id,
                    "items_processed": self.processed_lines,
                    "timestamp": datetime.now().isoformat()
                }))
                
        except Exception as e:
            logger.error(f"❌ WebSocket notification error: {e}")
    
    def stop_monitoring(self):
        """監視停止"""
        self.is_monitoring = False
        logger.info(f"🛑 Monitoring stopped: {self.processed_lines} items processed")

class WatchdogSpiderService:
    """scrapy crawlwithwatchdog マイクロサービス実装"""
    
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis: Optional[aioredis.Redis] = None
        self.active_monitors: Dict[str, WatchdogMonitor] = {}
        self.base_projects_path = Path("/app/scrapy_projects")
        
    async def initialize(self):
        """初期化"""
        try:
            # Redis接続
            self.redis = aioredis.from_url(
                "redis://localhost:6379",
                encoding="utf-8",
                decode_responses=True
            )
            
            # PostgreSQL接続
            self.db_pool = await asyncpg.create_pool(
                "postgresql://user:password@localhost:5432/scrapyui",
                min_size=2,
                max_size=10
            )
            
            logger.info("🔗 Watchdog Spider Service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize: {e}")
            raise
    
    async def execute_spider_with_watchdog(self, task: WatchdogTask, 
                                         websocket_callback: Optional[Callable] = None) -> Dict:
        """watchdog監視付きでスパイダーを実行"""
        try:
            logger.info(f"🚀 Starting spider with watchdog: {task.spider_name}")
            
            # タスク開始状態に更新
            task.status = "RUNNING"
            task.started_at = datetime.now().isoformat()
            
            await self.redis.hset(f"task:{task.task_id}", mapping={
                "status": "RUNNING",
                "started_at": task.started_at
            })
            
            # 監視開始
            monitor = WatchdogMonitor(task, self.db_pool, self.redis, websocket_callback)
            self.active_monitors[task.task_id] = monitor
            
            # 監視を別タスクで開始
            monitor_task = asyncio.create_task(monitor.start_monitoring())
            
            # Scrapyプロセス実行
            scrapy_result = await self._execute_scrapy_process(task)
            
            # 少し待ってから監視停止
            await asyncio.sleep(5)
            monitor.stop_monitoring()
            
            # 監視タスク終了待機
            try:
                await asyncio.wait_for(monitor_task, timeout=10)
            except asyncio.TimeoutError:
                monitor_task.cancel()
            
            # 最終統計更新
            await self._finalize_task_stats(task, monitor.processed_lines)
            
            # 監視リストから削除
            if task.task_id in self.active_monitors:
                del self.active_monitors[task.task_id]
            
            return {
                "success": scrapy_result["success"],
                "task_id": task.task_id,
                "items_processed": monitor.processed_lines,
                "return_code": scrapy_result.get("return_code", 0),
                "output_file": task.output_file
            }
            
        except Exception as e:
            logger.error(f"❌ Spider execution error: {e}")
            
            # エラー状態に更新
            await self.redis.hset(f"task:{task.task_id}", mapping={
                "status": "FAILED",
                "error": str(e),
                "finished_at": datetime.now().isoformat()
            })
            
            return {
                "success": False,
                "task_id": task.task_id,
                "error": str(e)
            }
    
    async def _execute_scrapy_process(self, task: WatchdogTask) -> Dict:
        """Scrapyプロセスを実行"""
        try:
            project_path = self.base_projects_path / task.project_path
            
            # コマンド構築
            cmd = [
                sys.executable, "-m", "scrapy", "crawl", task.spider_name,
                "-o", task.output_file,
                "-s", "FEED_FORMAT=jsonlines",
                "-s", "LOG_LEVEL=INFO"
            ]
            
            # 設定追加
            for key, value in task.settings.items():
                cmd.extend(["-s", f"{key}={value}"])
            
            logger.info(f"🕷️ Executing: {' '.join(cmd)}")
            
            # プロセス実行
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "return_code": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore')
            }
            
        except Exception as e:
            logger.error(f"❌ Scrapy process error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _finalize_task_stats(self, task: WatchdogTask, items_count: int):
        """タスク統計の最終更新"""
        try:
            task.status = "COMPLETED"
            task.finished_at = datetime.now().isoformat()
            task.items_count = items_count
            
            await self.redis.hset(f"task:{task.task_id}", mapping={
                "status": "COMPLETED",
                "finished_at": task.finished_at,
                "items_count": items_count
            })
            
            # 完了イベント発行
            await self.redis.publish("events:spider_completed", json.dumps({
                "task_id": task.task_id,
                "status": "COMPLETED",
                "items_count": items_count,
                "timestamp": task.finished_at
            }))
            
            logger.info(f"✅ Task completed: {task.task_id} ({items_count} items)")
            
        except Exception as e:
            logger.error(f"❌ Finalization error: {e}")
    
    async def stop_task(self, task_id: str) -> bool:
        """実行中タスクを停止"""
        try:
            if task_id in self.active_monitors:
                monitor = self.active_monitors[task_id]
                monitor.stop_monitoring()
                del self.active_monitors[task_id]
                
                await self.redis.hset(f"task:{task_id}", mapping={
                    "status": "CANCELLED",
                    "finished_at": datetime.now().isoformat()
                })
                
                logger.info(f"🛑 Task stopped: {task_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Stop task error: {e}")
            return False
    
    async def get_active_tasks(self) -> List[str]:
        """アクティブなタスク一覧を取得"""
        return list(self.active_monitors.keys())
    
    async def cleanup(self):
        """リソースクリーンアップ"""
        # 全監視停止
        for monitor in self.active_monitors.values():
            monitor.stop_monitoring()
        
        self.active_monitors.clear()
        
        # 接続クローズ
        if self.redis:
            await self.redis.close()
        if self.db_pool:
            await self.db_pool.close()
        
        logger.info("🧹 Watchdog Spider Service cleanup completed")
