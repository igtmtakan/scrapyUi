#!/usr/bin/env python3
"""
自動修復デーモン
失敗したタスクを定期的にチェックして、crawlwithwatchdog結果に基づいて修復する
"""

import sys
import os
import time
from datetime import datetime, timedelta

# パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, Task as DBTask, TaskStatus, Result as DBResult

def auto_repair_failed_tasks():
    """
    失敗したタスクを自動修復
    """
    db = SessionLocal()
    try:
        print(f"🔧 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting auto-repair check...")
        
        # 過去6時間以内の失敗タスクを取得
        cutoff_time = datetime.now() - timedelta(hours=6)
        
        failed_tasks = db.query(DBTask).filter(
            DBTask.status == TaskStatus.FAILED,
            DBTask.created_at >= cutoff_time
        ).all()
        
        print(f"   Found {len(failed_tasks)} failed tasks in last 6 hours")
        
        repaired_count = 0
        for task in failed_tasks:
            # crawlwithwatchdog でインサートされた行数を確認
            db_results_count = db.query(DBResult).filter(DBResult.task_id == task.id).count()
            
            print(f"   Checking task {task.id[:8]}... - crawlwithwatchdog results: {db_results_count}")
            
            # 失敗の定義: crawlwithwatchdog でインサートされた行がない場合
            if db_results_count > 0:
                print(f"   🔧 REPAIRING: Task has {db_results_count} crawlwithwatchdog results - converting to SUCCESS")
                
                # タスクを成功状態に修復
                task.status = TaskStatus.FINISHED
                task.items_count = db_results_count  # crawlwithwatchdog の結果数
                task.requests_count = max(db_results_count, task.requests_count or 1)
                task.error_count = 0
                
                repaired_count += 1
            else:
                print(f"   ✅ CONFIRMED FAILURE: No crawlwithwatchdog results - task remains failed")
        
        if repaired_count > 0:
            db.commit()
            print(f"✅ Auto-repaired {repaired_count} tasks")
        else:
            print("   No tasks needed repair")
            
        print(f"📊 Result: repaired_count={repaired_count}, checked_count={len(failed_tasks)}")
        
    except Exception as e:
        print(f"❌ Error in auto-repair: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

def main():
    """
    メインループ - 2分間隔で自動修復を実行
    """
    print("🚀 Auto-repair daemon started")
    print("   Checking failed tasks every 2 minutes...")
    print("   Press Ctrl+C to stop")
    
    try:
        while True:
            auto_repair_failed_tasks()
            print(f"😴 Sleeping for 2 minutes...")
            time.sleep(120)  # 2分間隔
    except KeyboardInterrupt:
        print("\n🛑 Auto-repair daemon stopped")
    except Exception as e:
        print(f"❌ Fatal error in auto-repair daemon: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
