#!/usr/bin/env python3
"""
データベースマイグレーション: Resultテーブルにクロールスタート日時と取得日時フィールドを追加
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

def add_datetime_fields():
    """Resultテーブルにクロールスタート日時と取得日時フィールドを追加"""
    
    # データベースファイルのパス
    db_path = Path("backend/database/scrapy_ui.db")
    
    if not db_path.exists():
        print(f"❌ データベースファイルが見つかりません: {db_path}")
        return False
    
    try:
        # データベースに接続
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 既存のカラムを確認
        cursor.execute("PRAGMA table_info(results)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print("🔍 現在のResultテーブル構造:")
        for column in columns:
            print(f"  - {column}")
        
        # crawl_start_datetimeカラムを追加
        if 'crawl_start_datetime' not in columns:
            print("\n🔧 crawl_start_datetimeカラムを追加中...")
            cursor.execute("""
                ALTER TABLE results 
                ADD COLUMN crawl_start_datetime DATETIME
            """)
            print("✅ crawl_start_datetimeカラムが追加されました")
        else:
            print("✅ crawl_start_datetimeカラムは既に存在します")
        
        # item_acquired_datetimeカラムを追加
        if 'item_acquired_datetime' not in columns:
            print("\n🔧 item_acquired_datetimeカラムを追加中...")
            cursor.execute("""
                ALTER TABLE results 
                ADD COLUMN item_acquired_datetime DATETIME
            """)
            print("✅ item_acquired_datetimeカラムが追加されました")
        else:
            print("✅ item_acquired_datetimeカラムは既に存在します")
        
        # 変更をコミット
        conn.commit()
        
        # 追加されたことを確認
        cursor.execute("PRAGMA table_info(results)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        
        print("\n📋 更新後のResultテーブル構造:")
        for column in cursor.fetchall():
            print(f"  - {column[1]} ({column[2]})")
        
        # 新しいフィールドが追加されたことを確認
        if 'crawl_start_datetime' in updated_columns and 'item_acquired_datetime' in updated_columns:
            print("\n✅ 両方のフィールドが正常に追加されました")
            return True
        else:
            print("\n❌ フィールドの追加に失敗しました")
            return False
            
    except Exception as e:
        print(f"❌ マイグレーションエラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def update_existing_data():
    """既存のデータに日時フィールドを設定"""
    
    db_path = Path("backend/database/scrapy_ui.db")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("\n🔄 既存データの日時フィールドを更新中...")
        
        # 既存のresultsレコード数を確認
        cursor.execute("SELECT COUNT(*) FROM results")
        total_results = cursor.fetchone()[0]
        print(f"📊 既存結果レコード数: {total_results}件")
        
        if total_results > 0:
            # 既存のresultsレコードを取得（task_idでグループ化）
            cursor.execute("""
                SELECT DISTINCT r.task_id, t.started_at, t.finished_at
                FROM results r
                LEFT JOIN tasks t ON r.task_id = t.id
                WHERE r.crawl_start_datetime IS NULL OR r.item_acquired_datetime IS NULL
            """)
            
            task_info = cursor.fetchall()
            
            updated_count = 0
            for task_id, started_at, finished_at in task_info:
                if task_id:
                    # クロールスタート日時はタスクの開始時刻を使用
                    crawl_start = started_at if started_at else datetime.now().isoformat()
                    
                    # アイテム取得日時はタスクの完了時刻を使用（なければ現在時刻）
                    item_acquired = finished_at if finished_at else datetime.now().isoformat()
                    
                    # 該当するresultsレコードを更新
                    cursor.execute("""
                        UPDATE results 
                        SET crawl_start_datetime = ?, 
                            item_acquired_datetime = ?
                        WHERE task_id = ? 
                        AND (crawl_start_datetime IS NULL OR item_acquired_datetime IS NULL)
                    """, (crawl_start, item_acquired, task_id))
                    
                    updated_count += cursor.rowcount
            
            conn.commit()
            print(f"✅ {updated_count}件のレコードを更新しました")
        else:
            print("📝 更新対象のレコードがありません")
        
        return True
        
    except Exception as e:
        print(f"❌ データ更新エラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def verify_migration():
    """マイグレーションの検証"""
    
    db_path = Path("backend/database/scrapy_ui.db")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("\n🔍 マイグレーション検証:")
        
        # テーブル構造を確認
        cursor.execute("PRAGMA table_info(results)")
        columns = cursor.fetchall()
        
        print("Resultテーブルの全カラム:")
        
        crawl_start_found = False
        item_acquired_found = False
        
        for column in columns:
            column_name = column[1]
            column_type = column[2]
            is_nullable = "NULL" if column[3] == 0 else "NOT NULL"
            
            if column_name == 'crawl_start_datetime':
                crawl_start_found = True
                print(f"  ✅ {column_name} ({column_type}) {is_nullable}")
            elif column_name == 'item_acquired_datetime':
                item_acquired_found = True
                print(f"  ✅ {column_name} ({column_type}) {is_nullable}")
            else:
                print(f"  - {column_name} ({column_type}) {is_nullable}")
        
        if crawl_start_found and item_acquired_found:
            print("\n✅ マイグレーション成功: 両方のフィールドが正常に追加されました")
            
            # サンプルデータを確認
            cursor.execute("""
                SELECT id, crawl_start_datetime, item_acquired_datetime 
                FROM results 
                WHERE crawl_start_datetime IS NOT NULL 
                LIMIT 3
            """)
            
            sample_data = cursor.fetchall()
            if sample_data:
                print("\n📊 サンプルデータ:")
                for result_id, crawl_start, item_acquired in sample_data:
                    print(f"  - {result_id}: クロール開始={crawl_start}, アイテム取得={item_acquired}")
            
            return True
        else:
            print("\n❌ マイグレーション失敗: 必要なフィールドが見つかりません")
            return False
            
    except Exception as e:
        print(f"❌ 検証エラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """メイン実行関数"""
    print("🚀 データベースマイグレーション開始")
    print("目的: Resultテーブルにクロールスタート日時と取得日時フィールドを追加")
    
    # 1. フィールド追加
    success = add_datetime_fields()
    
    if success:
        # 2. 既存データ更新
        update_existing_data()
        
        # 3. 検証実行
        verify_migration()
        
        print("\n🎉 マイグレーション完了！")
        print("これで、各結果アイテムにクロールスタート日時と取得日時が記録されるようになりました。")
        print("\n📋 新しいフィールド:")
        print("  - crawl_start_datetime: クロール開始日時")
        print("  - item_acquired_datetime: アイテム取得日時")
    else:
        print("\n❌ マイグレーション失敗")
        return False
    
    return True

if __name__ == "__main__":
    main()
