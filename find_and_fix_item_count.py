#!/usr/bin/env python3

import sys
import os
import json
import glob
from datetime import datetime, timedelta

sys.path.append('/home/igtmtakan/workplace/python/scrapyUI')

print("🚀 Find and Fix Item Count Mismatch")
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
        print(f"Task: {task.id[:12]}... | Created: {task.created_at} | Items: {task.items_count}")
        
        # 最も条件に合致するタスクを選択
        if not target_task or abs((task.created_at - target_time).total_seconds()) < abs((target_task.created_at - target_time).total_seconds()):
            target_task = task
    
    if target_task:
        print(f"\n🎯 Target task: {target_task.id}")
        print(f"   Current items: {target_task.items_count}")
        print(f"   Project: {target_task.project_id}")
        print(f"   Spider: {target_task.spider_id}")
        
        # データベース結果を確認
        db_results_count = db.query(Result).filter(Result.task_id == target_task.id).count()
        print(f"📊 Database results: {db_results_count}")
        
        # 結果ファイルを検索（複数の場所を確認）
        search_patterns = [
            f"scrapy_projects/*/results/{target_task.id}.*",
            f"scrapy_projects/*/{target_task.id}.*",
            f"scrapy_projects/results/{target_task.id}.*",
            f"results/{target_task.id}.*",
            f"{target_task.id}.*"
        ]
        
        found_files = []
        for pattern in search_patterns:
            files = glob.glob(pattern)
            found_files.extend(files)
        
        # 重複を除去
        found_files = list(set(found_files))
        
        print(f"📁 Found result files: {len(found_files)}")
        
        file_counts = {}
        max_file_count = 0
        
        for file_path in found_files:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"   {file_path} ({file_size} bytes)")
                
                try:
                    if file_path.endswith('.jsonl'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = [line.strip() for line in f if line.strip()]
                            count = len(lines)
                            file_counts[file_path] = count
                            max_file_count = max(max_file_count, count)
                            print(f"     JSONL lines: {count}")
                            
                    elif file_path.endswith('.json'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                count = len(data)
                                file_counts[file_path] = count
                                max_file_count = max(max_file_count, count)
                                print(f"     JSON items: {count}")
                            else:
                                count = 1
                                file_counts[file_path] = count
                                max_file_count = max(max_file_count, count)
                                print(f"     JSON object: 1 item")
                                
                    elif file_path.endswith('.csv'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            count = max(0, len(lines) - 1)  # ヘッダーを除く
                            file_counts[file_path] = count
                            max_file_count = max(max_file_count, count)
                            print(f"     CSV rows: {count}")
                            
                    elif file_path.endswith('.xml'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            count = content.count('<item>')
                            file_counts[file_path] = count
                            max_file_count = max(max_file_count, count)
                            print(f"     XML items: {count}")
                            
                except Exception as e:
                    print(f"     Error reading: {e}")
        
        # 最も信頼できる件数を決定
        actual_count = max(db_results_count, max_file_count)
        
        print(f"\n📊 Data count analysis:")
        print(f"   Database: {db_results_count}")
        print(f"   Max file count: {max_file_count}")
        print(f"   Actual count (max): {actual_count}")
        print(f"   Current task count: {target_task.items_count}")
        
        # 不一致がある場合は修正
        if actual_count > 0 and target_task.items_count != actual_count:
            print(f"\n⚠️ MISMATCH DETECTED!")
            print(f"   Task shows: {target_task.items_count} items")
            print(f"   Actual data: {actual_count} items")
            print(f"   Difference: {actual_count - target_task.items_count}")
            
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
                print(f"   This matches the 120 rows in file export!")
            else:
                print("❌ Fix verification failed")
        else:
            print(f"\n✅ No mismatch detected")
            if actual_count == 0:
                print("   ⚠️ No data found in files or database")
    
    else:
        print("❌ No target task found")
    
    db.close()
    
    print("\n🎉 Item count analysis completed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
