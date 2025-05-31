#!/usr/bin/env python3
"""
重複データクリーンアップスクリプト
"""

import sys
import os
import json
import hashlib
from datetime import datetime

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, Result, Task

def calculate_data_hash(data):
    """データのハッシュ値を計算"""
    # データから一意性を判断するフィールドを抽出
    unique_fields = {
        'title': data.get('title', ''),
        'price': data.get('price', ''),
        'product_url': data.get('product_url', ''),
        'rating': data.get('rating', ''),
        'reviews': data.get('reviews', '')
    }
    
    # JSON文字列にしてハッシュ化
    json_str = json.dumps(unique_fields, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(json_str.encode('utf-8')).hexdigest()

def cleanup_duplicates():
    """重複データをクリーンアップ"""
    db = SessionLocal()
    
    try:
        print("🔍 重複データクリーンアップを開始...")
        
        # 全ての結果を取得
        all_results = db.query(Result).order_by(Result.created_at.asc()).all()
        print(f"📊 総結果数: {len(all_results)}件")
        
        # ハッシュ値でグループ化
        hash_groups = {}
        for result in all_results:
            data_hash = calculate_data_hash(result.data)
            if data_hash not in hash_groups:
                hash_groups[data_hash] = []
            hash_groups[data_hash].append(result)
        
        # 重複を検出
        duplicates_found = 0
        duplicates_removed = 0
        
        for data_hash, results in hash_groups.items():
            if len(results) > 1:
                duplicates_found += len(results) - 1
                print(f"🔍 重複検出: {len(results)}件の同一データ")
                
                # 最初の結果を保持、残りを削除
                keep_result = results[0]
                remove_results = results[1:]
                
                for remove_result in remove_results:
                    print(f"   ❌ 削除: {remove_result.id[:8]}... - {remove_result.data.get('title', 'N/A')[:30]}...")
                    db.delete(remove_result)
                    duplicates_removed += 1
                
                print(f"   ✅ 保持: {keep_result.id[:8]}... - {keep_result.data.get('title', 'N/A')[:30]}...")
        
        # 変更をコミット
        db.commit()
        
        # 統計を更新
        remaining_results = db.query(Result).count()
        
        print(f"\n📊 クリーンアップ結果:")
        print(f"   重複検出数: {duplicates_found}件")
        print(f"   削除数: {duplicates_removed}件")
        print(f"   残存数: {remaining_results}件")
        
        # タスクの統計を更新
        print(f"\n🔄 タスク統計を更新中...")
        tasks = db.query(Task).all()
        for task in tasks:
            result_count = db.query(Result).filter(Result.task_id == task.id).count()
            task.items_count = result_count
            print(f"   📊 {task.id[:8]}... - アイテム数: {result_count}")
        
        db.commit()
        print(f"✅ タスク統計更新完了")
        
        print(f"\n🎉 重複データクリーンアップが完了しました！")
        
    except Exception as e:
        db.rollback()
        print(f"❌ エラー: {e}")
        import traceback
        print(f"❌ エラー詳細: {traceback.format_exc()}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_duplicates()
