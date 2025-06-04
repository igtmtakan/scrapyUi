#!/usr/bin/env python3
"""
タスクエグゼキューター
PENDINGタスクを検出して自動実行するサービス
"""

import asyncio
import threading
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from ..database import SessionLocal, Task as DBTask, TaskStatus, Spider as DBSpider, Project as DBProject

logger = logging.getLogger(__name__)


class TaskExecutor:
    """
    タスクエグゼキューター
    PENDINGタスクを検出して自動実行する
    """

    def __init__(self, max_concurrent_tasks: int = 3):
        self.running = False
        self.thread = None
        self.max_concurrent_tasks = max_concurrent_tasks
        self.current_tasks: Dict[str, Any] = {}
        self.check_interval = 5  # 5秒間隔でチェック
        self.last_check_time = None

    def start(self):
        """タスクエグゼキューターを開始"""
        if self.running:
            logger.warning("⚠️ Task executor is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_executor_loop, daemon=True)
        self.thread.start()
        logger.info("🚀 Task executor started")
        print("🚀 Task executor started")

    def stop(self):
        """タスクエグゼキューターを停止"""
        self.running = False

        # 実行中のタスクをキャンセル（現在は単純にクリア）
        self.current_tasks.clear()

        if self.thread:
            self.thread.join(timeout=10)

        logger.info("🛑 Task executor stopped")
        print("🛑 Task executor stopped")

    def _run_executor_loop(self):
        """エグゼキューターのメインループ"""
        logger.info("🔄 Task executor loop started")
        print("🔄 Task executor loop started")

        while self.running:
            try:
                current_time = datetime.now()
                
                # 完了したタスクをクリーンアップ
                self._cleanup_completed_tasks()
                
                # PENDINGタスクをチェックして実行
                if len(self.current_tasks) < self.max_concurrent_tasks:
                    pending_tasks = self._get_pending_tasks()
                    
                    for task in pending_tasks:
                        if len(self.current_tasks) >= self.max_concurrent_tasks:
                            break
                        
                        if task.id not in self.current_tasks:
                            self._execute_task(task)
                
                self.last_check_time = current_time
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"❌ Task executor error: {str(e)}")
                print(f"❌ Task executor error: {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(30)  # エラー時は30秒待機

    def _get_pending_tasks(self) -> List[DBTask]:
        """PENDINGタスクを取得"""
        db = SessionLocal()
        try:
            # 古い順にPENDINGタスクを取得
            tasks = db.query(DBTask).filter(
                DBTask.status == TaskStatus.PENDING
            ).order_by(DBTask.created_at.asc()).limit(
                self.max_concurrent_tasks - len(self.current_tasks)
            ).all()
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting pending tasks: {e}")
            return []
        finally:
            db.close()

    def _execute_task(self, task: DBTask):
        """タスクを実行"""
        try:
            logger.info(f"🚀 Starting execution of task {task.id[:8]}...")
            print(f"🚀 Starting execution of task {task.id[:8]}...")

            # タスクの詳細情報を取得
            spider_config = self._build_spider_config(task)

            if not spider_config:
                logger.error(f"❌ Failed to build spider config for task {task.id}")
                self._mark_task_failed(task.id, "Failed to build spider configuration")
                return

            # 既存のScrapyサービスを使用してタスクを実行
            from .scrapy_service import ScrapyPlaywrightService
            scrapy_service = ScrapyPlaywrightService()

            # タスクを実行中リストに追加（プレースホルダー）
            self.current_tasks[task.id] = "RUNNING"

            # タスクの開始時刻を設定
            self._mark_task_started(task.id)

            # 非同期でタスクを実行
            def run_task():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    # ScrapyPlaywrightServiceを使用してタスクを実行
                    result = loop.run_until_complete(
                        scrapy_service.run_spider_with_watchdog(
                            project_path=spider_config['project_path'],
                            spider_name=spider_config['spider_name'],
                            task_id=task.id,
                            settings=spider_config.get('settings', {})
                        )
                    )

                    # 実行完了後の処理
                    if result.get('success', False):
                        logger.info(f"✅ Task {task.id[:8]} completed successfully")
                        print(f"✅ Task {task.id[:8]} completed successfully")
                        self._mark_task_completed(task.id, result)
                    else:
                        logger.error(f"❌ Task {task.id[:8]} failed: {result.get('error', 'Unknown error')}")
                        print(f"❌ Task {task.id[:8]} failed: {result.get('error', 'Unknown error')}")
                        self._mark_task_failed(task.id, result.get('error', 'Unknown error'))

                except Exception as e:
                    logger.error(f"❌ Error executing task {task.id}: {e}")
                    print(f"❌ Error executing task {task.id}: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    # タスクを実行中リストから削除
                    if task.id in self.current_tasks:
                        del self.current_tasks[task.id]

            # 別スレッドでタスクを実行
            task_thread = threading.Thread(target=run_task, daemon=True)
            task_thread.start()

        except Exception as e:
            logger.error(f"❌ Error starting task {task.id}: {e}")
            print(f"❌ Error starting task {task.id}: {e}")
            self._mark_task_failed(task.id, str(e))

    def _build_spider_config(self, task: DBTask) -> Optional[Dict[str, Any]]:
        """タスクからスパイダー設定を構築"""
        db = SessionLocal()
        try:
            # スパイダーとプロジェクト情報を取得
            spider = db.query(DBSpider).filter(DBSpider.id == task.spider_id).first()
            project = db.query(DBProject).filter(DBProject.id == task.project_id).first()
            
            if not spider or not project:
                logger.error(f"Spider or project not found for task {task.id}")
                return None
            
            # プロジェクトパスを構築（ユーザー名_プロジェクト名の形式）
            from pathlib import Path
            # プロジェクトの実際のディレクトリ名を取得
            actual_project_name = f"{project.user.username}_{project.name}".lower()
            # ScrapyPlaywrightServiceのbase_projects_dirに追加されるため、scrapy_projectsは含めない
            project_path = Path(actual_project_name) / actual_project_name
            
            return {
                'spider_name': spider.name,
                'project_path': str(project_path),
                'project_name': project.name,
                'spider_id': spider.id,
                'project_id': project.id,
                'task_id': task.id,
                'use_realtime_engine': True,
                'settings': {
                    'ROBOTSTXT_OBEY': False,
                    'DOWNLOAD_DELAY': 1,
                    'CONCURRENT_REQUESTS': 1,
                    'FEED_EXPORT_ENCODING': 'utf-8'
                }
            }
            
        except Exception as e:
            logger.error(f"Error building spider config: {e}")
            return None
        finally:
            db.close()

    def _cleanup_completed_tasks(self):
        """完了したタスクをクリーンアップ"""
        completed_tasks = []

        # データベースから完了したタスクを確認
        db = SessionLocal()
        try:
            for task_id in list(self.current_tasks.keys()):
                task = db.query(DBTask).filter(DBTask.id == task_id).first()
                if task and task.status in [TaskStatus.FINISHED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    completed_tasks.append(task_id)
        except Exception as e:
            logger.error(f"Error checking completed tasks: {e}")
        finally:
            db.close()

        for task_id in completed_tasks:
            if task_id in self.current_tasks:
                del self.current_tasks[task_id]
                logger.info(f"🧹 Cleaned up completed task {task_id[:8]}")

    def _mark_task_started(self, task_id: str):
        """タスクを開始としてマーク"""
        db = SessionLocal()
        try:
            task = db.query(DBTask).filter(DBTask.id == task_id).first()
            if task:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                db.commit()
                logger.info(f"🚀 Marked task {task_id[:8]} as started")
        except Exception as e:
            logger.error(f"Error marking task as started: {e}")
            db.rollback()
        finally:
            db.close()

    def _mark_task_completed(self, task_id: str, result: Dict[str, Any]):
        """タスクを完了としてマーク"""
        db = SessionLocal()
        try:
            task = db.query(DBTask).filter(DBTask.id == task_id).first()
            if task:
                task.status = TaskStatus.FINISHED
                task.finished_at = datetime.now()
                if task.started_at is None:
                    task.started_at = datetime.now()

                # アイテム数を更新
                items_processed = result.get('items_processed', 0)
                if items_processed > 0:
                    task.items_count = items_processed

                db.commit()
                logger.info(f"✅ Marked task {task_id[:8]} as completed with {items_processed} items")
        except Exception as e:
            logger.error(f"Error marking task as completed: {e}")
            db.rollback()
        finally:
            db.close()

    def _mark_task_failed(self, task_id: str, error_message: str):
        """タスクを失敗としてマーク"""
        db = SessionLocal()
        try:
            task = db.query(DBTask).filter(DBTask.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED
                task.finished_at = datetime.now()
                if task.started_at is None:
                    task.started_at = datetime.now()
                task.error_message = error_message
                db.commit()
                logger.info(f"❌ Marked task {task_id[:8]} as failed: {error_message}")
        except Exception as e:
            logger.error(f"Error marking task as failed: {e}")
            db.rollback()
        finally:
            db.close()

    def _on_task_progress(self, progress_data: Dict[str, Any]):
        """タスク進捗コールバック"""
        task_id = progress_data.get('task_id', 'unknown')
        logger.debug(f"📊 Task {task_id[:8]} progress: {progress_data}")

    def _on_websocket_notification(self, notification_data: Dict[str, Any]):
        """WebSocket通知コールバック"""
        logger.debug(f"📡 WebSocket notification: {notification_data}")

    def get_status(self) -> Dict[str, Any]:
        """エグゼキューターの状態を取得"""
        return {
            "running": self.running,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "current_tasks_count": len(self.current_tasks),
            "current_tasks": list(self.current_tasks.keys()),
            "check_interval": self.check_interval,
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None
        }


# グローバルインスタンス
task_executor = TaskExecutor()
