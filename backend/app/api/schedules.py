from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime
from croniter import croniter

from ..database import get_db, Schedule as DBSchedule, Project as DBProject, Spider as DBSpider, Task as DBTask, User as DBUser, UserRole
from ..models.schemas import Schedule, ScheduleCreate, ScheduleUpdate
from ..tasks.scrapy_tasks import scheduled_spider_run
from ..services.scheduler_service import scheduler_service
from .auth import get_current_active_user

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
        # スケジュール実行による最新のタスクを取得
        # schedule_idが設定されているタスクのみを対象とする
        latest_task = db.query(DBTask).filter(
            DBTask.project_id == schedule.project_id,
            DBTask.spider_id == schedule.spider_id,
            DBTask.schedule_id == schedule.id  # スケジュール実行のタスクのみ
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
            latest_task_dict = {
                "id": latest_task.id,
                "status": latest_task.status,
                "items_count": latest_task.items_count,
                "requests_count": latest_task.requests_count,
                "error_count": latest_task.error_count,
                "started_at": latest_task.started_at,
                "finished_at": latest_task.finished_at,
                "created_at": latest_task.created_at
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
