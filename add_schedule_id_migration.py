#!/usr/bin/env python3
"""
データベースマイグレーション: TaskテーブルにSchedule_idカラムを追加
"""

import sqlite3
import os
from pathlib import Path

def add_schedule_id_column():
    """TaskテーブルにSchedule_idカラムを追加"""

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

        if 'schedule_id' in columns:
            print("✅ schedule_idカラムは既に存在します")
            return True

        print("🔧 TaskテーブルにSchedule_idカラムを追加中...")

        # schedule_idカラムを追加
        cursor.execute("""
            ALTER TABLE tasks
            ADD COLUMN schedule_id TEXT
            REFERENCES schedules(id)
        """)

        # 変更をコミット
        conn.commit()

        # 追加されたことを確認
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'schedule_id' in columns:
            print("✅ schedule_idカラムが正常に追加されました")

            # テーブル構造を表示
            print("\n📋 更新後のTaskテーブル構造:")
            cursor.execute("PRAGMA table_info(tasks)")
            for column in cursor.fetchall():
                print(f"  - {column[1]} ({column[2]})")

            return True
        else:
            print("❌ schedule_idカラムの追加に失敗しました")
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

        print("\n🔍 マイグレーション検証:")
        print("Taskテーブルの全カラム:")

        schedule_id_found = False
        for column in columns:
            column_name = column[1]
            column_type = column[2]
            is_nullable = "NULL" if column[3] == 0 else "NOT NULL"

            if column_name == 'schedule_id':
                schedule_id_found = True
                print(f"  ✅ {column_name} ({column_type}) {is_nullable}")
            else:
                print(f"  - {column_name} ({column_type}) {is_nullable}")

        if schedule_id_found:
            print("\n✅ マイグレーション成功: schedule_idカラムが正常に追加されました")

            # 外部キー制約の確認
            cursor.execute("PRAGMA foreign_key_list(tasks)")
            foreign_keys = cursor.fetchall()

            print("\n🔗 外部キー制約:")
            for fk in foreign_keys:
                if fk[3] == 'schedule_id':
                    print(f"  ✅ schedule_id -> schedules(id)")
                else:
                    print(f"  - {fk[3]} -> {fk[2]}({fk[4]})")

            return True
        else:
            print("\n❌ マイグレーション失敗: schedule_idカラムが見つかりません")
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
    print("目的: TaskテーブルにSchedule_idカラムを追加")

    # マイグレーション実行
    success = add_schedule_id_column()

    if success:
        # 検証実行
        verify_migration()
        print("\n🎉 マイグレーション完了！")
        print("これで、スケジュール実行されたタスクを正確に識別できるようになりました。")
    else:
        print("\n❌ マイグレーション失敗")
        return False

    return True

if __name__ == "__main__":
    main()
