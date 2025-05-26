from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime, timedelta

from ..database import get_db, Notification as DBNotification
from ..models.schemas import Notification, NotificationCreate

router = APIRouter(
    responses={
        404: {"description": "Not found"},
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"}
    }
)

@router.get(
    "/", 
    response_model=List[Notification],
    summary="通知一覧取得",
    description="通知の一覧を取得します。",
    response_description="通知のリスト"
)
async def get_notifications(
    is_read: Optional[bool] = Query(None, description="読み取り状態でフィルタリング"),
    type: Optional[str] = Query(None, description="通知タイプでフィルタリング"),
    limit: int = Query(50, ge=1, le=100, description="取得件数の制限"),
    offset: int = Query(0, ge=0, description="オフセット"),
    db: Session = Depends(get_db)
):
    """
    ## 通知一覧取得
    
    通知の一覧を取得します。
    
    ### パラメータ
    - **is_read** (optional): 読み取り状態でフィルタリング
    - **type** (optional): 通知タイプでフィルタリング (info, warning, error, success)
    - **limit**: 取得件数の制限 (1-100, デフォルト: 50)
    - **offset**: オフセット (デフォルト: 0)
    
    ### レスポンス
    - **200**: 通知のリストを返します
    - **500**: サーバーエラー
    """
    query = db.query(DBNotification)
    
    if is_read is not None:
        query = query.filter(DBNotification.is_read == is_read)
    if type:
        query = query.filter(DBNotification.type == type)
    
    notifications = query.order_by(DBNotification.created_at.desc()).offset(offset).limit(limit).all()
    return notifications

@router.get(
    "/unread/count",
    summary="未読通知数取得",
    description="未読通知の数を取得します。"
)
async def get_unread_count(db: Session = Depends(get_db)):
    """
    ## 未読通知数取得
    
    未読通知の数を取得します。
    
    ### レスポンス
    - **200**: 未読通知数を返します
    - **500**: サーバーエラー
    """
    count = db.query(DBNotification).filter(DBNotification.is_read == False).count()
    return {"unread_count": count}

@router.post(
    "/", 
    response_model=Notification, 
    status_code=status.HTTP_201_CREATED,
    summary="通知作成",
    description="新しい通知を作成します。",
    response_description="作成された通知の情報"
)
async def create_notification(notification: NotificationCreate, db: Session = Depends(get_db)):
    """
    ## 通知作成
    
    新しい通知を作成します。
    
    ### リクエストボディ
    - **title**: 通知のタイトル
    - **message**: 通知のメッセージ
    - **type**: 通知タイプ (info, warning, error, success)
    - **task_id** (optional): 関連するタスクのID
    - **project_id** (optional): 関連するプロジェクトのID
    
    ### レスポンス
    - **201**: 通知が正常に作成された場合
    - **400**: リクエストデータが不正な場合
    - **500**: サーバーエラー
    """
    db_notification = DBNotification(
        id=str(uuid.uuid4()),
        title=notification.title,
        message=notification.message,
        type=notification.type,
        task_id=notification.task_id,
        project_id=notification.project_id
    )
    
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    return db_notification

@router.put(
    "/{notification_id}/read",
    summary="通知を既読にする",
    description="指定された通知を既読状態にします。"
)
async def mark_as_read(notification_id: str, db: Session = Depends(get_db)):
    """
    ## 通知を既読にする
    
    指定された通知を既読状態にします。
    
    ### パラメータ
    - **notification_id**: 通知ID
    
    ### レスポンス
    - **200**: 通知が正常に既読になった場合
    - **404**: 通知が見つからない場合
    - **500**: サーバーエラー
    """
    notification = db.query(DBNotification).filter(DBNotification.id == notification_id).first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    notification.is_read = True
    db.commit()
    
    return {"message": "Notification marked as read"}

@router.put(
    "/read-all",
    summary="全通知を既読にする",
    description="すべての未読通知を既読状態にします。"
)
async def mark_all_as_read(db: Session = Depends(get_db)):
    """
    ## 全通知を既読にする
    
    すべての未読通知を既読状態にします。
    
    ### レスポンス
    - **200**: すべての通知が正常に既読になった場合
    - **500**: サーバーエラー
    """
    updated_count = db.query(DBNotification).filter(
        DBNotification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    
    return {"message": f"Marked {updated_count} notifications as read"}

@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="通知削除",
    description="指定された通知を削除します。"
)
async def delete_notification(notification_id: str, db: Session = Depends(get_db)):
    """
    ## 通知削除
    
    指定された通知を削除します。
    
    ### パラメータ
    - **notification_id**: 通知ID
    
    ### レスポンス
    - **204**: 通知が正常に削除された場合
    - **404**: 通知が見つからない場合
    - **500**: サーバーエラー
    """
    notification = db.query(DBNotification).filter(DBNotification.id == notification_id).first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    db.delete(notification)
    db.commit()
    
    return None

@router.delete(
    "/cleanup",
    summary="古い通知のクリーンアップ",
    description="指定された日数より古い既読通知を削除します。"
)
async def cleanup_old_notifications(
    days_old: int = Query(30, ge=1, le=365, description="削除対象の日数"),
    db: Session = Depends(get_db)
):
    """
    ## 古い通知のクリーンアップ
    
    指定された日数より古い既読通知を削除します。
    
    ### パラメータ
    - **days_old**: 削除対象の日数 (1-365, デフォルト: 30)
    
    ### レスポンス
    - **200**: クリーンアップが正常に完了した場合
    - **500**: サーバーエラー
    """
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    deleted_count = db.query(DBNotification).filter(
        DBNotification.created_at < cutoff_date,
        DBNotification.is_read == True
    ).delete()
    
    db.commit()
    
    return {
        "message": f"Deleted {deleted_count} old notifications",
        "cutoff_date": cutoff_date.isoformat()
    }

# 通知作成のヘルパー関数
async def create_task_notification(
    db: Session,
    task_id: str,
    title: str,
    message: str,
    notification_type: str = "info",
    project_id: str = None
):
    """タスク関連の通知を作成するヘルパー関数"""
    notification = DBNotification(
        id=str(uuid.uuid4()),
        title=title,
        message=message,
        type=notification_type,
        task_id=task_id,
        project_id=project_id
    )
    
    db.add(notification)
    db.commit()
    return notification

async def create_system_notification(
    db: Session,
    title: str,
    message: str,
    notification_type: str = "info"
):
    """システム関連の通知を作成するヘルパー関数"""
    notification = DBNotification(
        id=str(uuid.uuid4()),
        title=title,
        message=message,
        type=notification_type
    )
    
    db.add(notification)
    db.commit()
    return notification
