import os
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

class DatabaseType(Enum):
    """サポートするデータベースタイプ"""
    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    ELASTICSEARCH = "elasticsearch"
    REDIS = "redis"

@dataclass
class DatabaseConfig:
    """データベース設定クラス"""
    type: DatabaseType
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    charset: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

    # MongoDB/Elasticsearch固有
    hosts: Optional[list] = None
    index_prefix: Optional[str] = None

    def get_connection_url(self) -> str:
        """データベース接続URLを生成"""
        if self.type == DatabaseType.SQLITE:
            return f"sqlite:///{self.database}"

        elif self.type == DatabaseType.MYSQL:
            charset_param = f"?charset={self.charset}" if self.charset else ""
            return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}{charset_param}"

        elif self.type == DatabaseType.POSTGRESQL:
            return f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

        else:
            raise ValueError(f"Unsupported database type for SQLAlchemy: {self.type}")

    def get_mongodb_url(self) -> str:
        """MongoDB接続URLを生成"""
        if self.type != DatabaseType.MONGODB:
            raise ValueError("This method is only for MongoDB")

        auth_part = f"{self.username}:{self.password}@" if self.username and self.password else ""
        return f"mongodb://{auth_part}{self.host}:{self.port}/{self.database}"

    def get_elasticsearch_config(self) -> Dict[str, Any]:
        """Elasticsearch設定を生成"""
        if self.type != DatabaseType.ELASTICSEARCH:
            raise ValueError("This method is only for Elasticsearch")

        config = {
            "hosts": self.hosts or [f"http://{self.host}:{self.port}"],
            "index_prefix": self.index_prefix or "scrapy_ui"
        }

        if self.options:
            config.update(self.options)

        return config

    def get_redis_config(self) -> Dict[str, Any]:
        """Redis設定を生成"""
        if self.type != DatabaseType.REDIS:
            raise ValueError("This method is only for Redis")

        config = {
            "host": self.host,
            "port": self.port,
            "db": self.database or 0,
            "password": self.password
        }

        if self.options:
            config.update(self.options)

        return config

class DatabaseConfigManager:
    """データベース設定管理クラス"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_file()
        self.configs: Dict[str, DatabaseConfig] = {}
        self.default_database = "default"  # デフォルトで使用するデータベース環境
        self.load_config()

    def _get_default_config_file(self) -> str:
        """デフォルト設定ファイルパスを取得"""
        current_dir = Path(__file__).parent.parent.parent
        return str(current_dir / "config" / "database.yaml")

    def load_config(self) -> None:
        """設定ファイルを読み込み"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            # usedatabase設定を読み込み
            if 'usedatabase' in config_data:
                self.default_database = config_data['usedatabase']

            for env_name, config in config_data.items():
                if isinstance(config, dict) and 'type' in config:
                    self.configs[env_name] = self._parse_config(config)

        except FileNotFoundError:
            # デフォルト設定を使用 - backend/database/ディレクトリ内に配置
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = str(project_root / "backend" / "database" / "scrapy_ui.db")
            self.configs['default'] = DatabaseConfig(
                type=DatabaseType.SQLITE,
                database=db_path
            )
        except Exception as e:
            raise Exception(f"Failed to load database config: {str(e)}")

    def _parse_config(self, config: Dict[str, Any]) -> DatabaseConfig:
        """設定辞書をDatabaseConfigオブジェクトに変換"""
        db_type = DatabaseType(config['type'])

        # SQLiteの場合、相対パスを絶対パスに変換
        database_path = config.get('database')
        if db_type == DatabaseType.SQLITE and database_path and database_path != ":memory:":
            if not os.path.isabs(database_path):
                # ScrapyUIプロジェクトルートからの相対パス
                project_root = Path(__file__).parent.parent.parent.parent
                database_path = str(project_root / database_path)

        return DatabaseConfig(
            type=db_type,
            host=config.get('host'),
            port=config.get('port'),
            database=database_path,
            username=config.get('username'),
            password=config.get('password'),
            echo=config.get('echo', False),
            pool_size=config.get('pool_size', 5),
            max_overflow=config.get('max_overflow', 10),
            charset=config.get('charset'),
            options=config.get('options'),
            hosts=config.get('hosts'),
            index_prefix=config.get('index_prefix')
        )

    def get_config(self, environment: Optional[str] = None) -> DatabaseConfig:
        """指定環境の設定を取得"""
        # 環境変数から環境名を取得
        env = environment or os.getenv('SCRAPY_UI_ENV', 'default')

        # 環境変数での設定上書きをチェック
        config = self._get_config_with_env_override(env)

        return config

    def _get_config_with_env_override(self, environment: str) -> DatabaseConfig:
        """環境変数での設定上書きを適用"""
        # ベース設定を取得
        base_config = self.configs.get(environment, self.configs.get('default'))
        if not base_config:
            raise ValueError(f"No configuration found for environment: {environment}")

        # 環境変数での上書き
        env_database = os.getenv('DATABASE_NAME') or os.getenv('DATABASE_DB')
        # SQLiteの場合、相対パスを絶対パスに変換
        if env_database and base_config.type == DatabaseType.SQLITE and not os.path.isabs(env_database):
            # ScrapyUIプロジェクトルートからの相対パス
            project_root = Path(__file__).parent.parent.parent.parent
            env_database = str(project_root / env_database)

        env_overrides = {
            'type': os.getenv('DATABASE_TYPE'),
            'host': os.getenv('DATABASE_HOST'),
            'port': self._get_env_int('DATABASE_PORT'),
            'database': env_database,
            'username': os.getenv('DATABASE_USER') or os.getenv('DATABASE_USERNAME'),
            'password': os.getenv('DATABASE_PASSWORD') or os.getenv('DATABASE_PASS'),
            'echo': self._get_env_bool('DATABASE_ECHO'),
            'pool_size': self._get_env_int('DATABASE_POOL_SIZE'),
            'max_overflow': self._get_env_int('DATABASE_MAX_OVERFLOW'),
            'charset': os.getenv('DATABASE_CHARSET')
        }

        # None以外の値のみ適用
        for key, value in env_overrides.items():
            if value is not None:
                if key == 'type':
                    setattr(base_config, key, DatabaseType(value))
                else:
                    setattr(base_config, key, value)

        return base_config

    def _get_env_int(self, key: str) -> Optional[int]:
        """環境変数から整数値を取得"""
        value = os.getenv(key)
        return int(value) if value and value.isdigit() else None

    def _get_env_bool(self, key: str) -> Optional[bool]:
        """環境変数からブール値を取得"""
        value = os.getenv(key)
        if value is None:
            return None
        return value.lower() in ('true', '1', 'yes', 'on')

    def get_all_configs(self) -> Dict[str, DatabaseConfig]:
        """全設定を取得"""
        return self.configs.copy()

    def validate_config(self, config: DatabaseConfig) -> bool:
        """設定の妥当性をチェック"""
        if config.type in [DatabaseType.MYSQL, DatabaseType.POSTGRESQL]:
            required_fields = ['host', 'port', 'database', 'username', 'password']
            for field in required_fields:
                if not getattr(config, field):
                    raise ValueError(f"Missing required field for {config.type.value}: {field}")

        elif config.type == DatabaseType.SQLITE:
            if not config.database:
                raise ValueError("SQLite requires database file path")

        elif config.type == DatabaseType.MONGODB:
            required_fields = ['host', 'port', 'database']
            for field in required_fields:
                if not getattr(config, field):
                    raise ValueError(f"Missing required field for MongoDB: {field}")

        elif config.type == DatabaseType.ELASTICSEARCH:
            if not (config.hosts or (config.host and config.port)):
                raise ValueError("Elasticsearch requires hosts or host/port")

        elif config.type == DatabaseType.REDIS:
            if not config.host:
                raise ValueError("Redis requires host")

        return True

# グローバル設定マネージャーインスタンス
db_config_manager = DatabaseConfigManager()

def get_database_config(environment: Optional[str] = None) -> DatabaseConfig:
    """データベース設定を取得

    Args:
        environment: 使用する環境名。Noneの場合は以下の優先順位で決定:
                    1. 環境変数 SCRAPY_UI_DATABASE
                    2. コマンドライン引数 --database
                    3. database.yamlのusedatabase設定
                    4. "default"
    """
    if environment is None:
        # 環境変数から取得
        environment = os.getenv('SCRAPY_UI_DATABASE')

        # コマンドライン引数から取得（後で実装）
        if environment is None:
            environment = getattr(get_database_config, '_cli_database', None)

        # database.yamlのusedatabase設定から取得
        if environment is None:
            environment = db_config_manager.default_database

        # 最終的なフォールバック
        if environment is None:
            environment = "default"

    return db_config_manager.get_config(environment)
