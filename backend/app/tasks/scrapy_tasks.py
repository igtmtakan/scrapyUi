from celery import current_task
from datetime import datetime, timedelta
import uuid
import asyncio
import json
import psutil
import os

from ..celery_app import celery_app
from ..database import SessionLocal, Task as DBTask, Project as DBProject, Spider as DBSpider, TaskStatus, Result as DBResult, Log as DBLog
from ..services.scrapy_service import ScrapyPlaywrightService
from ..websocket.manager import manager

@celery_app.task(bind=True)
def run_spider_task(self, project_id: str, spider_id: str, settings: dict = None):
    """
    Celeryタスクとしてスパイダーを実行
    """
    db = SessionLocal()
    task_id = self.request.id

    try:
        # データベースからプロジェクトとスパイダー情報を取得
        project = db.query(DBProject).filter(DBProject.id == project_id).first()
        spider = db.query(DBSpider).filter(DBSpider.id == spider_id).first()

        if not project or not spider:
            raise Exception("Project or Spider not found")

        # タスクレコードを作成
        db_task = DBTask(
            id=task_id,
            project_id=project_id,
            spider_id=spider_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.now(),
            log_level=settings.get('log_level', 'INFO') if settings else 'INFO',
            settings=settings,
            user_id=settings.get('user_id', 'system') if settings else 'system'
        )
        db.add(db_task)
        db.commit()

        # WebSocketで開始通知（Celeryワーカー内では非同期処理をスキップ）
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(manager.send_task_update(task_id, {
                "status": "RUNNING",
                "started_at": datetime.now().isoformat(),
                "message": f"Started spider {spider.name}"
            }))
        except RuntimeError:
            # イベントループが動作していない場合はスキップ
            print(f"📡 WebSocket notification skipped (no event loop): Task {task_id} started")

        # Scrapyサービスでスパイダーを実行
        scrapy_service = ScrapyPlaywrightService()

        # プログレス更新のコールバック
        def progress_callback(items_count, requests_count, error_count):
            # データベース更新
            db_task.items_count = items_count
            db_task.requests_count = requests_count
            db_task.error_count = error_count
            db.commit()

            # WebSocket通知（Celeryワーカー内では非同期処理をスキップ）
            try:
                asyncio.create_task(manager.send_task_update(task_id, {
                    "items_count": items_count,
                    "requests_count": requests_count,
                    "error_count": error_count,
                    "progress": min(100, (items_count / 100) * 100) if items_count > 0 else 0
                }))
            except RuntimeError:
                print(f"📡 WebSocket progress update skipped: {items_count} items, {requests_count} requests")

        # ログコールバック
        def log_callback(level, message):
            # ログをデータベースに保存
            log_entry = DBLog(
                id=str(uuid.uuid4()),
                task_id=task_id,
                level=level,
                message=message
            )
            db.add(log_entry)
            db.commit()

            # WebSocketでログ送信（Celeryワーカー内では非同期処理をスキップ）
            try:
                asyncio.create_task(manager.send_log_message(task_id, {
                    "level": level,
                    "message": message
                }))
            except RuntimeError:
                print(f"📡 WebSocket log skipped: [{level}] {message}")

        # スパイダー実行
        task_result_id = scrapy_service.run_spider(
            project_path=project.path,
            spider_name=spider.name,
            task_id=task_id,
            settings=settings
        )

        print(f"✅ Spider started with task result ID: {task_result_id}")

        # スパイダーの実行完了を待機（非同期）
        # 実際の結果は ScrapyPlaywrightService の監視システムで処理される
        results = []  # 空の結果リストを返す（実際の結果はファイルに保存される）

        # タスクを実行中状態に更新（実際の完了は ScrapyPlaywrightService の監視システムで処理）
        db_task.status = TaskStatus.RUNNING
        db.commit()

        # 開始通知（Celeryワーカー内では非同期処理をスキップ）
        try:
            asyncio.create_task(manager.send_task_update(task_id, {
                "status": "RUNNING",
                "started_at": datetime.now().isoformat(),
                "message": f"Spider {spider.name} started successfully"
            }))
        except RuntimeError:
            print(f"📡 WebSocket start notification skipped: Task {task_id} started")

        return {
            "status": "started",
            "task_id": task_id,
            "spider_name": spider.name,
            "project_path": project.path,
            "message": "Spider execution started successfully"
        }

    except Exception as e:
        # エラー処理 - アイテム数・リクエスト数を保持
        if 'db_task' in locals():
            # 現在の進行状況を保持してからエラー状態に更新
            current_items = db_task.items_count or 0
            current_requests = db_task.requests_count or 0
            current_errors = db_task.error_count or 0

            db_task.status = TaskStatus.FAILED
            db_task.finished_at = datetime.now()
            # 進行状況データを保持
            db_task.items_count = current_items
            db_task.requests_count = current_requests
            db_task.error_count = current_errors + 1  # エラーカウントを増加
            db.commit()

            print(f"❌ Task {task_id} failed with error: {str(e)}")
            print(f"   Preserved progress: {current_items} items, {current_requests} requests, {current_errors + 1} errors")

        # エラー通知（Celeryワーカー内では非同期処理をスキップ）
        try:
            asyncio.create_task(manager.send_task_update(task_id, {
                "status": "FAILED",
                "finished_at": datetime.now().isoformat(),
                "error": str(e),
                "items_count": current_items if 'current_items' in locals() else 0,
                "requests_count": current_requests if 'current_requests' in locals() else 0,
                "error_count": (current_errors + 1) if 'current_errors' in locals() else 1
            }))
        except RuntimeError:
            print(f"📡 WebSocket error notification skipped: Task {task_id} failed with error: {str(e)}")

        raise e

    finally:
        db.close()

@celery_app.task
def cleanup_old_results(days_old: int = 30):
    """
    古い結果とログを削除するクリーンアップタスク
    """
    db = SessionLocal()

    try:
        cutoff_date = datetime.now() - timedelta(days=days_old)

        # 古いタスクを取得
        old_tasks = db.query(DBTask).filter(
            DBTask.created_at < cutoff_date,
            DBTask.status.in_([TaskStatus.FINISHED, TaskStatus.FAILED, TaskStatus.CANCELLED])
        ).all()

        deleted_count = 0
        for task in old_tasks:
            # 関連する結果とログも削除される（CASCADE設定により）
            db.delete(task)
            deleted_count += 1

        db.commit()

        return {
            "status": "success",
            "deleted_tasks": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

@celery_app.task
def system_health_check():
    """
    システムヘルスチェックタスク
    """
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # メモリ使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # ディスク使用率
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100

        # データベース接続チェック
        db = SessionLocal()
        try:
            db.execute("SELECT 1")
            db_status = "healthy"
        except Exception:
            db_status = "unhealthy"
        finally:
            db.close()

        health_data = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent,
            "database_status": db_status,
            "status": "healthy" if all([
                cpu_percent < 90,
                memory_percent < 90,
                disk_percent < 90,
                db_status == "healthy"
            ]) else "warning"
        }

        # WebSocketでシステム通知を送信
        asyncio.create_task(manager.send_system_notification({
            "type": "health_check",
            "data": health_data
        }))

        return health_data

    except Exception as e:
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error": str(e)
        }

        asyncio.create_task(manager.send_system_notification({
            "type": "health_check_error",
            "data": error_data
        }))

        return error_data

@celery_app.task
def scheduled_spider_run(schedule_id: str):
    """
    スケジュールされたスパイダー実行
    """
    from ..database import Schedule as DBSchedule

    db = SessionLocal()

    try:
        # スケジュール情報を取得
        schedule = db.query(DBSchedule).filter(DBSchedule.id == schedule_id).first()

        if not schedule:
            raise Exception(f"Schedule not found: {schedule_id}")

        print(f"🚀 Executing scheduled spider: {schedule.name}")
        print(f"   Project ID: {schedule.project_id}")
        print(f"   Spider ID: {schedule.spider_id}")

        # スパイダータスクを実行
        task = run_spider_task.delay(
            schedule.project_id,
            schedule.spider_id,
            schedule.settings or {}
        )

        print(f"✅ Scheduled spider task started: {task.id}")
        return task.id

    except Exception as e:
        print(f"❌ Error in scheduled_spider_run: {str(e)}")
        raise e
    finally:
        db.close()

@celery_app.task
def export_results_task(export_request: dict):
    """
    結果エクスポートの非同期処理
    """
    import pandas as pd
    import tempfile
    import os

    db = SessionLocal()

    try:
        task_ids = export_request.get("task_ids", [])
        export_format = export_request.get("format", "json")
        fields = export_request.get("fields", [])

        # 結果を取得
        query = db.query(DBResult)
        if task_ids:
            query = query.filter(DBResult.task_id.in_(task_ids))

        results = query.all()

        # データを整形
        export_data = []
        for result in results:
            data = {
                "id": result.id,
                "task_id": result.task_id,
                "url": result.url,
                "created_at": result.created_at.isoformat(),
                **result.data
            }

            if fields:
                data = {k: v for k, v in data.items() if k in fields}

            export_data.append(data)

        # ファイル生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scrapy_results_{timestamp}"

        if export_format == "csv":
            df = pd.DataFrame(export_data)
            filepath = f"/tmp/{filename}.csv"
            df.to_csv(filepath, index=False)

        elif export_format == "xlsx":
            df = pd.DataFrame(export_data)
            filepath = f"/tmp/{filename}.xlsx"
            df.to_excel(filepath, index=False)

        elif export_format == "xml":
            import xml.etree.ElementTree as ET

            # XMLエクスポート
            root = ET.Element("results")
            for item in export_data:
                item_element = ET.SubElement(root, "result")
                for key, value in item.items():
                    if isinstance(value, (dict, list)):
                        # ネストされたデータは文字列として保存
                        value = json.dumps(value)

                    child = ET.SubElement(item_element, key)
                    child.text = str(value) if value is not None else ""

            filepath = f"/tmp/{filename}.xml"
            tree = ET.ElementTree(root)
            tree.write(filepath, encoding='utf-8', xml_declaration=True)

        else:  # json
            filepath = f"/tmp/{filename}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

        return {
            "status": "success",
            "filepath": filepath,
            "filename": f"{filename}.{export_format}",
            "total_records": len(export_data)
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
    finally:
        db.close()
