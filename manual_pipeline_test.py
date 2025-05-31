#!/usr/bin/env python3
"""
手動でパイプライン処理をテスト
"""
import sys
import os
from pathlib import Path
import json
import sqlite3
from datetime import datetime

# ScrapyUIのバックエンドパスを追加
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# データベースパイプラインをインポート
try:
    from app.templates.database_pipeline import ScrapyUIDatabasePipeline, ScrapyUIJSONPipeline
    print("✅ データベースパイプラインのインポート成功")
except ImportError as e:
    print(f"❌ データベースパイプラインのインポート失敗: {e}")
    sys.exit(1)

# モックスパイダークラス
class MockSpider:
    def __init__(self, name="test_spider"):
        self.name = name
        self.logger = MockLogger()

class MockLogger:
    def info(self, msg):
        print(f"INFO: {msg}")
    
    def error(self, msg):
        print(f"ERROR: {msg}")
    
    def warning(self, msg):
        print(f"WARNING: {msg}")

def test_database_pipeline_directly():
    """データベースパイプラインを直接テスト"""
    
    print("🎯 データベースパイプライン直接テスト開始\n")
    
    # テスト用のタスクID
    test_task_id = "test_pipeline_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # データベースURL
    db_path = Path("backend/database/scrapy_ui.db")
    database_url = f"sqlite:///{db_path.absolute()}"
    
    print(f"📋 テスト設定:")
    print(f"  タスクID: {test_task_id}")
    print(f"  データベースURL: {database_url}")
    print(f"  データベースファイル: {db_path}")
    print(f"  データベース存在: {db_path.exists()}")
    
    # パイプラインを初期化
    try:
        pipeline = ScrapyUIDatabasePipeline(
            database_url=database_url,
            task_id=test_task_id
        )
        print("✅ パイプライン初期化成功")
    except Exception as e:
        print(f"❌ パイプライン初期化失敗: {e}")
        return False
    
    # モックスパイダーを作成
    spider = MockSpider("test_pipeline_spider")
    
    # パイプラインを開始
    try:
        pipeline.open_spider(spider)
        print("✅ パイプライン開始成功")
    except Exception as e:
        print(f"❌ パイプライン開始失敗: {e}")
        return False
    
    # テストアイテムを処理
    test_items = [
        {
            'id': 1,
            'title': 'Test Item 1',
            'description': 'This is a test item for pipeline testing',
            'url': 'https://example.com/1',
            'test_type': 'manual_pipeline_test',
            'crawl_start_datetime': datetime.now().isoformat(),
            'item_acquired_datetime': datetime.now().isoformat()
        },
        {
            'id': 2,
            'title': 'Test Item 2',
            'description': 'This is another test item for pipeline testing',
            'url': 'https://example.com/2',
            'test_type': 'manual_pipeline_test',
            'crawl_start_datetime': datetime.now().isoformat(),
            'item_acquired_datetime': datetime.now().isoformat()
        },
        {
            'id': 3,
            'title': 'Special Test Item',
            'description': 'This is a special test item with complex data',
            'url': 'https://example.com/special',
            'test_type': 'manual_pipeline_test_special',
            'complex_data': {
                'nested': True,
                'array': [1, 2, 3],
                'metadata': {'source': 'manual_test'}
            },
            'crawl_start_datetime': datetime.now().isoformat(),
            'item_acquired_datetime': datetime.now().isoformat()
        }
    ]
    
    processed_count = 0
    
    print(f"\n🔄 アイテム処理開始:")
    
    for i, item in enumerate(test_items, 1):
        try:
            processed_item = pipeline.process_item(item, spider)
            print(f"  {i}. ✅ アイテム処理成功: {item['title']}")
            processed_count += 1
        except Exception as e:
            print(f"  {i}. ❌ アイテム処理失敗: {item['title']} - {e}")
    
    # パイプラインを終了
    try:
        pipeline.close_spider(spider)
        print(f"\n✅ パイプライン終了成功")
        print(f"📊 処理されたアイテム数: {processed_count}件")
    except Exception as e:
        print(f"❌ パイプライン終了失敗: {e}")
        return False
    
    # データベースから結果を確認
    return verify_pipeline_results(test_task_id, processed_count)

def verify_pipeline_results(task_id: str, expected_count: int):
    """パイプライン結果を検証"""
    
    print(f"\n🔍 パイプライン結果検証:")
    
    db_path = Path("backend/database/scrapy_ui.db")
    
    if not db_path.exists():
        print(f"❌ データベースファイルが見つかりません: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 該当タスクの結果を確認
        cursor.execute("""
            SELECT COUNT(*) 
            FROM results 
            WHERE task_id = ?
        """, (task_id,))
        
        actual_count = cursor.fetchone()[0]
        print(f"  📊 期待件数: {expected_count}件")
        print(f"  📊 実際件数: {actual_count}件")
        
        if actual_count == expected_count:
            print(f"  ✅ 件数一致")
        else:
            print(f"  ❌ 件数不一致")
            return False
        
        if actual_count > 0:
            # 詳細な結果を確認
            cursor.execute("""
                SELECT id, data, crawl_start_datetime, item_acquired_datetime, created_at
                FROM results 
                WHERE task_id = ?
                ORDER BY created_at
            """, (task_id,))
            
            results = cursor.fetchall()
            
            print(f"\n📋 保存された結果:")
            
            success_count = 0
            
            for i, (result_id, data_json, crawl_start, item_acquired, created_at) in enumerate(results, 1):
                try:
                    data = json.loads(data_json) if isinstance(data_json, str) else data_json
                    
                    print(f"  {i}. 結果ID: {result_id}")
                    print(f"     タイトル: {data.get('title', '不明')}")
                    print(f"     テストタイプ: {data.get('test_type', '不明')}")
                    print(f"     クロールスタート: {crawl_start}")
                    print(f"     アイテム取得: {item_acquired}")
                    print(f"     作成日時: {created_at}")
                    
                    # データ整合性チェック
                    if (data.get('title') and 
                        data.get('test_type') and 
                        crawl_start and 
                        item_acquired):
                        print(f"     ✅ データ整合性: 正常")
                        success_count += 1
                    else:
                        print(f"     ❌ データ整合性: 問題あり")
                    
                    print(f"     ---")
                    
                except Exception as e:
                    print(f"     ❌ データ解析エラー: {e}")
            
            print(f"\n📊 検証結果:")
            print(f"  総件数: {actual_count}件")
            print(f"  成功件数: {success_count}件")
            print(f"  成功率: {success_count/actual_count*100:.1f}%")
            
            return success_count == actual_count
        else:
            print("⚠️ 保存された結果がありません")
            return False
        
    except Exception as e:
        print(f"❌ データベース検証エラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """メイン実行関数"""
    print("🎯 手動パイプライン処理テスト\n")
    
    # データベースパイプラインを直接テスト
    success = test_database_pipeline_directly()
    
    print("\n🎉 テスト完了！")
    
    if success:
        print("\n✅ パイプライン処理テスト成功")
        print("\n🔧 確認事項:")
        print("  ✅ データベースパイプラインが正常に動作")
        print("  ✅ アイテムがデータベースに正しく保存")
        print("  ✅ 日時フィールドが正しく設定")
        print("  ✅ データ整合性が保たれている")
    else:
        print("\n❌ パイプライン処理テスト失敗")
        print("\n🔧 確認が必要な項目:")
        print("  - データベース接続設定")
        print("  - パイプライン設定")
        print("  - データベーススキーマ")
        print("  - 権限設定")

if __name__ == "__main__":
    main()
