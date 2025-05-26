from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from typing import Dict, Any

from .manager import manager

router = APIRouter()

@router.websocket("/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket接続エンドポイント

    クライアントIDを使用してWebSocket接続を管理します。
    リアルタイムでタスクの状況、ログ、システム通知を受信できます。
    """
    await manager.connect(websocket)

    try:
        # 接続確認メッセージを送信
        await manager.send_personal_message(
            json.dumps({
                "type": "connection_established",
                "client_id": client_id,
                "message": "WebSocket connection established"
            }),
            websocket
        )

        while True:
            # クライアントからのメッセージを受信
            data = await websocket.receive_text()
            message = json.loads(data)

            # メッセージタイプに応じて処理
            await handle_websocket_message(websocket, message)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client {client_id} disconnected")
    except Exception as e:
        print(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(websocket)

async def handle_websocket_message(websocket: WebSocket, message: Dict[str, Any]):
    """WebSocketメッセージを処理"""

    message_type = message.get("type")

    if message_type == "subscribe_task":
        # タスクの更新を購読
        task_id = message.get("task_id")
        if task_id:
            manager.subscribe_to_task(task_id, websocket)
            await manager.send_personal_message(
                json.dumps({
                    "type": "subscription_confirmed",
                    "task_id": task_id
                }),
                websocket
            )

    elif message_type == "unsubscribe_task":
        # タスクの購読を解除
        task_id = message.get("task_id")
        if task_id:
            manager.unsubscribe_from_task(task_id, websocket)
            await manager.send_personal_message(
                json.dumps({
                    "type": "unsubscription_confirmed",
                    "task_id": task_id
                }),
                websocket
            )

    elif message_type == "ping":
        # ピング応答
        await manager.send_personal_message(
            json.dumps({
                "type": "pong",
                "timestamp": message.get("timestamp")
            }),
            websocket
        )

    elif message_type == "get_task_status":
        # タスクステータスの即座取得
        task_id = message.get("task_id")
        if task_id:
            # TODO: データベースからタスク情報を取得して送信
            pass

@router.websocket("/task/{task_id}")
async def task_websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    特定のタスク専用WebSocket接続

    指定されたタスクのリアルタイム更新のみを受信します。
    """
    await manager.connect(websocket)
    manager.subscribe_to_task(task_id, websocket)

    try:
        # 接続確認メッセージを送信
        await manager.send_personal_message(
            json.dumps({
                "type": "task_connection_established",
                "task_id": task_id,
                "message": f"Connected to task {task_id}"
            }),
            websocket
        )

        while True:
            # クライアントからのメッセージを受信（主にping/pong）
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await manager.send_personal_message(
                    json.dumps({
                        "type": "pong",
                        "task_id": task_id,
                        "timestamp": message.get("timestamp")
                    }),
                    websocket
                )

    except WebSocketDisconnect:
        manager.unsubscribe_from_task(task_id, websocket)
        manager.disconnect(websocket)
        print(f"Task {task_id} WebSocket disconnected")
    except Exception as e:
        print(f"Task WebSocket error for {task_id}: {e}")
        manager.unsubscribe_from_task(task_id, websocket)
        manager.disconnect(websocket)
