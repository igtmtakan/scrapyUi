#!/usr/bin/env python3
"""
最終的なユーザーデータベース修正スクリプト
実際にサーバーが使用しているデータベースにユーザーを作成します
"""

import sys
import os
import uuid
import sqlite3
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.auth.jwt_handler import PasswordHandler

def find_and_fix_database():
    """実際に使用されているデータベースを見つけて修正"""
    print("🔍 実際に使用されているデータベースを特定中...")
    
    # 可能性のあるデータベースファイルパス
    possible_paths = [
        "scrapy_ui",
        "./scrapy_ui", 
        "backend/scrapy_ui",
        "backend/app/scrapy_ui",
        "scrapy_ui.db",
        "./scrapy_ui.db",
        "backend/scrapy_ui.db",
        "backend/app/scrapy_ui.db"
    ]
    
    # 既存のSQLiteファイルを検索
    for path in possible_paths:
        if os.path.exists(path):
            print(f"📁 Found database file: {path}")
            try:
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                
                # usersテーブルが存在するかチェック
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cursor.fetchone():
                    # ユーザー数を確認
                    cursor.execute("SELECT COUNT(*) FROM users")
                    user_count = cursor.fetchone()[0]
                    print(f"🔍 Database {path} has {user_count} users")
                    
                    # このデータベースにユーザーを作成
                    create_users_in_database(path)
                    return True
                else:
                    print(f"⚠️  Database {path} has no users table")
                
                conn.close()
            except Exception as e:
                print(f"❌ Error checking {path}: {e}")
    
    # 新しいデータベースを作成
    print("📝 Creating new database with users...")
    create_new_database("scrapy_ui")
    return True

def create_users_in_database(db_path):
    """指定されたデータベースにユーザーを作成"""
    print(f"👥 Creating users in database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 既存ユーザーを削除（クリーンスタート）
        cursor.execute("DELETE FROM users")
        
        # 管理者ユーザーを作成
        admin_id = str(uuid.uuid4())
        admin_password = PasswordHandler.hash_password("admin123456")
        
        cursor.execute("""
            INSERT INTO users (
                id, email, username, full_name, hashed_password, 
                is_active, is_superuser, role, timezone, preferences,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            admin_id, "admin@scrapyui.com", "admin", "Administrator",
            admin_password, 1, 1, "ADMIN", "Asia/Tokyo", "{}",
            datetime.now().isoformat(), datetime.now().isoformat()
        ))
        
        # デモユーザーを作成
        demo_id = str(uuid.uuid4())
        demo_password = PasswordHandler.hash_password("demo12345")
        
        cursor.execute("""
            INSERT INTO users (
                id, email, username, full_name, hashed_password, 
                is_active, is_superuser, role, timezone, preferences,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            demo_id, "demo@example.com", "demo", "Demo User",
            demo_password, 1, 0, "USER", "Asia/Tokyo", "{}",
            datetime.now().isoformat(), datetime.now().isoformat()
        ))
        
        conn.commit()
        
        # 確認
        cursor.execute("SELECT email, username, role FROM users")
        users = cursor.fetchall()
        
        print("✅ Users created successfully:")
        for user in users:
            print(f"   {user[0]} | {user[1]} | {user[2]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating users: {e}")
        return False

def create_new_database(db_path):
    """新しいデータベースを作成"""
    print(f"🔧 Creating new database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # usersテーブルを作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                full_name VARCHAR(255),
                hashed_password VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_superuser BOOLEAN DEFAULT 0,
                role VARCHAR(20) DEFAULT 'USER',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                avatar_url VARCHAR(500),
                timezone VARCHAR(50) DEFAULT 'UTC',
                preferences TEXT DEFAULT '{}'
            )
        """)
        
        # 他の必要なテーブルも作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                path VARCHAR(500) UNIQUE NOT NULL,
                scrapy_version VARCHAR(50) DEFAULT '2.11.0',
                settings TEXT,
                is_active BOOLEAN DEFAULT 1,
                db_save_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id VARCHAR(36) NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spiders (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                code TEXT NOT NULL,
                template VARCHAR(100),
                framework VARCHAR(50),
                start_urls TEXT,
                settings TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                project_id VARCHAR(36) NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id VARCHAR(36) PRIMARY KEY,
                status VARCHAR(20) DEFAULT 'PENDING',
                started_at TIMESTAMP,
                finished_at TIMESTAMP,
                items_count INTEGER DEFAULT 0,
                requests_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                log_level VARCHAR(20) DEFAULT 'INFO',
                settings TEXT,
                celery_task_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                project_id VARCHAR(36) NOT NULL,
                spider_id VARCHAR(36) NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                schedule_id VARCHAR(36),
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (spider_id) REFERENCES spiders (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id VARCHAR(36) PRIMARY KEY,
                data TEXT NOT NULL,
                url VARCHAR(2000),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                crawl_start_datetime TIMESTAMP,
                item_acquired_datetime TIMESTAMP,
                data_hash VARCHAR(64),
                task_id VARCHAR(36) NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        """)
        
        # その他のテーブル
        for table_sql in [
            """CREATE TABLE IF NOT EXISTS logs (
                id VARCHAR(36) PRIMARY KEY,
                level VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                task_id VARCHAR(36) NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )""",
            """CREATE TABLE IF NOT EXISTS schedules (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                cron_expression VARCHAR(100) NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                project_id VARCHAR(36) NOT NULL,
                spider_id VARCHAR(36) NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (spider_id) REFERENCES spiders (id)
            )""",
            """CREATE TABLE IF NOT EXISTS notifications (
                id VARCHAR(36) PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                type VARCHAR(20) NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                task_id VARCHAR(36),
                project_id VARCHAR(36),
                user_id VARCHAR(36),
                FOREIGN KEY (task_id) REFERENCES tasks (id),
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )""",
            """CREATE TABLE IF NOT EXISTS project_files (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                path VARCHAR(500) NOT NULL,
                content TEXT NOT NULL,
                file_type VARCHAR(50) DEFAULT 'python',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                project_id VARCHAR(36) NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )""",
            """CREATE TABLE IF NOT EXISTS user_sessions (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                refresh_token VARCHAR(500) NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                user_agent VARCHAR(500),
                ip_address VARCHAR(45),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )"""
        ]:
            cursor.execute(table_sql)
        
        conn.commit()
        
        # ユーザーを作成
        create_users_in_database(db_path)
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def main():
    """メイン処理"""
    print("🚀 最終的なユーザーデータベース修正を開始します")
    print("=" * 60)
    
    if not find_and_fix_database():
        print("❌ データベース修正に失敗しました")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 ユーザーデータベース修正が完了しました！")
    print("\n📋 ログイン情報:")
    print("【管理者】")
    print("  Email: admin@scrapyui.com")
    print("  Password: admin123456")
    print("  権限: 管理者（全機能アクセス可能）")
    print("\n【デモユーザー】")
    print("  Email: demo@example.com")
    print("  Password: demo12345")
    print("  権限: 一般ユーザー（制限あり）")
    print("\n🌐 WebUIアクセス: http://localhost:4000")
    print("\n💡 サーバーを再起動してからログインしてください")

if __name__ == "__main__":
    main()
