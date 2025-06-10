#!/usr/bin/env python3
"""
重複データクリーンアップツール
"""
import sys
import argparse

# プロジェクトルートをパスに追加
sys.path.append('/home/igtmtakan/workplace/python/scrapyUI/backend')

from app.database import SessionLocal, Task, Result
from app.services.duplicate_prevention_service import DuplicatePreventionService
from sqlalchemy import desc

def list_tasks_with_duplicates():
    """重複があるタスクを一覧表示"""
    db = SessionLocal()
    try:
        dup_service = DuplicatePreventionService(db)
        
        # 最近のタスクを取得
        recent_tasks = db.query(Task).order_by(desc(Task.created_at)).limit(20).all()
        
        print("📋 最近のタスクの重複状況:")
        print("-" * 80)
        
        for task in recent_tasks:
            stats = dup_service.get_duplicate_stats(task.id)
            if stats['total_results'] > 0:
                duplicate_rate = (stats['hash_duplicates'] / stats['total_results']) * 100 if stats['total_results'] > 0 else 0
                status_icon = "⚠️" if stats['hash_duplicates'] > 0 else "✅"
                
                print(f"{status_icon} Task: {task.id[:8]}... | "
                      f"Total: {stats['total_results']} | "
                      f"Duplicates: {stats['hash_duplicates']} | "
                      f"Unique: {stats['unique_results']} | "
                      f"Rate: {duplicate_rate:.1f}% | "
                      f"Status: {task.status}")
        
    except Exception as e:
        print(f"❌ Error listing tasks: {e}")
    finally:
        db.close()

def cleanup_task_duplicates(task_id: str, dry_run: bool = True):
    """指定されたタスクの重複をクリーンアップ"""
    db = SessionLocal()
    try:
        dup_service = DuplicatePreventionService(db)
        
        # タスクの存在確認
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print(f"❌ Task not found: {task_id}")
            return
        
        print(f"🔍 Analyzing task: {task_id}")
        
        # 重複統計を表示
        stats = dup_service.get_duplicate_stats(task_id)
        print(f"📊 Current stats:")
        print(f"   Total results: {stats['total_results']}")
        print(f"   Hash duplicates: {stats['hash_duplicates']}")
        print(f"   Unique results: {stats['unique_results']}")
        
        if stats['hash_duplicates'] == 0:
            print("✅ No duplicates found!")
            return
        
        # クリーンアップ実行
        cleanup_stats = dup_service.cleanup_duplicates(task_id, dry_run=dry_run)
        
        if dry_run:
            print(f"🔍 Dry run completed:")
            print(f"   Would remove: {cleanup_stats['removed']} duplicates")
            print(f"   Would keep: {cleanup_stats['kept']} unique items")
            print("   Use --execute to perform actual cleanup")
        else:
            print(f"✅ Cleanup completed:")
            print(f"   Removed: {cleanup_stats['removed']} duplicates")
            print(f"   Kept: {cleanup_stats['kept']} unique items")
            
            # タスクのアイテム数を更新
            task.items_count = cleanup_stats['kept']
            db.commit()
            print(f"📝 Updated task items_count to {cleanup_stats['kept']}")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
    finally:
        db.close()

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='Cleanup duplicate results')
    parser.add_argument('--list', action='store_true', help='List tasks with duplicates')
    parser.add_argument('--task-id', help='Cleanup specific task')
    parser.add_argument('--execute', action='store_true', help='Execute cleanup (default is dry run)')
    
    args = parser.parse_args()
    
    if args.list:
        list_tasks_with_duplicates()
    elif args.task_id:
        cleanup_task_duplicates(args.task_id, dry_run=not args.execute)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
