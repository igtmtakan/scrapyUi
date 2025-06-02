#!/usr/bin/env python3
"""
タスク 25630b76-9648-4416-a8b7-7d8ec26b4309 の完全同期処理
ファイルエクスポートとDBエクスポートの件数差を修正
"""
import json
import sys
import os
import hashlib
sys.path.append('/home/igtmtakan/workplace/python/scrapyUI/backend')

from app.database import get_db, Result as DBResult, Task as DBTask
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

def generate_data_hash_with_item_type(data: dict) -> str:
    """item_typeを考慮したハッシュ生成"""
    # item_typeを含めてハッシュを生成
    hash_data = {
        'ranking_position': data.get('ranking_position'),
        'item_type': data.get('item_type'),
        'product_url': data.get('product_url'),
        'source_url': data.get('source_url'),
        'page_number': data.get('page_number')
    }
    
    # 辞書をソートしてJSON文字列に変換
    hash_string = json.dumps(hash_data, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(hash_string.encode('utf-8')).hexdigest()

def sync_task_results():
    """タスク結果の完全同期"""
    
    # データベース接続
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # タスクID
        task_id = "25630b76-9648-4416-a8b7-7d8ec26b4309"
        
        # JSONLファイルパス
        jsonl_file = f"/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects/admin_mytest0001/results_{task_id}.jsonl"
        
        print(f"📁 JSONLファイル読み込み: {jsonl_file}")
        
        # JSONLファイル読み込み
        items = []
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        item = json.loads(line)
                        items.append(item)
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON解析エラー (行{line_num}): {e}")
        
        print(f"📊 読み込んだアイテム数: {len(items)}")
        
        # item_type別集計
        item_types = {}
        for item in items:
            item_type = item.get('item_type', 'unknown')
            item_types[item_type] = item_types.get(item_type, 0) + 1
        
        print(f"📈 item_type別集計:")
        for item_type, count in item_types.items():
            print(f"   {item_type}: {count}件")
        
        # 既存の結果を削除
        existing_results = db.query(DBResult).filter(DBResult.task_id == task_id).all()
        for result in existing_results:
            db.delete(result)
        print(f"🗑️ 既存結果削除: {len(existing_results)}件")
        
        # 新しい結果を追加（item_typeを考慮したハッシュ付き）
        added_count = 0
        for item in items:
            # item_typeを考慮したハッシュ生成
            data_hash = generate_data_hash_with_item_type(item)
            
            result = DBResult(
                id=str(uuid.uuid4()),
                task_id=task_id,
                data=item,
                data_hash=data_hash,
                item_acquired_datetime=datetime.now(),
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
        
        # item_type別DB集計
        db_item_types = {}
        db_results = db.query(DBResult).filter(DBResult.task_id == task_id).all()
        for result in db_results:
            item_type = result.data.get('item_type', 'unknown')
            db_item_types[item_type] = db_item_types.get(item_type, 0) + 1
        
        print(f"📈 DB内item_type別集計:")
        for item_type, count in db_item_types.items():
            print(f"   {item_type}: {count}件")
        
        # サンプルデータ表示
        sample_results = db.query(DBResult).filter(DBResult.task_id == task_id).limit(5).all()
        print(f"\n📋 サンプルデータ:")
        for i, result in enumerate(sample_results, 1):
            data = result.data
            print(f"{i}. ranking_position: {data.get('ranking_position', 'N/A')}")
            print(f"   item_type: {data.get('item_type', 'N/A')}")
            print(f"   rating: {data.get('rating', 'N/A')}")
            print(f"   data_hash: {result.data_hash[:8]}...")
            print(f"   ---")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    sync_task_results()
