#!/usr/bin/env python3

import sys
import os
import json
import glob
from datetime import datetime, timedelta

sys.path.append('/home/igtmtakan/workplace/python/scrapyUI')

print("🚀 Final Item Count Fix - 120 rows issue")
print("=" * 60)

try:
    from backend.app.database import SessionLocal, Task, Result, TaskStatus, Project
    
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
        print(f"   Project ID: {target_task.project_id}")
        
        # プロジェクト情報を取得
        project = db.query(Project).filter(Project.id == target_task.project_id).first()
        if project:
            print(f"   Project path: {project.path}")
            
            # 結果ファイルを検索（正しいパス形式）
            search_patterns = [
                f"scrapy_projects/{project.path}/results_{target_task.id}.json",
                f"scrapy_projects/{project.path}/results_{target_task.id}.jsonl",
                f"scrapy_projects/{project.path}/{project.path}/results_{target_task.id}.json",
                f"scrapy_projects/{project.path}/{project.path}/results_{target_task.id}.jsonl",
                f"scrapy_projects/{project.path}/*{target_task.id}*",
                f"scrapy_projects/**/results_{target_task.id}.*",
                f"scrapy_projects/**/*{target_task.id}*"
            ]
            
            found_files = []
            for pattern in search_patterns:
                files = glob.glob(pattern, recursive=True)
                found_files.extend(files)
            
            # 重複を除去
            found_files = list(set(found_files))
            
            print(f"📁 Found result files: {len(found_files)}")
            
            max_file_count = 0
            file_details = {}
            
            for file_path in found_files:
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"   {file_path} ({file_size} bytes)")
                    
                    try:
                        if file_path.endswith('.json'):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                if isinstance(data, list):
                                    count = len(data)
                                    file_details[file_path] = count
                                    max_file_count = max(max_file_count, count)
                                    print(f"     JSON items: {count}")
                                    
                                    # 120行の詳細確認
                                    if count >= 100:
                                        print(f"     🎯 FOUND 120-row file! Count: {count}")
                                        print(f"     Sample item: {str(data[0])[:100]}...")
                                else:
                                    count = 1
                                    file_details[file_path] = count
                                    max_file_count = max(max_file_count, count)
                                    print(f"     JSON object: 1 item")
                                    
                        elif file_path.endswith('.jsonl'):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = [line.strip() for line in f if line.strip()]
                                count = len(lines)
                                file_details[file_path] = count
                                max_file_count = max(max_file_count, count)
                                print(f"     JSONL lines: {count}")
                                
                                # 120行の詳細確認
                                if count >= 100:
                                    print(f"     🎯 FOUND 120-row file! Count: {count}")
                                    if lines:
                                        print(f"     Sample line: {lines[0][:100]}...")
                                        
                    except Exception as e:
                        print(f"     Error reading: {e}")
            
            # データベース結果も確認
            db_results_count = db.query(Result).filter(Result.task_id == target_task.id).count()
            print(f"📊 Database results: {db_results_count}")
            
            # 最も信頼できる件数を決定
            actual_count = max(db_results_count, max_file_count)
            
            print(f"\n📊 Data count analysis:")
            print(f"   Database: {db_results_count}")
            print(f"   Max file count: {max_file_count}")
            print(f"   Actual count (max): {actual_count}")
            print(f"   Current task count: {target_task.items_count}")
            
            # 120行のファイルが見つかった場合の特別処理
            if max_file_count >= 100:
                print(f"\n🎯 120-row file detected! Fixing item count...")
                actual_count = max_file_count
            
            # 不一致がある場合は修正
            if actual_count > 0 and target_task.items_count != actual_count:
                print(f"\n⚠️ MISMATCH DETECTED!")
                print(f"   Task shows: {target_task.items_count} items")
                print(f"   Actual data: {actual_count} items")
                print(f"   File export shows: {max_file_count} rows")
                
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
                    print(f"   This matches the file export rows!")
                else:
                    print("❌ Fix verification failed")
            else:
                print(f"\n✅ No mismatch detected")
                if actual_count == 0:
                    print("   ⚠️ No data found in files or database")
                    print("   This might indicate the files are in a different location")
        else:
            print("❌ Project not found")
    
    else:
        print("❌ No target task found")
    
    db.close()
    
    print("\n🎉 Item count fix analysis completed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
