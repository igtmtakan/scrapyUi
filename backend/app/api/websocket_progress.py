from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
from typing import Dict, Set
import logging

from ..database import SessionLocal, Task as DBTask
from ..services.realtime_websocket_manager import realtime_websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# タスクIDごとのWebSocket接続を管理
task_connections: Dict[str, Set[WebSocket]] = {}

@router.websocket("/ws/progress/{task_id}")
async def websocket_progress_endpoint(websocket: WebSocket, task_id: str):
    """
    進捗バー用WebSocketエンドポイント
    特定のタスクの進捗情報をリアルタイムで送信
    """
    client_ip = websocket.client.host if websocket.client else "unknown"
    logger.info(f"📡 進捗WebSocket接続試行: タスクID {task_id}, クライアント: {client_ip}")

    try:
        await websocket.accept()
        logger.info(f"📡 進捗WebSocket接続受諾完了: タスクID {task_id}, クライアント: {client_ip}")
    except Exception as accept_error:
        logger.error(f"❌ 進捗WebSocket接続受諾エラー: {type(accept_error).__name__}: {str(accept_error)}")
        return

    # 接続をタスクIDごとに管理
    if task_id not in task_connections:
        task_connections[task_id] = set()
    task_connections[task_id].add(websocket)

    logger.info(f"📡 Rich進捗WebSocket接続: タスクID {task_id}, クライアント: {websocket.client}")
    logger.info(f"📡 現在の接続数: {len(task_connections[task_id])}")

    try:
        # データベースセッションを作成
        db = SessionLocal()

        # 初期データを送信
        task = db.query(DBTask).filter(DBTask.id == task_id).first()
        if task:
            # started_atがNULLの場合はcreated_atを使用
            effective_start_time = task.started_at or task.created_at

            # 経過時間を計算
            elapsed_time = 0
            if effective_start_time:
                from datetime import datetime
                if task.finished_at:
                    elapsed_time = int((task.finished_at - effective_start_time).total_seconds())
                else:
                    elapsed_time = int((datetime.now() - effective_start_time).total_seconds())

            # 進捗率を計算
            progress_percentage = 0
            items_scraped = task.items_count or 0
            requests_count = task.requests_count or 0

            if requests_count > 0:
                progress_percentage = min((items_scraped / requests_count) * 100, 100)
            elif items_scraped > 0:
                # アイテムがある場合は最低10%表示
                progress_percentage = max(10, min(items_scraped / 10, 100))

            initial_data = {
                "type": "rich_progress",
                "data": {
                    "taskId": task.id,
                    "status": task.status.value.lower() if task.status else "unknown",
                    "itemsScraped": items_scraped,
                    "requestsCount": requests_count,
                    "errorCount": task.error_count or 0,
                    "startedAt": effective_start_time.isoformat() if effective_start_time else None,
                    "finishedAt": task.finished_at.isoformat() if task.finished_at else None,
                    "elapsedTime": elapsed_time,
                    "progressPercentage": progress_percentage,
                    "itemsPerSecond": (items_scraped / max(elapsed_time, 1)) if elapsed_time > 0 else 0,
                    "requestsPerSecond": (requests_count / max(elapsed_time, 1)) if elapsed_time > 0 else 0
                }
            }

            try:
                await websocket.send_text(json.dumps(initial_data, ensure_ascii=False))
                logger.info(f"📡 Rich進捗初期データ送信完了: タスクID {task_id}")
            except Exception as send_error:
                logger.error(f"❌ Rich進捗初期データ送信エラー: {type(send_error).__name__}: {str(send_error)}")
                logger.error(f"❌ 送信データ: {json.dumps(initial_data, ensure_ascii=False)[:200]}...")
                return
        else:
            # タスクが見つからない場合はエラーメッセージを送信
            error_data = {
                "type": "error",
                "data": {
                    "message": f"タスクID {task_id} が見つかりません",
                    "code": "TASK_NOT_FOUND"
                }
            }
            try:
                await websocket.send_text(json.dumps(error_data, ensure_ascii=False))
            except Exception:
                pass
            return
        
        # 接続を維持し、定期的にデータを更新
        while True:
            # 30秒ごとにタスクデータを更新して送信
            await asyncio.sleep(30)
            
            # 最新のタスクデータを取得（新しいセッションを使用）
            with SessionLocal() as fresh_db:
                task = fresh_db.query(DBTask).filter(DBTask.id == task_id).first()
            if task:
                # started_atがNULLの場合はcreated_atを使用
                effective_start_time = task.started_at or task.created_at

                # 経過時間を計算
                elapsed_time = 0
                if effective_start_time:
                    from datetime import datetime
                    if task.finished_at:
                        elapsed_time = int((task.finished_at - effective_start_time).total_seconds())
                    else:
                        elapsed_time = int((datetime.now() - effective_start_time).total_seconds())

                # 進捗率を計算
                progress_percentage = 0
                items_scraped = task.items_count or 0
                requests_count = task.requests_count or 0

                if requests_count > 0:
                    progress_percentage = min((items_scraped / requests_count) * 100, 100)
                elif items_scraped > 0:
                    # アイテムがある場合は最低10%表示
                    progress_percentage = max(10, min(items_scraped / 10, 100))

                # 進捗データを作成
                progress_data = {
                    "type": "progress",
                    "data": {
                        "taskId": task.id,
                        "status": task.status.value.lower() if task.status else "unknown",
                        "itemsScraped": items_scraped,
                        "requestsCount": requests_count,
                        "errorCount": task.error_count or 0,
                        "startedAt": effective_start_time.isoformat() if effective_start_time else None,
                        "finishedAt": task.finished_at.isoformat() if task.finished_at else None,
                        "elapsedTime": elapsed_time,
                        "progressPercentage": progress_percentage,
                        "itemsPerSecond": (items_scraped / max(elapsed_time, 1)) if elapsed_time > 0 else 0,
                        "requestsPerSecond": (requests_count / max(elapsed_time, 1)) if elapsed_time > 0 else 0
                    }
                }
                
                # 実行中の場合は追加の統計情報を計算
                if task.status.value == "RUNNING" and elapsed_time > 0:
                    items_per_second = (task.items_count or 0) / elapsed_time
                    requests_per_second = (task.requests_count or 0) / elapsed_time
                    
                    progress_data["data"]["itemsPerSecond"] = round(items_per_second, 2)
                    progress_data["data"]["requestsPerSecond"] = round(requests_per_second, 2)
                
                # 完了時の処理
                if task.status.value in ["FINISHED", "FAILED"] and task.finished_at:
                    progress_data["data"]["status"] = "completed" if task.status.value == "FINISHED" else "failed"

                try:
                    await websocket.send_text(json.dumps(progress_data, ensure_ascii=False))
                except Exception as send_error:
                    logger.error(f"❌ Rich進捗データ送信エラー: {type(send_error).__name__}: {str(send_error)}")
                    logger.error(f"❌ 送信データ: {json.dumps(progress_data, ensure_ascii=False)[:200]}...")
                    logger.error(f"❌ WebSocket状態: {websocket.client_state}")
                    break

                # タスクが完了している場合は接続を終了
                if task.status.value in ["FINISHED", "FAILED"]:
                    logger.info(f"📡 Rich進捗WebSocket終了: タスク完了 {task_id}")
                    break
            else:
                # タスクが見つからない場合は接続を終了
                logger.warning(f"📡 Rich進捗WebSocket終了: タスク未発見 {task_id}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"📡 Rich進捗WebSocket切断: タスクID {task_id}, クライアント: {websocket.client}")
    except Exception as e:
        logger.error(f"❌ Rich進捗WebSocketエラー: {type(e).__name__}: {str(e)}")
        logger.error(f"❌ タスクID: {task_id}, クライアント: {websocket.client}")
    finally:
        # データベースセッションをクリーンアップ
        try:
            db.close()
        except:
            pass

        # 接続を削除
        if task_id in task_connections:
            task_connections[task_id].discard(websocket)
            remaining_connections = len(task_connections[task_id])
            logger.info(f"📡 接続削除後の残り接続数: {remaining_connections}")
            if not task_connections[task_id]:
                del task_connections[task_id]
                logger.info(f"📡 タスクID {task_id} の接続管理を削除")


async def broadcast_progress_update(task_id: str, progress_data: dict):
    """
    特定のタスクの進捗更新をすべての接続クライアントにブロードキャスト
    """
    if task_id not in task_connections:
        return
    
    message = {
        "type": "progress",
        "data": progress_data
    }
    
    message_str = json.dumps(message, ensure_ascii=False)
    disconnected = set()
    
    for websocket in task_connections[task_id].copy():
        try:
            await websocket.send_text(message_str)
        except Exception as e:
            logger.error(f"❌ 進捗ブロードキャストエラー: {type(e).__name__}: {str(e)}")
            logger.error(f"❌ ブロードキャストデータ: {message_str[:200]}...")
            disconnected.add(websocket)
    
    # 切断された接続を削除
    for websocket in disconnected:
        task_connections[task_id].discard(websocket)
    
    if not task_connections[task_id]:
        del task_connections[task_id]


@router.websocket("/ws/schedules")
async def websocket_schedules_endpoint(websocket: WebSocket):
    """
    スケジュール全体の状態更新用WebSocketエンドポイント
    """
    await websocket.accept()
    
    # リアルタイムWebSocketマネージャーに接続を追加
    realtime_websocket_manager.add_connection(websocket)
    
    logger.info("📡 スケジュール状態WebSocket接続")
    
    try:
        # 接続を維持
        while True:
            # クライアントからのメッセージを待機（keepalive）
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # タイムアウトの場合はpingを送信
                await websocket.send_text(json.dumps({"type": "ping"}, ensure_ascii=False))
                
    except WebSocketDisconnect:
        logger.info("📡 スケジュール状態WebSocket切断")
    except Exception as e:
        logger.error(f"❌ スケジュール状態WebSocketエラー: {e}")
    finally:
        # 接続を削除
        realtime_websocket_manager.remove_connection(websocket)


def get_task_connections_count() -> int:
    """現在のタスク進捗WebSocket接続数を取得"""
    return sum(len(connections) for connections in task_connections.values())


def get_connected_task_ids() -> list:
    """接続中のタスクIDリストを取得"""
    return list(task_connections.keys())
