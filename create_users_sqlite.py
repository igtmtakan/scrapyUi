#!/usr/bin/env python3
"""
SQLiteデータベースにユーザー作成スクリプト
現在使用されているSQLiteデータベースに管理者ユーザーとデモユーザーを作成します
"""

import sys
import os
import uuid
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import SessionLocal, User, UserRole
from app.auth.jwt_handler import PasswordHandler

def create_users_in_sqlite():
    """現在のSQLiteデータベースに管理者ユーザーとデモユーザーを作成"""
    print("👥 SQLiteデータベースにユーザーを作成中...")
    
    db = SessionLocal()
    try:
        # 既存ユーザーを確認
        existing_admin = db.query(User).filter(User.email == "admin@scrapyui.com").first()
        existing_demo = db.query(User).filter(User.email == "demo@example.com").first()
        
        users_created = 0
        
        # 管理者ユーザーの作成
        if not existing_admin:
            admin_user = User(
                id=str(uuid.uuid4()),
                email="admin@scrapyui.com",
                username="admin",
                full_name="Administrator",
                hashed_password=PasswordHandler.hash_password("admin123456"),
                is_active=True,
                is_superuser=True,
                role=UserRole.ADMIN,
                timezone="Asia/Tokyo",
                preferences={}
            )
            db.add(admin_user)
            users_created += 1
            print("✅ 管理者ユーザーを作成しました")
            print("   Email: admin@scrapyui.com")
            print("   Password: admin123456")
            print("   Role: ADMIN")
        else:
            print("ℹ️  管理者ユーザーは既に存在します")
            # パスワードを更新
            existing_admin.hashed_password = PasswordHandler.hash_password("admin123456")
            existing_admin.role = UserRole.ADMIN
            existing_admin.is_superuser = True
            print("🔄 管理者ユーザーのパスワードと権限を更新しました")
        
        # デモユーザーの作成
        if not existing_demo:
            demo_user = User(
                id=str(uuid.uuid4()),
                email="demo@example.com",
                username="demo",
                full_name="Demo User",
                hashed_password=PasswordHandler.hash_password("demo12345"),
                is_active=True,
                is_superuser=False,
                role=UserRole.USER,
                timezone="Asia/Tokyo",
                preferences={}
            )
            db.add(demo_user)
            users_created += 1
            print("✅ デモユーザーを作成しました")
            print("   Email: demo@example.com")
            print("   Password: demo12345")
            print("   Role: USER")
        else:
            print("ℹ️  デモユーザーは既に存在します")
            # パスワードを更新
            existing_demo.hashed_password = PasswordHandler.hash_password("demo12345")
            existing_demo.role = UserRole.USER
            existing_demo.is_superuser = False
            print("🔄 デモユーザーのパスワードと権限を更新しました")
        
        # 変更をコミット
        db.commit()
        
        # 作成されたユーザーを確認
        total_users = db.query(User).count()
        admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
        user_count = db.query(User).filter(User.role == UserRole.USER).count()
        
        print(f"\n📊 ユーザー統計:")
        print(f"   総ユーザー数: {total_users}")
        print(f"   管理者: {admin_count}")
        print(f"   一般ユーザー: {user_count}")
        
        if users_created > 0:
            print(f"\n🎉 {users_created}人のユーザーを新規作成しました")
        else:
            print("\n🔄 既存ユーザーの情報を更新しました")
        
        return True
        
    except Exception as e:
        print(f"❌ ユーザー作成エラー: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_login():
    """作成したユーザーでログインテスト"""
    print("\n🧪 ユーザーログインテスト...")
    
    db = SessionLocal()
    try:
        # 管理者ユーザーテスト
        admin_user = db.query(User).filter(User.email == "admin@scrapyui.com").first()
        if admin_user:
            print("✅ 管理者ユーザーが見つかりました")
            print(f"   ID: {admin_user.id}")
            print(f"   Username: {admin_user.username}")
            print(f"   Role: {admin_user.role}")
            print(f"   Is Superuser: {admin_user.is_superuser}")
            
            # パスワード検証
            is_valid = PasswordHandler.verify_password("admin123456", admin_user.hashed_password)
            print(f"   Password Verification: {is_valid}")
        else:
            print("❌ 管理者ユーザーが見つかりません")
        
        # デモユーザーテスト
        demo_user = db.query(User).filter(User.email == "demo@example.com").first()
        if demo_user:
            print("✅ デモユーザーが見つかりました")
            print(f"   ID: {demo_user.id}")
            print(f"   Username: {demo_user.username}")
            print(f"   Role: {demo_user.role}")
            print(f"   Is Superuser: {demo_user.is_superuser}")
            
            # パスワード検証
            is_valid = PasswordHandler.verify_password("demo12345", demo_user.hashed_password)
            print(f"   Password Verification: {is_valid}")
        else:
            print("❌ デモユーザーが見つかりません")
        
        return True
        
    except Exception as e:
        print(f"❌ ログインテストエラー: {e}")
        return False
    finally:
        db.close()

def main():
    """メイン処理"""
    print("🚀 SQLite ユーザー作成を開始します")
    print("=" * 50)
    
    # ユーザー作成
    if not create_users_in_sqlite():
        print("❌ ユーザー作成に失敗しました")
        sys.exit(1)
    
    # ログインテスト
    if not test_login():
        print("❌ ログインテストに失敗しました")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 SQLite ユーザー作成が完了しました！")
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
    print("\n💡 注意: 現在SQLiteデータベースを使用しています")
    print("   MySQLに切り替える場合は、設定ファイルを確認してください")

if __name__ == "__main__":
    main()
