"""
タスク自動修復サービス
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from ..database import SessionLocal, Task as DBTask, TaskStatus
from .task_statistics_validator import task_validator

logger = logging.getLogger(__name__)


class TaskAutoRepairService:
    """タスク自動修復サービス"""
    
    def __init__(self):
        self.logger = logger
    
    def repair_failed_tasks(self, hours_back: int = 24) -> Dict:
        """失敗したタスクを自動修復"""
        try:
            db = SessionLocal()
            try:
                # 過去N時間の失敗タスクを取得
                cutoff_time = datetime.now() - timedelta(hours=hours_back)
                failed_tasks = db.query(DBTask).filter(
                    DBTask.status == TaskStatus.FAILED,
                    DBTask.created_at >= cutoff_time
                ).all()
                
                repaired_count = 0
                total_failed = len(failed_tasks)
                
                self.logger.info(f"🔧 Starting auto-repair for {total_failed} failed tasks")
                
                for task in failed_tasks:
                    try:
                        # 統計検証・修復を実行
                        result = task_validator._validate_and_fix_task(task, db)
                        
                        if result.get("fixed", False):
                            repaired_count += 1
                            self.logger.info(f"✅ Repaired task {task.id}: {result.get('before')} → {result.get('after')}")
                    
                    except Exception as e:
                        self.logger.error(f"❌ Error repairing task {task.id}: {str(e)}")
                
                # 変更をコミット
                db.commit()
                
                result = {
                    "timestamp": datetime.now().isoformat(),
                    "total_failed_tasks": total_failed,
                    "repaired_count": repaired_count,
                    "success_rate": (repaired_count / total_failed * 100) if total_failed > 0 else 0,
                    "status": "completed"
                }
                
                self.logger.info(f"🎉 Auto-repair completed: {repaired_count}/{total_failed} tasks repaired")
                return result
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"❌ Error in auto-repair: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "failed"
            }
    
    def repair_specific_task(self, task_id: str) -> Dict:
        """特定のタスクを修復"""
        try:
            db = SessionLocal()
            try:
                task = db.query(DBTask).filter(DBTask.id == task_id).first()
                if not task:
                    return {"error": f"Task {task_id} not found"}
                
                # 修復前の状態を記録
                before_state = {
                    "items_count": task.items_count,
                    "requests_count": task.requests_count,
                    "status": task.status.value,
                    "error_count": task.error_count
                }
                
                # 統計検証・修復を実行
                result = task_validator._validate_and_fix_task(task, db)
                db.commit()
                
                if result.get("fixed", False):
                    self.logger.info(f"✅ Task {task_id} repaired successfully")
                    return {
                        "task_id": task_id,
                        "repaired": True,
                        "before": before_state,
                        "after": result.get("after", {}),
                        "changes": result
                    }
                else:
                    return {
                        "task_id": task_id,
                        "repaired": False,
                        "message": "No repairs needed"
                    }
                    
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"❌ Error repairing specific task {task_id}: {str(e)}")
            return {
                "task_id": task_id,
                "error": str(e)
            }
    
    def get_repair_candidates(self, hours_back: int = 24) -> List[Dict]:
        """修復候補のタスクを取得"""
        try:
            db = SessionLocal()
            try:
                cutoff_time = datetime.now() - timedelta(hours=hours_back)
                
                # 修復候補の条件
                candidates = db.query(DBTask).filter(
                    DBTask.created_at >= cutoff_time
                ).filter(
                    # 失敗したタスク、またはアイテム数が0の完了タスク
                    (DBTask.status == TaskStatus.FAILED) |
                    ((DBTask.status == TaskStatus.FINISHED) & (DBTask.items_count == 0))
                ).all()
                
                result = []
                for task in candidates:
                    # ファイル統計を確認
                    file_items, file_requests = task_validator._get_file_statistics(task)
                    
                    candidate_info = {
                        "task_id": task.id,
                        "current_status": task.status.value,
                        "current_items": task.items_count or 0,
                        "current_requests": task.requests_count or 0,
                        "file_items": file_items,
                        "file_requests": file_requests,
                        "needs_repair": False,
                        "repair_reason": []
                    }
                    
                    # 修復が必要かチェック
                    if file_items > 0 and task.status == TaskStatus.FAILED:
                        candidate_info["needs_repair"] = True
                        candidate_info["repair_reason"].append("Has items but marked as FAILED")
                    
                    if file_items != task.items_count:
                        candidate_info["needs_repair"] = True
                        candidate_info["repair_reason"].append(f"Items mismatch: DB={task.items_count}, File={file_items}")
                    
                    if file_requests > 0 and file_requests != task.requests_count:
                        candidate_info["needs_repair"] = True
                        candidate_info["repair_reason"].append(f"Requests mismatch: DB={task.requests_count}, File={file_requests}")
                    
                    if candidate_info["needs_repair"]:
                        result.append(candidate_info)
                
                return result
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"❌ Error getting repair candidates: {str(e)}")
            return []


# グローバルインスタンス
task_auto_repair = TaskAutoRepairService()
