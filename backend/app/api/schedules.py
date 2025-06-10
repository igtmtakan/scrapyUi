from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime
from croniter import croniter
from pydantic import BaseModel

from ..database import get_db, Schedule as DBSchedule, Project as DBProject, Spider as DBSpider, Task as DBTask, Result as DBResult, User as DBUser, UserRole, TaskStatus
from ..models.schemas import Schedule, ScheduleCreate, ScheduleUpdate
# Celery廃止済み - マイクロサービス対応
# from ..tasks.scrapy_tasks import scheduled_spider_run
from ..services.scheduler_service import scheduler_service
from ..services.realtime_websocket_manager import realtime_websocket_manager
from .auth import get_current_active_user
import asyncio

# リクエストモデル
class ResetTasksRequest(BaseModel):
    hours_back: int = 24
    cleanup_orphaned: bool = True
    reset_all: bool = False

router = APIRouter(
    responses={
        404: {"description": "Not found"},
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"}
    }
)

@router.get(
    "/",
    summary="スケジュール一覧取得",
    description="登録されているスケジュールの一覧を取得します。",
    response_description="スケジュールのリスト"
)
async def get_schedules(
    project_id: str = None,
    is_active: bool = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
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
    # JOINクエリでプロジェクトとスパイダー情報を含める
    query = db.query(
        DBSchedule,
        DBProject.name.label('project_name'),
        DBSpider.name.label('spider_name')
    ).join(
        DBProject, DBSchedule.project_id == DBProject.id
    ).join(
        DBSpider, DBSchedule.spider_id == DBSpider.id
    )

    # 管理者は全スケジュール、一般ユーザーは自分のプロジェクトのスケジュールのみ
    is_admin = (current_user.role == UserRole.ADMIN or
                current_user.role == "ADMIN" or
                current_user.role == "admin")
    if not is_admin:
        query = query.filter(DBProject.user_id == current_user.id)

    if project_id:
        query = query.filter(DBSchedule.project_id == project_id)
    if is_active is not None:
        query = query.filter(DBSchedule.is_active == is_active)

    results = query.order_by(DBSchedule.created_at.desc()).all()

    # レスポンス形式を調整
    schedules = []
    for schedule, project_name, spider_name in results:
        # スケジュール実行による最新のタスクを取得（実行中を優先）
        # まず実行中・待機中のタスクを確認（Celery Workerの実際の状態も考慮）
        active_task = db.query(DBTask).filter(
            DBTask.project_id == schedule.project_id,
            DBTask.spider_id == schedule.spider_id,
            DBTask.schedule_id == schedule.id,  # スケジュール実行のタスクのみ
            DBTask.status.in_(['RUNNING', 'PENDING'])
        ).order_by(DBTask.created_at.desc()).first()

        # マイクロサービス対応: 実行中タスクの状態確認
        if active_task:
            try:
                from ..services.microservice_client import microservice_client

                # マイクロサービスが利用可能かチェック
                if not microservice_client.is_microservice_available():
                    print(f"⚠️ Microservice not available. Marking task {active_task.id} as failed.")
                    try:
                        active_task.status = 'FAILED'
                        active_task.finished_at = datetime.now()
                        db.commit()
                        active_task = None  # 実行中タスクとして扱わない
                    except Exception as db_error:
                        print(f"⚠️ Database error when updating task status: {db_error}")
                        db.rollback()
                        active_task = None

            except Exception as e:
                print(f"⚠️ Error checking microservice status: {e}")
                # エラーの場合は安全側に倒して、実行中タスクとして扱わない
                if active_task:
                    try:
                        active_task.status = 'FAILED'
                        active_task.finished_at = datetime.now()
                        db.commit()
                        active_task = None
                    except Exception as db_error:
                        print(f"⚠️ Database error when updating task status: {db_error}")
                        db.rollback()
                        active_task = None

        # 実行中・待機中のタスクがあればそれを使用、なければ最新の完了タスク
        if active_task:
            latest_task = active_task
        else:
            # スケジュール実行のタスクを優先、なければ手動実行も含める
            latest_task = db.query(DBTask).filter(
                DBTask.project_id == schedule.project_id,
                DBTask.spider_id == schedule.spider_id,
                DBTask.schedule_id == schedule.id  # スケジュール実行のタスクのみ
            ).order_by(DBTask.created_at.desc()).first()

            # スケジュール実行のタスクがない場合は、手動実行も含めて最新タスクを取得
            if not latest_task:
                latest_task = db.query(DBTask).filter(
                    DBTask.project_id == schedule.project_id,
                    DBTask.spider_id == schedule.spider_id
                ).order_by(DBTask.created_at.desc()).first()

        # Cron式から間隔（分）を推定
        interval_minutes = None
        try:
            # 簡易的な間隔計算（より正確な実装が必要な場合は改善）
            if schedule.cron_expression.startswith("*/"):
                # */7 * * * * 形式
                parts = schedule.cron_expression.split()
                if len(parts) >= 1 and parts[0].startswith("*/"):
                    interval_minutes = int(parts[0][2:])
            elif " " in schedule.cron_expression:
                # 0 */2 * * * 形式（時間間隔）
                parts = schedule.cron_expression.split()
                if len(parts) >= 2 and parts[1].startswith("*/"):
                    interval_minutes = int(parts[1][2:]) * 60
        except:
            pass

        # 最新タスクの情報を含める
        latest_task_dict = None
        if latest_task:
            # Rich progressと同じ方法で全統計情報を取得
            from ..services.scrapy_service import ScrapyPlaywrightService
            scrapy_service = ScrapyPlaywrightService()

            # Scrapyの統計ファイルから全パラメータを取得
            full_stats = scrapy_service._get_scrapy_full_stats(latest_task.id, latest_task.project_id)

            # 実際のDB結果数を確認してタスクのカウントを同期
            actual_db_count = db.query(DBResult).filter(DBResult.task_id == latest_task.id).count()

            # タスクのアイテム数が実際のDB結果数と異なる場合は同期
            if latest_task.items_count != actual_db_count and actual_db_count > 0:
                print(f"🔧 Syncing task {latest_task.id[:8]}... items count: {latest_task.items_count} → {actual_db_count}")
                latest_task.items_count = actual_db_count
                latest_task.requests_count = max(actual_db_count, latest_task.requests_count or 1)
                db.commit()

            # 基本統計情報（優先順位：Rich統計 > 実際のDB結果数 > データベース値 > 0）
            # Rich progress extensionの統計情報を最優先
            final_items = full_stats.get('items_count', 0) if full_stats and full_stats.get('items_count', 0) > 0 else (actual_db_count if actual_db_count > 0 else (latest_task.items_count or 0))
            final_requests = full_stats.get('requests_count', 0) if full_stats and full_stats.get('requests_count', 0) > 0 else (max(actual_db_count, latest_task.requests_count or 0) if actual_db_count > 0 else (latest_task.requests_count or 0))
            final_responses = full_stats.get('responses_count', 0) if full_stats else 0
            final_errors = (latest_task.error_count or 0) if (latest_task.error_count or 0) >= 0 else (full_stats.get('errors_count', 0) if full_stats else 0)

            # Scrapyの実際のステータスをそのまま使用（独自判定を削除）
            actual_status = latest_task.status.value if hasattr(latest_task.status, 'value') else latest_task.status

            latest_task_dict = {
                "id": latest_task.id,
                "status": actual_status,  # Scrapyの実際のステータスを使用
                "items_count": final_items,
                "requests_count": final_requests,
                "responses_count": final_responses,
                "error_count": final_errors,
                "started_at": latest_task.started_at,
                "finished_at": latest_task.finished_at,
                "created_at": latest_task.created_at,
                "rich_stats": full_stats,
                "scrapy_stats_used": bool(full_stats)
            }

        schedule_dict = {
            "id": schedule.id,
            "name": schedule.name,
            "description": schedule.description,
            "cron_expression": schedule.cron_expression,
            "interval_minutes": interval_minutes,
            "project_id": schedule.project_id,
            "spider_id": schedule.spider_id,
            "is_active": schedule.is_active,
            "last_run": schedule.last_run,
            "next_run": schedule.next_run,
            "created_at": schedule.created_at,
            "updated_at": schedule.updated_at,
            "settings": schedule.settings,
            "project_name": project_name,
            "spider_name": spider_name,
            "latest_task": latest_task_dict
        }
        schedules.append(schedule_dict)

    return schedules

@router.get(
    "/{schedule_id}",
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
    # JOINクエリでプロジェクトとスパイダー情報を含める
    result = db.query(
        DBSchedule,
        DBProject.name.label('project_name'),
        DBSpider.name.label('spider_name')
    ).join(
        DBProject, DBSchedule.project_id == DBProject.id
    ).join(
        DBSpider, DBSchedule.spider_id == DBSpider.id
    ).filter(DBSchedule.id == schedule_id).first()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )

    schedule, project_name, spider_name = result

    # レスポンス形式を調整
    schedule_dict = {
        "id": schedule.id,
        "name": schedule.name,
        "description": schedule.description,
        "cron_expression": schedule.cron_expression,
        "project_id": schedule.project_id,
        "spider_id": schedule.spider_id,
        "is_active": schedule.is_active,
        "last_run": schedule.last_run,
        "next_run": schedule.next_run,
        "created_at": schedule.created_at,
        "updated_at": schedule.updated_at,
        "settings": schedule.settings,
        "project_name": project_name,
        "spider_name": spider_name
    }

    return schedule_dict

@router.post(
    "/",
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

    # Cron式の詳細検証
    try:
        # 基本的なCron式検証
        cron = croniter(schedule.cron_expression, datetime.now())
        next_run = cron.get_next(datetime)

        # 追加の安全性チェック
        cron_parts = schedule.cron_expression.split()
        if len(cron_parts) != 5:
            raise ValueError("Cron expression must have exactly 5 parts")

        # 分の範囲チェック（0-59）
        minute_part = cron_parts[0]
        if minute_part != '*' and not minute_part.startswith('*/'):
            try:
                minute_val = int(minute_part)
                if minute_val < 0 or minute_val > 59:
                    raise ValueError("Minute must be between 0-59")
            except ValueError:
                pass  # 複雑な式は croniter に任せる

        # 時間の範囲チェック（0-23）
        hour_part = cron_parts[1]
        if hour_part != '*' and not hour_part.startswith('*/'):
            try:
                hour_val = int(hour_part)
                if hour_val < 0 or hour_val > 23:
                    raise ValueError("Hour must be between 0-23")
            except ValueError:
                pass

        # 実行頻度の妥当性チェック（1分未満の実行を防止）
        if minute_part.startswith('*/'):
            interval = int(minute_part[2:])
            if interval == 0:
                raise ValueError("Execution interval cannot be 0")

        # 次回実行時刻が妥当かチェック
        if next_run <= datetime.now():
            # 1秒後の時刻で再計算
            future_time = datetime.now().replace(second=0, microsecond=0)
            cron = croniter(schedule.cron_expression, future_time)
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

    # プロジェクト・スパイダー名を含めてレスポンス
    schedule_dict = {
        "id": db_schedule.id,
        "name": db_schedule.name,
        "description": db_schedule.description,
        "cron_expression": db_schedule.cron_expression,
        "project_id": db_schedule.project_id,
        "spider_id": db_schedule.spider_id,
        "is_active": db_schedule.is_active,
        "last_run": db_schedule.last_run,
        "next_run": db_schedule.next_run,
        "created_at": db_schedule.created_at,
        "updated_at": db_schedule.updated_at,
        "settings": db_schedule.settings,
        "project_name": project.name if project else "N/A",
        "spider_name": spider.name if spider else "N/A"
    }

    return schedule_dict

@router.put(
    "/{schedule_id}",
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

    # プロジェクト・スパイダー名を取得
    project = db.query(DBProject).filter(DBProject.id == db_schedule.project_id).first()
    spider = db.query(DBSpider).filter(DBSpider.id == db_schedule.spider_id).first()

    # プロジェクト・スパイダー名を含めてレスポンス
    schedule_dict = {
        "id": db_schedule.id,
        "name": db_schedule.name,
        "description": db_schedule.description,
        "cron_expression": db_schedule.cron_expression,
        "project_id": db_schedule.project_id,
        "spider_id": db_schedule.spider_id,
        "is_active": db_schedule.is_active,
        "last_run": db_schedule.last_run,
        "next_run": db_schedule.next_run,
        "created_at": db_schedule.created_at,
        "updated_at": db_schedule.updated_at,
        "settings": db_schedule.settings,
        "project_name": project.name if project else "N/A",
        "spider_name": spider.name if spider else "N/A"
    }

    return schedule_dict

@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="スケジュール削除",
    description="指定されたスケジュールを削除します。関連する待機タスクも削除されます。"
)
async def delete_schedule(schedule_id: str, db: Session = Depends(get_db)):
    """
    ## スケジュール削除

    指定されたスケジュールを削除します。関連する待機タスクも削除されます。

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

    try:
        # スケジュールに関連する待機中タスクを削除
        related_pending_tasks = db.query(DBTask).filter(
            DBTask.project_id == db_schedule.project_id,
            DBTask.spider_id == db_schedule.spider_id,
            DBTask.status == TaskStatus.PENDING
        ).all()

        deleted_tasks_count = 0
        if related_pending_tasks:
            print(f"🗑️ Deleting {len(related_pending_tasks)} pending tasks related to schedule {db_schedule.name}")
            for task in related_pending_tasks:
                print(f"  - Deleting pending task: {task.id[:8]}... (created: {task.created_at})")
                db.delete(task)
                deleted_tasks_count += 1

        # スケジュール自体を削除
        print(f"🗑️ Deleting schedule: {db_schedule.name} (ID: {db_schedule.id})")
        db.delete(db_schedule)

        # 変更をコミット
        db.commit()

        print(f"✅ Successfully deleted schedule and {deleted_tasks_count} related pending tasks")

    except Exception as e:
        print(f"⚠️ Error deleting schedule and related tasks: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete schedule and related tasks: {str(e)}"
        )

    return None

@router.post(
    "/{schedule_id}/run",
    summary="スケジュール手動実行",
    description="スケジュールを手動で実行します。"
)
async def run_schedule_now(schedule_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
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

    # プロジェクトとスパイダーの存在確認
    project = db.query(DBProject).filter(DBProject.id == db_schedule.project_id).first()
    spider = db.query(DBSpider).filter(DBSpider.id == db_schedule.spider_id).first()

    if not project or not spider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project or Spider not found"
        )

    # 実行中タスクチェック（重複実行防止）
    running_tasks = db.query(DBTask).filter(
        DBTask.project_id == db_schedule.project_id,
        DBTask.spider_id == db_schedule.spider_id,
        DBTask.status.in_([TaskStatus.RUNNING, TaskStatus.PENDING])
    ).all()

    if running_tasks:
        running_task_info = []
        for task in running_tasks:
            elapsed = (datetime.now() - task.started_at).total_seconds() if task.started_at else 0
            running_task_info.append(f"Task {task.id[:8]}... (running for {elapsed:.0f}s)")

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot execute schedule: {len(running_tasks)} task(s) already running. {', '.join(running_task_info)}"
        )

    # タスクIDを生成
    import uuid
    task_id = str(uuid.uuid4())

    # データベースにタスクを作成
    db_task = DBTask(
        id=task_id,
        spider_id=spider.id,
        project_id=project.id,
        user_id=current_user.id,
        status=TaskStatus.PENDING,
        settings=db_schedule.settings or {},
        created_at=datetime.now()
    )
    db.add(db_task)

    # マイクロサービス経由でwatchdog実行を開始
    import os
    if not os.getenv("TESTING", False):
        from ..services.microservice_client import microservice_client

        # マイクロサービスが利用可能かチェック
        if microservice_client.is_microservice_available():
            try:
                # マイクロサービス経由で実行
                result = microservice_client.execute_spider_with_watchdog_sync(
                    project_id=str(project.id),
                    spider_id=str(spider.id),
                    project_path=project.path,
                    spider_name=spider.name,
                    task_id=task_id,
                    settings=db_schedule.settings or {}
                )

                if result["success"]:
                    print(f"🚀 Microservice execution started for task: {task_id}")
                    print(f"   Project: {project.name}")
                    print(f"   Spider: {spider.name}")
                    print(f"   Task ID: {task_id}")
                else:
                    print(f"❌ Microservice execution failed: {result.get('error')}")
                    raise Exception(f"Microservice execution failed: {result.get('error')}")

            except Exception as e:
                print(f"❌ Failed to start microservice task for manual execution: {e}")
                # フォールバック: 直接実行
                from ..services.scrapy_service import ScrapyPlaywrightService
                scrapy_service = ScrapyPlaywrightService()

                # バックグラウンドでリアルタイム実行を開始
                import threading
                def run_spider_background():
                    try:
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        # WebSocketコールバック関数
                        def websocket_callback(data: dict):
                            try:
                                from ..api.websocket_progress import broadcast_rich_progress_update
                                asyncio.create_task(broadcast_rich_progress_update(task_id, data))
                            except Exception as e:
                                print(f"⚠️ WebSocket callback error in schedule run: {e}")

                        # watchdog監視付きで実行
                        result = loop.run_until_complete(
                            scrapy_service.run_spider_with_watchdog(
                                project_path=project.path,
                                spider_name=spider.name,
                                task_id=task_id,
                                settings=db_schedule.settings or {},
                                websocket_callback=websocket_callback
                            )
                        )
                        print(f"✅ Fallback spider execution completed: {result}")
                    except Exception as e:
                        print(f"❌ Fallback spider execution error: {e}")
                    finally:
                        loop.close()

                thread = threading.Thread(target=run_spider_background, daemon=True)
                thread.start()
                print(f"🔄 Fallback execution started for task: {task_id}")
        else:
            print("⚠️ Microservice not available, using legacy execution")
            # 従来のバックグラウンド実行を使用
            from ..services.scrapy_service import ScrapyPlaywrightService
            scrapy_service = ScrapyPlaywrightService()

            import threading
            def run_spider_background():
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    def websocket_callback(data: dict):
                        try:
                            from ..api.websocket_progress import broadcast_rich_progress_update
                            asyncio.create_task(broadcast_rich_progress_update(task_id, data))
                        except Exception as e:
                            print(f"⚠️ WebSocket callback error: {e}")

                    result = loop.run_until_complete(
                        scrapy_service.run_spider_with_watchdog(
                            project_path=project.path,
                            spider_name=spider.name,
                            task_id=task_id,
                            settings=db_schedule.settings or {},
                            websocket_callback=websocket_callback
                        )
                    )

                    print(f"✅ Legacy spider execution completed: {task_id}")

                except Exception as e:
                    print(f"❌ Legacy spider execution error: {e}")
                finally:
                    loop.close()

            thread = threading.Thread(target=run_spider_background, daemon=True)
            thread.start()
            print(f"🔄 Legacy execution started for task: {task_id}")

    else:
        print(f"🧪 Testing mode: Skipping actual spider execution for task: {task_id}")

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
        "message": "Schedule executed successfully with realtime monitoring",
        "task_id": task_id,
        "schedule_id": schedule_id,
        "realtime": True,
        "command": "scrapy crawlwithwatchdog"
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
    db.refresh(db_schedule)

    # プロジェクトとスパイダー情報を取得
    project = db.query(DBProject).filter(DBProject.id == db_schedule.project_id).first()
    spider = db.query(DBSpider).filter(DBSpider.id == db_schedule.spider_id).first()

    # 完全なスケジュールオブジェクトを返す
    schedule_dict = {
        "id": db_schedule.id,
        "name": db_schedule.name,
        "description": db_schedule.description,
        "cron_expression": db_schedule.cron_expression,
        "project_id": db_schedule.project_id,
        "spider_id": db_schedule.spider_id,
        "is_active": db_schedule.is_active,
        "last_run": db_schedule.last_run,
        "next_run": db_schedule.next_run,
        "created_at": db_schedule.created_at,
        "updated_at": db_schedule.updated_at,
        "settings": db_schedule.settings,
        "project_name": project.name if project else "N/A",
        "spider_name": spider.name if spider else "N/A"
    }

    return schedule_dict

@router.get(
    "/{schedule_id}/tasks",
    summary="スケジュール実行履歴取得",
    description="指定されたスケジュールの実行履歴（タスク一覧）を取得します。"
)
async def get_schedule_tasks(
    schedule_id: str,
    limit: int = 20,
    offset: int = 0,
    status: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    ## スケジュール実行履歴取得

    指定されたスケジュールの実行履歴（タスク一覧）を取得します。

    ### パラメータ
    - **schedule_id**: スケジュールID
    - **limit**: 取得件数の制限 (デフォルト: 20)
    - **offset**: オフセット (デフォルト: 0)
    - **status**: ステータスでフィルタリング (optional)

    ### レスポンス
    - **200**: タスクのリストを返します
    - **404**: スケジュールが見つからない場合
    - **500**: サーバーエラー
    """
    try:
        print(f"🔍 Getting schedule tasks for schedule_id: {schedule_id}")
        print(f"🔍 Parameters: limit={limit}, offset={offset}, status={status}")
        print(f"🔍 User: {current_user.email if current_user else 'None'}")

        # スケジュールの存在確認
        schedule = db.query(DBSchedule).filter(DBSchedule.id == schedule_id).first()
        if not schedule:
            print(f"❌ Schedule not found: {schedule_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )

        print(f"✅ Schedule found: {schedule.name}")

        # 権限チェック
        is_admin = (current_user.role == UserRole.ADMIN or
                    current_user.role == "ADMIN" or
                    current_user.role == "admin")

        print(f"🔍 User role: {current_user.role}, is_admin: {is_admin}")

        if not is_admin:
            # 一般ユーザーは自分のプロジェクトのスケジュールのみアクセス可能
            project = db.query(DBProject).filter(DBProject.id == schedule.project_id).first()
            if not project or project.user_id != current_user.id:
                print(f"❌ Access denied for user {current_user.email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )

        # タスク一覧を取得
        query = db.query(DBTask).filter(DBTask.schedule_id == schedule_id)
        print(f"🔍 Base query created for schedule_id: {schedule_id}")

        if status:
            status_list = [s.strip().upper() for s in status.split(',')]
            query = query.filter(DBTask.status.in_(status_list))
            print(f"🔍 Status filter applied: {status_list}")

        # 総件数を取得
        total_count = query.count()
        print(f"🔍 Total count: {total_count}")

        # ページネーション適用
        tasks = query.order_by(DBTask.created_at.desc()).offset(offset).limit(limit).all()
        print(f"🔍 Retrieved {len(tasks)} tasks")

        # レスポンス形式に変換
        task_list = []
        for task in tasks:
            try:
                # ステータスを文字列に変換
                status_str = task.status
                if hasattr(task.status, 'value'):
                    status_str = task.status.value
                elif hasattr(task.status, 'name'):
                    status_str = task.status.name
                else:
                    status_str = str(task.status)

                task_dict = {
                    "id": task.id,
                    "status": status_str,
                    "items_count": task.items_count or 0,
                    "requests_count": task.requests_count or 0,
                    "error_count": task.error_count or 0,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "finished_at": task.finished_at.isoformat() if task.finished_at else None,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                    "log_level": task.log_level,
                    "settings": task.settings,
                    "celery_task_id": task.celery_task_id,
                    "error_message": getattr(task, 'error_message', None)
                }
                task_list.append(task_dict)
                print(f"✅ Successfully converted task {task.id}: {status_str}")
            except Exception as e:
                print(f"❌ Error converting task {task.id}: {str(e)}")
                import traceback
                traceback.print_exc()
                # エラーが発生したタスクはスキップして続行
                continue

        response = {
            "tasks": task_list,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "schedule_id": schedule_id
        }

        print(f"✅ Successfully returning {len(task_list)} tasks")
        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in get_schedule_tasks: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schedule tasks: {str(e)}"
        )

@router.get(
    "/pending-tasks/count",
    summary="待機タスク数取得",
    description="現在待機中のタスク数を取得します。"
)
async def get_pending_tasks_count(db: Session = Depends(get_db)):
    """待機中のタスク数を取得"""
    try:
        pending_count = db.query(DBTask).filter(DBTask.status == TaskStatus.PENDING).count()

        # 古いタスク（24時間以上前）の数も取得
        from datetime import datetime, timedelta
        cutoff_time = datetime.now() - timedelta(hours=24)
        old_pending_count = db.query(DBTask).filter(
            DBTask.status == TaskStatus.PENDING,
            DBTask.created_at < cutoff_time
        ).count()

        return {
            "total_pending": pending_count,
            "old_pending": old_pending_count,
            "recent_pending": pending_count - old_pending_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending tasks count: {str(e)}"
        )

@router.post(
    "/pending-tasks/reset",
    summary="待機タスクリセット",
    description="古い待機タスクと孤立タスクをキャンセルします。"
)
async def reset_pending_tasks(
    request: ResetTasksRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """古い待機タスクと孤立タスクをキャンセル"""
    try:
        from datetime import datetime, timedelta

        # 管理者権限チェック
        is_admin = (current_user.role == UserRole.ADMIN or
                    current_user.role == "ADMIN" or
                    current_user.role == "admin")

        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )

        # リクエストパラメータを取得
        hours_back = request.hours_back
        cleanup_orphaned = request.cleanup_orphaned
        reset_all = request.reset_all

        print(f"🗑️ Starting task reset process...")
        print(f"  - Hours back: {hours_back}")
        print(f"  - Cleanup orphaned: {cleanup_orphaned}")
        print(f"  - Reset all: {reset_all}")
        print(f"  - User: {current_user.email}")

        cancelled_count = 0
        orphaned_count = 0
        running_count = 0

        if reset_all:
            # 全てのRUNNINGとPENDINGタスクを取得
            active_tasks = db.query(DBTask).filter(
                DBTask.status.in_([TaskStatus.RUNNING, TaskStatus.PENDING])
            ).all()

            print(f"🗑️ Cancelling ALL {len(active_tasks)} active tasks (RUNNING and PENDING)")
            for task in active_tasks:
                if task.status == TaskStatus.RUNNING:
                    print(f"  - Cancelling running task: {task.id[:8]}... (started: {task.started_at})")
                    running_count += 1
                else:
                    print(f"  - Cancelling pending task: {task.id[:8]}... (created: {task.created_at})")
                    cancelled_count += 1

                task.status = TaskStatus.CANCELLED
                task.finished_at = datetime.now()
        else:
            # 1. 指定時間以上前の待機中タスクを取得
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            old_pending_tasks = db.query(DBTask).filter(
                DBTask.status == TaskStatus.PENDING,
                DBTask.created_at < cutoff_time
            ).all()

            print(f"🗑️ Cancelling {len(old_pending_tasks)} old pending tasks (older than {hours_back} hours)")
            for task in old_pending_tasks:
                print(f"  - Cancelling old task: {task.id[:8]}... (created: {task.created_at})")
                task.status = TaskStatus.CANCELLED
                task.finished_at = datetime.now()
                cancelled_count += 1

        # 2. 孤立した待機タスクのクリーンアップ（オプション、reset_allの場合はスキップ）
        if cleanup_orphaned and not reset_all:
            # 関連するスケジュールが存在しない待機タスクを取得
            all_pending_tasks = db.query(DBTask).filter(DBTask.status == TaskStatus.PENDING).all()

            for task in all_pending_tasks:
                # 対応するスケジュールが存在するかチェック
                related_schedule = db.query(DBSchedule).filter(
                    DBSchedule.project_id == task.project_id,
                    DBSchedule.spider_id == task.spider_id
                ).first()

                if not related_schedule:
                    print(f"🗑️ Cancelling orphaned task: {task.id[:8]}... (no related schedule)")
                    task.status = TaskStatus.CANCELLED
                    task.finished_at = datetime.now()
                    orphaned_count += 1

        db.commit()

        # 残りの待機タスク数を取得
        remaining_pending = db.query(DBTask).filter(DBTask.status == TaskStatus.PENDING).count()
        remaining_running = db.query(DBTask).filter(DBTask.status == TaskStatus.RUNNING).count()

        if reset_all:
            total_cancelled = cancelled_count + running_count
            message = f"Successfully cancelled ALL active tasks: {running_count} running and {cancelled_count} pending tasks"
        else:
            message_parts = []
            if cancelled_count > 0:
                message_parts.append(f"{cancelled_count} old pending tasks")
            if orphaned_count > 0:
                message_parts.append(f"{orphaned_count} orphaned tasks")

            message = f"Successfully cancelled {' and '.join(message_parts) if message_parts else 'no tasks'}"
            total_cancelled = cancelled_count + orphaned_count

        return {
            "message": message,
            "cancelled_count": cancelled_count,
            "running_count": running_count,
            "orphaned_count": orphaned_count,
            "total_cancelled": total_cancelled,
            "remaining_pending": remaining_pending,
            "remaining_running": remaining_running,
            "hours_back": hours_back,
            "cleanup_orphaned": cleanup_orphaned,
            "reset_all": reset_all
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset pending tasks: {str(e)}"
        )

@router.get(
    "/scheduler/status",
    summary="スケジューラー状態取得",
    description="スケジューラーサービスの状態を取得します。"
)
async def get_scheduler_status():
    """スケジューラーサービスの状態を取得"""
    try:
        status = scheduler_service.get_status()
        return status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scheduler status: {str(e)}"
        )

@router.post(
    "/scheduler/health-check",
    summary="スケジューラ健全性チェック",
    description="全スケジュールの健全性をチェックし、問題があれば修正します。"
)
async def scheduler_health_check(db: Session = Depends(get_db)):
    """スケジューラの健全性チェックと自動修正"""
    try:
        # 全スケジュールを取得
        schedules = db.query(DBSchedule).all()

        health_report = {
            "timestamp": datetime.now().isoformat(),
            "total_schedules": len(schedules),
            "healthy_schedules": 0,
            "fixed_schedules": 0,
            "error_schedules": 0,
            "issues": [],
            "fixes": []
        }

        for schedule in schedules:
            schedule_issues = []
            schedule_fixes = []

            # 1. Cron式の検証
            try:
                cron = croniter(schedule.cron_expression, datetime.now())
                next_run = cron.get_next(datetime)

                # 次回実行時刻を更新（古い場合）
                if not schedule.next_run or schedule.next_run < datetime.now():
                    old_next_run = schedule.next_run
                    schedule.next_run = next_run
                    schedule_fixes.append(f"Updated next_run from {old_next_run} to {next_run}")

            except Exception as e:
                schedule_issues.append(f"Invalid cron expression: {e}")

            # 2. プロジェクト・スパイダーの存在確認
            if not schedule.project:
                schedule_issues.append("Associated project not found")
            if not schedule.spider:
                schedule_issues.append("Associated spider not found")

            # 3. 実行頻度の妥当性チェック
            try:
                cron_parts = schedule.cron_expression.split()
                if len(cron_parts) >= 1:
                    minute_part = cron_parts[0]
                    if minute_part.startswith('*/'):
                        interval = int(minute_part[2:])
                        if interval < 1:
                            schedule_issues.append("Execution interval too frequent (< 1 minute)")
                        elif interval > 1440:  # 24時間
                            schedule_issues.append("Execution interval too long (> 24 hours)")
            except:
                pass

            # 4. 最終実行時刻の妥当性
            if schedule.last_run and schedule.last_run > datetime.now():
                schedule.last_run = None
                schedule_fixes.append("Reset invalid last_run time")

            # 結果の集計
            if schedule_issues:
                health_report["error_schedules"] += 1
                health_report["issues"].append({
                    "schedule_id": schedule.id,
                    "schedule_name": schedule.name,
                    "issues": schedule_issues
                })
            else:
                health_report["healthy_schedules"] += 1

            if schedule_fixes:
                health_report["fixed_schedules"] += 1
                health_report["fixes"].append({
                    "schedule_id": schedule.id,
                    "schedule_name": schedule.name,
                    "fixes": schedule_fixes
                })

        # 修正をコミット
        if health_report["fixed_schedules"] > 0:
            db.commit()

        # 健全性スコアを計算
        if health_report["total_schedules"] > 0:
            health_score = (health_report["healthy_schedules"] / health_report["total_schedules"]) * 100
            health_report["health_score"] = round(health_score, 1)
        else:
            health_report["health_score"] = 100.0

        return health_report

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform health check: {str(e)}"
        )

@router.post(
    "/clear-cache",
    summary="WebUIキャッシュクリア",
    description="WebUIの表示キャッシュをクリアし、最新の状態を強制更新します。"
)
async def clear_webui_cache(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    ## WebUIキャッシュクリア

    WebUIの表示キャッシュをクリアし、最新の状態を強制更新します。

    ### 機能
    - ブラウザキャッシュの無効化指示
    - WebSocket接続の再同期
    - 最新のタスク状態を取得

    ### レスポンス
    - **200**: キャッシュクリアが正常に完了した場合
    - **500**: サーバーエラー
    """
    try:
        # 最新のスケジュール情報を取得
        schedules = db.query(DBSchedule).filter(DBSchedule.is_active == True).all()

        # 各スケジュールの最新タスク状態を確認
        cache_clear_data = {
            "timestamp": datetime.now().isoformat(),
            "schedules_count": len(schedules),
            "active_tasks": [],
            "completed_tasks": []
        }

        for schedule in schedules:
            # 実行中タスクを確認
            active_task = db.query(DBTask).filter(
                DBTask.schedule_id == schedule.id,
                DBTask.status.in_(['RUNNING', 'PENDING'])
            ).order_by(DBTask.created_at.desc()).first()

            if active_task:
                cache_clear_data["active_tasks"].append({
                    "schedule_id": schedule.id,
                    "schedule_name": schedule.name,
                    "task_id": active_task.id,
                    "status": active_task.status.value if hasattr(active_task.status, 'value') else active_task.status
                })

            # 最新の完了タスクを確認
            completed_task = db.query(DBTask).filter(
                DBTask.schedule_id == schedule.id,
                DBTask.status.in_(['SUCCESS', 'FAILURE', 'REVOKED'])
            ).order_by(DBTask.created_at.desc()).first()

            if completed_task:
                cache_clear_data["completed_tasks"].append({
                    "schedule_id": schedule.id,
                    "schedule_name": schedule.name,
                    "task_id": completed_task.id,
                    "status": completed_task.status.value if hasattr(completed_task.status, 'value') else completed_task.status,
                    "items_count": completed_task.items_count or 0,
                    "requests_count": completed_task.requests_count or 0,
                    "finished_at": completed_task.finished_at
                })

        # WebSocket経由でキャッシュクリア通知を送信
        try:
            await realtime_websocket_manager.broadcast_message({
                "type": "cache_clear",
                "data": cache_clear_data,
                "message": "WebUIキャッシュがクリアされました。ページを更新してください。"
            })
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")

        return {
            "message": "WebUIキャッシュクリアが完了しました",
            "cache_clear_data": cache_clear_data,
            "instructions": [
                "ブラウザでF5キーまたはCtrl+F5を押してページを更新してください",
                "WebSocket接続が自動的に再同期されます",
                "最新のタスク状態が表示されます"
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"キャッシュクリア中にエラーが発生しました: {str(e)}"
        )
