#!/usr/bin/env python3
"""
ScrapyUI データベース設定確認スクリプト

現在のデータベース設定を確認し、接続テストを実行します。
"""

import sys
import os
from pathlib import Path

# ScrapyUIのパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_database_config():
    """データベース設定を確認"""
    try:
        from app.config.database_config import get_database_config, db_config_manager
        
        print("🔍 ScrapyUI データベース設定確認")
        print("=" * 60)
        
        # 現在の設定を取得
        config = get_database_config()
        
        print(f"✅ 現在のデータベース設定:")
        print(f"   📊 タイプ: {config.type.value}")
        
        if config.type.value == 'sqlite':
            print(f"   📁 データベースファイル: {config.database}")
            print(f"   📂 ファイル存在: {os.path.exists(config.database)}")
            if os.path.exists(config.database):
                file_size = os.path.getsize(config.database)
                print(f"   📏 ファイルサイズ: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        else:
            print(f"   🌐 ホスト: {config.host}")
            print(f"   🔌 ポート: {config.port}")
            print(f"   🗄️ データベース名: {config.database}")
            print(f"   👤 ユーザー: {config.username}")
            print(f"   🔧 プールサイズ: {config.pool_size}")
            print(f"   ⚡ 最大オーバーフロー: {config.max_overflow}")
        
        print(f"   🔊 SQLエコー: {config.echo}")
        
        # 利用可能な環境設定を表示
        print(f"\n🌍 利用可能な環境設定:")
        for env_name, env_config in db_config_manager.configs.items():
            status = "🟢 アクティブ" if env_name == "default" else "⚪ 利用可能"
            print(f"   {status} {env_name}: {env_config.type.value}")
            if env_config.type.value == 'sqlite':
                print(f"      📁 {env_config.database}")
            else:
                print(f"      🌐 {env_config.username}@{env_config.host}:{env_config.port}/{env_config.database}")
        
        return config
        
    except Exception as e:
        print(f"❌ 設定確認エラー: {e}")
        return None

def test_database_connection(config):
    """データベース接続テスト"""
    print(f"\n🔗 データベース接続テスト")
    print("-" * 40)
    
    try:
        if config.type.value == 'sqlite':
            # SQLite接続テスト
            import sqlite3
            
            if not os.path.exists(config.database):
                print(f"⚠️ データベースファイルが存在しません: {config.database}")
                return False
            
            conn = sqlite3.connect(config.database)
            cursor = conn.cursor()
            
            # テーブル一覧を取得
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print(f"✅ SQLite接続成功")
            print(f"📋 テーブル数: {len(tables)}")
            if tables:
                print(f"📝 テーブル一覧:")
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    print(f"   - {table[0]}: {count:,} レコード")
            
            conn.close()
            return True
            
        else:
            # MySQL/PostgreSQL接続テスト
            from sqlalchemy import create_engine
            
            connection_url = config.get_connection_url()
            engine = create_engine(connection_url, echo=False)
            
            # 接続テスト
            with engine.connect() as conn:
                if config.type.value == 'mysql':
                    result = conn.execute("SELECT VERSION()")
                elif config.type.value == 'postgresql':
                    result = conn.execute("SELECT version()")
                
                version = result.fetchone()[0]
                print(f"✅ {config.type.value.upper()}接続成功")
                print(f"📊 バージョン: {version}")
                
                # テーブル一覧を取得
                if config.type.value == 'mysql':
                    result = conn.execute("SHOW TABLES")
                elif config.type.value == 'postgresql':
                    result = conn.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                
                tables = result.fetchall()
                print(f"📋 テーブル数: {len(tables)}")
                
                if tables:
                    print(f"📝 テーブル一覧:")
                    for table in tables:
                        table_name = table[0]
                        count_result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = count_result.fetchone()[0]
                        print(f"   - {table_name}: {count:,} レコード")
            
            return True
            
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        return False

def check_dependencies():
    """必要な依存関係を確認"""
    print(f"\n📦 依存関係確認")
    print("-" * 40)
    
    dependencies = {
        'sqlite3': 'SQLite (標準ライブラリ)',
        'pymysql': 'MySQL接続',
        'psycopg2': 'PostgreSQL接続',
        'sqlalchemy': 'SQLAlchemy ORM'
    }
    
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {module}: {description}")
        except ImportError:
            print(f"❌ {module}: {description} (未インストール)")

def main():
    print("🎯 ScrapyUI データベース診断ツール")
    print("=" * 60)
    
    # 依存関係確認
    check_dependencies()
    
    # 設定確認
    config = check_database_config()
    
    if config:
        # 接続テスト
        success = test_database_connection(config)
        
        print(f"\n📊 診断結果")
        print("-" * 40)
        if success:
            print("✅ データベース設定は正常です")
            print("🚀 ScrapyUIを起動できます")
        else:
            print("❌ データベース接続に問題があります")
            print("🔧 設定を確認してください")
    
    print(f"\n💡 ヒント:")
    print(f"   - データベースを切り替える: python scripts/switch_database.py --help")
    print(f"   - 設定ファイル: backend/config/database.yaml")
    print(f"   - 環境変数ファイル: backend/.env")

if __name__ == '__main__':
    main()
