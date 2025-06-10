#!/usr/bin/env python3
"""
データベースマイグレーション: TaskテーブルにError_messageカラムを追加
"""

import sqlite3
import os
from pathlib import Path

def add_error_message_column():
    """TaskテーブルにError_messageカラムを追加"""

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
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'error_message' in columns:
            print("✅ error_messageカラムは既に存在します")
            return True

        print("🔧 TaskテーブルにError_messageカラムを追加中...")

        # error_messageカラムを追加
        cursor.execute("""
            ALTER TABLE tasks
            ADD COLUMN error_message TEXT
        """)

        # 変更をコミット
        conn.commit()

        # 追加されたことを確認
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'error_message' in columns:
            print("✅ error_messageカラムが正常に追加されました")

            # テーブル構造を表示
            print("\n📋 更新後のTaskテーブル構造:")
            cursor.execute("PRAGMA table_info(tasks)")
            for column in cursor.fetchall():
                print(f"  - {column[1]} ({column[2]})")

            return True
        else:
            print("❌ error_messageカラムの追加に失敗しました")
            return False

    except Exception as e:
        print(f"❌ マイグレーションエラー: {e}")
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
        
        # テーブル構造を確認
        cursor.execute("PRAGMA table_info(tasks)")
        columns = cursor.fetchall()
        
        print("\n🔍 現在のTaskテーブル構造:")
        for column in columns:
            print(f"  - {column[1]} ({column[2]}) {'NOT NULL' if column[3] else 'NULL'}")
        
        # error_messageカラムの存在確認
        column_names = [column[1] for column in columns]
        if 'error_message' in column_names:
            print("\n✅ error_messageカラムが正常に存在します")
            return True
        else:
            print("\n❌ error_messageカラムが見つかりません")
            return False
            
    except Exception as e:
        print(f"❌ 検証エラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 TaskテーブルにError_messageカラムを追加するマイグレーションを開始...")
    
    # マイグレーション実行
    if add_error_message_column():
        print("\n🔍 マイグレーション結果を検証中...")
        if verify_migration():
            print("\n🎉 マイグレーションが正常に完了しました！")
        else:
            print("\n❌ マイグレーションの検証に失敗しました")
    else:
        print("\n❌ マイグレーションに失敗しました")
