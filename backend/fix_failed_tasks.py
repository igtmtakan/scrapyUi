#!/usr/bin/env python3
"""
失敗タスクの修正スクリプト

結果ファイルが存在するのに「FAILED」ステータスになっているタスクを
「FINISHED」ステータスに修正します。
"""

import os
import sys
import json
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, Task as DBTask, TaskStatus

def check_results_file_exists(task_id: str) -> bool:
    """結果ファイルの存在をチェック（複数の場所を検索）"""
    try:
        # 複数の可能な場所を検索
        possible_paths = [
            f"results_{task_id}.jsonl",  # カレントディレクトリ
            f"../results_{task_id}.jsonl",  # 親ディレクトリ
            f"../scrapy_projects/*/results_{task_id}.jsonl",  # プロジェクトディレクトリ
        ]

        import glob
        for pattern in possible_paths:
            files = glob.glob(pattern)
            for file_path in files:
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    return True

        return False
    except Exception:
        return False

def get_task_stats_from_file(task_id: str) -> dict:
    """結果ファイルから統計情報を取得"""
    try:
        results_file = f"results_{task_id}.jsonl"
        
        if not os.path.exists(results_file):
            return {'items_count': 0, 'requests_count': 0}
        
        items_count = 0
        with open(results_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    items_count += 1
        
        return {
            'items_count': items_count,
            'requests_count': items_count,  # 簡易的な推定
        }
        
    except Exception as e:
        print(f"Error reading task stats from file: {e}")
        return {'items_count': 0, 'requests_count': 0}

def fix_failed_tasks():
    """失敗タスクを修正"""
    db = SessionLocal()
    try:
        print("🔍 Checking for failed tasks with results...")
        
        # FAILEDステータスのタスクを取得
        failed_tasks = db.query(DBTask).filter(DBTask.status == TaskStatus.FAILED).all()
        
        print(f"Found {len(failed_tasks)} failed tasks")
        
        fixed_count = 0
        for task in failed_tasks:
            print(f"\n📋 Checking task {task.id[:8]}...")
            
            # 結果ファイルをチェック
            if check_results_file_exists(task.id):
                # 結果ファイルから統計情報を取得
                stats = get_task_stats_from_file(task.id)
                
                print(f"  📊 Found {stats['items_count']} items in results file")
                
                if stats['items_count'] > 0:
                    # データがあるので成功に変更
                    old_status = task.status
                    task.status = TaskStatus.FINISHED
                    task.items_count = stats['items_count']
                    task.requests_count = stats.get('requests_count', 0)
                    task.error_count = 0
                    task.error_message = None
                    
                    if not task.finished_at:
                        task.finished_at = datetime.now()
                    
                    fixed_count += 1
                    
                    print(f"  ✅ Fixed: {old_status.value} → FINISHED ({stats['items_count']} items)")
                else:
                    print(f"  ⚠️ Results file exists but no items found")
            else:
                print(f"  ❌ No results file found")
        
        if fixed_count > 0:
            db.commit()
            print(f"\n🎉 Successfully fixed {fixed_count} failed tasks!")
        else:
            print(f"\n💡 No failed tasks with results found to fix")
            
    except Exception as e:
        print(f"❌ Error fixing failed tasks: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def fix_specific_task(task_id: str):
    """特定のタスクを修正"""
    db = SessionLocal()
    try:
        print(f"🔍 Checking specific task {task_id[:8]}...")
        
        task = db.query(DBTask).filter(DBTask.id == task_id).first()
        if not task:
            print(f"❌ Task {task_id} not found")
            return
        
        print(f"📋 Current status: {task.status.value}")
        print(f"📊 Current items count: {task.items_count}")
        
        # 結果ファイルをチェック
        if check_results_file_exists(task_id):
            stats = get_task_stats_from_file(task_id)
            print(f"📁 Results file found with {stats['items_count']} items")
            
            if stats['items_count'] > 0:
                old_status = task.status
                task.status = TaskStatus.FINISHED
                task.items_count = stats['items_count']
                task.requests_count = stats.get('requests_count', 0)
                task.error_count = 0
                task.error_message = None
                
                if not task.finished_at:
                    task.finished_at = datetime.now()
                
                db.commit()
                print(f"✅ Fixed: {old_status.value} → FINISHED ({stats['items_count']} items)")
            else:
                print(f"⚠️ Results file exists but no items found")
        else:
            print(f"❌ No results file found for task {task_id}")
            
    except Exception as e:
        print(f"❌ Error fixing task: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 特定のタスクIDが指定された場合
        task_id = sys.argv[1]
        fix_specific_task(task_id)
    else:
        # 全ての失敗タスクをチェック
        fix_failed_tasks()
