#!/usr/bin/env python3
"""
タスクアイテム数同期サービス
タスクのアイテム数を実際のDB結果数とJSONLファイル数と同期する
"""

import threading
import time
import os
from datetime import datetime, timedelta
from typing import List
from pathlib import Path

from ..database import SessionLocal, Task as DBTask, Result as DBResult


class TaskSyncService:
    """
    タスクアイテム数同期サービス
    定期的にタスクのアイテム数を実際のDB結果数とJSONLファイル数と同期
    """

    def __init__(self):
        self.running = False
        self.thread = None
        self.sync_interval = 300  # 5分間隔
        self.last_sync_time = None
        self.base_projects_dir = Path("/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects")

    def start(self):
        """同期サービスを開始"""
        if self.running:
            print("⚠️ Task sync service is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_sync_loop, daemon=True)
        self.thread.start()
        print("✅ Task sync service started")

    def stop(self):
        """同期サービスを停止"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("🛑 Task sync service stopped")

    def _count_jsonl_items(self, task_id: str) -> int:
        """JSONLファイルからアイテム数をカウント"""
        try:
            # 各プロジェクトディレクトリでresults_task_*.jsonlファイルを検索
            result_files = list(self.base_projects_dir.glob(f"*/results_{task_id}.jsonl"))

            total_count = 0
            for result_file in result_files:
                if result_file.exists():
                    try:
                        with open(result_file, 'r', encoding='utf-8') as f:
                            line_count = sum(1 for line in f if line.strip())
                        total_count += line_count
                    except Exception as e:
                        print(f"❌ Error reading {result_file}: {e}")
                        continue

            return total_count

        except Exception as e:
            print(f"❌ Error counting JSONL items for {task_id}: {e}")
            return 0

    def _run_sync_loop(self):
        """同期ループのメイン処理"""
        print("🔄 Task sync loop started")

        while self.running:
            try:
                current_time = datetime.now()
                print(f"🔧 Starting task sync at {current_time.strftime('%H:%M:%S')}")
                
                sync_result = self._sync_all_tasks()
                self.last_sync_time = current_time
                
                print(f"✅ Task sync completed: {sync_result['synced_count']} tasks synced")
                
                time.sleep(self.sync_interval)
                
            except Exception as e:
                print(f"❌ Task sync error: {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(60)  # エラー時は1分待機

    def _sync_all_tasks(self) -> dict:
        """すべてのタスクのアイテム数を同期"""
        db = SessionLocal()
        
        try:
            # 過去24時間のタスクを対象
            cutoff_time = datetime.now() - timedelta(hours=24)
            tasks = db.query(DBTask).filter(
                DBTask.created_at >= cutoff_time
            ).all()
            
            synced_count = 0
            total_checked = len(tasks)
            
            print(f"🔍 Checking {total_checked} tasks from last 24 hours")
            
            for task in tasks:
                try:
                    # 実際のDB結果数を取得
                    actual_db_count = db.query(DBResult).filter(
                        DBResult.task_id == task.id
                    ).count()

                    # JSONLファイルからアイテム数を取得
                    jsonl_count = self._count_jsonl_items(task.id)

                    # より多い方を実際のアイテム数とする
                    actual_count = max(actual_db_count, jsonl_count)

                    # アイテム数が不一致の場合は同期
                    if task.items_count != actual_count:
                        print(f"🔧 Syncing task {task.id[:8]}...: {task.items_count} → {actual_count} (DB:{actual_db_count}, JSONL:{jsonl_count})")

                        task.items_count = actual_count
                        task.requests_count = max(actual_count, task.requests_count or 1)

                        synced_count += 1

                except Exception as e:
                    print(f"❌ Error syncing task {task.id[:8]}...: {str(e)}")
                    continue
            
            # 変更をコミット
            if synced_count > 0:
                db.commit()
                print(f"💾 Committed {synced_count} task updates")
            
            return {
                "synced_count": synced_count,
                "total_checked": total_checked,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error in sync_all_tasks: {str(e)}")
            return {
                "synced_count": 0,
                "total_checked": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        finally:
            db.close()

    def sync_task(self, task_id: str) -> dict:
        """特定のタスクのアイテム数を同期"""
        db = SessionLocal()
        
        try:
            task = db.query(DBTask).filter(DBTask.id == task_id).first()
            if not task:
                return {"error": "Task not found", "task_id": task_id}
            
            # 実際のDB結果数を取得
            actual_db_count = db.query(DBResult).filter(
                DBResult.task_id == task_id
            ).count()

            # JSONLファイルからアイテム数を取得
            jsonl_count = self._count_jsonl_items(task_id)

            # より多い方を実際のアイテム数とする
            actual_count = max(actual_db_count, jsonl_count)

            old_count = task.items_count

            # アイテム数を同期
            task.items_count = actual_count
            task.requests_count = max(actual_count, task.requests_count or 1)

            db.commit()

            print(f"🔧 Synced task {task_id[:8]}...: {old_count} → {actual_count} (DB:{actual_db_count}, JSONL:{jsonl_count})")
            
            return {
                "task_id": task_id,
                "old_count": old_count,
                "new_count": actual_count,
                "db_count": actual_db_count,
                "jsonl_count": jsonl_count,
                "synced": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error syncing task {task_id}: {str(e)}")
            return {
                "task_id": task_id,
                "error": str(e),
                "synced": False,
                "timestamp": datetime.now().isoformat()
            }
        finally:
            db.close()

    def get_status(self) -> dict:
        """同期サービスの状態を取得"""
        return {
            "running": self.running,
            "sync_interval": self.sync_interval,
            "last_sync": self.last_sync_time.isoformat() if self.last_sync_time else None
        }


# グローバルインスタンス
task_sync_service = TaskSyncService()
