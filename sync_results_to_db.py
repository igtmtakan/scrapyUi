#!/usr/bin/env python3
import json
import sys
import os
sys.path.append('/home/igtmtakan/workplace/python/scrapyUI/backend')

from app.database import get_db, Result as DBResult, Task as DBTask
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

def sync_results_to_db():
    """JSONファイルからDBに結果を同期"""
    
    # データベース接続
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # タスクID
        task_id = "4072a826-8404-4682-ae0b-933dbde2194d"
        
        # JSONファイルパス
        json_file = f"/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects/admin_admin_omocha20/results_{task_id}.json"
        
        print(f"📁 JSONファイル読み込み: {json_file}")
        
        # JSONファイル読み込み
        with open(json_file, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        print(f"📊 読み込んだアイテム数: {len(items)}")
        
        # 既存の結果を削除
        existing_results = db.query(DBResult).filter(DBResult.task_id == task_id).all()
        for result in existing_results:
            db.delete(result)
        print(f"🗑️ 既存結果削除: {len(existing_results)}件")
        
        # 新しい結果を追加
        added_count = 0
        for item in items:
            result = DBResult(
                id=str(uuid.uuid4()),
                task_id=task_id,
                data=item,
                created_at=datetime.now()
            )
            db.add(result)
            added_count += 1
        
        # タスクの統計を更新
        task = db.query(DBTask).filter(DBTask.id == task_id).first()
        if task:
            task.items_count = len(items)
            task.status = "FINISHED"
            task.finished_at = datetime.now()
            print(f"📊 タスク統計更新: {len(items)}件")
        
        # コミット
        db.commit()
        print(f"✅ DB同期完了: {added_count}件の結果を追加")
        
        # 結果確認
        total_results = db.query(DBResult).filter(DBResult.task_id == task_id).count()
        print(f"🔍 DB内結果数: {total_results}件")
        
        # サンプルデータ表示
        sample_results = db.query(DBResult).filter(DBResult.task_id == task_id).limit(3).all()
        print(f"\n📋 サンプルデータ:")
        for i, result in enumerate(sample_results, 1):
            data = result.data
            print(f"{i}. {data.get('title', 'タイトルなし')}")
            print(f"   価格: {data.get('price', '価格なし')}")
            print(f"   評価: {data.get('rating', '評価なし')}")
            print(f"   ---")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    sync_results_to_db()
