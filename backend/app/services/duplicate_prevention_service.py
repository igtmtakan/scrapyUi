"""
重複防止サービス
複数のデータ保存経路での重複を防止する
"""
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import Result, Task

class DuplicatePreventionService:
    """重複防止サービス"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_content_hash(self, item_data: Dict[str, Any]) -> str:
        """コンテンツベースのハッシュを生成"""
        try:
            # 重要なフィールドのみを使用
            key_fields = ['title', 'product_url', 'ranking_position', 'price', 'rating']
            hash_data = {}
            
            for field in key_fields:
                if field in item_data and item_data[field] is not None:
                    hash_data[field] = str(item_data[field]).strip()
            
            # URLからASINを抽出
            product_url = item_data.get('product_url', '')
            if '/dp/' in product_url:
                asin = product_url.split('/dp/')[1].split('/')[0]
                hash_data['asin'] = asin
            
            # ソートされた辞書から文字列を生成
            data_str = json.dumps(hash_data, sort_keys=True, ensure_ascii=False)
            return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
            
        except Exception as e:
            print(f"❌ Error generating content hash: {e}")
            # フォールバック：全データのハッシュ
            data_str = json.dumps(item_data, sort_keys=True, ensure_ascii=False)
            return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    
    def check_duplicate_by_hash(self, task_id: str, data_hash: str) -> bool:
        """ハッシュベースの重複チェック"""
        try:
            existing = self.db.query(Result).filter(
                Result.task_id == task_id,
                Result.data_hash == data_hash
            ).first()
            return existing is not None
        except Exception as e:
            print(f"❌ Error checking duplicate by hash: {e}")
            return False
    
    def check_duplicate_by_content(self, task_id: str, item_data: Dict[str, Any]) -> bool:
        """コンテンツベースの重複チェック"""
        try:
            # ASINベースのチェック
            product_url = item_data.get('product_url', '')
            if '/dp/' in product_url:
                asin = product_url.split('/dp/')[1].split('/')[0]
                existing = self.db.query(Result).filter(
                    Result.task_id == task_id,
                    Result.data['product_url'].astext.like(f'%/dp/{asin}/%')
                ).first()
                if existing:
                    return True
            
            # タイトル + ランキング位置ベースのチェック
            title = item_data.get('title', '').strip()
            ranking_position = item_data.get('ranking_position')
            
            if title and ranking_position:
                existing = self.db.query(Result).filter(
                    Result.task_id == task_id,
                    Result.data['title'].astext == title,
                    Result.data['ranking_position'].astext == str(ranking_position)
                ).first()
                if existing:
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error checking duplicate by content: {e}")
            return False
    
    def is_duplicate(self, task_id: str, item_data: Dict[str, Any], data_hash: str = None) -> bool:
        """総合的な重複チェック"""
        try:
            # ハッシュベースのチェック
            if data_hash and self.check_duplicate_by_hash(task_id, data_hash):
                return True
            
            # コンテンツベースのチェック
            if self.check_duplicate_by_content(task_id, item_data):
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error in duplicate check: {e}")
            return False
    
    def get_duplicate_stats(self, task_id: str) -> Dict[str, int]:
        """重複統計を取得"""
        try:
            total_results = self.db.query(Result).filter(Result.task_id == task_id).count()
            
            # ハッシュベースの重複チェック
            hash_duplicates = self.db.query(Result.data_hash).filter(
                Result.task_id == task_id,
                Result.data_hash.isnot(None)
            ).group_by(Result.data_hash).having(func.count(Result.data_hash) > 1).count()
            
            return {
                'total_results': total_results,
                'hash_duplicates': hash_duplicates,
                'unique_results': total_results - hash_duplicates
            }
            
        except Exception as e:
            print(f"❌ Error getting duplicate stats: {e}")
            return {'total_results': 0, 'hash_duplicates': 0, 'unique_results': 0}
    
    def cleanup_duplicates(self, task_id: str, dry_run: bool = True) -> Dict[str, int]:
        """重複データのクリーンアップ"""
        try:
            stats = {'removed': 0, 'kept': 0}
            
            # ハッシュベースの重複を検索
            duplicate_hashes = self.db.query(Result.data_hash).filter(
                Result.task_id == task_id,
                Result.data_hash.isnot(None)
            ).group_by(Result.data_hash).having(func.count(Result.data_hash) > 1).all()
            
            for (data_hash,) in duplicate_hashes:
                # 同じハッシュの結果を取得（最新を除く）
                duplicates = self.db.query(Result).filter(
                    Result.task_id == task_id,
                    Result.data_hash == data_hash
                ).order_by(Result.created_at.desc()).offset(1).all()
                
                for duplicate in duplicates:
                    if not dry_run:
                        self.db.delete(duplicate)
                    stats['removed'] += 1
                
                stats['kept'] += 1
            
            if not dry_run:
                self.db.commit()
                print(f"✅ Cleanup completed: {stats['removed']} duplicates removed, {stats['kept']} unique items kept")
            else:
                print(f"🔍 Dry run: Would remove {stats['removed']} duplicates, keep {stats['kept']} unique items")
            
            return stats
            
        except Exception as e:
            if not dry_run:
                self.db.rollback()
            print(f"❌ Error during cleanup: {e}")
            return {'removed': 0, 'kept': 0}
