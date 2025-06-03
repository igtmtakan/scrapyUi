#!/usr/bin/env python3
"""
現在使用中のデータベース初期化スクリプト
バックエンドサーバーが実際に使用しているSQLiteデータベースを初期化します
"""

import sys
import os
import uuid
import sqlite3
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.auth.jwt_handler import PasswordHandler

def init_sqlite_database():
    """SQLiteデータベースを初期化"""
    print("🔧 SQLiteデータベースを初期化中...")
    
    db_path = "scrapy_ui"  # Engine URLから推測
    
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
        
        # projectsテーブルを作成
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
        
        # spidersテーブルを作成
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
        
        # tasksテーブルを作成
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
        
        # resultsテーブルを作成
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
        
        # その他の必要なテーブルを作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id VARCHAR(36) PRIMARY KEY,
                level VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                task_id VARCHAR(36) NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
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
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
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
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_files (
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
            )
        """)
        
        # 変更をコミット
        conn.commit()
        
        print("✅ データベーステーブルを作成しました")
        
        # 管理者ユーザーとデモユーザーを作成
        admin_id = str(uuid.uuid4())
        admin_password = PasswordHandler.hash_password("admin123456")
        
        cursor.execute("""
            INSERT INTO users (
                id, email, username, full_name, hashed_password, 
                is_active, is_superuser, role, timezone, preferences
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            admin_id, "admin@scrapyui.com", "admin", "Administrator",
            admin_password, 1, 1, "ADMIN", "Asia/Tokyo", "{}"
        ))
        
        demo_id = str(uuid.uuid4())
        demo_password = PasswordHandler.hash_password("demo12345")
        
        cursor.execute("""
            INSERT INTO users (
                id, email, username, full_name, hashed_password, 
                is_active, is_superuser, role, timezone, preferences
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            demo_id, "demo@example.com", "demo", "Demo User",
            demo_password, 1, 0, "USER", "Asia/Tokyo", "{}"
        ))
        
        conn.commit()
        
        print("✅ 管理者ユーザーとデモユーザーを作成しました")
        
        # 作成されたユーザーを確認
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        print(f"📊 総ユーザー数: {total_users}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("🚀 SQLite データベース初期化を開始します")
    print("=" * 50)
    
    if not init_sqlite_database():
        print("❌ データベース初期化に失敗しました")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 SQLite データベース初期化が完了しました！")
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

if __name__ == "__main__":
    main()
