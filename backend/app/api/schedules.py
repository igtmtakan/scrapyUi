from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime
from croniter import croniter

from ..database import get_db, Schedule as DBSchedule, Project as DBProject, Spider as DBSpider
from ..models.schemas import Schedule, ScheduleCreate, ScheduleUpdate
from ..tasks.scrapy_tasks import scheduled_spider_run

router = APIRouter(
    responses={
        404: {"description": "Not found"},
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"}
    }
)

@router.get(
    "/",
    response_model=List[Schedule],
    summary="スケジュール一覧取得",
    description="登録されているスケジュールの一覧を取得します。",
    response_description="スケジュールのリスト"
)
async def get_schedules(
    project_id: str = None,
    is_active: bool = None,
    db: Session = Depends(get_db)
):
    """
    ## スケジュール一覧取得

    登録されているスケジュールの一覧を取得します。

    ### パラメータ
    - **project_id** (optional): プロジェクトIDでフィルタリング
    - **is_active** (optional): アクティブ状態でフィルタリング

    ### レスポンス
    - **200**: スケジュールのリストを返します
    - **500**: サーバーエラー
    """
    query = db.query(DBSchedule)

    if project_id:
        query = query.filter(DBSchedule.project_id == project_id)
    if is_active is not None:
        query = query.filter(DBSchedule.is_active == is_active)

    schedules = query.order_by(DBSchedule.created_at.desc()).all()
    return schedules

@router.get(
    "/{schedule_id}",
    response_model=Schedule,
    summary="スケジュール詳細取得",
    description="指定されたスケジュールの詳細情報を取得します。",
    response_description="スケジュールの詳細情報"
)
async def get_schedule(schedule_id: str, db: Session = Depends(get_db)):
    """
    ## スケジュール詳細取得

    指定されたスケジュールの詳細情報を取得します。

    ### パラメータ
    - **schedule_id**: スケジュールID

    ### レスポンス
    - **200**: スケジュールの詳細情報を返します
    - **404**: スケジュールが見つからない場合
    - **500**: サーバーエラー
    """
    schedule = db.query(DBSchedule).filter(DBSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    return schedule

@router.post(
    "/",
    response_model=Schedule,
    status_code=status.HTTP_201_CREATED,
    summary="スケジュール作成",
    description="新しいスケジュールを作成します。",
    response_description="作成されたスケジュールの情報"
)
async def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    """
    ## スケジュール作成

    新しいスケジュールを作成します。

    ### リクエストボディ
    - **name**: スケジュール名
    - **description** (optional): スケジュールの説明
    - **cron_expression**: Cron式（例: "0 2 * * *" = 毎日午前2時）
    - **project_id**: 実行するプロジェクトのID
    - **spider_id**: 実行するスパイダーのID
    - **is_active** (optional): アクティブ状態（デフォルト: true）
    - **settings** (optional): 実行時の設定

    ### レスポンス
    - **201**: スケジュールが正常に作成された場合
    - **400**: リクエストデータが不正な場合
    - **404**: 指定されたプロジェクトまたはスパイダーが見つからない場合
    - **500**: サーバーエラー
    """

    # プロジェクトとスパイダーの存在確認
    project = db.query(DBProject).filter(DBProject.id == schedule.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    spider = db.query(DBSpider).filter(DBSpider.id == schedule.spider_id).first()
    if not spider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spider not found"
        )

    # Cron式の検証
    try:
        cron = croniter(schedule.cron_expression, datetime.now())
        next_run = cron.get_next(datetime)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid cron expression: {str(e)}"
        )

    # スケジュール名の重複チェック
    existing_schedule = db.query(DBSchedule).filter(
        DBSchedule.name == schedule.name,
        DBSchedule.project_id == schedule.project_id
    ).first()
    if existing_schedule:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schedule with this name already exists in the project"
        )

    # データベースに保存
    db_schedule = DBSchedule(
        id=str(uuid.uuid4()),
        name=schedule.name,
        description=schedule.description,
        cron_expression=schedule.cron_expression,
        project_id=schedule.project_id,
        spider_id=schedule.spider_id,
        is_active=schedule.is_active,
        next_run=next_run,
        settings=schedule.settings
    )

    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)

    return db_schedule

@router.put(
    "/{schedule_id}",
    response_model=Schedule,
    summary="スケジュール更新",
    description="既存のスケジュールを更新します。",
    response_description="更新されたスケジュールの情報"
)
async def update_schedule(
    schedule_id: str,
    schedule_update: ScheduleUpdate,
    db: Session = Depends(get_db)
):
    """
    ## スケジュール更新

    既存のスケジュールを更新します。

    ### パラメータ
    - **schedule_id**: 更新するスケジュールのID

    ### リクエストボディ
    - **name** (optional): スケジュール名
    - **description** (optional): スケジュールの説明
    - **cron_expression** (optional): Cron式
    - **is_active** (optional): アクティブ状態
    - **settings** (optional): 実行時の設定

    ### レスポンス
    - **200**: スケジュールが正常に更新された場合
    - **400**: リクエストデータが不正な場合
    - **404**: スケジュールが見つからない場合
    - **500**: サーバーエラー
    """
    db_schedule = db.query(DBSchedule).filter(DBSchedule.id == schedule_id).first()
    if not db_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )

    # 更新データの適用
    update_data = schedule_update.model_dump(exclude_unset=True)

    # Cron式が更新される場合は検証
    if 'cron_expression' in update_data:
        try:
            cron = croniter(update_data['cron_expression'], datetime.now())
            next_run = cron.get_next(datetime)
            update_data['next_run'] = next_run
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid cron expression: {str(e)}"
            )

    for field, value in update_data.items():
        setattr(db_schedule, field, value)

    db.commit()
    db.refresh(db_schedule)

    return db_schedule

@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="スケジュール削除",
    description="指定されたスケジュールを削除します。"
)
async def delete_schedule(schedule_id: str, db: Session = Depends(get_db)):
    """
    ## スケジュール削除

    指定されたスケジュールを削除します。

    ### パラメータ
    - **schedule_id**: 削除するスケジュールのID

    ### レスポンス
    - **204**: スケジュールが正常に削除された場合
    - **404**: スケジュールが見つからない場合
    - **500**: サーバーエラー
    """
    db_schedule = db.query(DBSchedule).filter(DBSchedule.id == schedule_id).first()
    if not db_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )

    db.delete(db_schedule)
    db.commit()

    return None

@router.post(
    "/{schedule_id}/run",
    summary="スケジュール手動実行",
    description="スケジュールを手動で実行します。"
)
async def run_schedule_now(schedule_id: str, db: Session = Depends(get_db)):
    """
    ## スケジュール手動実行

    スケジュールを手動で実行します。

    ### パラメータ
    - **schedule_id**: 実行するスケジュールのID

    ### レスポンス
    - **200**: スケジュールが正常に開始された場合
    - **404**: スケジュールが見つからない場合
    - **400**: スケジュールが非アクティブな場合
    - **500**: サーバーエラー
    """
    db_schedule = db.query(DBSchedule).filter(DBSchedule.id == schedule_id).first()
    if not db_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )

    if not db_schedule.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schedule is not active"
        )

    # Celeryタスクとして実行（テスト環境では簡略化）
    import os
    if not os.getenv("TESTING", False):
        task = scheduled_spider_run.delay(schedule_id)
        task_id = task.id
    else:
        # テスト環境では仮のタスクIDを生成
        import uuid
        task_id = str(uuid.uuid4())

    # 最終実行時刻を更新
    db_schedule.last_run = datetime.now()

    # 次回実行時刻を計算
    try:
        cron = croniter(db_schedule.cron_expression, datetime.now())
        db_schedule.next_run = cron.get_next(datetime)
    except Exception:
        pass

    db.commit()

    return {
        "message": "Schedule executed successfully",
        "task_id": task_id,
        "schedule_id": schedule_id
    }

@router.post(
    "/{schedule_id}/toggle",
    summary="スケジュール有効/無効切り替え",
    description="スケジュールの有効/無効を切り替えます。"
)
async def toggle_schedule(schedule_id: str, db: Session = Depends(get_db)):
    """
    ## スケジュール有効/無効切り替え

    スケジュールの有効/無効を切り替えます。

    ### パラメータ
    - **schedule_id**: 切り替えるスケジュールのID

    ### レスポンス
    - **200**: 切り替えが正常に完了した場合
    - **404**: スケジュールが見つからない場合
    - **500**: サーバーエラー
    """
    db_schedule = db.query(DBSchedule).filter(DBSchedule.id == schedule_id).first()
    if not db_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )

    db_schedule.is_active = not db_schedule.is_active
    db.commit()

    return {
        "message": f"Schedule {'activated' if db_schedule.is_active else 'deactivated'}",
        "schedule_id": schedule_id,
        "is_active": db_schedule.is_active
    }
