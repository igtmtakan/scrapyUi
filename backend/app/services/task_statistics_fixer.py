"""
タスク統計情報の修正サービス

結果ファイルから実際の統計情報を読み取り、データベースを更新
"""

import os
import json
import logging
from pathlib import Path
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal, Task

logger = logging.getLogger(__name__)

class TaskStatisticsFixer:
    """タスク統計情報の修正クラス"""
    
    def __init__(self):
        self.base_projects_dir = Path("scrapy_projects")
    
    def fix_task_statistics(self, task_id: str) -> dict:
        """指定されたタスクの統計情報を修正"""
        try:
            db = SessionLocal()
            try:
                # タスクを取得
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    return {"success": False, "error": f"Task {task_id} not found"}
                
                # 結果ファイルから実際の統計を取得
                actual_items, actual_requests = self._get_file_statistics(task)
                
                # データベースを更新
                old_items = task.items_count
                old_requests = task.requests_count
                
                task.items_count = actual_items
                task.requests_count = actual_requests
                
                db.commit()
                
                logger.info(f"✅ Fixed task {task_id}: items {old_items}→{actual_items}, requests {old_requests}→{actual_requests}")
                
                return {
                    "success": True,
                    "task_id": task_id,
                    "old_stats": {"items": old_items, "requests": old_requests},
                    "new_stats": {"items": actual_items, "requests": actual_requests},
                    "fixed": actual_items != old_items or actual_requests != old_requests
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error fixing task statistics for {task_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def fix_all_recent_tasks(self, hours_back: int = 24) -> dict:
        """最近のタスクの統計情報を一括修正"""
        try:
            from datetime import datetime, timedelta
            
            db = SessionLocal()
            try:
                # 最近のタスクを取得
                cutoff_time = datetime.now() - timedelta(hours=hours_back)
                tasks = db.query(Task).filter(
                    Task.created_at >= cutoff_time,
                    Task.status == "FINISHED"
                ).all()
                
                results = {
                    "total_tasks": len(tasks),
                    "fixed_tasks": 0,
                    "errors": [],
                    "details": []
                }
                
                for task in tasks:
                    try:
                        result = self.fix_task_statistics(task.id)
                        if result["success"] and result["fixed"]:
                            results["fixed_tasks"] += 1
                            results["details"].append(result)
                    except Exception as e:
                        error_msg = f"Error fixing task {task.id}: {str(e)}"
                        results["errors"].append(error_msg)
                        logger.error(error_msg)
                
                logger.info(f"✅ Fixed {results['fixed_tasks']}/{results['total_tasks']} tasks")
                return results
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error fixing all recent tasks: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_file_statistics(self, task: Task) -> Tuple[int, int]:
        """結果ファイルから統計情報を取得"""
        try:
            # プロジェクトディレクトリを取得
            project_path = task.project.path if task.project else task.project_id
            project_dir = self.base_projects_dir / project_path
            
            items_count = 0
            requests_count = 0
            
            # 1. 結果ファイルを確認（JSONL形式）
            result_file = project_dir / "results" / f"{task.id}.jsonl"
            if result_file.exists():
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        items_count = len([line for line in lines if line.strip()])
                        requests_count = max(items_count + 5, 1)  # 推定値
                        
                    logger.info(f"📊 JSONL file found for task {task.id}: {items_count} items")
                    return items_count, requests_count
                except Exception as e:
                    logger.warning(f"⚠️ Error reading JSONL file for task {task.id}: {e}")
            
            # 2. JSON形式の結果ファイルを確認
            json_result_file = project_dir / "results" / f"{task.id}.json"
            if json_result_file.exists():
                try:
                    with open(json_result_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        items_count = len(data) if isinstance(data, list) else 1
                        requests_count = max(items_count + 5, 1)
                        
                    logger.info(f"📊 JSON file found for task {task.id}: {items_count} items")
                    return items_count, requests_count
                except Exception as e:
                    logger.warning(f"⚠️ Error reading JSON file for task {task.id}: {e}")
            
            # 3. 統計ファイルを確認
            stats_file = project_dir / f"stats_{task.id}.json"
            if stats_file.exists():
                try:
                    with open(stats_file, 'r', encoding='utf-8') as f:
                        stats = json.load(f)
                        items_count = stats.get('item_scraped_count', 0)
                        requests_count = stats.get('downloader/request_count', 0)
                        
                    logger.info(f"📊 Stats file found for task {task.id}: items={items_count}, requests={requests_count}")
                    return items_count, requests_count
                except Exception as e:
                    logger.warning(f"⚠️ Error reading stats file for task {task.id}: {e}")
            
            logger.warning(f"⚠️ No result files found for task {task.id}")
            return 0, 0
            
        except Exception as e:
            logger.error(f"❌ Error getting file statistics for task {task.id}: {e}")
            return 0, 0


# 統計修正サービスのインスタンス
task_statistics_fixer = TaskStatisticsFixer()
