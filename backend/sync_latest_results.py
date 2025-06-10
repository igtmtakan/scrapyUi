#!/usr/bin/env python3
"""
最新の実行結果のみをデータベースに同期するスクリプト
"""
import json
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
sys.path.append('/home/igtmtakan/workplace/python/scrapyUI/backend')

from app.database import SessionLocal, Task, Result, TaskStatus

def generate_data_hash(item_data):
    """データハッシュを生成"""
    data_str = str(sorted(item_data.items()))
    return hashlib.sha256(data_str.encode()).hexdigest()

def sync_latest_results():
    """最新の実行結果をデータベースに同期"""
    
    jsonl_path = Path("../scrapy_projects/admin_aiueo3/ranking_results.jsonl")
    if not jsonl_path.exists():
        print(f"❌ File not found: {jsonl_path}")
        return False
    
    print(f"🔄 Syncing latest results to database")
    
    # データベースセッション
    db = SessionLocal()
    
    try:
        # 最新のタスクを取得（または新規作成）
        from sqlalchemy import desc
        latest_task = db.query(Task).order_by(desc(Task.created_at)).first()
        if not latest_task:
            print("❌ No tasks found")
            return False

        print(f"📋 Using latest task: {latest_task.id}")

        # JSONLファイルの最後の100行を読み込み（最新の実行結果）
        items_data = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 最後の100行を処理
        recent_lines = lines[-100:] if len(lines) > 100 else lines

        for line_num, line in enumerate(recent_lines, 1):
            try:
                item_data = json.loads(line.strip())
                # 最新の実行時刻でフィルタ（2025-06-11T05:40:xx）
                scraped_at = item_data.get('scraped_at', '')
                if '2025-06-11T05:40:' in scraped_at:
                    items_data.append(item_data)
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON decode error at line {line_num}: {e}")
                continue
        
        if not items_data:
            print("❌ No recent data found")
            return False
        
        print(f"📊 Found {len(items_data)} recent items to sync")
        
        # バルクインサート
        bulk_data = []
        skipped_count = 0
        
        for item_data in items_data:
            # データハッシュを生成
            data_hash = generate_data_hash(item_data)
            
            # 重複チェック
            existing = db.query(Result).filter(
                Result.task_id == latest_task.id,
                Result.data_hash == data_hash
            ).first()

            if existing:
                skipped_count += 1
                continue

            # 結果データを作成
            result_data = Result(
                id=str(uuid.uuid4()),
                task_id=latest_task.id,
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
            latest_task.items_count = len(bulk_data)
            latest_task.updated_at = datetime.now()
            
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
    success = sync_latest_results()
    
    if success:
        print("🎉 Sync completed successfully!")
        sys.exit(0)
    else:
        print("💥 Sync failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
