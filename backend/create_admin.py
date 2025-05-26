#!/usr/bin/env python3
"""
管理者ユーザーを作成するスクリプト
"""

import sys
import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, User, UserRole
from app.auth.jwt_handler import PasswordHandler

def create_admin_user():
    """管理者ユーザーを作成"""
    db = SessionLocal()

    try:
        # 既存の管理者ユーザーをチェック
        existing_admin = db.query(User).filter(User.email == "admin@scrapyui.com").first()

        if existing_admin:
            print("管理者ユーザーは既に存在します。")
            print(f"ユーザーID: {existing_admin.id}")
            print(f"メール: {existing_admin.email}")
            print(f"ロール: {existing_admin.role}")
            return existing_admin

        # 管理者ユーザーを作成
        admin_user = User(
            id="admin-user-id",
            email="admin@scrapyui.com",
            username="admin",
            full_name="System Administrator",
            hashed_password=PasswordHandler.hash_password("admin123456"),
            role=UserRole.ADMIN,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("✅ 管理者ユーザーが正常に作成されました！")
        print(f"ユーザーID: {admin_user.id}")
        print(f"メール: {admin_user.email}")
        print(f"ユーザー名: {admin_user.username}")
        print(f"フルネーム: {admin_user.full_name}")
        print(f"ロール: {admin_user.role}")
        print(f"アクティブ: {admin_user.is_active}")
        print(f"作成日時: {admin_user.created_at}")

        return admin_user

    except Exception as e:
        db.rollback()
        print(f"❌ エラーが発生しました: {str(e)}")
        raise
    finally:
        db.close()

def verify_admin_login():
    """管理者ログインの検証"""

    db = SessionLocal()

    try:
        admin_user = db.query(User).filter(User.email == "admin@scrapyui.com").first()

        if not admin_user:
            print("❌ 管理者ユーザーが見つかりません。")
            return False

        # パスワード検証
        if PasswordHandler.verify_password("admin123456", admin_user.hashed_password):
            print("✅ 管理者ログイン認証が正常に動作します。")
            return True
        else:
            print("❌ パスワード認証に失敗しました。")
            return False

    except Exception as e:
        print(f"❌ 検証エラー: {str(e)}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 管理者ユーザー作成スクリプトを開始...")
    print("=" * 50)

    # 管理者ユーザーを作成
    admin_user = create_admin_user()

    print("\n" + "=" * 50)
    print("🔍 ログイン認証をテスト...")

    # ログイン認証をテスト
    verify_admin_login()

    print("\n" + "=" * 50)
    print("✅ 管理者ユーザー作成完了！")
    print("\n📋 ログイン情報:")
    print("   メール: admin@scrapyui.com")
    print("   パスワード: admin123456")
    print("   ロール: admin")
    print("\n🌐 フロントエンドでログインしてください:")
    print("   URL: http://localhost:3001")
