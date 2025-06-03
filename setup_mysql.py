#!/usr/bin/env python3
"""
MySQL セットアップスクリプト
ScrapyUI用のMySQLデータベースとユーザーを作成します
"""

import subprocess
import sys
import os
import mysql.connector
from mysql.connector import Error
import getpass

def run_command(command, check=True):
    """コマンドを実行"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode

def check_mysql_service():
    """MySQLサービスの状態を確認"""
    print("🔍 MySQLサービスの状態を確認中...")
    
    stdout, stderr, returncode = run_command("mysqladmin ping", check=False)
    if "mysqld is alive" in stdout or "Access denied" in stderr:
        print("✅ MySQLサービスが動作しています")
        return True
    else:
        print("❌ MySQLサービスが動作していません")
        print(f"エラー: {stderr}")
        return False

def get_mysql_root_connection():
    """MySQL rootユーザーでの接続を取得"""
    print("🔑 MySQL root認証情報を入力してください")
    
    # 複数の認証方法を試行
    auth_methods = [
        {'password': None, 'auth_plugin': 'mysql_native_password'},  # パスワードなし
        {'password': '', 'auth_plugin': 'mysql_native_password'},    # 空パスワード
        {'password': 'root', 'auth_plugin': 'mysql_native_password'}, # デフォルトパスワード
    ]
    
    connection = None
    
    # 自動認証を試行
    for auth in auth_methods:
        try:
            print(f"🔑 自動認証を試行中...")
            
            config = {
                'host': 'localhost',
                'user': 'root',
                'charset': 'utf8mb4',
                'autocommit': True
            }
            
            if auth['password'] is not None:
                config['password'] = auth['password']
            
            connection = mysql.connector.connect(**config)
            print("✅ MySQL rootに接続しました（自動認証）")
            return connection
            
        except Error as e:
            print(f"❌ 自動認証失敗: {e}")
            continue
    
    # 手動でパスワード入力
    max_attempts = 3
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
            return connection
            
        except Error as e:
            print(f"❌ 接続失敗: {e}")
            if attempt == max_attempts - 1:
                print("❌ 最大試行回数に達しました")
                return None
    
    return None

def create_database_and_user(connection):
    """データベースとユーザーを作成"""
    print("🔧 MySQLデータベースとユーザーを作成中...")
    
    try:
        cursor = connection.cursor()
        
        # ユーザーが既に存在するかチェック
        cursor.execute("SELECT User FROM mysql.user WHERE User='scrapy_user' AND Host='localhost'")
        user_exists = cursor.fetchone()
        
        if user_exists:
            print("ℹ️  ユーザー 'scrapy_user' は既に存在します")
            # 既存ユーザーを削除して再作成
            print("🔄 既存ユーザーを削除して再作成します...")
            cursor.execute("DROP USER 'scrapy_user'@'localhost'")
        
        # ユーザー作成（強力なパスワードを使用）
        print("👤 ユーザー 'scrapy_user' を作成中...")
        strong_password = "ScrapyUser@2024!"
        cursor.execute(f"CREATE USER 'scrapy_user'@'localhost' IDENTIFIED BY '{strong_password}'")
        print("✅ ユーザー 'scrapy_user' を作成しました")
        print(f"🔑 パスワード: {strong_password}")
        
        # データベースが既に存在するかチェック
        cursor.execute("SHOW DATABASES LIKE 'scrapy_ui'")
        db_exists = cursor.fetchone()
        
        if db_exists:
            print("ℹ️  データベース 'scrapy_ui' は既に存在します")
            print("🔄 既存データベースを削除して再作成します...")
            cursor.execute("DROP DATABASE scrapy_ui")
        
        # データベース作成
        print("🗄️  データベース 'scrapy_ui' を作成中...")
        cursor.execute("CREATE DATABASE scrapy_ui CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("✅ データベース 'scrapy_ui' を作成しました")
        
        # ユーザーに権限を付与
        print("🔐 ユーザーに権限を付与中...")
        cursor.execute("GRANT ALL PRIVILEGES ON scrapy_ui.* TO 'scrapy_user'@'localhost'")
        cursor.execute("FLUSH PRIVILEGES")
        print("✅ 権限を付与しました")
        
        return True
        
    except Error as e:
        print(f"❌ データベース操作エラー: {e}")
        return False

def test_connection():
    """作成したデータベースへの接続をテスト"""
    print("🧪 データベース接続をテスト中...")
    
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='scrapy_user',
            password='ScrapyUser@2024!',
            database='scrapy_ui',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"✅ 接続成功: MySQL {version}")
        
        # テーブル作成テスト
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # テストデータ挿入
        cursor.execute("INSERT INTO test_table (name) VALUES ('test')")
        cursor.execute("SELECT LAST_INSERT_ID()")
        test_id = cursor.fetchone()[0]
        print(f"✅ テストテーブル作成・データ挿入成功 (ID: {test_id})")
        
        # テストテーブル削除
        cursor.execute("DROP TABLE test_table")
        print("✅ テストテーブル削除成功")
        
        connection.commit()
        connection.close()
        
        return True
        
    except Error as e:
        print(f"❌ 接続テスト失敗: {e}")
        return False

def install_python_dependencies():
    """Python依存関係をインストール"""
    print("📦 Python MySQL依存関係をインストール中...")
    
    try:
        # mysql-connector-pythonをインストール
        stdout, stderr, returncode = run_command("pip install mysql-connector-python")
        if returncode == 0:
            print("✅ mysql-connector-python をインストールしました")
        else:
            print(f"❌ mysql-connector-python インストール失敗: {stderr}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 依存関係インストールエラー: {e}")
        return False

def main():
    """メイン処理"""
    print("🚀 MySQL セットアップを開始します")
    print("=" * 50)
    
    # MySQLサービス確認
    if not check_mysql_service():
        print("❌ MySQLサービスが動作していません。先にMySQLをインストール・起動してください。")
        sys.exit(1)
    
    # Python依存関係インストール
    if not install_python_dependencies():
        print("❌ Python依存関係のインストールに失敗しました")
        sys.exit(1)
    
    # MySQL root接続
    connection = get_mysql_root_connection()
    if not connection:
        print("❌ MySQL rootに接続できませんでした")
        sys.exit(1)
    
    try:
        # データベースとユーザー作成
        if not create_database_and_user(connection):
            print("❌ データベースとユーザーの作成に失敗しました")
            sys.exit(1)
    finally:
        connection.close()
    
    # 接続テスト
    if not test_connection():
        print("❌ データベース接続テストに失敗しました")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 MySQL セットアップが完了しました！")
    print("\n📋 作成された設定:")
    print("  ホスト: localhost")
    print("  ポート: 3306")
    print("  データベース: scrapy_ui")
    print("  ユーザー: scrapy_user")
    print("  パスワード: ScrapyUser@2024!")
    print("  文字セット: utf8mb4")
    print("\n📝 次のステップ:")
    print("  1. ScrapyUIの設定をMySQLに切り替え")
    print("  2. データベーステーブルの初期化")
    print("  3. アプリケーションの再起動")

if __name__ == "__main__":
    main()
