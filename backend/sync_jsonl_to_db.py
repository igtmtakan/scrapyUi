#!/usr/bin/env python3
"""
JSONLファイルからデータベースに手動同期するスクリプト
"""
import json
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append('/home/igtmtakan/workplace/python/scrapyUI/backend')

from app.database import SessionLocal, Task, Result, TaskStatus

def generate_data_hash(item_data):
    """データハッシュを生成"""
    data_str = str(sorted(item_data.items()))
    return hashlib.sha256(data_str.encode()).hexdigest()

def sync_jsonl_to_db(jsonl_file_path, task_id=None, spider_name=None):
    """JSONLファイルをデータベースに同期"""
    
    jsonl_path = Path(jsonl_file_path)
    if not jsonl_path.exists():
        print(f"❌ File not found: {jsonl_file_path}")
        return False
    
    print(f"🔄 Syncing JSONL file to database: {jsonl_file_path}")
    
    # データベースセッション
    db = SessionLocal()
    
    try:
        # タスクIDが指定されていない場合は新規作成
        if not task_id:
            task_id = str(uuid.uuid4())
            print(f"📝 Creating new task: {task_id}")
            
            # 新しいタスクを作成
            new_task = Task(
                id=task_id,
                status=TaskStatus.FINISHED,
                started_at=datetime.now(),
                finished_at=datetime.now(),
                items_count=0,
                requests_count=1,
                error_count=0
            )
            db.add(new_task)
            db.commit()
        else:
            # 既存タスクを確認
            existing_task = db.query(Task).filter(Task.id == task_id).first()
            if not existing_task:
                print(f"❌ Task not found: {task_id}")
                return False
            print(f"📋 Using existing task: {task_id}")
        
        # JSONLファイルを読み込み
        items_data = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    item_data = json.loads(line.strip())
                    items_data.append(item_data)
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON decode error at line {line_num}: {e}")
                    continue
        
        if not items_data:
            print("❌ No valid JSON data found")
            return False
        
        print(f"📊 Found {len(items_data)} items to sync")
        
        # バルクインサート
        bulk_data = []
        skipped_count = 0
        
        for item_data in items_data:
            # データハッシュを生成
            data_hash = generate_data_hash(item_data)
            
            # 重複チェック
            existing = db.query(Result).filter(
                Result.task_id == task_id,
                Result.data_hash == data_hash
            ).first()
            
            if existing:
                skipped_count += 1
                continue
            
            # 結果データを作成
            result_data = Result(
                id=str(uuid.uuid4()),
                task_id=task_id,
                data=item_data,
                data_hash=data_hash,
                item_acquired_datetime=datetime.now(),
                created_at=datetime.now()
            )
            bulk_data.append(result_data)
        
        # バルクインサート実行
        if bulk_data:
            db.bulk_save_objects(bulk_data)
            
            # タスクのアイテム数を更新
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.items_count = len(bulk_data)
                task.updated_at = datetime.now()
            
            db.commit()
            print(f"✅ Successfully synced {len(bulk_data)} items to database")
            if skipped_count > 0:
                print(f"⚠️ Skipped {skipped_count} duplicate items")
        else:
            print("⚠️ No new items to sync (all duplicates)")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during sync: {e}")
        return False
    finally:
        db.close()

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync JSONL file to database')
    parser.add_argument('jsonl_file', help='Path to JSONL file')
    parser.add_argument('--task-id', help='Task ID (optional, will create new if not provided)')
    parser.add_argument('--spider-name', help='Spider name (optional)')
    
    args = parser.parse_args()
    
    success = sync_jsonl_to_db(
        jsonl_file_path=args.jsonl_file,
        task_id=args.task_id,
        spider_name=args.spider_name
    )
    
    if success:
        print("🎉 Sync completed successfully!")
        sys.exit(0)
    else:
        print("💥 Sync failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
