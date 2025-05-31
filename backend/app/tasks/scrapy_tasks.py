from celery import current_task
from datetime import datetime, timedelta
import uuid
import asyncio
import json
import psutil
import os
import tempfile

from ..celery_app import celery_app
from ..database import SessionLocal, Task as DBTask, Project as DBProject, Spider as DBSpider, TaskStatus, Result as DBResult, Log as DBLog
from ..services.scrapy_service import ScrapyPlaywrightService
from ..websocket.manager import manager


def _safe_websocket_notify(task_id: str, data: dict):
    """Celeryワーカー内で安全にWebSocket通知を送信"""
    try:
        # HTTPリクエストでWebSocket通知を送信（Celeryワーカーから安全に実行可能）
        import requests
        import json

        # バックエンドのWebSocket通知エンドポイントに送信
        notification_url = "http://localhost:8000/api/tasks/internal/websocket-notify"
        payload = {
            "task_id": task_id,
            "data": data
        }

        # 非同期でHTTPリクエストを送信（タイムアウト設定）
        response = requests.post(
            notification_url,
            json=payload,
            timeout=1.0,  # 1秒でタイムアウト
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            print(f"📡 WebSocket notification sent: Task {task_id} - {data.get('status', 'update')}")
        else:
            print(f"📡 WebSocket notification failed: {response.status_code}")

    except requests.exceptions.Timeout:
        print(f"📡 WebSocket notification timeout: Task {task_id}")
    except Exception as e:
        print(f"📡 WebSocket notification error: {str(e)}")

@celery_app.task(bind=True, soft_time_limit=1800, time_limit=2100)  # 30分のソフトタイムアウト、35分のハードタイムアウト
def run_spider_task(self, project_id: str, spider_id: str, settings: dict = None):
    """
    Celeryタスクとしてスパイダーを実行
    """
    db = SessionLocal()
    celery_task_id = self.request.id

    try:
        # データベースからプロジェクトとスパイダー情報を取得
        project = db.query(DBProject).filter(DBProject.id == project_id).first()
        spider = db.query(DBSpider).filter(DBSpider.id == spider_id).first()

        if not project or not spider:
            print(f"❌ Project or Spider not found:")
            print(f"   Project ID: {project_id} -> Found: {project is not None}")
            print(f"   Spider ID: {spider_id} -> Found: {spider is not None}")
            raise Exception("Project or Spider not found")

        # 既存のタスクレコードを検索（task_idまたはcelery_task_idで関連付けられたもの）
        db_task = None

        # まず、task_idで検索（スケジュール実行の場合）
        if task_id:
            db_task = db.query(DBTask).filter(DBTask.id == task_id).first()
            if db_task:
                print(f"✅ Found existing task by task_id: {task_id}")
                # Celery task IDを更新
                db_task.celery_task_id = celery_task_id

        # task_idで見つからない場合、celery_task_idで検索
        if not db_task:
            db_task = db.query(DBTask).filter(DBTask.celery_task_id == celery_task_id).first()
            if db_task:
                print(f"✅ Found existing task by celery_task_id: {celery_task_id}")

        if not db_task:
            # 新しいタスクレコードを作成（通常はAPIで作成済みのはず）
            print(f"⚠️ No existing task found for Celery task {celery_task_id}, creating new one")
            new_task_id = task_id or str(uuid.uuid4())
            db_task = DBTask(
                id=new_task_id,
                project_id=project_id,
                spider_id=spider_id,
                status=TaskStatus.RUNNING,
                started_at=datetime.now(),
                log_level=settings.get('log_level', 'INFO') if settings else 'INFO',
                settings=settings,
                user_id=settings.get('user_id', 'system') if settings else 'system',
                celery_task_id=celery_task_id
            )
            db.add(db_task)
        else:
            # 既存のタスクを実行中状態に更新
            db_task.status = TaskStatus.RUNNING
            db_task.started_at = datetime.now()
            db_task.celery_task_id = celery_task_id  # Celery task IDを確実に設定

        db.commit()
        task_id = db_task.id  # 実際のタスクIDを使用

        # WebSocketで開始通知（Celeryワーカー内では安全にスキップ）
        _safe_websocket_notify(task_id, {
            "status": "RUNNING",
            "started_at": datetime.now().isoformat(),
            "message": f"Started spider {spider.name}"
        })

        # Scrapyサービスでスパイダーを実行
        scrapy_service = ScrapyPlaywrightService()

        # プログレス更新のコールバック
        def progress_callback(items_count, requests_count, error_count):
            # データベース更新（より詳細な状態管理）
            db_task.items_count = items_count
            db_task.requests_count = requests_count
            db_task.error_count = error_count

            # 実行状態の確実な記録
            if items_count > 0 or requests_count > 0:
                db_task.status = TaskStatus.RUNNING
                if not db_task.started_at:
                    db_task.started_at = datetime.now()

            # 即座にコミット（WebUIとの同期を確実に）
            db.commit()

            # プログレス計算（改良版 - より正確な進行表示）
            elapsed_seconds = (datetime.now() - db_task.started_at).total_seconds() if db_task.started_at else 0

            if items_count > 0:
                # アイテムベースの進行計算
                pending_items = max(0, min(60 - items_count, max(requests_count - items_count, 10)))
                total_estimated = items_count + pending_items
                item_progress = (items_count / total_estimated) * 100 if total_estimated > 0 else 10

                # 時間ベースの進行推定
                time_progress = min(80, elapsed_seconds * 1.5)  # 時間による進行推定

                # 複合プログレス（より安定した進行表示）
                progress_percentage = min(95, max(item_progress, time_progress))
            else:
                # 初期段階の進行
                progress_percentage = min(15, elapsed_seconds * 2) if elapsed_seconds > 0 else 5

            # WebSocket通知（HTTPリクエスト経由で送信）
            _safe_websocket_notify(task_id, {
                "id": task_id,
                "status": "RUNNING",
                "items_count": items_count,
                "requests_count": requests_count,
                "error_count": error_count,
                "progress": progress_percentage,
                "elapsed_seconds": elapsed_seconds
            })

            print(f"📊 Enhanced progress: Task {task_id} - Items: {items_count}, Requests: {requests_count}, Errors: {error_count}, Progress: {progress_percentage:.1f}%, Elapsed: {elapsed_seconds:.1f}s")

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

        # データベースからスパイダーコードをファイルシステムに同期
        try:
            print(f"🔄 Syncing spider code from database to filesystem: {spider.name}")
            scrapy_service.save_spider_code(project.path, spider.name, spider.code)
            print(f"✅ Spider code synchronized successfully: {spider.name}")
        except Exception as sync_error:
            print(f"⚠️ Warning: Failed to sync spider code: {sync_error}")
            # 同期に失敗してもタスクは継続（既存ファイルがある可能性）

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

        # progress_callbackが確実に動作するように追加の監視を開始
        print(f"🔍 Starting additional monitoring for Celery task {task_id}")

        # 結果ファイルパスを推定
        from pathlib import Path
        project_path_obj = Path(scrapy_service.base_projects_dir) / project.path
        output_file = project_path_obj / f"results_{task_id}.json"

        # 追加の監視スレッドを開始（Celery環境用）
        def celery_monitor():
            import time
            monitor_count = 0
            max_monitors = 30  # 最大60秒監視（2秒間隔）

            while monitor_count < max_monitors:
                try:
                    # 結果ファイルから統計情報を取得
                    items_count, requests_count = scrapy_service._get_real_time_statistics(task_id, str(output_file))

                    if items_count > 0 or requests_count > 0:
                        # progress_callbackを手動で呼び出し
                        progress_callback(items_count, requests_count, 0)
                        print(f"📊 Celery monitor: Task {task_id} - Items: {items_count}, Requests: {requests_count}")

                    time.sleep(2)  # 2秒間隔で監視
                    monitor_count += 1

                except Exception as monitor_error:
                    print(f"⚠️ Celery monitor error: {monitor_error}")
                    break

            print(f"🏁 Celery monitoring completed for task {task_id}")

        # 別スレッドで監視を開始
        import threading
        monitor_thread = threading.Thread(target=celery_monitor, daemon=True)
        monitor_thread.start()
        print(f"🚀 Celery monitor thread started for task {task_id}")

        # 開始通知（Celeryワーカー内では安全にスキップ）
        _safe_websocket_notify(task_id, {
            "status": "RUNNING",
            "started_at": datetime.now().isoformat(),
            "message": f"Spider {spider.name} started successfully"
        })

        return {
            "status": "started",
            "task_id": task_id,
            "spider_name": spider.name,
            "project_path": project.path,
            "message": "Spider execution started successfully"
        }

    except Exception as e:
        # 詳細なエラー情報を収集
        import traceback
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': traceback.format_exc(),
            'task_id': task_id,
            'timestamp': datetime.now().isoformat()
        }

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

            # エラー詳細をsettingsに保存
            if not db_task.settings:
                db_task.settings = {}
            db_task.settings['error_details'] = error_details

            db.commit()

            print(f"❌ Task {task_id} failed with detailed error:")
            print(f"   Error Type: {error_details['error_type']}")
            print(f"   Error Message: {error_details['error_message']}")
            print(f"   Preserved progress: {current_items} items, {current_requests} requests, {current_errors + 1} errors")
            print(f"   Full traceback saved to database")

        # エラーログをデータベースに保存
        try:
            error_log = DBLog(
                id=str(uuid.uuid4()),
                task_id=task_id,
                level='ERROR',
                message=f"Task failed: {error_details['error_type']}: {error_details['error_message']}"
            )
            db.add(error_log)
            db.commit()
        except Exception as log_error:
            print(f"Failed to save error log: {str(log_error)}")

        # エラー通知（Celeryワーカー内では非同期処理をスキップ）
        try:
            asyncio.create_task(manager.send_task_update(task_id, {
                "status": "FAILED",
                "finished_at": datetime.now().isoformat(),
                "error": error_details['error_message'],
                "error_type": error_details['error_type'],
                "items_count": current_items if 'current_items' in locals() else 0,
                "requests_count": current_requests if 'current_requests' in locals() else 0,
                "error_count": (current_errors + 1) if 'current_errors' in locals() else 1
            }))
        except RuntimeError:
            print(f"📡 WebSocket error notification skipped: Task {task_id} failed with error: {str(e)}")

        # 詳細なエラー情報を含む例外を再発生
        enhanced_error = Exception(f"Task {task_id} failed: {error_details['error_type']}: {error_details['error_message']}")
        enhanced_error.error_details = error_details
        raise enhanced_error

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

        # タスクレコードを作成（schedule_idを設定）
        task_id = str(uuid.uuid4())
        db_task = DBTask(
            id=task_id,
            project_id=schedule.project_id,
            spider_id=schedule.spider_id,
            schedule_id=schedule_id,  # スケジュールIDを設定
            status=TaskStatus.PENDING,
            log_level="INFO",
            settings=schedule.settings or {},
            user_id="system"  # スケジュール実行はシステムユーザー
        )
        db.add(db_task)
        db.commit()

        print(f"✅ Task record created: {task_id} (schedule: {schedule_id})")

        # Celery task IDを設定
        db_task.celery_task_id = scheduled_spider_run.request.id
        db.commit()

        print(f"✅ Task record updated with Celery ID: {scheduled_spider_run.request.id}")

        # 直接スパイダーを実行（run_spider_taskを呼び出さない）
        try:
            # スパイダー実行の準備
            from ..services.scrapy_service import ScrapyPlaywrightService

            scrapy_service = ScrapyPlaywrightService()

            # タスクを実行中状態に更新
            db_task.status = TaskStatus.RUNNING
            db_task.started_at = datetime.now()
            db.commit()

            print(f"🚀 Starting spider execution for task: {task_id}")

            # プロジェクト情報を取得
            project = db.query(DBProject).filter(DBProject.id == schedule.project_id).first()
            spider = db.query(DBSpider).filter(DBSpider.id == schedule.spider_id).first()

            if not project or not spider:
                raise Exception(f"Project or Spider not found: {schedule.project_id}, {schedule.spider_id}")

            # スパイダーを実行（正しい引数順序）
            result = scrapy_service.run_spider(
                project.path,  # project_path
                spider.name,   # spider_name
                task_id,       # task_id
                schedule.settings or {}  # settings
            )

            print(f"✅ Spider execution completed: {result}")
            return {"task_id": task_id, "result": result}

        except Exception as e:
            print(f"❌ Error in spider execution: {str(e)}")
            # タスクを失敗状態に更新
            db_task.status = TaskStatus.FAILED
            db_task.finished_at = datetime.now()
            db_task.error_message = str(e)
            db.commit()
            raise

    except Exception as e:
        print(f"❌ Error in scheduled_spider_run: {str(e)}")
        db.rollback()
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

@celery_app.task(bind=True, soft_time_limit=1800, time_limit=2100)
def run_spider_with_watchdog_task(self, project_id: str, spider_id: str, settings: dict = None):
    """
    watchdog監視付きでスパイダーを実行するCeleryタスク
    """
    db = SessionLocal()
    task_id = str(uuid.uuid4())

    try:
        print(f"🔍 Starting spider task with watchdog monitoring: {spider_id} in project {project_id}")

        # プロジェクトとスパイダーの存在確認
        project = db.query(DBProject).filter(DBProject.id == project_id).first()
        spider = db.query(DBSpider).filter(DBSpider.id == spider_id).first()

        if not project:
            raise Exception(f"Project not found: {project_id}")
        if not spider:
            raise Exception(f"Spider not found: {spider_id}")

        # タスクレコードを作成
        db_task = DBTask(
            id=task_id,
            project_id=project_id,
            spider_id=spider_id,
            status=TaskStatus.PENDING,
            log_level="INFO",
            settings=settings or {},
            user_id=spider.user_id,
            celery_task_id=self.request.id
        )
        db.add(db_task)
        db.commit()

        print(f"✅ Task record created: {task_id}")

        # プログレスコールバック関数
        def progress_callback(items_count: int, requests_count: int, error_count: int):
            try:
                # データベースのタスク情報を更新
                db_task.items_count = items_count
                db_task.requests_count = requests_count
                db_task.error_count = error_count
                db_task.updated_at = datetime.now()
                db.commit()

                # WebSocket通知
                _safe_websocket_notify(task_id, {
                    "status": "RUNNING",
                    "items_count": items_count,
                    "requests_count": requests_count,
                    "error_count": error_count,
                    "updated_at": datetime.now().isoformat()
                })

                print(f"📊 Progress update: Task {task_id} - Items: {items_count}, Requests: {requests_count}, Errors: {error_count}")

            except Exception as e:
                print(f"⚠️ Progress callback error: {e}")

        # WebSocketコールバック関数
        def websocket_callback(data: dict):
            try:
                _safe_websocket_notify(task_id, data)
            except Exception as e:
                print(f"⚠️ WebSocket callback error: {e}")

        # ScrapyServiceを使用してwatchdog監視付きでスパイダーを実行
        scrapy_service = ScrapyPlaywrightService()

        # タスクを実行中状態に更新
        db_task.status = TaskStatus.RUNNING
        db_task.started_at = datetime.now()
        db.commit()

        print(f"🚀 Starting watchdog spider execution for task: {task_id}")

        # 非同期実行をCeleryタスク内で処理
        import asyncio

        async def run_async_with_watchdog():
            return await scrapy_service.run_spider_with_watchdog(
                project_path=project.path,
                spider_name=spider.name,
                task_id=task_id,
                settings=settings,
                websocket_callback=websocket_callback
            )

        # 新しいイベントループで実行
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(run_async_with_watchdog())
            loop.close()
        except Exception as e:
            print(f"❌ Error in async spider execution with watchdog: {str(e)}")
            raise

        # 実行結果を処理
        if result.get('success', False):
            db_task.status = TaskStatus.FINISHED
            db_task.finished_at = datetime.now()
            db_task.items_count = result.get('items_processed', 0)

            # 成功通知
            _safe_websocket_notify(task_id, {
                "status": "FINISHED",
                "finished_at": datetime.now().isoformat(),
                "items_processed": result.get('items_processed', 0),
                "message": f"Spider {spider.name} completed successfully with watchdog monitoring"
            })

            print(f"✅ Watchdog spider task completed: {spider.name} - {result.get('items_processed', 0)} items processed")
        else:
            db_task.status = TaskStatus.FAILED
            db_task.finished_at = datetime.now()
            db_task.error_message = result.get('error', 'Unknown error')

            # エラー通知
            _safe_websocket_notify(task_id, {
                "status": "FAILED",
                "finished_at": datetime.now().isoformat(),
                "error": result.get('error', 'Unknown error'),
                "message": f"Spider {spider.name} failed with watchdog monitoring"
            })

            print(f"❌ Watchdog spider task failed: {spider.name} - {result.get('error', 'Unknown error')}")

        db.commit()

        return {
            "status": "completed" if result.get('success', False) else "failed",
            "task_id": task_id,
            "spider_name": spider.name,
            "project_path": project.path,
            "items_processed": result.get('items_processed', 0),
            "monitoring_type": "watchdog_jsonl",
            "result": result
        }

    except Exception as e:
        # エラー処理
        import traceback
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': traceback.format_exc(),
            'task_id': task_id,
            'timestamp': datetime.now().isoformat()
        }

        if 'db_task' in locals():
            db_task.status = TaskStatus.FAILED
            db_task.finished_at = datetime.now()
            db_task.error_message = str(e)

            if not db_task.settings:
                db_task.settings = {}
            db_task.settings['error_details'] = error_details

            db.commit()

        # エラー通知
        _safe_websocket_notify(task_id, {
            "status": "FAILED",
            "finished_at": datetime.now().isoformat(),
            "error": str(e),
            "error_type": type(e).__name__,
            "monitoring_type": "watchdog_jsonl"
        })

        print(f"❌ Watchdog spider task failed with error: {str(e)}")
        raise

    finally:
        db.close()