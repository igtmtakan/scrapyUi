from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Optional
import json
import asyncio
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket接続を管理するクラス（強化版）"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.task_subscribers: Dict[str, List[WebSocket]] = {}

        # 信頼性向上のための機能
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        self.message_queue: Dict[WebSocket, deque] = defaultdict(deque)
        self.retry_counts: Dict[str, int] = defaultdict(int)
        self.failed_messages: deque = deque(maxlen=1000)  # 失敗メッセージの履歴

        # 統計情報
        self.stats = {
            'total_connections': 0,
            'total_messages_sent': 0,
            'total_messages_failed': 0,
            'last_cleanup': datetime.now()
        }
    
    async def connect(self, websocket: WebSocket, client_info: Optional[Dict[str, Any]] = None):
        """WebSocket接続を受け入れる（強化版）"""
        await websocket.accept()
        self.active_connections.append(websocket)

        # 接続メタデータを保存
        self.connection_metadata[websocket] = {
            'connected_at': datetime.now(),
            'client_info': client_info or {},
            'last_ping': datetime.now(),
            'message_count': 0
        }

        self.stats['total_connections'] += 1
        logger.info(f"✅ WebSocket connected: {len(self.active_connections)} active connections")
    
    def disconnect(self, websocket: WebSocket):
        """WebSocket接続を切断する（強化版）"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # メタデータとキューをクリーンアップ
        if websocket in self.connection_metadata:
            connection_time = datetime.now() - self.connection_metadata[websocket]['connected_at']
            logger.info(f"🔌 WebSocket disconnected after {connection_time.total_seconds():.1f}s")
            del self.connection_metadata[websocket]

        if websocket in self.message_queue:
            del self.message_queue[websocket]

        # タスク購読からも削除
        for task_id, subscribers in list(self.task_subscribers.items()):
            if websocket in subscribers:
                subscribers.remove(websocket)
                if not subscribers:  # 購読者がいなくなったら削除
                    del self.task_subscribers[task_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """特定のWebSocketに個人メッセージを送信"""
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """全ての接続にメッセージをブロードキャスト"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # 切断された接続を削除
        for connection in disconnected:
            self.disconnect(connection)
    
    def subscribe_to_task(self, task_id: str, websocket: WebSocket):
        """特定のタスクの更新を購読"""
        if task_id not in self.task_subscribers:
            self.task_subscribers[task_id] = []
        
        if websocket not in self.task_subscribers[task_id]:
            self.task_subscribers[task_id].append(websocket)
    
    def unsubscribe_from_task(self, task_id: str, websocket: WebSocket):
        """タスクの購読を解除"""
        if task_id in self.task_subscribers and websocket in self.task_subscribers[task_id]:
            self.task_subscribers[task_id].remove(websocket)
    
    async def send_task_update(self, task_id: str, update: Dict[str, Any], retry_count: int = 3):
        """特定のタスクの購読者に更新を送信（強化版）"""
        if task_id not in self.task_subscribers:
            logger.debug(f"No subscribers for task {task_id}")
            return

        message_data = {
            "type": "task_update",
            "task_id": task_id,
            "data": update,
            "timestamp": datetime.now().isoformat(),
            "retry_count": retry_count
        }

        message = json.dumps(message_data)

        disconnected = []
        successful_sends = 0

        for websocket in self.task_subscribers[task_id]:
            success = await self._send_message_with_retry(websocket, message, task_id, retry_count)
            if success:
                successful_sends += 1
            else:
                disconnected.append(websocket)

        # 切断された接続を削除
        for websocket in disconnected:
            self.unsubscribe_from_task(task_id, websocket)

        # 統計更新
        self.stats['total_messages_sent'] += successful_sends
        self.stats['total_messages_failed'] += len(disconnected)

        logger.debug(f"📡 Task update sent to {successful_sends}/{len(self.task_subscribers[task_id])} subscribers for task {task_id}")

    async def _send_message_with_retry(self, websocket: WebSocket, message: str, context: str = "", max_retries: int = 3) -> bool:
        """リトライ機能付きメッセージ送信"""
        for attempt in range(max_retries):
            try:
                await websocket.send_text(message)

                # 成功時のメタデータ更新
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]['message_count'] += 1
                    self.connection_metadata[websocket]['last_ping'] = datetime.now()

                return True

            except Exception as e:
                logger.warning(f"⚠️ WebSocket send failed (attempt {attempt + 1}/{max_retries}) for {context}: {e}")

                if attempt < max_retries - 1:
                    await asyncio.sleep(0.1 * (attempt + 1))  # 指数バックオフ
                else:
                    # 最終的に失敗した場合
                    self.failed_messages.append({
                        'timestamp': datetime.now(),
                        'context': context,
                        'error': str(e),
                        'message_preview': message[:100] + '...' if len(message) > 100 else message
                    })
                    return False

        return False
    
    async def send_log_message(self, task_id: str, log_data: Dict[str, Any]):
        """ログメッセージを送信"""
        if task_id not in self.task_subscribers:
            return
        
        message = json.dumps({
            "type": "log",
            "task_id": task_id,
            "data": log_data,
            "timestamp": datetime.now().isoformat()
        })
        
        disconnected = []
        for websocket in self.task_subscribers[task_id]:
            try:
                await websocket.send_text(message)
            except:
                disconnected.append(websocket)
        
        # 切断された接続を削除
        for websocket in disconnected:
            self.unsubscribe_from_task(task_id, websocket)
    
    async def send_system_notification(self, notification: Dict[str, Any]):
        """システム通知を全体にブロードキャスト"""
        message = json.dumps({
            "type": "system_notification",
            "data": notification,
            "timestamp": datetime.now().isoformat()
        })
        
        await self.broadcast(message)

    async def cleanup_stale_connections(self):
        """古い接続をクリーンアップ"""
        current_time = datetime.now()
        stale_connections = []

        for websocket, metadata in list(self.connection_metadata.items()):
            # 5分以上応答がない接続を古いとみなす
            if current_time - metadata['last_ping'] > timedelta(minutes=5):
                stale_connections.append(websocket)

        for websocket in stale_connections:
            logger.warning(f"🧹 Cleaning up stale WebSocket connection")
            self.disconnect(websocket)

        if stale_connections:
            logger.info(f"🧹 Cleaned up {len(stale_connections)} stale connections")

    def get_stats(self) -> Dict[str, Any]:
        """WebSocket統計情報を取得"""
        current_time = datetime.now()

        # 接続時間の統計
        connection_durations = []
        for metadata in self.connection_metadata.values():
            duration = current_time - metadata['connected_at']
            connection_durations.append(duration.total_seconds())

        # タスク購読統計
        subscription_stats = {}
        for task_id, subscribers in self.task_subscribers.items():
            subscription_stats[task_id] = len(subscribers)

        return {
            **self.stats,
            'active_connections': len(self.active_connections),
            'task_subscriptions': len(self.task_subscribers),
            'total_subscribers': sum(len(subs) for subs in self.task_subscribers.values()),
            'failed_messages_recent': len(self.failed_messages),
            'connection_durations': {
                'count': len(connection_durations),
                'average': sum(connection_durations) / len(connection_durations) if connection_durations else 0,
                'max': max(connection_durations) if connection_durations else 0
            },
            'subscription_stats': subscription_stats,
            'last_cleanup': self.stats.get('last_cleanup', current_time)
        }

    async def health_check(self) -> Dict[str, Any]:
        """WebSocketの健康状態をチェック"""
        stats = self.get_stats()

        health_status = "healthy"
        issues = []

        # 接続数チェック
        if stats['active_connections'] == 0:
            health_status = "warning"
            issues.append("No active connections")
        elif stats['active_connections'] > 100:
            health_status = "warning"
            issues.append(f"High connection count: {stats['active_connections']}")

        # 失敗メッセージ数チェック
        if stats['total_messages_failed'] > stats['total_messages_sent'] * 0.1:
            health_status = "error"
            issues.append(f"High failure rate: {stats['total_messages_failed']}/{stats['total_messages_sent']}")

        # 古い接続のクリーンアップ
        await self.cleanup_stale_connections()

        return {
            "status": health_status,
            "stats": stats,
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        }

# グローバルインスタンス
manager = ConnectionManager()
