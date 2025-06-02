"""
ScrapyUI コマンドライン引数設定

コマンドライン引数を解析し、設定を管理します。
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

class CLIConfigManager:
    """コマンドライン引数設定管理クラス"""
    
    def __init__(self):
        self.parser = self._create_parser()
        self.args: Optional[argparse.Namespace] = None
        self._parsed = False
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """コマンドライン引数パーサーを作成"""
        parser = argparse.ArgumentParser(
            prog='scrapyui',
            description='ScrapyUI - Web Scraping Management Interface',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用例:
  scrapyui                                    # デフォルト設定で起動
  scrapyui -c custom_database.yaml           # カスタム設定ファイルを使用
  scrapyui --database development             # development環境のDBを使用
  scrapyui --database mysql_prod --port 8080 # mysql_prod環境、ポート8080で起動
  scrapyui --host 0.0.0.0 --debug            # 全IPからアクセス可能、デバッグモード

環境変数:
  SCRAPY_UI_DATABASE=development              # 使用するデータベース環境
  SCRAPY_UI_CONFIG=./config/database.yaml    # 設定ファイルパス
  SCRAPY_UI_HOST=0.0.0.0                     # バインドホスト
  SCRAPY_UI_PORT=8000                        # バインドポート
            """
        )
        
        # 設定ファイル関連
        parser.add_argument(
            '-c', '--config',
            type=str,
            help='データベース設定ファイルのパス (デフォルト: backend/config/database.yaml)'
        )
        
        # データベース関連
        parser.add_argument(
            '--database', '--db',
            type=str,
            help='使用するデータベース環境 (例: default, development, production)'
        )
        
        # サーバー関連
        parser.add_argument(
            '--host',
            type=str,
            default='127.0.0.1',
            help='バインドするホストアドレス (デフォルト: 127.0.0.1)'
        )
        
        parser.add_argument(
            '--port', '-p',
            type=int,
            default=8000,
            help='バインドするポート番号 (デフォルト: 8000)'
        )
        
        # 動作モード
        parser.add_argument(
            '--debug',
            action='store_true',
            help='デバッグモードで起動'
        )
        
        parser.add_argument(
            '--reload',
            action='store_true',
            help='ファイル変更時の自動リロードを有効化'
        )
        
        # ログ関連
        parser.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default='INFO',
            help='ログレベル (デフォルト: INFO)'
        )

        parser.add_argument(
            '--log-file',
            type=str,
            help='ログファイルのパス'
        )

        # タイムゾーン関連
        parser.add_argument(
            '--timezone', '--tz',
            type=str,
            help='使用するタイムゾーン (例: Asia/Tokyo, UTC, America/New_York)'
        )
        
        # その他
        parser.add_argument(
            '--version', '-v',
            action='version',
            version='ScrapyUI 1.0.0'
        )
        
        parser.add_argument(
            '--check-config',
            action='store_true',
            help='設定を確認して終了'
        )
        
        return parser
    
    def parse_args(self, args: Optional[list] = None) -> argparse.Namespace:
        """コマンドライン引数を解析"""
        if not self._parsed:
            self.args = self.parser.parse_args(args)
            self._parsed = True
            
            # 環境変数での上書き
            self._apply_env_overrides()
            
            # データベース設定をグローバルに設定
            if self.args.database:
                from .database_config import get_database_config
                get_database_config._cli_database = self.args.database
        
        return self.args
    
    def _apply_env_overrides(self):
        """環境変数での設定上書き"""
        env_mappings = {
            'SCRAPY_UI_CONFIG': 'config',
            'SCRAPY_UI_DATABASE': 'database',
            'SCRAPY_UI_HOST': 'host',
            'SCRAPY_UI_PORT': 'port',
            'SCRAPY_UI_DEBUG': 'debug',
            'SCRAPY_UI_LOG_LEVEL': 'log_level',
            'SCRAPY_UI_LOG_FILE': 'log_file',
            'SCRAPY_UI_TIMEZONE': 'timezone',
        }
        
        for env_var, arg_name in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value and not getattr(self.args, arg_name, None):
                if arg_name == 'port':
                    setattr(self.args, arg_name, int(env_value))
                elif arg_name == 'debug':
                    setattr(self.args, arg_name, env_value.lower() in ('true', '1', 'yes', 'on'))
                else:
                    setattr(self.args, arg_name, env_value)
    
    def get_config_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で取得"""
        if not self._parsed:
            self.parse_args()
        
        return {
            'config_file': self.args.config,
            'database_env': self.args.database,
            'host': self.args.host,
            'port': self.args.port,
            'debug': self.args.debug,
            'reload': self.args.reload,
            'log_level': self.args.log_level,
            'log_file': self.args.log_file,
            'timezone': self.args.timezone,
            'check_config': self.args.check_config,
        }
    
    def print_config_summary(self):
        """設定サマリーを表示"""
        if not self._parsed:
            self.parse_args()
        
        print("🎯 ScrapyUI 設定サマリー")
        print("=" * 50)
        
        config = self.get_config_dict()
        
        print(f"📁 設定ファイル: {config['config_file'] or 'デフォルト'}")
        print(f"🗄️ データベース環境: {config['database_env'] or 'auto-detect'}")
        print(f"🌐 ホスト: {config['host']}")
        print(f"🔌 ポート: {config['port']}")
        print(f"🐛 デバッグモード: {'有効' if config['debug'] else '無効'}")
        print(f"🔄 自動リロード: {'有効' if config['reload'] else '無効'}")
        print(f"📝 ログレベル: {config['log_level']}")
        if config['log_file']:
            print(f"📄 ログファイル: {config['log_file']}")
        if config['timezone']:
            print(f"🌍 タイムゾーン: {config['timezone']}")
        else:
            print(f"🌍 タイムゾーン: auto-detect")

# グローバルインスタンス
cli_config_manager = CLIConfigManager()

def get_cli_config() -> Dict[str, Any]:
    """CLI設定を取得する便利関数"""
    return cli_config_manager.get_config_dict()

def parse_cli_args(args: Optional[list] = None) -> argparse.Namespace:
    """コマンドライン引数を解析する便利関数"""
    return cli_config_manager.parse_args(args)
