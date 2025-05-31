"""
タスク自動修復サービス

失敗と判定されたが実際にはデータが存在するタスクを自動修復する機能
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any

from sqlalchemy.orm import Session
from ..database import SessionLocal, Task as DBTask, TaskStatus, Project as DBProject

logger = logging.getLogger(__name__)

class TaskAutoRecoveryService:
    """タスク自動修復サービス"""
    
    def __init__(self, base_projects_dir: str = "scrapy_projects"):
        self.base_projects_dir = Path(base_projects_dir)
        
    async def run_auto_recovery(self, hours_back: int = 24) -> Dict[str, Any]:
        """自動修復を実行"""
        try:
            logger.info(f"🔧 Starting auto recovery for tasks in last {hours_back} hours")
            
            # 過去N時間の失敗タスクを取得
            failed_tasks = self._get_failed_tasks(hours_back)
            logger.info(f"Found {len(failed_tasks)} failed tasks to check")
            
            recovery_results = {
                'checked_tasks': len(failed_tasks),
                'recovered_tasks': 0,
                'recovery_details': []
            }
            
            for task in failed_tasks:
                recovery_result = await self._attempt_task_recovery(task)
                if recovery_result['recovered']:
                    recovery_results['recovered_tasks'] += 1
                    recovery_results['recovery_details'].append(recovery_result)
                    
            logger.info(f"✅ Auto recovery completed: {recovery_results['recovered_tasks']}/{recovery_results['checked_tasks']} tasks recovered")
            return recovery_results
            
        except Exception as e:
            logger.error(f"Error in auto recovery: {e}")
            return {'error': str(e)}
    
    def _get_failed_tasks(self, hours_back: int) -> List[DBTask]:
        """過去N時間の失敗タスクを取得"""
        db = SessionLocal()
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            
            failed_tasks = db.query(DBTask).filter(
                DBTask.status == TaskStatus.FAILED,
                DBTask.created_at >= cutoff_time
            ).all()
            
            return failed_tasks
            
        finally:
            db.close()
    
    async def _attempt_task_recovery(self, task: DBTask) -> Dict[str, Any]:
        """個別タスクの修復を試行"""
        try:
            logger.info(f"🔍 Checking task {task.id} for recovery")
            
            # プロジェクト情報を取得
            db = SessionLocal()
            try:
                project = db.query(DBProject).filter(DBProject.id == task.project_id).first()
                if not project:
                    return {'task_id': task.id, 'recovered': False, 'reason': 'Project not found'}
                
                # 結果ファイルをチェック
                recovery_data = self._check_result_files(task.id, project.path)
                
                if recovery_data['has_data']:
                    # タスクを修復
                    success = self._recover_task(db, task, recovery_data)
                    
                    if success:
                        logger.info(f"✅ Recovered task {task.id}: {recovery_data['items_count']} items")
                        return {
                            'task_id': task.id,
                            'recovered': True,
                            'items_count': recovery_data['items_count'],
                            'files_found': recovery_data['files_found']
                        }
                    else:
                        return {'task_id': task.id, 'recovered': False, 'reason': 'Recovery failed'}
                else:
                    return {'task_id': task.id, 'recovered': False, 'reason': 'No data files found'}
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error recovering task {task.id}: {e}")
            return {'task_id': task.id, 'recovered': False, 'reason': f'Error: {str(e)}'}
    
    def _check_result_files(self, task_id: str, project_path: str) -> Dict[str, Any]:
        """結果ファイルの存在とデータをチェック"""
        try:
            base_filename = f"results_{task_id}"
            project_dir = self.base_projects_dir / project_path
            
            possible_files = [
                project_dir / f"{base_filename}.jsonl",
                project_dir / f"{base_filename}.json",
                project_dir / f"{base_filename}.csv",
                project_dir / f"{base_filename}.xml"
            ]
            
            files_found = []
            total_items = 0
            
            for file_path in possible_files:
                if file_path.exists() and file_path.stat().st_size > 0:
                    files_found.append(str(file_path.name))
                    
                    # JSONLファイルからアイテム数を取得
                    if file_path.suffix == '.jsonl':
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = [line.strip() for line in f.readlines() if line.strip()]
                                total_items = max(total_items, len(lines))
                        except Exception as e:
                            logger.warning(f"Error reading JSONL file {file_path}: {e}")
                    
                    # JSONファイルからアイテム数を取得
                    elif file_path.suffix == '.json':
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                if isinstance(data, list):
                                    total_items = max(total_items, len(data))
                        except Exception as e:
                            logger.warning(f"Error reading JSON file {file_path}: {e}")
            
            return {
                'has_data': len(files_found) > 0 and total_items > 0,
                'files_found': files_found,
                'items_count': total_items
            }
            
        except Exception as e:
            logger.error(f"Error checking result files for task {task_id}: {e}")
            return {'has_data': False, 'files_found': [], 'items_count': 0}
    
    def _recover_task(self, db: Session, task: DBTask, recovery_data: Dict[str, Any]) -> bool:
        """タスクを修復"""
        try:
            # タスクステータスと統計情報を更新
            task.status = TaskStatus.FINISHED
            task.items_count = recovery_data['items_count']
            task.requests_count = max(recovery_data['items_count'], task.requests_count or 0)
            task.error_count = 0
            
            # 完了時刻を設定（まだ設定されていない場合）
            if not task.finished_at:
                task.finished_at = datetime.now(timezone.utc)
            
            db.commit()
            
            logger.info(f"📊 Task {task.id} recovered: status=FINISHED, items={recovery_data['items_count']}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating recovered task {task.id}: {e}")
            db.rollback()
            return False

# グローバルインスタンス
task_auto_recovery_service = TaskAutoRecoveryService()
