#!/usr/bin/env python3
"""
データベースマイグレーション: Projectテーブルにdb_save_enabledフィールドを追加
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

def add_db_save_enabled_field():
    """Projectテーブルにdb_save_enabledフィールドを追加"""
    
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
        cursor.execute("PRAGMA table_info(projects)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print("🔍 現在のProjectテーブル構造:")
        for column in columns:
            print(f"  - {column}")
        
        # db_save_enabledカラムを追加
        if 'db_save_enabled' not in columns:
            print("\n🔧 db_save_enabledカラムを追加中...")
            cursor.execute("""
                ALTER TABLE projects 
                ADD COLUMN db_save_enabled BOOLEAN DEFAULT 1 NOT NULL
            """)
            print("✅ db_save_enabledカラムが追加されました")
        else:
            print("✅ db_save_enabledカラムは既に存在します")
        
        # 変更をコミット
        conn.commit()
        
        # 追加されたことを確認
        cursor.execute("PRAGMA table_info(projects)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        
        print("\n📋 更新後のProjectテーブル構造:")
        cursor.execute("PRAGMA table_info(projects)")
        for column in cursor.fetchall():
            print(f"  - {column[1]} ({column[2]}) {'NOT NULL' if column[3] else 'NULL'} DEFAULT: {column[4]}")
        
        # 新しいフィールドが追加されたことを確認
        if 'db_save_enabled' in updated_columns:
            print("\n✅ db_save_enabledフィールドが正常に追加されました")
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

def update_existing_projects():
    """既存のプロジェクトのdb_save_enabledフィールドを設定"""
    
    db_path = Path("backend/database/scrapy_ui.db")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("\n🔄 既存プロジェクトのdb_save_enabledフィールドを更新中...")
        
        # 既存のプロジェクト数を確認
        cursor.execute("SELECT COUNT(*) FROM projects")
        total_projects = cursor.fetchone()[0]
        print(f"📊 既存プロジェクト数: {total_projects}件")
        
        if total_projects > 0:
            # 既存のプロジェクトを全てdb_save_enabled=1（有効）に設定
            cursor.execute("""
                UPDATE projects 
                SET db_save_enabled = 1 
                WHERE db_save_enabled IS NULL
            """)
            
            updated_count = cursor.rowcount
            conn.commit()
            print(f"✅ {updated_count}件のプロジェクトを更新しました")
        else:
            print("📝 更新対象のプロジェクトがありません")
        
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
        cursor.execute("PRAGMA table_info(projects)")
        columns = cursor.fetchall()
        
        print("Projectテーブルの全カラム:")
        
        db_save_enabled_found = False
        
        for column in columns:
            column_name = column[1]
            column_type = column[2]
            is_nullable = "NULL" if column[3] == 0 else "NOT NULL"
            default_value = column[4]
            
            if column_name == 'db_save_enabled':
                db_save_enabled_found = True
                print(f"  ✅ {column_name} ({column_type}) {is_nullable} DEFAULT: {default_value}")
            else:
                print(f"  - {column_name} ({column_type}) {is_nullable}")
        
        if db_save_enabled_found:
            print("\n✅ マイグレーション成功: db_save_enabledフィールドが正常に追加されました")
            
            # サンプルデータを確認
            cursor.execute("""
                SELECT id, name, db_save_enabled 
                FROM projects 
                LIMIT 5
            """)
            
            sample_data = cursor.fetchall()
            if sample_data:
                print("\n📊 サンプルデータ:")
                for project_id, name, db_save_enabled in sample_data:
                    status = "有効" if db_save_enabled else "無効"
                    print(f"  - {name}: DB保存={status}")
            
            return True
        else:
            print("\n❌ マイグレーション失敗: db_save_enabledフィールドが見つかりません")
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
    print("目的: Projectテーブルにdb_save_enabledフィールドを追加")
    
    # 1. フィールド追加
    success = add_db_save_enabled_field()
    
    if success:
        # 2. 既存データ更新
        update_existing_projects()
        
        # 3. 検証実行
        verify_migration()
        
        print("\n🎉 マイグレーション完了！")
        print("これで、プロジェクト作成時にDB保存設定を選択できるようになりました。")
        print("\n📋 新しいフィールド:")
        print("  - db_save_enabled: 結果をDBに保存するかどうか（デフォルト: 有効）")
    else:
        print("\n❌ マイグレーション失敗")
        return False
    
    return True

if __name__ == "__main__":
    main()
