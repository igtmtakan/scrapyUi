"""
タスク統計検証・修正サービス
データベースとファイルの不一致を自動検出・修正
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

from ..database import SessionLocal, Task as DBTask, TaskStatus, Project as DBProject

logger = logging.getLogger(__name__)


class TaskStatisticsValidator:
    """タスク統計の検証・修正を行うサービス"""

    def __init__(self):
        # ScrapyUIプロジェクトルートからの相対パス
        project_root = Path(__file__).parent.parent.parent.parent
        self.base_projects_dir = project_root / "scrapy_projects"

    def validate_and_fix_all_tasks(self, hours_back: int = 24) -> dict:
        """指定時間内のタスクを検証・修正"""
        try:
            db = SessionLocal()
            try:
                # 指定時間内のタスクを取得
                cutoff_time = datetime.now() - timedelta(hours=hours_back)
                tasks = db.query(DBTask).filter(
                    DBTask.created_at >= cutoff_time
                ).order_by(DBTask.created_at.desc()).all()

                results = {
                    "total_checked": len(tasks),
                    "fixed_tasks": [],
                    "errors": [],
                    "summary": {
                        "items_fixed": 0,
                        "requests_fixed": 0,
                        "status_fixed": 0
                    }
                }

                logger.info(f"🔍 Validating {len(tasks)} tasks from last {hours_back} hours")

                for task in tasks:
                    try:
                        fix_result = self._validate_and_fix_task(task, db)
                        if fix_result["fixed"]:
                            results["fixed_tasks"].append(fix_result)
                            if fix_result["items_changed"]:
                                results["summary"]["items_fixed"] += 1
                            if fix_result["requests_changed"]:
                                results["summary"]["requests_fixed"] += 1
                            if fix_result["status_changed"]:
                                results["summary"]["status_fixed"] += 1
                    except Exception as e:
                        error_msg = f"Error validating task {task.id}: {str(e)}"
                        logger.error(error_msg)
                        results["errors"].append(error_msg)

                # 変更をコミット
                db.commit()

                logger.info(f"✅ Validation complete: {results['summary']}")
                return results

            finally:
                db.close()

        except Exception as e:
            logger.error(f"❌ Error in validate_and_fix_all_tasks: {str(e)}")
            return {"error": str(e)}

    def _validate_and_fix_task(self, task: DBTask, db) -> dict:
        """単一タスクの検証・修正"""
        result = {
            "task_id": task.id,
            "spider_name": getattr(task, 'spider_name', 'unknown'),
            "fixed": False,
            "items_changed": False,
            "requests_changed": False,
            "status_changed": False,
            "before": {
                "items_count": task.items_count,
                "requests_count": task.requests_count,
                "status": task.status.value
            },
            "after": {},
            "file_stats": {}
        }

        try:
            # 結果ファイルから実際の統計を取得
            file_items, file_requests = self._get_file_statistics(task)
            result["file_stats"] = {
                "items_count": file_items,
                "requests_count": file_requests
            }

            # 修正が必要かチェック
            needs_fix = False

            # アイテム数の修正
            if file_items > 0 and file_items != task.items_count:
                logger.info(f"📊 Task {task.id}: Items mismatch - DB: {task.items_count}, File: {file_items}")
                task.items_count = file_items
                result["items_changed"] = True
                needs_fix = True

            # リクエスト数の修正
            if file_requests > 0 and file_requests != task.requests_count:
                logger.info(f"📊 Task {task.id}: Requests mismatch - DB: {task.requests_count}, File: {file_requests}")
                task.requests_count = file_requests
                result["requests_changed"] = True
                needs_fix = True

            # ステータスの修正（改善版）
            if file_items > 0 and task.status == TaskStatus.FAILED:
                logger.info(f"📊 Task {task.id}: Status correction - FAILED → FINISHED (has {file_items} items)")
                task.status = TaskStatus.FINISHED
                task.error_count = 0
                result["status_changed"] = True
                needs_fix = True
            elif file_items == 0 and task.status == TaskStatus.FINISHED:
                # アイテムが0なのに完了になっている場合は失敗に変更
                logger.info(f"📊 Task {task.id}: Status correction - FINISHED → FAILED (no items)")
                task.status = TaskStatus.FAILED
                task.error_count = 1
                result["status_changed"] = True
                needs_fix = True

            if needs_fix:
                result["fixed"] = True
                result["after"] = {
                    "items_count": task.items_count,
                    "requests_count": task.requests_count,
                    "status": task.status.value
                }
                logger.info(f"✅ Task {task.id} fixed: {result['before']} → {result['after']}")

            return result

        except Exception as e:
            logger.error(f"❌ Error validating task {task.id}: {str(e)}")
            result["error"] = str(e)
            return result

    def _get_file_statistics(self, task: DBTask) -> Tuple[int, int]:
        """結果ファイルから統計情報を取得（改善版）"""
        try:
            # プロジェクト情報を取得
            db = SessionLocal()
            try:
                project = db.query(DBProject).filter(DBProject.id == task.project_id).first()
                if not project:
                    return 0, 0
                project_path = project.path
            finally:
                db.close()

            project_dir = self.base_projects_dir / project_path
            items_count = 0
            requests_count = 0

            # 1. 統計ファイルを確認（最優先）
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
                    logger.warning(f"⚠️ Error reading stats file for task {task.id}: {str(e)}")

            # 2. JSONLファイルを確認
            jsonl_file = project_dir / f"results_{task.id}.jsonl"
            if jsonl_file.exists():
                try:
                    with open(jsonl_file, 'r', encoding='utf-8') as f:
                        items_count = sum(1 for _ in f)

                    # リクエスト数を推定（アイテム数 + 初期リクエスト）
                    if items_count > 0:
                        requests_count = max(items_count // 20 + 1, 1)  # ページ数を推定

                    logger.info(f"📊 JSONL file found for task {task.id}: items={items_count}, estimated_requests={requests_count}")
                    return items_count, requests_count
                except Exception as e:
                    logger.warning(f"⚠️ Error reading JSONL file for task {task.id}: {str(e)}")

            # 3. JSONファイルを確認（フォールバック）
            json_file = project_dir / f"results_{task.id}.json"
            if json_file.exists():
                try:
                    file_size = json_file.stat().st_size
                    if file_size < 50:  # 50バイト未満は空ファイル
                        return 0, 0

                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if isinstance(data, list):
                        items_count = len(data)
                        requests_count = max(items_count + 10, 20)
                        logger.info(f"📊 JSON file found for task {task.id}: items={items_count}, requests={requests_count}")
                        return items_count, requests_count
                    else:
                        return 1, 10

                except json.JSONDecodeError:
                    # JSONエラーでもファイルサイズから推定
                    if file_size > 5000:  # 5KB以上
                        estimated_items = max(file_size // 100, 10)
                        estimated_requests = estimated_items + 10
                        return estimated_items, estimated_requests
                except Exception as e:
                    logger.warning(f"⚠️ Error reading JSON file for task {task.id}: {str(e)}")

            logger.info(f"📊 No result files found for task {task.id}")
            return 0, 0

        except Exception as e:
            logger.error(f"❌ Error getting file statistics for task {task.id}: {str(e)}")
            return 0, 0

    def validate_specific_task(self, task_id: str) -> dict:
        """特定のタスクを検証・修正"""
        try:
            db = SessionLocal()
            try:
                task = db.query(DBTask).filter(DBTask.id == task_id).first()
                if not task:
                    return {"error": f"Task {task_id} not found"}

                result = self._validate_and_fix_task(task, db)
                db.commit()

                return result

            finally:
                db.close()

        except Exception as e:
            logger.error(f"❌ Error validating specific task {task_id}: {str(e)}")
            return {"error": str(e)}


# グローバルインスタンス
task_validator = TaskStatisticsValidator()


def validate_recent_tasks(hours_back: int = 24) -> dict:
    """最近のタスクを検証・修正（外部から呼び出し可能）"""
    return task_validator.validate_and_fix_all_tasks(hours_back)


def validate_task(task_id: str) -> dict:
    """特定のタスクを検証・修正（外部から呼び出し可能）"""
    return task_validator.validate_specific_task(task_id)
