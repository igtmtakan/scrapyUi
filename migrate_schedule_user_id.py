#!/usr/bin/env python3
"""
Schedule テーブルに user_id カラムを追加するマイグレーション
"""

import sqlite3
import sys
import os
from pathlib import Path

def migrate_schedule_user_id():
    """Schedule テーブルに user_id カラムを追加"""
    
    # データベースファイルのパス
    # スクリプトの実行場所に応じてパスを調整
    if Path("backend/database/scrapy_ui.db").exists():
        db_path = Path("backend/database/scrapy_ui.db")
    elif Path("database/scrapy_ui.db").exists():
        db_path = Path("database/scrapy_ui.db")
    else:
        db_path = Path("backend/database/scrapy_ui.db")  # デフォルト
    
    if not db_path.exists():
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 現在のスキーマを確認
        cursor.execute("PRAGMA table_info(schedules)")
        columns = cursor.fetchall()
        
        print("📋 Current schedules table schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # user_id カラムが既に存在するかチェック
        column_names = [col[1] for col in columns]
        if 'user_id' in column_names:
            print("✅ user_id column already exists")
            return True
        
        print("\n🔧 Adding user_id column to schedules table...")
        
        # user_id カラムを追加
        cursor.execute("""
            ALTER TABLE schedules 
            ADD COLUMN user_id VARCHAR(36)
        """)
        
        # 既存のスケジュールにデフォルトのuser_idを設定
        # admin ユーザーのIDを取得
        cursor.execute("SELECT id FROM users WHERE email = 'admin@scrapyui.com' LIMIT 1")
        admin_user = cursor.fetchone()
        
        if admin_user:
            admin_user_id = admin_user[0]
            print(f"📝 Setting default user_id to admin user: {admin_user_id}")
            
            cursor.execute("""
                UPDATE schedules 
                SET user_id = ? 
                WHERE user_id IS NULL
            """, (admin_user_id,))
            
            updated_count = cursor.rowcount
            print(f"✅ Updated {updated_count} schedules with admin user_id")
        else:
            print("⚠️ Admin user not found, leaving user_id as NULL")
        
        # 外部キー制約を追加（SQLiteでは制約の追加は複雑なので、今回はスキップ）
        print("⚠️ Note: Foreign key constraint for user_id should be added manually if needed")
        
        conn.commit()
        
        # 更新後のスキーマを確認
        cursor.execute("PRAGMA table_info(schedules)")
        columns = cursor.fetchall()
        
        print("\n📋 Updated schedules table schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # スケジュール数を確認
        cursor.execute("SELECT COUNT(*) FROM schedules")
        schedule_count = cursor.fetchone()[0]
        print(f"\n📊 Total schedules: {schedule_count}")
        
        if schedule_count > 0:
            cursor.execute("SELECT COUNT(*) FROM schedules WHERE user_id IS NOT NULL")
            with_user_id = cursor.fetchone()[0]
            print(f"📊 Schedules with user_id: {with_user_id}")
        
        conn.close()
        
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("🚀 Starting Schedule user_id migration...")
    success = migrate_schedule_user_id()
    
    if success:
        print("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("💥 Migration failed!")
        sys.exit(1)
