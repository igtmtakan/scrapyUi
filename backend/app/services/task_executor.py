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

                    # 実行完了後の処理（改善された成功判定）
                    success = self._determine_task_success(task.id, result)

                    if success:
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

    def _determine_task_success(self, task_id: str, result: Dict[str, Any]) -> bool:
        """タスクの成功を総合的に判定"""
        try:
            # 1. 明示的な成功フラグをチェック
            explicit_success = result.get('success', False)

            # 2. アイテム数をチェック
            items_processed = result.get('items_processed', 0)

            # 3. 結果ファイルの存在をチェック
            results_file_exists = self._check_results_file_exists(task_id)

            # 4. エラーメッセージの有無をチェック
            has_critical_error = bool(result.get('error')) and 'critical' in str(result.get('error', '')).lower()

            # 成功判定ロジック
            success_conditions = [
                explicit_success,  # 明示的な成功フラグ
                items_processed > 0,  # アイテムが処理された
                results_file_exists,  # 結果ファイルが存在する
            ]

            # 失敗条件
            failure_conditions = [
                has_critical_error,  # 重大なエラーがある
            ]

            # いずれかの成功条件が満たされ、失敗条件がない場合は成功
            is_success = any(success_conditions) and not any(failure_conditions)

            logger.info(f"🔍 Task {task_id[:8]} success determination:")
            logger.info(f"  - Explicit success: {explicit_success}")
            logger.info(f"  - Items processed: {items_processed}")
            logger.info(f"  - Results file exists: {results_file_exists}")
            logger.info(f"  - Has critical error: {has_critical_error}")
            logger.info(f"  - Final decision: {'SUCCESS' if is_success else 'FAILED'}")

            return is_success

        except Exception as e:
            logger.error(f"Error determining task success: {e}")
            # エラーが発生した場合は、アイテム数で判定
            return result.get('items_processed', 0) > 0

    def _check_results_file_exists(self, task_id: str) -> bool:
        """結果ファイルの存在をチェック"""
        try:
            import os
            results_file = f"results_{task_id}.jsonl"
            return os.path.exists(results_file) and os.path.getsize(results_file) > 0
        except Exception:
            return False

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

                # その他の統計情報も更新
                if 'requests_count' in result:
                    task.requests_count = result['requests_count']
                if 'error_count' in result:
                    task.error_count = result['error_count']

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

    def fix_failed_tasks_with_results(self):
        """結果があるのに失敗とマークされたタスクを修正"""
        db = SessionLocal()
        try:
            from ..database import Task as DBTask, TaskStatus

            # FAILEDステータスのタスクを取得
            failed_tasks = db.query(DBTask).filter(DBTask.status == TaskStatus.FAILED).all()

            fixed_count = 0
            for task in failed_tasks:
                # 結果ファイルをチェック
                if self._check_results_file_exists(task.id):
                    # 結果ファイルから統計情報を取得
                    stats = self._get_task_stats_from_file(task.id)

                    if stats['items_count'] > 0:
                        # データがあるので成功に変更
                        task.status = TaskStatus.FINISHED
                        task.items_count = stats['items_count']
                        task.requests_count = stats.get('requests_count', 0)
                        task.error_count = 0
                        task.error_message = None
                        fixed_count += 1

                        logger.info(f"🔧 Fixed task {task.id[:8]}: {stats['items_count']} items found, marked as FINISHED")
                        print(f"🔧 Fixed task {task.id[:8]}: {stats['items_count']} items found, marked as FINISHED")

            if fixed_count > 0:
                db.commit()
                logger.info(f"✅ Fixed {fixed_count} failed tasks that actually had results")
                print(f"✅ Fixed {fixed_count} failed tasks that actually had results")
            else:
                logger.info("ℹ️ No failed tasks with results found to fix")
                print("ℹ️ No failed tasks with results found to fix")

        except Exception as e:
            logger.error(f"Error fixing failed tasks: {e}")
            db.rollback()
        finally:
            db.close()

    def _get_task_stats_from_file(self, task_id: str) -> Dict[str, int]:
        """結果ファイルから統計情報を取得"""
        try:
            import json
            import os
            results_file = f"results_{task_id}.jsonl"

            if not os.path.exists(results_file):
                return {'items_count': 0, 'requests_count': 0}

            items_count = 0
            with open(results_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        items_count += 1

            return {
                'items_count': items_count,
                'requests_count': items_count,  # 簡易的な推定
            }

        except Exception as e:
            logger.error(f"Error reading task stats from file: {e}")
            return {'items_count': 0, 'requests_count': 0}


# グローバルインスタンス
task_executor = TaskExecutor()
