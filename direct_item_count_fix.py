#!/usr/bin/env python3

import sys
import os
import json
from datetime import datetime, timedelta

sys.path.append('/home/igtmtakan/workplace/python/scrapyUI')

print("🚀 Direct Item Count Mismatch Fix")
print("=" * 60)

try:
    from backend.app.database import SessionLocal, Task, Result, TaskStatus
    
    db = SessionLocal()
    
    # 2025/6/21 16:54:14 前後のタスクを検索
    target_time = datetime(2025, 6, 21, 16, 54, 14)
    time_range_start = target_time - timedelta(minutes=5)
    time_range_end = target_time + timedelta(minutes=10)
    
    print(f"🔍 Searching for tasks between {time_range_start} and {time_range_end}")
    
    tasks = db.query(Task).filter(
        Task.created_at >= time_range_start,
        Task.created_at <= time_range_end,
        Task.status == TaskStatus.FINISHED
    ).all()
    
    print(f"📋 Found {len(tasks)} tasks in time range")
    
    target_task = None
    for task in tasks:
        duration = 0
        if task.started_at and task.finished_at:
            duration = (task.finished_at - task.started_at).total_seconds()
        
        print(f"Task: {task.id[:12]}... | Created: {task.created_at} | Items: {task.items_count} | Requests: {task.requests_count}")
        
        # 最も条件に合致するタスクを選択
        if not target_task or abs((task.created_at - target_time).total_seconds()) < abs((target_task.created_at - target_time).total_seconds()):
            target_task = task
    
    if target_task:
        print(f"\n🎯 Target task: {target_task.id}")
        print(f"   Current items: {target_task.items_count}")
        print(f"   Current requests: {target_task.requests_count}")
        
        # データベース結果を確認
        db_results_count = db.query(Result).filter(Result.task_id == target_task.id).count()
        print(f"📊 Database results: {db_results_count}")
        
        # 結果ファイルを確認
        file_counts = {}
        file_patterns = [
            f"scrapy_projects/results/{target_task.id}.jsonl",
            f"scrapy_projects/results/{target_task.id}.json",
            f"scrapy_projects/results/{target_task.id}.csv"
        ]
        
        for file_path in file_patterns:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"📁 Found: {file_path} ({file_size} bytes)")
                
                try:
                    if file_path.endswith('.jsonl'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = [line.strip() for line in f if line.strip()]
                            file_counts['jsonl'] = len(lines)
                            print(f"   JSONL lines: {len(lines)}")
                            
                    elif file_path.endswith('.json'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                file_counts['json'] = len(data)
                                print(f"   JSON items: {len(data)}")
                            else:
                                file_counts['json'] = 1
                                print(f"   JSON object: 1 item")
                                
                    elif file_path.endswith('.csv'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            csv_count = max(0, len(lines) - 1)  # ヘッダーを除く
                            file_counts['csv'] = csv_count
                            print(f"   CSV rows: {csv_count}")
                            
                except Exception as e:
                    print(f"   Error reading {file_path}: {e}")
        
        # 最も信頼できる件数を決定
        actual_count = max(db_results_count, max(file_counts.values()) if file_counts else 0)
        
        print(f"\n📊 Data count analysis:")
        print(f"   Database: {db_results_count}")
        print(f"   Files: {file_counts}")
        print(f"   Actual count (max): {actual_count}")
        print(f"   Current task count: {target_task.items_count}")
        
        # 不一致がある場合は修正
        if actual_count > 0 and target_task.items_count != actual_count:
            print(f"\n⚠️ MISMATCH DETECTED!")
            print(f"   Task shows: {target_task.items_count} items")
            print(f"   Actual data: {actual_count} items")
            
            # 修正を実行
            old_items = target_task.items_count
            old_requests = target_task.requests_count
            
            target_task.items_count = actual_count
            target_task.requests_count = max(actual_count + 10, old_requests)
            target_task.updated_at = datetime.now()
            
            db.commit()
            
            print(f"✅ Item count fixed:")
            print(f"   Items: {old_items} → {actual_count}")
            print(f"   Requests: {old_requests} → {target_task.requests_count}")
            
            # 検証
            updated_task = db.query(Task).filter(Task.id == target_task.id).first()
            if updated_task and updated_task.items_count == actual_count:
                print("🎉 ITEM COUNT MISMATCH FIX SUCCESSFUL!")
                print(f"   Task now shows correct item count: {actual_count}")
            else:
                print("❌ Fix verification failed")
        else:
            print(f"\n✅ No mismatch detected or already correct")
    
    else:
        print("❌ No target task found")
    
    # 最近のすべてのタスクもチェック
    print(f"\n🔍 Checking all recent tasks for mismatches...")
    recent_cutoff = datetime.now() - timedelta(hours=6)
    recent_tasks = db.query(Task).filter(
        Task.created_at >= recent_cutoff,
        Task.status == TaskStatus.FINISHED
    ).all()
    
    print(f"📋 Found {len(recent_tasks)} recent tasks")
    
    fixed_count = 0
    for task in recent_tasks:
        # データベース結果を確認
        db_count = db.query(Result).filter(Result.task_id == task.id).count()
        
        # 結果ファイルを確認
        jsonl_file = f"scrapy_projects/results/{task.id}.jsonl"
        file_count = 0
        if os.path.exists(jsonl_file):
            try:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    file_count = sum(1 for line in f if line.strip())
            except:
                pass
        
        actual_count = max(db_count, file_count)
        
        # 不一致がある場合は修正
        if actual_count > 0 and task.items_count != actual_count:
            print(f"Fixing: {task.id[:12]}... | DB:{task.items_count} → Actual:{actual_count}")
            
            task.items_count = actual_count
            task.requests_count = max(actual_count + 10, task.requests_count or 0)
            task.updated_at = datetime.now()
            
            fixed_count += 1
    
    if fixed_count > 0:
        db.commit()
        print(f"✅ Fixed {fixed_count} additional tasks")
    
    db.close()
    
    print("\n🎉 Item count mismatch fix completed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
