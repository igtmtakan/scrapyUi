from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    """WebSocket接続を管理するクラス"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.task_subscribers: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        """WebSocket接続を受け入れる"""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """WebSocket接続を切断する"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # タスク購読からも削除
        for task_id, subscribers in self.task_subscribers.items():
            if websocket in subscribers:
                subscribers.remove(websocket)
    
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
    
    async def send_task_update(self, task_id: str, update: Dict[str, Any]):
        """特定のタスクの購読者に更新を送信"""
        if task_id not in self.task_subscribers:
            return
        
        message = json.dumps({
            "type": "task_update",
            "task_id": task_id,
            "data": update,
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

# グローバルインスタンス
manager = ConnectionManager()
