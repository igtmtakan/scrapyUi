"""
自動修復サービス
システムの問題を自動的に検出・修復する
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from ..database import SessionLocal, Task, TaskStatus

logger = logging.getLogger(__name__)

class AutoRepairService:
    """自動修復サービス"""
    
    def __init__(self):
        self.running = False
        self.base_projects_dir = Path("/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects")
        self.db_config = {
            'host': 'localhost',
            'user': 'scrapy_user',
            'password': 'ScrapyUser@2024#',
            'database': 'scrapy_ui'
        }
        self.repair_stats = {
            'total_repairs': 0,
            'item_count_repairs': 0,
            'stuck_task_repairs': 0,
            'file_sync_repairs': 0,
            'last_repair_time': None
        }

    async def start_auto_repair(self):
        """自動修復開始"""
        self.running = True
        logger.info("🔧 Auto repair service started")
        
        # 定期修復ループ
        asyncio.create_task(self._repair_loop())

    async def stop_auto_repair(self):
        """自動修復停止"""
        self.running = False
        logger.info("🛑 Auto repair service stopped")

    async def _repair_loop(self):
        """修復ループ"""
        while self.running:
            try:
                await self._perform_auto_repairs()
                await asyncio.sleep(300)  # 5分間隔
            except Exception as e:
                logger.error(f"❌ Auto repair error: {e}")
                await asyncio.sleep(60)

    async def _perform_auto_repairs(self):
        """自動修復実行"""
        logger.debug("🔧 Performing auto repairs...")
        
        # 1. アイテム数の修復
        await self._repair_item_counts()
        
        # 2. スタックしたタスクの修復
        await self._repair_stuck_tasks()
        
        # 3. ファイル同期の修復
        await self._repair_file_sync()
        
        self.repair_stats['last_repair_time'] = datetime.now()

    async def _repair_item_counts(self):
        """アイテム数の自動修復"""
        try:
            with SessionLocal() as db:
                # アイテム数が0のFINISHEDタスクを検索
                zero_item_tasks = db.query(Task).filter(
                    Task.status == TaskStatus.FINISHED,
                    Task.items_count == 0
                ).limit(20).all()  # 一度に20件まで処理
                
                for task in zero_item_tasks:
                    # 対応する結果データを確認
                    from sqlalchemy import text
                    result_count = db.execute(
                        text("SELECT COUNT(*) FROM results WHERE task_id = :task_id"),
                        {"task_id": task.id}
                    ).fetchone()
                    
                    if result_count and result_count[0] > 0:
                        # アイテム数を修正
                        task.items_count = result_count[0]
                        self.repair_stats['item_count_repairs'] += 1
                        self.repair_stats['total_repairs'] += 1
                        logger.info(f"🔧 Repaired item count for task {task.id}: 0 → {result_count[0]}")
                
                db.commit()
                
        except Exception as e:
            logger.error(f"❌ Item count repair failed: {e}")

    async def _repair_stuck_tasks(self):
        """スタックしたタスクの自動修復（強化版）"""
        try:
            with SessionLocal() as db:
                # 1. 長時間RUNNINGのタスクを検索（1時間以上）
                stuck_threshold = datetime.now() - timedelta(hours=1)
                stuck_tasks = db.query(Task).filter(
                    Task.status == TaskStatus.RUNNING,
                    Task.started_at < stuck_threshold
                ).limit(20).all()  # 一度に20件まで処理

                for task in stuck_tasks:
                    # プロセスが実際に動いているかチェック
                    is_process_running = await self._check_task_process(task.id)

                    if not is_process_running:
                        # 結果ファイルから実際の状態を判定
                        actual_status = await self._determine_actual_task_status(task)

                        if actual_status == "FINISHED":
                            task.status = TaskStatus.FINISHED
                            task.finished_at = datetime.now()
                            logger.info(f"🔧 Repaired stuck task as FINISHED: {task.id}")
                        else:
                            task.status = TaskStatus.FAILED
                            task.finished_at = datetime.now()
                            logger.info(f"🔧 Repaired stuck task as FAILED: {task.id}")

                        self.repair_stats['stuck_task_repairs'] += 1
                        self.repair_stats['total_repairs'] += 1

                # 2. 長時間PENDINGのタスクをチェック（30分以上）
                pending_threshold = datetime.now() - timedelta(minutes=30)
                pending_tasks = db.query(Task).filter(
                    Task.status == TaskStatus.PENDING,
                    Task.created_at < pending_threshold
                ).limit(10).all()

                for task in pending_tasks:
                    # PENDINGタスクをFAILEDに変更
                    task.status = TaskStatus.FAILED
                    task.finished_at = datetime.now()
                    self.repair_stats['stuck_task_repairs'] += 1
                    self.repair_stats['total_repairs'] += 1
                    logger.info(f"🔧 Repaired stuck PENDING task: {task.id}")

                db.commit()

        except Exception as e:
            logger.error(f"❌ Stuck task repair failed: {e}")

    async def _check_task_process(self, task_id: str) -> bool:
        """タスクのプロセスが実際に動いているかチェック"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any(task_id in arg for arg in cmdline):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception:
            return False

    async def _determine_actual_task_status(self, task) -> str:
        """結果ファイルから実際のタスク状態を判定"""
        try:
            # 結果ファイルの存在確認
            result_file = self.base_projects_dir / f"{task.project.name}/results/{task.id}.jsonl"

            if result_file.exists():
                # ファイルサイズと行数をチェック
                file_size = result_file.stat().st_size
                if file_size > 0:
                    # 行数をカウント
                    with open(result_file, 'r', encoding='utf-8') as f:
                        line_count = sum(1 for _ in f)

                    if line_count > 0:
                        # アイテム数を更新
                        task.items_count = line_count
                        return "FINISHED"

            return "FAILED"

        except Exception as e:
            logger.error(f"❌ Error determining task status for {task.id}: {e}")
            return "FAILED"

    async def _repair_file_sync(self):
        """ファイル同期の自動修復"""
        try:
            # 結果ファイルとデータベースの同期チェック
            result_files = list(self.base_projects_dir.glob("**/results_*.jsonl"))
            
            with SessionLocal() as db:
                for file_path in result_files[:10]:  # 一度に10件まで処理
                    try:
                        # ファイル名からタスクIDを抽出
                        task_id = file_path.stem.replace("results_", "")
                        
                        # ファイル内のアイテム数をカウント
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_items = sum(1 for line in f if line.strip())
                        
                        # データベース内のタスクを確認
                        task = db.query(Task).filter(Task.id == task_id).first()
                        
                        if task and task.items_count != file_items:
                            # 不整合を修正
                            task.items_count = file_items
                            self.repair_stats['file_sync_repairs'] += 1
                            self.repair_stats['total_repairs'] += 1
                            logger.info(f"🔧 Synced file data for task {task_id}: {task.items_count} → {file_items}")
                    
                    except Exception as e:
                        logger.warning(f"⚠️ File sync repair failed for {file_path}: {e}")
                
                db.commit()
                
        except Exception as e:
            logger.error(f"❌ File sync repair failed: {e}")

    async def manual_repair_all(self) -> Dict[str, Any]:
        """手動での包括的修復"""
        logger.info("🔧 Starting manual comprehensive repair...")
        start_time = datetime.now()
        
        repair_results = {
            'started_at': start_time,
            'item_count_repairs': 0,
            'stuck_task_repairs': 0,
            'file_sync_repairs': 0,
            'errors': []
        }
        
        try:
            # アイテム数修復
            await self._repair_item_counts()
            repair_results['item_count_repairs'] = self.repair_stats['item_count_repairs']
            
            # スタックタスク修復
            await self._repair_stuck_tasks()
            repair_results['stuck_task_repairs'] = self.repair_stats['stuck_task_repairs']
            
            # ファイル同期修復
            await self._repair_file_sync()
            repair_results['file_sync_repairs'] = self.repair_stats['file_sync_repairs']
            
            repair_results['completed_at'] = datetime.now()
            repair_results['duration'] = (repair_results['completed_at'] - start_time).total_seconds()
            
            logger.info(f"✅ Manual repair completed in {repair_results['duration']:.2f}s")
            
        except Exception as e:
            error_msg = f"Manual repair failed: {e}"
            repair_results['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
        
        return repair_results

    async def get_repair_stats(self) -> Dict[str, Any]:
        """修復統計を取得"""
        return self.repair_stats.copy()

    async def repair_specific_task(self, task_id: str) -> Dict[str, Any]:
        """特定タスクの修復"""
        try:
            with SessionLocal() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    return {"status": "error", "message": "Task not found"}
                
                # 結果データ数を確認
                from sqlalchemy import text
                result_count = db.execute(
                    text("SELECT COUNT(*) FROM results WHERE task_id = :task_id"),
                    {"task_id": task_id}
                ).fetchone()
                
                if result_count and result_count[0] > 0:
                    old_count = task.items_count
                    task.items_count = result_count[0]
                    
                    # スタックしている場合の修復
                    if task.status == TaskStatus.RUNNING:
                        time_diff = datetime.now() - task.started_at
                        if time_diff.total_seconds() > 3600:  # 1時間以上
                            task.status = TaskStatus.FINISHED
                            task.finished_at = datetime.now()
                    
                    db.commit()
                    
                    return {
                        "status": "success",
                        "message": f"Task repaired: items {old_count} → {result_count[0]}",
                        "old_count": old_count,
                        "new_count": result_count[0]
                    }
                else:
                    return {"status": "info", "message": "No repair needed"}
                    
        except Exception as e:
            logger.error(f"❌ Task repair failed for {task_id}: {e}")
            return {"status": "error", "message": str(e)}

# グローバルインスタンス
auto_repair_service = AutoRepairService()
