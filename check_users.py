#!/usr/bin/env python3
"""
ユーザー情報確認スクリプト
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import SessionLocal, User
from app.auth.jwt_handler import PasswordHandler

def check_users():
    """データベースのユーザー情報を確認"""
    print("🔍 データベースのユーザー情報を確認中...")
    
    db = SessionLocal()
    try:
        # 全ユーザーを取得
        users = db.query(User).all()
        
        print(f"\n📊 総ユーザー数: {len(users)}")
        
        for user in users:
            print(f"\n👤 ユーザー情報:")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Full Name: {user.full_name}")
            print(f"   Role: {user.role}")
            print(f"   Is Active: {user.is_active}")
            print(f"   Is Superuser: {user.is_superuser}")
            print(f"   Hashed Password: {user.hashed_password[:50]}...")
            
            # パスワード検証テスト
            if user.email == "admin@scrapyui.com":
                is_valid = PasswordHandler.verify_password("admin123456", user.hashed_password)
                print(f"   Password Verification (admin123456): {is_valid}")
            elif user.email == "demo@example.com":
                is_valid = PasswordHandler.verify_password("demo12345", user.hashed_password)
                print(f"   Password Verification (demo12345): {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    finally:
        db.close()

def test_password_hash():
    """パスワードハッシュ化のテスト"""
    print("\n🧪 パスワードハッシュ化テスト...")
    
    test_password = "admin123456"
    hashed = PasswordHandler.hash_password(test_password)
    verified = PasswordHandler.verify_password(test_password, hashed)
    
    print(f"   元のパスワード: {test_password}")
    print(f"   ハッシュ化: {hashed[:50]}...")
    print(f"   検証結果: {verified}")

def main():
    """メイン処理"""
    print("🚀 ユーザー情報確認を開始します")
    print("=" * 50)
    
    if not check_users():
        print("❌ ユーザー情報確認に失敗しました")
        sys.exit(1)
    
    test_password_hash()
    
    print("\n" + "=" * 50)
    print("✅ ユーザー情報確認が完了しました")

if __name__ == "__main__":
    main()
