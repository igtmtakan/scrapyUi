#!/usr/bin/env python3
"""
現在使用中のデータベースにユーザー作成スクリプト
バックエンドサーバーが実際に使用しているデータベースにユーザーを作成します
"""

import sys
import os
import uuid
import sqlite3
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.auth.jwt_handler import PasswordHandler

def create_users_in_current_db():
    """現在使用中のデータベースにユーザーを作成"""
    print("👥 現在使用中のデータベースにユーザーを作成中...")
    
    # SQLiteデータベースファイルのパス（Engine URLから推測）
    db_path = "scrapy_ui"  # sqlite:///scrapy_ui から
    
    print(f"📁 データベースファイル: {db_path}")
    
    try:
        # SQLiteデータベースに直接接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # usersテーブルが存在するか確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ usersテーブルが存在しません。データベースを初期化してください。")
            return False
        
        # 既存ユーザーを確認
        cursor.execute("SELECT email FROM users WHERE email IN ('admin@scrapyui.com', 'demo@example.com')")
        existing_users = [row[0] for row in cursor.fetchall()]
        
        users_created = 0
        
        # 管理者ユーザーの作成
        if "admin@scrapyui.com" not in existing_users:
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
                admin_password, True, True, "ADMIN", "Asia/Tokyo", "{}",
                datetime.now().isoformat(), datetime.now().isoformat()
            ))
            
            users_created += 1
            print("✅ 管理者ユーザーを作成しました")
            print("   Email: admin@scrapyui.com")
            print("   Password: admin123456")
            print("   Role: ADMIN")
        else:
            print("ℹ️  管理者ユーザーは既に存在します")
            # パスワードを更新
            admin_password = PasswordHandler.hash_password("admin123456")
            cursor.execute("""
                UPDATE users SET 
                    hashed_password = ?, role = 'ADMIN', is_superuser = 1,
                    updated_at = ?
                WHERE email = 'admin@scrapyui.com'
            """, (admin_password, datetime.now().isoformat()))
            print("🔄 管理者ユーザーのパスワードと権限を更新しました")
        
        # デモユーザーの作成
        if "demo@example.com" not in existing_users:
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
                demo_password, True, False, "USER", "Asia/Tokyo", "{}",
                datetime.now().isoformat(), datetime.now().isoformat()
            ))
            
            users_created += 1
            print("✅ デモユーザーを作成しました")
            print("   Email: demo@example.com")
            print("   Password: demo12345")
            print("   Role: USER")
        else:
            print("ℹ️  デモユーザーは既に存在します")
            # パスワードを更新
            demo_password = PasswordHandler.hash_password("demo12345")
            cursor.execute("""
                UPDATE users SET 
                    hashed_password = ?, role = 'USER', is_superuser = 0,
                    updated_at = ?
                WHERE email = 'demo@example.com'
            """, (demo_password, datetime.now().isoformat()))
            print("🔄 デモユーザーのパスワードと権限を更新しました")
        
        # 変更をコミット
        conn.commit()
        
        # 作成されたユーザーを確認
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'ADMIN'")
        admin_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'USER'")
        user_count = cursor.fetchone()[0]
        
        print(f"\n📊 ユーザー統計:")
        print(f"   総ユーザー数: {total_users}")
        print(f"   管理者: {admin_count}")
        print(f"   一般ユーザー: {user_count}")
        
        if users_created > 0:
            print(f"\n🎉 {users_created}人のユーザーを新規作成しました")
        else:
            print("\n🔄 既存ユーザーの情報を更新しました")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ ユーザー作成エラー: {e}")
        return False

def test_login():
    """作成したユーザーでログインテスト"""
    print("\n🧪 ユーザーログインテスト...")
    
    db_path = "scrapy_ui"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 管理者ユーザーテスト
        cursor.execute("SELECT id, username, role, is_superuser, hashed_password FROM users WHERE email = 'admin@scrapyui.com'")
        admin_user = cursor.fetchone()
        
        if admin_user:
            print("✅ 管理者ユーザーが見つかりました")
            print(f"   ID: {admin_user[0]}")
            print(f"   Username: {admin_user[1]}")
            print(f"   Role: {admin_user[2]}")
            print(f"   Is Superuser: {admin_user[3]}")
            
            # パスワード検証
            is_valid = PasswordHandler.verify_password("admin123456", admin_user[4])
            print(f"   Password Verification: {is_valid}")
        else:
            print("❌ 管理者ユーザーが見つかりません")
        
        # デモユーザーテスト
        cursor.execute("SELECT id, username, role, is_superuser, hashed_password FROM users WHERE email = 'demo@example.com'")
        demo_user = cursor.fetchone()
        
        if demo_user:
            print("✅ デモユーザーが見つかりました")
            print(f"   ID: {demo_user[0]}")
            print(f"   Username: {demo_user[1]}")
            print(f"   Role: {demo_user[2]}")
            print(f"   Is Superuser: {demo_user[3]}")
            
            # パスワード検証
            is_valid = PasswordHandler.verify_password("demo12345", demo_user[4])
            print(f"   Password Verification: {is_valid}")
        else:
            print("❌ デモユーザーが見つかりません")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ ログインテストエラー: {e}")
        return False

def main():
    """メイン処理"""
    print("🚀 現在使用中のデータベースにユーザー作成を開始します")
    print("=" * 60)
    
    # ユーザー作成
    if not create_users_in_current_db():
        print("❌ ユーザー作成に失敗しました")
        sys.exit(1)
    
    # ログインテスト
    if not test_login():
        print("❌ ログインテストに失敗しました")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 現在使用中のデータベースにユーザー作成が完了しました！")
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
