#!/usr/bin/env python3
"""
ScrapyUI データベース切り替えスクリプト

使用方法:
  python scripts/switch_database.py --db sqlite
  python scripts/switch_database.py --db mysql --host localhost --user scrapy_user --password your_password
  python scripts/switch_database.py --db postgresql --host localhost --user scrapy_user --password your_password
"""

import argparse
import os
import sys
from pathlib import Path
import yaml

# ScrapyUIのルートディレクトリを取得
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATABASE_CONFIG_PATH = PROJECT_ROOT / "backend" / "config" / "database.yaml"
ENV_FILE_PATH = PROJECT_ROOT / "backend" / ".env"

def load_database_config():
    """現在のデータベース設定を読み込み"""
    try:
        with open(DATABASE_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ 設定ファイルが見つかりません: {DATABASE_CONFIG_PATH}")
        sys.exit(1)

def save_database_config(config):
    """データベース設定を保存"""
    try:
        with open(DATABASE_CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        print(f"✅ 設定ファイルを更新しました: {DATABASE_CONFIG_PATH}")
    except Exception as e:
        print(f"❌ 設定ファイルの保存に失敗しました: {e}")
        sys.exit(1)

def update_usedatabase_setting(config, target_env):
    """usedatabase設定を更新"""
    config['usedatabase'] = target_env
    print(f"✅ usedatabase設定を '{target_env}' に更新しました")

def create_env_file(db_type, **kwargs):
    """環境変数ファイルを作成"""
    env_content = f"""# ScrapyUI Environment Configuration
# データベース設定: {db_type.upper()}

SCRAPY_UI_ENV=production
DEBUG=false
SECRET_KEY=your-secret-key-here

"""

    if db_type == "sqlite":
        env_content += """# SQLite設定
DATABASE_TYPE=sqlite
DATABASE_NAME=backend/database/scrapy_ui.db
DATABASE_ECHO=false
"""
    elif db_type == "mysql":
        env_content += f"""# MySQL設定
DATABASE_TYPE=mysql
DATABASE_HOST={kwargs.get('host', 'localhost')}
DATABASE_PORT={kwargs.get('port', 3306)}
DATABASE_NAME={kwargs.get('database', 'scrapy_ui')}
DATABASE_USER={kwargs.get('user', 'scrapy_user')}
DATABASE_PASSWORD={kwargs.get('password', 'your_password')}
DATABASE_CHARSET=utf8mb4
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_ECHO=false
"""
    elif db_type == "postgresql":
        env_content += f"""# PostgreSQL設定
DATABASE_TYPE=postgresql
DATABASE_HOST={kwargs.get('host', 'localhost')}
DATABASE_PORT={kwargs.get('port', 5432)}
DATABASE_NAME={kwargs.get('database', 'scrapy_ui')}
DATABASE_USER={kwargs.get('user', 'scrapy_user')}
DATABASE_PASSWORD={kwargs.get('password', 'your_password')}
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_ECHO=false
"""

    env_content += """
# JWT設定
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Scrapy設定
SCRAPY_PROJECTS_DIR=./scrapy_projects
SCRAPY_LOGS_DIR=./logs
SCRAPY_RESULTS_DIR=./results

# セキュリティ設定
CORS_ORIGINS=http://localhost:4000,http://localhost:3001,http://localhost:3002
ALLOWED_HOSTS=localhost,127.0.0.1

# ログ設定
LOG_LEVEL=INFO
LOG_FILE=scrapy_ui.log
"""

    try:
        with open(ENV_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"✅ 環境変数ファイルを作成しました: {ENV_FILE_PATH}")
    except Exception as e:
        print(f"❌ 環境変数ファイルの作成に失敗しました: {e}")

def switch_to_sqlite():
    """SQLiteに切り替え"""
    print("🔄 SQLiteデータベースに切り替えています...")

    config = load_database_config()
    config['default'] = {
        'type': 'sqlite',
        'database': 'backend/database/scrapy_ui.db',
        'echo': False
    }

    # usedatabase設定も更新
    update_usedatabase_setting(config, 'default')

    save_database_config(config)
    create_env_file('sqlite')

    print("✅ SQLiteデータベースに切り替えました")
    print(f"📁 データベースファイル: {PROJECT_ROOT}/backend/database/scrapy_ui.db")

def switch_to_mysql(host, port, database, user, password):
    """MySQLに切り替え"""
    print("🔄 MySQLデータベースに切り替えています...")

    config = load_database_config()
    config['default'] = {
        'type': 'mysql',
        'host': host,
        'port': port,
        'database': database,
        'username': user,
        'password': password,
        'charset': 'utf8mb4',
        'echo': False,
        'pool_size': 10,
        'max_overflow': 20
    }

    # usedatabase設定も更新
    update_usedatabase_setting(config, 'default')

    save_database_config(config)
    create_env_file('mysql', host=host, port=port, database=database, user=user, password=password)

    print("✅ MySQLデータベースに切り替えました")
    print(f"🔗 接続先: mysql://{user}@{host}:{port}/{database}")

def switch_to_postgresql(host, port, database, user, password):
    """PostgreSQLに切り替え"""
    print("🔄 PostgreSQLデータベースに切り替えています...")

    config = load_database_config()
    config['default'] = {
        'type': 'postgresql',
        'host': host,
        'port': port,
        'database': database,
        'username': user,
        'password': password,
        'echo': False,
        'pool_size': 10,
        'max_overflow': 20
    }

    # usedatabase設定も更新
    update_usedatabase_setting(config, 'default')

    save_database_config(config)
    create_env_file('postgresql', host=host, port=port, database=database, user=user, password=password)

    print("✅ PostgreSQLデータベースに切り替えました")
    print(f"🔗 接続先: postgresql://{user}@{host}:{port}/{database}")

def main():
    parser = argparse.ArgumentParser(description='ScrapyUI データベース切り替えツール')
    parser.add_argument('--db', choices=['sqlite', 'mysql', 'postgresql'], required=True,
                       help='使用するデータベースタイプ')
    parser.add_argument('--host', default='localhost', help='データベースホスト')
    parser.add_argument('--port', type=int, help='データベースポート')
    parser.add_argument('--database', default='scrapy_ui', help='データベース名')
    parser.add_argument('--user', default='scrapy_user', help='データベースユーザー')
    parser.add_argument('--password', help='データベースパスワード')
    
    args = parser.parse_args()
    
    print(f"🎯 ScrapyUI データベース切り替えツール")
    print(f"📊 切り替え先: {args.db.upper()}")
    print("=" * 50)
    
    if args.db == 'sqlite':
        switch_to_sqlite()
    elif args.db == 'mysql':
        port = args.port or 3306
        password = args.password or input("MySQLパスワードを入力してください: ")
        switch_to_mysql(args.host, port, args.database, args.user, password)
    elif args.db == 'postgresql':
        port = args.port or 5432
        password = args.password or input("PostgreSQLパスワードを入力してください: ")
        switch_to_postgresql(args.host, port, args.database, args.user, password)
    
    print("\n🔄 変更を適用するには、ScrapyUIを再起動してください")
    print("   ./stop_servers.sh && ./start_servers.sh")

if __name__ == '__main__':
    main()
