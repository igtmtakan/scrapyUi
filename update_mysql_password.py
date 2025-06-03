#!/usr/bin/env python3
"""
MySQLパスワード更新スクリプト
"""

import mysql.connector
from mysql.connector import Error
import getpass

def update_password():
    """MySQLユーザーのパスワードを更新"""
    print("🔧 MySQLユーザーのパスワードを更新中...")
    
    # MySQL root接続
    max_attempts = 3
    connection = None
    
    for attempt in range(max_attempts):
        try:
            password = getpass.getpass(f"MySQL rootパスワードを入力してください (試行 {attempt + 1}/{max_attempts}): ")
            
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password=password,
                charset='utf8mb4',
                autocommit=True
            )
            
            print("✅ MySQL rootに接続しました")
            break
            
        except Error as e:
            print(f"❌ 接続失敗: {e}")
            if attempt == max_attempts - 1:
                print("❌ 最大試行回数に達しました")
                return False
    
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # パスワード更新（より強力なパスワード）
        new_password = "ScrapyUser@2024#"
        cursor.execute(f"ALTER USER 'scrapy_user'@'localhost' IDENTIFIED BY '{new_password}'")
        cursor.execute("FLUSH PRIVILEGES")
        
        print(f"✅ ユーザー 'scrapy_user' のパスワードを '{new_password}' に更新しました")
        
        return True
        
    except Error as e:
        print(f"❌ パスワード更新エラー: {e}")
        return False
    finally:
        if connection:
            connection.close()

def test_connection():
    """更新後の接続をテスト"""
    print("🧪 更新後の接続をテスト中...")
    
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='scrapy_user',
            password='ScrapyUser@2024#',
            database='scrapy_ui',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"✅ 接続成功: MySQL {version}")
        
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ 接続テスト失敗: {e}")
        return False

def main():
    """メイン処理"""
    print("🚀 MySQLパスワード更新を開始します")
    print("=" * 50)
    
    if not update_password():
        print("❌ パスワード更新に失敗しました")
        return False
    
    if not test_connection():
        print("❌ 接続テストに失敗しました")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 MySQLパスワード更新が完了しました！")
    print("\n📋 更新された設定:")
    print("  ユーザー: scrapy_user")
    print("  新しいパスワード: ScrapyUser@2024#")
    
    return True

if __name__ == "__main__":
    main()
