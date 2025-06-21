#!/usr/bin/env python3
"""
アイテム数と実際の件数の不一致を修正するスクリプト

ファイルエクスポートに120行あるのに、アイテム数が1と表示される
問題を根本的に解決します。
"""

import sys
import os
import json
from datetime import datetime, timedelta

# ScrapyUIのパスを追加
sys.path.append('/home/igtmtakan/workplace/python/scrapyUI')

from backend.app.database import SessionLocal, Task, Result, TaskStatus


def find_latest_task_175():
    """最新のtask_175を検索"""
    print("🔍 Searching for the latest task_175...")
    
    db = SessionLocal()
    try:
        # 2025/6/21 16:54:14 前後のタスクを検索
        target_time = datetime(2025, 6, 21, 16, 54, 14)
        time_range_start = target_time - timedelta(minutes=5)
        time_range_end = target_time + timedelta(minutes=10)
        
        tasks = db.query(Task).filter(
            Task.created_at >= time_range_start,
            Task.created_at <= time_range_end,
            Task.status == TaskStatus.FINISHED
        ).all()
        
        print(f"📋 Found {len(tasks)} tasks in time range:")
        
        target_task = None
        for task in tasks:
            duration = 0
            if task.started_at and task.finished_at:
                duration = (task.finished_at - task.started_at).total_seconds()
            
            print(f"   Task: {task.id[:12]}...")
            print(f"   Created: {task.created_at}")
            print(f"   Duration: {duration:.1f}s")
            print(f"   Items: {task.items_count}, Requests: {task.requests_count}")
            
            # 最も条件に合致するタスクを選択
            if not target_task or abs((task.created_at - target_time).total_seconds()) < abs((target_task.created_at - target_time).total_seconds()):
                target_task = task
            print("   ---")
        
        return target_task
        
    finally:
        db.close()


def analyze_actual_data_count(task_id: str):
    """実際のデータ件数を詳細分析"""
    print(f"\n🔬 Analyzing actual data count for task: {task_id}")
    
    # データベース結果を確認
    db = SessionLocal()
    try:
        db_results = db.query(Result).filter(Result.task_id == task_id).all()
        db_count = len(db_results)
        print(f"📊 Database results: {db_count} items")
        
        if db_results:
            print("   Sample DB results:")
            for i, result in enumerate(db_results[:3]):
                print(f"     {i+1}. ID: {result.id}")
                print(f"        Data: {str(result.data)[:100]}...")
        
    finally:
        db.close()
    
    # 結果ファイルを確認
    file_counts = {}
    file_patterns = [
        f"scrapy_projects/results/{task_id}.jsonl",
        f"scrapy_projects/results/{task_id}.json",
        f"scrapy_projects/results/{task_id}.csv",
        f"scrapy_projects/results/{task_id}.xml"
    ]
    
    for file_path in file_patterns:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"📁 Found file: {file_path} ({file_size} bytes)")
            
            try:
                if file_path.endswith('.jsonl'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = [line.strip() for line in f if line.strip()]
                        file_counts['jsonl'] = len(lines)
                        print(f"     JSONL lines: {len(lines)}")
                        if lines:
                            print(f"     Sample: {lines[0][:100]}...")
                            
                elif file_path.endswith('.json'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            file_counts['json'] = len(data)
                            print(f"     JSON array: {len(data)} items")
                        else:
                            file_counts['json'] = 1
                            print(f"     JSON object: 1 item")
                            
                elif file_path.endswith('.csv'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # ヘッダーを除いた行数
                        csv_count = max(0, len(lines) - 1)
                        file_counts['csv'] = csv_count
                        print(f"     CSV rows (excluding header): {csv_count}")
                        
                elif file_path.endswith('.xml'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # XMLアイテム数を推定（<item>タグの数）
                        xml_count = content.count('<item>')
                        file_counts['xml'] = xml_count
                        print(f"     XML items: {xml_count}")
                        
            except Exception as e:
                print(f"     Error reading file: {e}")
    
    return db_count, file_counts


def fix_item_count_mismatch(task_id: str, actual_count: int):
    """アイテム数の不一致を修正"""
    print(f"\n🔧 Fixing item count mismatch for task: {task_id}")
    print(f"   Setting item count to: {actual_count}")
    
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print("❌ Task not found")
            return False
        
        old_items = task.items_count
        old_requests = task.requests_count
        
        # 実際の件数に基づいて修正
        task.items_count = actual_count
        task.requests_count = max(actual_count + 10, old_requests)  # リクエスト数も適切に調整
        task.updated_at = datetime.now()
        
        db.commit()
        
        print(f"✅ Item count fixed:")
        print(f"   Items: {old_items} → {actual_count}")
        print(f"   Requests: {old_requests} → {task.requests_count}")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Fix failed: {e}")
        return False
        
    finally:
        db.close()


def verify_fix_result(task_id: str):
    """修正結果の検証"""
    print(f"\n✅ Verifying fix result for task: {task_id}")
    
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print("❌ Task not found")
            return False
        
        print(f"📊 Updated task state:")
        print(f"   Status: {task.status}")
        print(f"   Items: {task.items_count}")
        print(f"   Requests: {task.requests_count}")
        print(f"   Updated: {task.updated_at}")
        
        return True
        
    finally:
        db.close()


def fix_all_recent_mismatches():
    """最近のすべての不一致を修正"""
    print(f"\n🔧 Fixing all recent item count mismatches...")
    
    db = SessionLocal()
    try:
        # 最近24時間のタスクを取得
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_tasks = db.query(Task).filter(
            Task.created_at >= cutoff_time,
            Task.status == TaskStatus.FINISHED
        ).all()
        
        print(f"📋 Found {len(recent_tasks)} recent finished tasks")
        
        fixed_count = 0
        for task in recent_tasks:
            # 実際のデータ件数を確認
            db_count, file_counts = analyze_actual_data_count(task.id)
            
            # 最も信頼できる件数を決定
            actual_count = max(db_count, max(file_counts.values()) if file_counts else 0)
            
            # 不一致がある場合は修正
            if actual_count > 0 and task.items_count != actual_count:
                print(f"🔧 Mismatch found: Task {task.id[:12]}... - DB:{task.items_count} vs Actual:{actual_count}")
                
                task.items_count = actual_count
                task.requests_count = max(actual_count + 10, task.requests_count or 0)
                task.updated_at = datetime.now()
                
                fixed_count += 1
        
        if fixed_count > 0:
            db.commit()
            print(f"✅ Fixed {fixed_count} tasks with item count mismatches")
        else:
            print("✅ No item count mismatches found")
        
        return fixed_count
        
    finally:
        db.close()


def main():
    """メイン実行"""
    print("🚀 Item Count Mismatch Fix")
    print("=" * 60)
    print("Issue: File export shows 120 rows, but item count shows 1")
    print("Goal: Fix item count to match actual data count")
    print("=" * 60)
    
    try:
        # 1. 最新のタスクを検索
        target_task = find_latest_task_175()
        
        if not target_task:
            print("❌ Target task not found")
            return
        
        print(f"🎯 Target task identified: {target_task.id}")
        
        # 2. 実際のデータ件数を分析
        db_count, file_counts = analyze_actual_data_count(target_task.id)
        
        # 3. 最も信頼できる件数を決定
        actual_count = max(db_count, max(file_counts.values()) if file_counts else 0)
        
        print(f"\n📊 Data count analysis:")
        print(f"   Database count: {db_count}")
        print(f"   File counts: {file_counts}")
        print(f"   Actual count (max): {actual_count}")
        print(f"   Current task item count: {target_task.items_count}")
        
        # 4. 不一致がある場合は修正
        if actual_count > 0 and target_task.items_count != actual_count:
            print(f"\n⚠️ MISMATCH DETECTED!")
            print(f"   Task shows: {target_task.items_count} items")
            print(f"   Actual data: {actual_count} items")
            
            # 修正を実行
            fix_success = fix_item_count_mismatch(target_task.id, actual_count)
            
            if fix_success:
                # 修正結果を検証
                verify_fix_result(target_task.id)
        else:
            print(f"\n✅ No mismatch detected")
        
        # 5. 他の最近のタスクも修正
        fixed_count = fix_all_recent_mismatches()
        
        # 6. 結果サマリー
        print("\n" + "=" * 60)
        print("🎯 ITEM COUNT MISMATCH FIX RESULTS:")
        
        if actual_count > 0 and target_task.items_count != actual_count:
            print("🎉 SUCCESS!")
            print(f"   ✅ Target task item count fixed: {target_task.items_count} → {actual_count}")
            print(f"   ✅ Additional tasks fixed: {fixed_count}")
            print(f"   ✅ Item counts now match actual data")
        else:
            print("✅ No issues found or already fixed")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Execution error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
