"""
キャッシュ管理サービス
WebUIの状態同期とキャッシュクリア機能を提供
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from ..websocket.manager import manager
from ..database import SessionLocal, Task, TaskStatus

logger = logging.getLogger(__name__)

class CacheManager:
    """キャッシュ管理サービス"""
    
    def __init__(self):
        self.cache_stats = {
            'total_clears': 0,
            'auto_clears': 0,
            'manual_clears': 0,
            'last_clear': None
        }
        
        # キャッシュクリア条件
        self.auto_clear_conditions = {
            'task_status_change': True,
            'task_completion': True,
            'schedule_update': True,
            'system_restart': True
        }
        
        # 監視対象のタスク状態変更
        self.monitored_status_changes = [
            (TaskStatus.RUNNING, TaskStatus.FINISHED),
            (TaskStatus.RUNNING, TaskStatus.FAILED),
            (TaskStatus.PENDING, TaskStatus.RUNNING),
            (TaskStatus.PENDING, TaskStatus.FAILED)
        ]
        
        self.running = False

    async def start_cache_monitoring(self):
        """キャッシュ監視開始"""
        self.running = True
        logger.info("🗄️ Cache monitoring started")
        
        # 定期的なキャッシュクリア
        asyncio.create_task(self._periodic_cache_clear())
        
        # タスク状態変更監視
        asyncio.create_task(self._monitor_task_changes())

    async def stop_cache_monitoring(self):
        """キャッシュ監視停止"""
        self.running = False
        logger.info("🛑 Cache monitoring stopped")

    async def _periodic_cache_clear(self):
        """定期的なキャッシュクリア"""
        while self.running:
            try:
                await asyncio.sleep(300)  # 5分間隔
                await self._auto_cache_clear("periodic")
            except Exception as e:
                logger.error(f"❌ Periodic cache clear error: {e}")
                await asyncio.sleep(60)

    async def _monitor_task_changes(self):
        """タスク状態変更監視"""
        last_check = datetime.now()
        
        while self.running:
            try:
                await asyncio.sleep(30)  # 30秒間隔
                
                # 最近変更されたタスクをチェック
                with SessionLocal() as db:
                    recent_changes = db.query(Task).filter(
                        Task.updated_at >= last_check
                    ).all()
                    
                    if recent_changes:
                        await self._handle_task_changes(recent_changes)
                        last_check = datetime.now()
                        
            except Exception as e:
                logger.error(f"❌ Task change monitoring error: {e}")
                await asyncio.sleep(60)

    async def _handle_task_changes(self, changed_tasks: List[Task]):
        """タスク変更の処理"""
        significant_changes = []
        
        for task in changed_tasks:
            # 重要な状態変更かチェック
            if self._is_significant_change(task):
                significant_changes.append(task)
        
        if significant_changes:
            logger.info(f"🔄 Detected {len(significant_changes)} significant task changes")
            await self._auto_cache_clear("task_change", {
                'changed_tasks': [task.id for task in significant_changes]
            })

    def _is_significant_change(self, task: Task) -> bool:
        """重要な変更かどうかを判定"""
        # タスクの完了、失敗、開始などの重要な状態変更
        return task.status in [TaskStatus.FINISHED, TaskStatus.FAILED, TaskStatus.RUNNING]

    async def _auto_cache_clear(self, reason: str, context: Optional[Dict] = None):
        """自動キャッシュクリア"""
        try:
            clear_data = {
                "type": "auto_cache_clear",
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # WebSocket経由でキャッシュクリア通知
            await manager.broadcast(json.dumps({
                "type": "cache_clear",
                "data": clear_data,
                "message": f"キャッシュがクリアされました（理由: {reason}）"
            }))
            
            self.cache_stats['auto_clears'] += 1
            self.cache_stats['total_clears'] += 1
            self.cache_stats['last_clear'] = datetime.now()
            
            logger.info(f"✅ Auto cache clear completed: {reason}")
            
        except Exception as e:
            logger.error(f"❌ Auto cache clear failed: {e}")

    async def manual_cache_clear(self, reason: str = "manual", user_id: Optional[str] = None) -> Dict[str, Any]:
        """手動キャッシュクリア"""
        try:
            # 現在のタスク状況を取得
            with SessionLocal() as db:
                running_tasks = db.query(Task).filter(
                    Task.status == TaskStatus.RUNNING
                ).count()
                
                recent_completed = db.query(Task).filter(
                    Task.status.in_([TaskStatus.FINISHED, TaskStatus.FAILED]),
                    Task.finished_at >= datetime.now() - timedelta(hours=1)
                ).all()
            
            clear_data = {
                "type": "manual_cache_clear",
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "system_status": {
                    "running_tasks": running_tasks,
                    "recent_completed": len(recent_completed)
                },
                "completed_tasks": [
                    {
                        "task_id": task.id,
                        "status": task.status.value,
                        "items_count": task.items_count or 0,
                        "finished_at": task.finished_at.isoformat() if task.finished_at else None
                    }
                    for task in recent_completed
                ]
            }
            
            # WebSocket経由でキャッシュクリア通知
            await manager.broadcast(json.dumps({
                "type": "cache_clear",
                "data": clear_data,
                "message": "WebUIキャッシュがクリアされました。ページを更新してください。"
            }))
            
            self.cache_stats['manual_clears'] += 1
            self.cache_stats['total_clears'] += 1
            self.cache_stats['last_clear'] = datetime.now()
            
            logger.info(f"✅ Manual cache clear completed by user {user_id}")
            
            return {
                "status": "success",
                "message": "Cache cleared successfully",
                "data": clear_data
            }
            
        except Exception as e:
            logger.error(f"❌ Manual cache clear failed: {e}")
            return {
                "status": "error",
                "message": f"Cache clear failed: {str(e)}"
            }

    async def force_task_sync(self, task_id: str) -> Dict[str, Any]:
        """特定タスクの強制同期"""
        try:
            with SessionLocal() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                
                if not task:
                    return {
                        "status": "error",
                        "message": f"Task {task_id} not found"
                    }
                
                # タスクの最新状態をWebSocketで送信
                task_data = {
                    "id": task.id,
                    "status": task.status.value,
                    "itemsCount": task.items_count or 0,
                    "requestsCount": task.requests_count or 0,
                    "startedAt": task.started_at.isoformat() if task.started_at else None,
                    "finishedAt": task.finished_at.isoformat() if task.finished_at else None
                }
                
                await manager.send_task_update(task_id, task_data)
                
                logger.info(f"✅ Force sync completed for task {task_id}")
                
                return {
                    "status": "success",
                    "message": f"Task {task_id} synced successfully",
                    "task_data": task_data
                }
                
        except Exception as e:
            logger.error(f"❌ Force task sync failed for {task_id}: {e}")
            return {
                "status": "error",
                "message": f"Force sync failed: {str(e)}"
            }

    def get_cache_stats(self) -> Dict[str, Any]:
        """キャッシュ統計情報を取得"""
        return {
            **self.cache_stats,
            "monitoring_status": "running" if self.running else "stopped",
            "auto_clear_conditions": self.auto_clear_conditions
        }

# グローバルインスタンス
cache_manager = CacheManager()
