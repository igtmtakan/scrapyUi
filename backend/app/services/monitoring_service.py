"""
監視サービス
タスクの異常検知、アラート機能、ヘルスチェック機能を提供
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import deque

from ..database import SessionLocal, Task, TaskStatus, Schedule
from ..websocket.manager import manager
from .cache_manager import cache_manager

logger = logging.getLogger(__name__)

class MonitoringService:
    """監視サービス"""
    
    def __init__(self):
        self.monitoring_stats = {
            'total_alerts': 0,
            'stuck_task_alerts': 0,
            'failed_task_alerts': 0,
            'system_alerts': 0,
            'last_check': None
        }
        
        # アラート履歴（最大1000件）
        self.alert_history = deque(maxlen=1000)
        
        # 監視設定
        self.monitoring_config = {
            'stuck_task_threshold_minutes': 60,  # 1時間でスタック判定
            'pending_task_threshold_minutes': 30,  # 30分でPENDING異常判定
            'failed_task_alert_enabled': True,
            'system_health_check_enabled': True,
            'websocket_health_check_enabled': True
        }
        
        self.running = False
        self.last_task_counts = {}

    async def start_monitoring(self):
        """監視開始"""
        self.running = True
        logger.info("🔍 Task monitoring started")
        
        # 各監視タスクを並行実行
        await asyncio.gather(
            self._monitor_stuck_tasks(),
            self._monitor_failed_tasks(),
            self._monitor_system_health(),
            self._monitor_websocket_health(),
            return_exceptions=True
        )

    async def stop_monitoring(self):
        """監視停止"""
        self.running = False
        logger.info("🛑 Task monitoring stopped")

    async def _monitor_stuck_tasks(self):
        """スタックタスク監視"""
        while self.running:
            try:
                await asyncio.sleep(300)  # 5分間隔
                
                with SessionLocal() as db:
                    # スタックタスクを検索
                    stuck_threshold = datetime.now() - timedelta(
                        minutes=self.monitoring_config['stuck_task_threshold_minutes']
                    )
                    
                    stuck_tasks = db.query(Task).filter(
                        Task.status == TaskStatus.RUNNING,
                        Task.started_at < stuck_threshold
                    ).all()
                    
                    if stuck_tasks:
                        await self._send_stuck_task_alert(stuck_tasks)
                        
                    # 長時間PENDINGタスクもチェック
                    pending_threshold = datetime.now() - timedelta(
                        minutes=self.monitoring_config['pending_task_threshold_minutes']
                    )
                    
                    pending_tasks = db.query(Task).filter(
                        Task.status == TaskStatus.PENDING,
                        Task.created_at < pending_threshold
                    ).all()
                    
                    if pending_tasks:
                        await self._send_pending_task_alert(pending_tasks)
                        
            except Exception as e:
                logger.error(f"❌ Stuck task monitoring error: {e}")
                await asyncio.sleep(60)

    async def _monitor_failed_tasks(self):
        """失敗タスク監視"""
        while self.running:
            try:
                await asyncio.sleep(180)  # 3分間隔
                
                if not self.monitoring_config['failed_task_alert_enabled']:
                    continue
                
                with SessionLocal() as db:
                    # 最近失敗したタスクを検索
                    recent_threshold = datetime.now() - timedelta(minutes=10)
                    
                    failed_tasks = db.query(Task).filter(
                        Task.status == TaskStatus.FAILED,
                        Task.finished_at >= recent_threshold
                    ).all()
                    
                    if failed_tasks:
                        await self._send_failed_task_alert(failed_tasks)
                        
            except Exception as e:
                logger.error(f"❌ Failed task monitoring error: {e}")
                await asyncio.sleep(60)

    async def _monitor_system_health(self):
        """システムヘルス監視"""
        while self.running:
            try:
                await asyncio.sleep(600)  # 10分間隔
                
                if not self.monitoring_config['system_health_check_enabled']:
                    continue
                
                health_issues = []
                
                with SessionLocal() as db:
                    # タスク統計を取得
                    running_tasks = db.query(Task).filter(Task.status == TaskStatus.RUNNING).count()
                    failed_tasks = db.query(Task).filter(
                        Task.status == TaskStatus.FAILED,
                        Task.finished_at >= datetime.now() - timedelta(hours=1)
                    ).count()
                    
                    # 異常な状況をチェック
                    if running_tasks > 10:
                        health_issues.append(f"実行中タスクが多すぎます: {running_tasks}件")
                    
                    if failed_tasks > 5:
                        health_issues.append(f"1時間以内の失敗タスクが多すぎます: {failed_tasks}件")
                    
                    # スケジュール状況をチェック
                    active_schedules = db.query(Schedule).filter(Schedule.is_active == True).count()
                    if active_schedules == 0:
                        health_issues.append("アクティブなスケジュールがありません")
                
                if health_issues:
                    await self._send_system_health_alert(health_issues)
                    
            except Exception as e:
                logger.error(f"❌ System health monitoring error: {e}")
                await asyncio.sleep(60)

    async def _monitor_websocket_health(self):
        """WebSocket接続監視"""
        while self.running:
            try:
                await asyncio.sleep(300)  # 5分間隔
                
                if not self.monitoring_config['websocket_health_check_enabled']:
                    continue
                
                # WebSocket統計を取得
                try:
                    ws_stats = manager.get_stats()
                    connection_count = len(manager.active_connections)
                except Exception as e:
                    logger.error(f"❌ Failed to get WebSocket stats: {e}")
                    ws_stats = {}
                    connection_count = 0
                
                # 接続数の異常をチェック
                if connection_count == 0:
                    await self._send_websocket_alert("WebSocket接続がありません")
                elif connection_count > 50:
                    await self._send_websocket_alert(f"WebSocket接続数が異常に多いです: {connection_count}件")
                
                # 失敗メッセージ数をチェック
                failed_messages = ws_stats.get('total_messages_failed', 0)
                if failed_messages > 100:
                    await self._send_websocket_alert(f"WebSocketメッセージ送信失敗が多発しています: {failed_messages}件")
                    
            except Exception as e:
                logger.error(f"❌ WebSocket health monitoring error: {e}")
                await asyncio.sleep(60)

    async def _send_stuck_task_alert(self, stuck_tasks: List[Task]):
        """スタックタスクアラート送信"""
        alert_data = {
            "type": "stuck_task_alert",
            "severity": "warning",
            "timestamp": datetime.now().isoformat(),
            "message": f"{len(stuck_tasks)}個のタスクがスタックしています",
            "tasks": [
                {
                    "task_id": task.id,
                    "project_name": task.project.name if task.project else "Unknown",
                    "spider_name": task.spider.name if task.spider else "Unknown",
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "duration_minutes": int((datetime.now() - task.started_at).total_seconds() / 60) if task.started_at else 0
                }
                for task in stuck_tasks
            ]
        }
        
        await self._send_alert(alert_data)
        self.monitoring_stats['stuck_task_alerts'] += 1

    async def _send_pending_task_alert(self, pending_tasks: List[Task]):
        """長時間PENDINGタスクアラート送信"""
        alert_data = {
            "type": "pending_task_alert",
            "severity": "warning",
            "timestamp": datetime.now().isoformat(),
            "message": f"{len(pending_tasks)}個のタスクが長時間PENDING状態です",
            "tasks": [
                {
                    "task_id": task.id,
                    "project_name": task.project.name if task.project else "Unknown",
                    "spider_name": task.spider.name if task.spider else "Unknown",
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "pending_minutes": int((datetime.now() - task.created_at).total_seconds() / 60) if task.created_at else 0
                }
                for task in pending_tasks
            ]
        }
        
        await self._send_alert(alert_data)
        self.monitoring_stats['stuck_task_alerts'] += 1

    async def _send_failed_task_alert(self, failed_tasks: List[Task]):
        """失敗タスクアラート送信"""
        alert_data = {
            "type": "failed_task_alert",
            "severity": "error",
            "timestamp": datetime.now().isoformat(),
            "message": f"{len(failed_tasks)}個のタスクが失敗しました",
            "tasks": [
                {
                    "task_id": task.id,
                    "project_name": task.project.name if task.project else "Unknown",
                    "spider_name": task.spider.name if task.spider else "Unknown",
                    "finished_at": task.finished_at.isoformat() if task.finished_at else None,
                    "error_message": getattr(task, 'error_message', 'Unknown error')
                }
                for task in failed_tasks
            ]
        }
        
        await self._send_alert(alert_data)
        self.monitoring_stats['failed_task_alerts'] += 1

    async def _send_system_health_alert(self, health_issues: List[str]):
        """システムヘルスアラート送信"""
        alert_data = {
            "type": "system_health_alert",
            "severity": "warning",
            "timestamp": datetime.now().isoformat(),
            "message": f"システムヘルスに{len(health_issues)}個の問題があります",
            "issues": health_issues
        }
        
        await self._send_alert(alert_data)
        self.monitoring_stats['system_alerts'] += 1

    async def _send_websocket_alert(self, message: str):
        """WebSocketアラート送信"""
        alert_data = {
            "type": "websocket_alert",
            "severity": "warning",
            "timestamp": datetime.now().isoformat(),
            "message": message
        }
        
        await self._send_alert(alert_data)
        self.monitoring_stats['system_alerts'] += 1

    async def _send_alert(self, alert_data: Dict[str, Any]):
        """アラート送信"""
        try:
            # アラート履歴に追加
            self.alert_history.append(alert_data)
            
            # WebSocket経由でアラート送信
            await manager.broadcast(json.dumps({
                "type": "monitoring_alert",
                "data": alert_data
            }))
            
            # 必要に応じてキャッシュクリアをトリガー
            if alert_data["type"] in ["stuck_task_alert", "pending_task_alert"]:
                await cache_manager.manual_cache_clear(
                    reason=f"monitoring_alert_{alert_data['type']}",
                    user_id="system"
                )
            
            self.monitoring_stats['total_alerts'] += 1
            self.monitoring_stats['last_check'] = datetime.now()
            
            logger.warning(f"🚨 Alert sent: {alert_data['message']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send alert: {e}")

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """監視統計情報を取得"""
        return {
            **self.monitoring_stats,
            "monitoring_status": "running" if self.running else "stopped",
            "config": self.monitoring_config,
            "recent_alerts": list(self.alert_history)[-10:]  # 最新10件
        }

    def update_monitoring_config(self, config: Dict[str, Any]):
        """監視設定を更新"""
        self.monitoring_config.update(config)
        logger.info(f"📊 Monitoring config updated: {config}")

# グローバルインスタンス
monitoring_service = MonitoringService()
