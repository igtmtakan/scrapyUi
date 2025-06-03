#!/usr/bin/env python3
"""
PostgreSQL セットアップスクリプト
ScrapyUI用のPostgreSQLデータベースとユーザーを作成します
"""

import subprocess
import sys
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def run_command(command, check=True):
    """コマンドを実行"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode

def check_postgresql_service():
    """PostgreSQLサービスの状態を確認"""
    print("🔍 PostgreSQLサービスの状態を確認中...")
    
    stdout, stderr, returncode = run_command("pg_isready", check=False)
    if returncode == 0:
        print("✅ PostgreSQLサービスが動作しています")
        return True
    else:
        print("❌ PostgreSQLサービスが動作していません")
        print(f"エラー: {stderr}")
        return False

def create_database_and_user():
    """データベースとユーザーを作成"""
    print("🔧 PostgreSQLデータベースとユーザーを作成中...")
    
    # PostgreSQLに接続するための設定
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'postgres',  # デフォルトデータベースに接続
        'user': 'postgres'
    }
    
    # 複数の認証方法を試行
    auth_methods = [
        {'password': None},  # パスワードなし（peer認証）
        {'password': ''},    # 空パスワード
        {'password': 'postgres'},  # デフォルトパスワード
    ]
    
    connection = None
    
    for auth in auth_methods:
        try:
            print(f"🔑 認証方法を試行中: {auth}")
            
            # 接続設定を更新
            config = db_config.copy()
            if auth['password'] is not None:
                config['password'] = auth['password']
            
            connection = psycopg2.connect(**config)
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            print("✅ PostgreSQLに接続しました")
            break
            
        except psycopg2.Error as e:
            print(f"❌ 接続失敗: {e}")
            continue
    
    if not connection:
        print("❌ PostgreSQLに接続できませんでした")
        return False
    
    try:
        cursor = connection.cursor()
        
        # ユーザーが既に存在するかチェック
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='scrapy_user'")
        user_exists = cursor.fetchone()
        
        if not user_exists:
            # ユーザー作成
            print("👤 ユーザー 'scrapy_user' を作成中...")
            cursor.execute("CREATE USER scrapy_user WITH PASSWORD 'scrapy_userpass'")
            print("✅ ユーザー 'scrapy_user' を作成しました")
        else:
            print("ℹ️  ユーザー 'scrapy_user' は既に存在します")
            # パスワードを更新
            cursor.execute("ALTER USER scrapy_user WITH PASSWORD 'scrapy_userpass'")
            print("🔄 ユーザー 'scrapy_user' のパスワードを更新しました")
        
        # データベースが既に存在するかチェック
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='scrapy_ui'")
        db_exists = cursor.fetchone()
        
        if not db_exists:
            # データベース作成
            print("🗄️  データベース 'scrapy_ui' を作成中...")
            cursor.execute("CREATE DATABASE scrapy_ui OWNER scrapy_user")
            print("✅ データベース 'scrapy_ui' を作成しました")
        else:
            print("ℹ️  データベース 'scrapy_ui' は既に存在します")
            # オーナーを設定
            cursor.execute("ALTER DATABASE scrapy_ui OWNER TO scrapy_user")
            print("🔄 データベース 'scrapy_ui' のオーナーを更新しました")
        
        # ユーザーに権限を付与
        print("🔐 ユーザーに権限を付与中...")
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE scrapy_ui TO scrapy_user")
        cursor.execute("ALTER USER scrapy_user CREATEDB")
        print("✅ 権限を付与しました")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ データベース操作エラー: {e}")
        return False
    finally:
        if connection:
            connection.close()

def test_connection():
    """作成したデータベースへの接続をテスト"""
    print("🧪 データベース接続をテスト中...")
    
    try:
        connection = psycopg2.connect(
            host='localhost',
            port=5432,
            database='scrapy_ui',
            user='scrapy_user',
            password='scrapy_userpass'
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ 接続成功: {version}")
        
        # テーブル作成テスト
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # テストデータ挿入
        cursor.execute("INSERT INTO test_table (name) VALUES ('test') RETURNING id")
        test_id = cursor.fetchone()[0]
        print(f"✅ テストテーブル作成・データ挿入成功 (ID: {test_id})")
        
        # テストテーブル削除
        cursor.execute("DROP TABLE test_table")
        print("✅ テストテーブル削除成功")
        
        connection.commit()
        connection.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ 接続テスト失敗: {e}")
        return False

def install_python_dependencies():
    """Python依存関係をインストール"""
    print("📦 Python PostgreSQL依存関係をインストール中...")
    
    try:
        # psycopg2-binaryをインストール
        stdout, stderr, returncode = run_command("pip install psycopg2-binary")
        if returncode == 0:
            print("✅ psycopg2-binary をインストールしました")
        else:
            print(f"❌ psycopg2-binary インストール失敗: {stderr}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 依存関係インストールエラー: {e}")
        return False

def main():
    """メイン処理"""
    print("🚀 PostgreSQL セットアップを開始します")
    print("=" * 50)
    
    # PostgreSQLサービス確認
    if not check_postgresql_service():
        print("❌ PostgreSQLサービスが動作していません。先にPostgreSQLをインストール・起動してください。")
        sys.exit(1)
    
    # Python依存関係インストール
    if not install_python_dependencies():
        print("❌ Python依存関係のインストールに失敗しました")
        sys.exit(1)
    
    # データベースとユーザー作成
    if not create_database_and_user():
        print("❌ データベースとユーザーの作成に失敗しました")
        sys.exit(1)
    
    # 接続テスト
    if not test_connection():
        print("❌ データベース接続テストに失敗しました")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 PostgreSQL セットアップが完了しました！")
    print("\n📋 作成された設定:")
    print("  ホスト: localhost")
    print("  ポート: 5432")
    print("  データベース: scrapy_ui")
    print("  ユーザー: scrapy_user")
    print("  パスワード: scrapy_userpass")
    print("\n📝 次のステップ:")
    print("  1. ScrapyUIの設定をPostgreSQLに切り替え")
    print("  2. データベーステーブルの初期化")
    print("  3. アプリケーションの再起動")

if __name__ == "__main__":
    main()
