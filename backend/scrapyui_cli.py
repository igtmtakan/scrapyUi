#!/usr/bin/env python3
"""
ScrapyUI コマンドラインインターフェース

使用方法:
  python scrapyui_cli.py
  python scrapyui_cli.py -c custom_database.yaml --database development
  python scrapyui_cli.py --host 0.0.0.0 --port 8080 --debug
"""

import sys
import os
from pathlib import Path

# ScrapyUIのパスを追加
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """メイン関数"""
    try:
        from app.config.cli_config import cli_config_manager
        from app.config.database_config import db_config_manager, get_database_config
        
        # コマンドライン引数を解析
        args = cli_config_manager.parse_args()
        
        # カスタム設定ファイルが指定された場合
        if args.config:
            config_path = Path(args.config)
            if not config_path.exists():
                print(f"❌ 設定ファイルが見つかりません: {config_path}")
                sys.exit(1)
            
            # 新しい設定ファイルでマネージャーを再初期化
            from app.config.database_config import DatabaseConfigManager
            global db_config_manager
            db_config_manager = DatabaseConfigManager(str(config_path))
        
        # 設定確認モード
        if args.check_config:
            check_configuration(args)
            return
        
        # 設定サマリーを表示
        cli_config_manager.print_config_summary()

        # タイムゾーン設定
        if args.timezone:
            try:
                from app.services.timezone_service import timezone_service
                success = timezone_service.set_timezone(args.timezone)
                if success:
                    print(f"\n✅ タイムゾーンを {args.timezone} に設定しました")
                else:
                    print(f"❌ タイムゾーンの設定に失敗: {args.timezone}")
                    sys.exit(1)
            except Exception as e:
                print(f"❌ タイムゾーン設定エラー: {e}")
                sys.exit(1)

        # データベース設定を確認
        try:
            db_config = get_database_config()
            print(f"\n✅ データベース設定:")
            print(f"   タイプ: {db_config.type.value}")
            if db_config.type.value == 'sqlite':
                print(f"   ファイル: {db_config.database}")
            else:
                print(f"   接続先: {db_config.username}@{db_config.host}:{db_config.port}/{db_config.database}")
        except Exception as e:
            print(f"❌ データベース設定エラー: {e}")
            sys.exit(1)
        
        # FastAPIサーバーを起動
        start_server(args)
        
    except KeyboardInterrupt:
        print("\n🛑 ScrapyUIを停止しています...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        sys.exit(1)

def check_configuration(args):
    """設定確認モード"""
    print("🔍 ScrapyUI 設定確認モード")
    print("=" * 60)

    # CLI設定
    from app.config.cli_config import cli_config_manager
    cli_config_manager.print_config_summary()
    
    # データベース設定
    try:
        from app.config.database_config import get_database_config, db_config_manager
        
        print(f"\n🗄️ データベース設定詳細:")
        print(f"   設定ファイル: {db_config_manager.config_file}")
        print(f"   デフォルト環境: {db_config_manager.default_database}")
        
        # 利用可能な環境を表示
        print(f"\n🌍 利用可能なデータベース環境:")
        for env_name, config in db_config_manager.configs.items():
            status = "🟢 選択中" if env_name == db_config_manager.default_database else "⚪ 利用可能"
            print(f"   {status} {env_name}: {config.type.value}")
            if config.type.value == 'sqlite':
                print(f"      📁 {config.database}")
                print(f"      📂 存在: {os.path.exists(config.database)}")
            else:
                print(f"      🌐 {config.username}@{config.host}:{config.port}/{config.database}")
        
        # 現在の設定をテスト
        current_config = get_database_config()
        print(f"\n🔗 現在の設定でのデータベース接続テスト:")
        test_database_connection(current_config)
        
    except Exception as e:
        print(f"❌ データベース設定確認エラー: {e}")
    
    print(f"\n💡 使用方法:")
    print(f"   python scrapyui_cli.py --database development  # development環境を使用")
    print(f"   python scrapyui_cli.py -c custom.yaml          # カスタム設定ファイルを使用")
    print(f"   SCRAPY_UI_DATABASE=production python scrapyui_cli.py  # 環境変数で指定")

def test_database_connection(config):
    """データベース接続テスト"""
    try:
        if config.type.value == 'sqlite':
            import sqlite3
            if config.database == ":memory:":
                print("   ✅ インメモリデータベース（テスト用）")
                return
            
            if not os.path.exists(config.database):
                print(f"   ⚠️ データベースファイルが存在しません: {config.database}")
                return
            
            conn = sqlite3.connect(config.database)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            conn.close()
            
            print(f"   ✅ SQLite接続成功 (テーブル数: {table_count})")
            
        else:
            from sqlalchemy import create_engine
            connection_url = config.get_connection_url()
            engine = create_engine(connection_url, echo=False)
            
            with engine.connect() as conn:
                if config.type.value == 'mysql':
                    result = conn.execute("SELECT VERSION()")
                elif config.type.value == 'postgresql':
                    result = conn.execute("SELECT version()")
                
                version = result.fetchone()[0]
                print(f"   ✅ {config.type.value.upper()}接続成功")
                
    except Exception as e:
        print(f"   ❌ 接続エラー: {e}")

def start_server(args):
    """FastAPIサーバーを起動"""
    try:
        import uvicorn
        from app.main import app
        
        print(f"\n🚀 ScrapyUIサーバーを起動しています...")
        print(f"   URL: http://{args.host}:{args.port}")
        print(f"   停止: Ctrl+C")
        print("=" * 50)
        
        # Uvicornでサーバーを起動
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level.lower(),
            access_log=True
        )
        
    except ImportError:
        print("❌ uvicornがインストールされていません")
        print("   pip install uvicorn でインストールしてください")
        sys.exit(1)
    except Exception as e:
        print(f"❌ サーバー起動エラー: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
