#!/usr/bin/env python3
import json
import sys
import os
import re
sys.path.append('/home/igtmtakan/workplace/python/scrapyUI/backend')

from app.database import get_db, Result as DBResult, Task as DBTask
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

def fix_json_file(file_path):
    """不正なJSONファイルを修正"""
    print(f"📁 JSONファイル修正: {file_path}")
    
    # ファイル読み込み
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # JSONオブジェクトを分割
    json_objects = []
    
    # 正規表現で個別のJSONオブジェクトを抽出
    pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(pattern, content)
    
    for match in matches:
        try:
            obj = json.loads(match)
            json_objects.append(obj)
        except json.JSONDecodeError:
            continue
    
    print(f"📊 抽出されたオブジェクト数: {len(json_objects)}")
    
    # 修正されたJSONファイルを保存
    fixed_file = file_path.replace('.json', '_fixed.json')
    with open(fixed_file, 'w', encoding='utf-8') as f:
        json.dump(json_objects, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 修正ファイル保存: {fixed_file}")
    return fixed_file, json_objects

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
        
        # JSONファイル修正
        fixed_file, items = fix_json_file(json_file)
        
        print(f"📊 読み込んだアイテム数: {len(items)}")
        
        # 既存の結果を削除
        existing_results = db.query(DBResult).filter(DBResult.task_id == task_id).all()
        for result in existing_results:
            db.delete(result)
        print(f"🗑️ 既存結果削除: {len(existing_results)}件")
        
        # 新しい結果を追加
        added_count = 0
        for item in items:
            # 必要なフィールドがあることを確認
            if 'url' in item and 'title' in item:
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
            task.items_count = added_count
            task.status = "FINISHED"
            task.finished_at = datetime.now()
            print(f"📊 タスク統計更新: {added_count}件")
        
        # コミット
        db.commit()
        print(f"✅ DB同期完了: {added_count}件の結果を追加")
        
        # 結果確認
        total_results = db.query(DBResult).filter(DBResult.task_id == task_id).count()
        print(f"🔍 DB内結果数: {total_results}件")
        
        # サンプルデータ表示
        sample_results = db.query(DBResult).filter(DBResult.task_id == task_id).limit(5).all()
        print(f"\n📋 サンプルデータ:")
        for i, result in enumerate(sample_results, 1):
            data = result.data
            print(f"{i}. {data.get('title', 'タイトルなし')}")
            print(f"   価格: {data.get('price', '価格なし')}")
            print(f"   評価: {data.get('rating', '評価なし')}")
            print(f"   レビュー: {data.get('reviews', 'レビューなし')}")
            print(f"   URL: {data.get('url', 'URLなし')[:80]}...")
            print(f"   ---")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = sync_results_to_db()
    if success:
        print(f"\n🎉 omocha20スパイダーの結果がDBに正常に反映されました！")
        print(f"🌐 WebUI: http://localhost:4000/projects/e38e4e04-1fd6-4c18-94d1-333e579e41d9/tasks")
    else:
        print(f"\n❌ DB同期に失敗しました")
