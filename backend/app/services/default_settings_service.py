"""
デフォルト設定サービス
JSONL形式と大容量データ処理に最適化されたデフォルト設定を提供
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json


class DefaultSettingsService:
    """デフォルト設定管理サービス"""
    
    def __init__(self):
        self.settings_file = Path("config/default_settings.json")
        self.settings_file.parent.mkdir(exist_ok=True)
        self.default_settings = self._load_default_settings()
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """デフォルト設定を読み込み"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading default settings: {e}")
        
        # デフォルト設定を作成
        return self._create_default_settings()
    
    def _create_default_settings(self) -> Dict[str, Any]:
        """デフォルト設定を作成"""
        settings = {
            "timezone": {
                "default": "Asia/Tokyo",
                "display_format": "%Y-%m-%d %H:%M:%S %Z",
                "available_timezones": [
                    "Asia/Tokyo",
                    "UTC",
                    "America/New_York",
                    "America/Los_Angeles",
                    "Europe/London",
                    "Europe/Paris",
                    "Asia/Shanghai",
                    "Asia/Seoul"
                ],
                "auto_detect": False
            },
            "auth": {
                "access_token_expire_minutes": 360,
                "refresh_token_expire_days": 7,
                "secret_key_env": "SECRET_KEY",
                "algorithm": "HS256",
                "password_hash_schemes": ["bcrypt", "argon2"],
                "bcrypt_rounds": 12,
                "session_timeout_minutes": 360,
                "auto_refresh_threshold_minutes": 30
            },
            "spider_defaults": {
                "feed_settings": {
                    "default_format": "jsonl",
                    "encoding": "utf-8",
                    "store_empty": False,
                    "item_export_kwargs": {
                        "ensure_ascii": False
                    },
                    "feeds": {
                        "results.jsonl": {
                            "format": "jsonl",
                            "encoding": "utf-8",
                            "store_empty": False,
                            "item_export_kwargs": {
                                "ensure_ascii": False
                            }
                        },
                        "results.json": {
                            "format": "json",
                            "encoding": "utf-8",
                            "store_empty": False,
                            "item_export_kwargs": {
                                "ensure_ascii": False
                            }
                        },
                        "results.csv": {
                            "format": "csv",
                            "encoding": "utf-8",
                            "store_empty": False,
                            "fields_to_export": None,
                            "csv_kwargs": {
                                "delimiter": ",",
                                "quotechar": "\"",
                                "quoting": "QUOTE_MINIMAL"
                            }
                        },
                        "results.xml": {
                            "format": "xml",
                            "encoding": "utf-8",
                            "store_empty": False,
                            "root_element": "items",
                            "item_element": "item"
                        },
                        "results.xlsx": {
                            "format": "xlsx",
                            "encoding": "utf-8",
                            "store_empty": False,
                            "sheet_name": "Results",
                            "excel_kwargs": {
                                "index": False,
                                "header": True
                            }
                        }
                    }
                },
                # Playwright設定は削除済み - 新アーキテクチャのPlaywright専用サービス（ポート8004）を使用
                "performance_settings": {
                    "concurrent_requests": 1,
                    "download_delay": 0.5,
                    "randomize_download_delay": True,
                    "autothrottle_enabled": True,
                    "autothrottle_start_delay": 1,
                    "autothrottle_max_delay": 60,
                    "autothrottle_target_concurrency": 1.0,
                    "autothrottle_debug": False
                },
                "memory_settings": {
                    # 新アーキテクチャ: 標準リアクターを使用（Playwright専用サービスと分離）
                    "reactor": "twisted.internet.selectreactor.SelectReactor",
                    "memusage_enabled": True,
                    "memusage_limit_mb": 2048,
                    "memusage_warning_mb": 1024
                },
                "error_handling": {
                    "retry_enabled": True,
                    "retry_times": 2,
                    "retry_http_codes": [500, 502, 503, 504, 408, 429],
                    "download_timeout": 180,
                    "robotstxt_obey": True
                }
            },
            "large_data_settings": {
                "streaming_enabled": True,
                "batch_size": 1000,
                "memory_limit_mb": 4096,
                "disk_cache_enabled": True,
                "compression_enabled": True
            },
            "export_settings": {
                "default_format": "jsonl",
                "supported_formats": ["jsonl", "json", "csv", "excel", "xml"],
                "max_export_items": 100000,
                "streaming_export": True
            }
        }
        
        # 設定ファイルに保存
        self._save_settings(settings)
        return settings
    
    def _save_settings(self, settings: Dict[str, Any]):
        """設定をファイルに保存"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_spider_default_settings(self, spider_type: str = "basic") -> Dict[str, Any]:
        """スパイダーのデフォルト設定を取得"""
        # デフォルト設定からfeed設定を取得
        feed_settings = self.default_settings["spider_defaults"]["feed_settings"]

        base_settings = {
            # TWISTED_REACTOR設定は削除済み - 新アーキテクチャでは標準リアクターを使用
            'FEED_EXPORT_ENCODING': feed_settings["encoding"],
            'FEEDS': feed_settings.get("feeds", {
                'results.jsonl': {
                    'format': 'jsonl',
                    'encoding': 'utf-8',
                    'store_empty': False,
                    'item_export_kwargs': {
                        'ensure_ascii': False
                    }
                },
                'results.json': {
                    'format': 'json',
                    'encoding': 'utf-8',
                    'store_empty': False,
                    'item_export_kwargs': {
                        'ensure_ascii': False
                    }
                },
                'results.csv': {
                    'format': 'csv',
                    'encoding': 'utf-8',
                    'store_empty': False
                },
                'results.xml': {
                    'format': 'xml',
                    'encoding': 'utf-8',
                    'store_empty': False
                },
                'results.xlsx': {
                    'format': 'xlsx',
                    'encoding': 'utf-8',
                    'store_empty': False
                }
            }),
            # Playwright設定は削除済み - 新アーキテクチャのPlaywright専用サービス（ポート8004）を使用
            'CONCURRENT_REQUESTS': self.default_settings["spider_defaults"]["performance_settings"]["concurrent_requests"],
            'DOWNLOAD_DELAY': self.default_settings["spider_defaults"]["performance_settings"]["download_delay"],
            'RANDOMIZE_DOWNLOAD_DELAY': self.default_settings["spider_defaults"]["performance_settings"]["randomize_download_delay"],
            'AUTOTHROTTLE_ENABLED': self.default_settings["spider_defaults"]["performance_settings"]["autothrottle_enabled"],
            'AUTOTHROTTLE_START_DELAY': self.default_settings["spider_defaults"]["performance_settings"]["autothrottle_start_delay"],
            'AUTOTHROTTLE_MAX_DELAY': self.default_settings["spider_defaults"]["performance_settings"]["autothrottle_max_delay"],
            'AUTOTHROTTLE_TARGET_CONCURRENCY': self.default_settings["spider_defaults"]["performance_settings"]["autothrottle_target_concurrency"],
            'RETRY_ENABLED': self.default_settings["spider_defaults"]["error_handling"]["retry_enabled"],
            'RETRY_TIMES': self.default_settings["spider_defaults"]["error_handling"]["retry_times"],
            'RETRY_HTTP_CODES': self.default_settings["spider_defaults"]["error_handling"]["retry_http_codes"],
            'DOWNLOAD_TIMEOUT': self.default_settings["spider_defaults"]["error_handling"]["download_timeout"],
            'ROBOTSTXT_OBEY': self.default_settings["spider_defaults"]["error_handling"]["robotstxt_obey"],
            'MEMUSAGE_ENABLED': self.default_settings["spider_defaults"]["memory_settings"]["memusage_enabled"],
            'MEMUSAGE_LIMIT_MB': self.default_settings["spider_defaults"]["memory_settings"]["memusage_limit_mb"],
            'MEMUSAGE_WARNING_MB': self.default_settings["spider_defaults"]["memory_settings"]["memusage_warning_mb"],
            'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # 標準Scrapy拡張機能のみ使用（Rich進捗バー拡張機能は無効化）
            'EXTENSIONS': {
                'scrapy.extensions.telnet.TelnetConsole': None,
                'scrapy.extensions.corestats.CoreStats': 500,
                'scrapy.extensions.memusage.MemoryUsage': 500,
                'scrapy.extensions.logstats.LogStats': 500,
                # Rich進捗バー拡張機能は削除済み - 軽量進捗システムを使用
            },
            # 軽量プログレスシステム設定
            'LIGHTWEIGHT_PROGRESS_WEBSOCKET': True,
            'LIGHTWEIGHT_BULK_INSERT': True
        }
        
        # スパイダータイプ別の設定
        if spider_type == "large_data":
            base_settings.update(self.get_large_data_settings())
        elif spider_type == "mobile":
            base_settings.update(self.get_mobile_settings())
        elif spider_type == "ecommerce":
            base_settings.update(self.get_ecommerce_settings())
        elif spider_type == "amazon-ranking60":
            base_settings.update(self.get_amazon_ranking60_settings())
        elif spider_type == "puppeteer":
            base_settings.update(self.get_puppeteer_settings())

        return base_settings
    
    def get_large_data_settings(self) -> Dict[str, Any]:
        """大容量データ処理用設定"""
        # デフォルト設定からfeed設定を取得
        feed_settings = self.default_settings["spider_defaults"]["feed_settings"]

        return {
            'CONCURRENT_REQUESTS': 2,
            'DOWNLOAD_DELAY': 1.0,
            'AUTOTHROTTLE_ENABLED': True,
            'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
            'MEMUSAGE_LIMIT_MB': self.default_settings["large_data_settings"]["memory_limit_mb"],
            'FEEDS': feed_settings.get("feeds", {
                'results.jsonl': {
                    'format': 'jsonl',
                    'encoding': 'utf-8',
                    'store_empty': False,
                    'item_export_kwargs': {
                        'ensure_ascii': False
                    }
                },
                'results.json': {
                    'format': 'json',
                    'encoding': 'utf-8',
                    'store_empty': False,
                    'item_export_kwargs': {
                        'ensure_ascii': False
                    }
                },
                'results.csv': {
                    'format': 'csv',
                    'encoding': 'utf-8',
                    'store_empty': False
                },
                'results.xml': {
                    'format': 'xml',
                    'encoding': 'utf-8',
                    'store_empty': False
                },
                'results.xlsx': {
                    'format': 'xlsx',
                    'encoding': 'utf-8',
                    'store_empty': False
                }
            })
        }
    
    def get_mobile_settings(self) -> Dict[str, Any]:
        """モバイル用設定（新アーキテクチャ対応）"""
        return {
            # Playwright設定は削除済み - 新アーキテクチャのPlaywright専用サービス（ポート8004）を使用
            # 'PLAYWRIGHT_CONTEXTS': {  # 削除済み
            #     'mobile': {
            #         'viewport': {'width': 375, 'height': 667},
            #         'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
            #         'is_mobile': True,
            #         'has_touch': True,
            #     }
            # },
            'USER_AGENT': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1'
        }
    
    def get_ecommerce_settings(self) -> Dict[str, Any]:
        """Eコマース用設定"""
        return {
            'DOWNLOAD_DELAY': 2.0,
            'RANDOMIZE_DOWNLOAD_DELAY': True,
            'AUTOTHROTTLE_ENABLED': True,
            'AUTOTHROTTLE_START_DELAY': 2,
            'AUTOTHROTTLE_MAX_DELAY': 10,
            'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'COOKIES_ENABLED': True,
            'SESSION_PERSISTENCE': True
        }

    def get_amazon_ranking60_settings(self) -> Dict[str, Any]:
        """AmazonRanking60スパイダー用設定"""
        return {
            'DOWNLOAD_DELAY': 3.0,
            'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
            'CONCURRENT_REQUESTS': 1,
            'DEPTH_LIMIT': 3,
            'AUTOTHROTTLE_ENABLED': False,  # 手動で制御
            'ROBOTSTXT_OBEY': True,
            'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'DEFAULT_REQUEST_HEADERS': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
            },
            # Playwright設定は削除済み - 新アーキテクチャのPlaywright専用サービス（ポート8004）を使用
            # 'PLAYWRIGHT_BROWSER_TYPE': 'chromium',  # 削除済み
            # 'PLAYWRIGHT_LAUNCH_OPTIONS': {  # 削除済み
            #     'headless': True,
            #     'timeout': 30000,
            # },
            # 'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 30000,  # 削除済み
            'FEEDS': {
                'ranking_results.jsonl': {
                    'format': 'jsonlines',
                    'encoding': 'utf8',
                    'store_empty': False,
                    'item_export_kwargs': {
                        'ensure_ascii': False,
                    },
                },
                'ranking_results.json': {
                    'format': 'json',
                    'encoding': 'utf8',
                    'store_empty': False,
                    'item_export_kwargs': {
                        'ensure_ascii': False,
                    },
                },
                'ranking_results.csv': {
                    'format': 'csv',
                    'encoding': 'utf8',
                    'store_empty': False,
                },
            }
        }

    def get_puppeteer_settings(self) -> Dict[str, Any]:
        """Node.js Puppeteer用設定"""
        return {
            'DOWNLOAD_DELAY': 2.0,
            'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
            'CONCURRENT_REQUESTS': 1,
            'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
            'AUTOTHROTTLE_ENABLED': True,
            'AUTOTHROTTLE_START_DELAY': 1,
            'AUTOTHROTTLE_MAX_DELAY': 10,
            'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
            'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'DEFAULT_REQUEST_HEADERS': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
            },
            # Puppeteer特有の設定
            'PUPPETEER_SERVICE_URL': 'http://localhost:3001',
            'PUPPETEER_TIMEOUT': 30000,
            'PUPPETEER_WAIT_FOR': 3000,
            'PUPPETEER_VIEWPORT': {'width': 1920, 'height': 1080},
            'PUPPETEER_HEADLESS': True,
            'FEEDS': {
                'puppeteer_results.jsonl': {
                    'format': 'jsonlines',
                    'encoding': 'utf8',
                    'store_empty': False,
                    'item_export_kwargs': {
                        'ensure_ascii': False,
                    },
                },
                'puppeteer_results.json': {
                    'format': 'json',
                    'encoding': 'utf8',
                    'store_empty': False,
                    'item_export_kwargs': {
                        'ensure_ascii': False,
                    },
                },
                'puppeteer_results.csv': {
                    'format': 'csv',
                    'encoding': 'utf8',
                    'store_empty': False,
                },
            }
        }

    def get_export_settings(self) -> Dict[str, Any]:
        """エクスポート設定を取得"""
        return self.default_settings["export_settings"]

    def get_timezone_settings(self) -> Dict[str, Any]:
        """タイムゾーン設定を取得"""
        return self.default_settings.get("timezone", {
            "default": "Asia/Tokyo",
            "display_format": "%Y-%m-%d %H:%M:%S %Z",
            "available_timezones": [
                "Asia/Tokyo",
                "UTC",
                "America/New_York",
                "America/Los_Angeles",
                "Europe/London",
                "Europe/Paris",
                "Asia/Shanghai",
                "Asia/Seoul"
            ],
            "auto_detect": False
        })

    def get_auth_settings(self) -> Dict[str, Any]:
        """認証設定を取得"""
        return self.default_settings.get("auth", {
            "access_token_expire_minutes": 360,
            "refresh_token_expire_days": 7,
            "secret_key_env": "SECRET_KEY",
            "algorithm": "HS256",
            "password_hash_schemes": ["bcrypt", "argon2"],
            "bcrypt_rounds": 12,
            "session_timeout_minutes": 360,
            "auto_refresh_threshold_minutes": 30
        })
    
    def update_settings(self, section: str, new_settings: Dict[str, Any]):
        """設定を更新"""
        if section in self.default_settings:
            self.default_settings[section].update(new_settings)
            self._save_settings(self.default_settings)
    
    def reset_to_defaults(self):
        """設定をデフォルトにリセット"""
        self.default_settings = self._create_default_settings()


# サービスインスタンス
default_settings_service = DefaultSettingsService()
