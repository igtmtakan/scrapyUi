#!/usr/bin/env python3
"""
強化されたスケジュール実行システム
Playwright専用サービスと統合した信頼性の高いスケジューラー
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from sqlalchemy.orm import Session
from ..database import SessionLocal, Schedule, Task, TaskStatus, Project, Spider
from .playwright_client import PlaywrightServiceClient
import subprocess
import tempfile

logger = logging.getLogger(__name__)

class EnhancedSchedulerService:
    """強化されたスケジューラーサービス"""
    
    def __init__(self, playwright_service_url: str = "http://localhost:8004"):
        self.playwright_service_url = playwright_service_url
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.base_projects_dir = Path(__file__).parent.parent.parent.parent / "scrapy_projects"
        
    async def health_check(self) -> Dict[str, Any]:
        """システムヘルスチェック"""
        health_status = {
            "scheduler": "healthy",
            "playwright_service": "unknown",
            "database": "unknown",
            "running_tasks": len(self.running_tasks),
            "timestamp": datetime.now().isoformat()
        }
        
        # Playwright サービスのヘルスチェック
        try:
            async with PlaywrightServiceClient(self.playwright_service_url) as client:
                playwright_health = await client.health_check()
                health_status["playwright_service"] = playwright_health.get("status", "unknown")
        except Exception as e:
            health_status["playwright_service"] = f"error: {str(e)}"
        
        # データベースのヘルスチェック
        try:
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            health_status["database"] = "healthy"
        except Exception as e:
            health_status["database"] = f"error: {str(e)}"
        
        return health_status
    
    async def execute_scheduled_task(self, schedule_id: str) -> Dict[str, Any]:
        """スケジュールされたタスクを実行"""
        db = SessionLocal()
        try:
            # スケジュール情報を取得
            schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
            if not schedule:
                raise ValueError(f"Schedule {schedule_id} not found")
            
            # プロジェクトとスパイダー情報を取得
            project = db.query(Project).filter(Project.id == schedule.project_id).first()
            spider = db.query(Spider).filter(Spider.id == schedule.spider_id).first()
            
            if not project or not spider:
                raise ValueError("Project or Spider not found")
            
            # タスクIDを生成
            task_id = f"task_{int(datetime.now().timestamp())}"
            
            # データベースにタスクを作成
            db_task = Task(
                id=task_id,
                status=TaskStatus.PENDING,
                project_id=project.id,
                spider_id=spider.id,
                user_id=schedule.user_id,
                schedule_id=schedule.id,
                settings=schedule.settings or {}
            )
            db.add(db_task)
            db.commit()
            
            logger.info(f"🚀 Starting enhanced scheduled task: {task_id}")
            
            # 非同期でタスクを実行
            task = asyncio.create_task(
                self._execute_spider_with_playwright(
                    task_id=task_id,
                    project_path=project.path,
                    spider_name=spider.name,
                    settings=schedule.settings or {}
                )
            )
            
            self.running_tasks[task_id] = task
            
            return {
                "task_id": task_id,
                "status": "started",
                "schedule_id": schedule_id,
                "project_name": project.name,
                "spider_name": spider.name
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to execute scheduled task: {e}")
            raise
        finally:
            db.close()
    
    async def _execute_spider_with_playwright(self, task_id: str, project_path: str, 
                                            spider_name: str, settings: Dict[str, Any]):
        """Playwright統合でスパイダーを実行"""
        db = SessionLocal()
        try:
            # タスクを実行中に更新
            db_task = db.query(Task).filter(Task.id == task_id).first()
            db_task.status = TaskStatus.RUNNING
            db_task.started_at = datetime.now()
            db.commit()
            
            # プロジェクトディレクトリを構築
            full_project_path = self.base_projects_dir / project_path
            
            # 環境変数を設定
            env = os.environ.copy()
            env.update({
                'SCRAPY_TASK_ID': task_id,
                'PLAYWRIGHT_SERVICE_URL': self.playwright_service_url,
                'SCRAPY_SETTINGS_MODULE': f'{project_path}.settings',
                'PYTHONPATH': str(self.base_projects_dir.parent),
            })
            
            # 出力ファイルを設定
            output_file = full_project_path / f"results_{task_id}.jsonl"
            
            # Scrapyコマンドを構築
            cmd = [
                'python', '-m', 'scrapy', 'crawl', spider_name,
                '-o', str(output_file),
                '-s', 'FEED_FORMAT=jsonlines',
                '-s', 'LOG_LEVEL=INFO',
                '-s', f'PLAYWRIGHT_SERVICE_URL={self.playwright_service_url}',
                '-s', 'DOWNLOAD_HANDLERS={"http": "backend.app.services.playwright_client.PlaywrightMiddleware", "https": "backend.app.services.playwright_client.PlaywrightMiddleware"}'
            ]
            
            # 追加設定を適用
            for key, value in settings.items():
                cmd.extend(['-s', f'{key}={value}'])
            
            logger.info(f"📋 Executing command: {' '.join(cmd)}")
            logger.info(f"📁 Working directory: {full_project_path}")
            
            # プロセスを実行
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(full_project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            # プロセスの完了を待機
            stdout, stderr = await process.communicate()
            
            # 結果を処理
            items_count = 0
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    items_count = sum(1 for line in f if line.strip())
            
            # タスクを完了に更新
            db_task.status = TaskStatus.FINISHED if process.returncode == 0 else TaskStatus.FAILED
            db_task.finished_at = datetime.now()
            db_task.items_count = items_count
            db_task.requests_count = 1  # 最低1リクエスト
            
            if process.returncode != 0:
                error_message = stderr.decode('utf-8')[:2000]  # エラーメッセージを制限
                db_task.error_message = error_message
                logger.error(f"❌ Spider execution failed: {error_message}")
            else:
                logger.info(f"✅ Spider execution completed: {items_count} items")
            
            db.commit()
            
            # 結果ファイルをデータベースに保存
            if output_file.exists() and items_count > 0:
                await self._save_results_to_database(task_id, output_file)
            
        except Exception as e:
            logger.error(f"❌ Spider execution error: {e}")
            
            # エラー状態に更新
            db_task = db.query(Task).filter(Task.id == task_id).first()
            if db_task:
                db_task.status = TaskStatus.FAILED
                db_task.finished_at = datetime.now()
                db_task.error_message = str(e)[:2000]
                db.commit()
                
        finally:
            # 実行中タスクリストから削除
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            db.close()
    
    async def _save_results_to_database(self, task_id: str, output_file: Path):
        """結果をデータベースに保存"""
        db = SessionLocal()
        try:
            from ..database import Result
            import hashlib
            
            with open(output_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line.strip())
                            
                            # データハッシュを生成
                            data_str = json.dumps(data, sort_keys=True)
                            data_hash = hashlib.sha256(data_str.encode()).hexdigest()
                            
                            # 重複チェック
                            existing = db.query(Result).filter(
                                Result.task_id == task_id,
                                Result.data_hash == data_hash
                            ).first()
                            
                            if not existing:
                                result = Result(
                                    id=str(uuid.uuid4()),
                                    task_id=task_id,
                                    data=data,
                                    url=data.get('url'),
                                    data_hash=data_hash,
                                    crawl_start_datetime=datetime.now(),
                                    item_acquired_datetime=datetime.now()
                                )
                                db.add(result)
                        except json.JSONDecodeError:
                            continue
            
            db.commit()
            logger.info(f"✅ Results saved to database for task {task_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save results to database: {e}")
        finally:
            db.close()
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """タスクの状態を取得"""
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return {"error": "Task not found"}
            
            return {
                "task_id": task.id,
                "status": task.status.value,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "finished_at": task.finished_at.isoformat() if task.finished_at else None,
                "items_count": task.items_count,
                "requests_count": task.requests_count,
                "error_count": task.error_count,
                "error_message": task.error_message,
                "is_running": task_id in self.running_tasks
            }
        finally:
            db.close()
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """タスクをキャンセル"""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.cancel()
            del self.running_tasks[task_id]
            
            # データベースを更新
            db = SessionLocal()
            try:
                db_task = db.query(Task).filter(Task.id == task_id).first()
                if db_task:
                    db_task.status = TaskStatus.CANCELLED
                    db_task.finished_at = datetime.now()
                    db.commit()
            finally:
                db.close()
            
            return {"message": f"Task {task_id} cancelled"}
        else:
            return {"error": "Task not found or not running"}

# グローバルスケジューラーインスタンス
enhanced_scheduler = EnhancedSchedulerService()
