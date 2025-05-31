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
            "spider_defaults": {
                "feed_settings": {
                    "format": "jsonl",
                    "encoding": "utf-8",
                    "store_empty": False,
                    "item_export_kwargs": {
                        "ensure_ascii": False
                    }
                },
                "playwright_settings": {
                    "browser_type": "chromium",
                    "launch_options": {
                        "headless": True,
                        "args": ["--no-sandbox", "--disable-dev-shm-usage"]
                    },
                    "navigation_timeout": 10000,
                    "page_timeout": 30000
                },
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
                    "reactor": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
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
        base_settings = {
            'TWISTED_REACTOR': self.default_settings["spider_defaults"]["memory_settings"]["reactor"],
            'FEED_EXPORT_ENCODING': 'utf-8',
            'FEEDS': {
                'results.jsonl': {
                    'format': self.default_settings["spider_defaults"]["feed_settings"]["format"],
                    'encoding': self.default_settings["spider_defaults"]["feed_settings"]["encoding"],
                    'store_empty': self.default_settings["spider_defaults"]["feed_settings"]["store_empty"],
                    'item_export_kwargs': self.default_settings["spider_defaults"]["feed_settings"]["item_export_kwargs"]
                }
            },
            'PLAYWRIGHT_BROWSER_TYPE': self.default_settings["spider_defaults"]["playwright_settings"]["browser_type"],
            'PLAYWRIGHT_LAUNCH_OPTIONS': self.default_settings["spider_defaults"]["playwright_settings"]["launch_options"],
            'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': self.default_settings["spider_defaults"]["playwright_settings"]["navigation_timeout"],
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
            'MEMUSAGE_WARNING_MB': self.default_settings["spider_defaults"]["memory_settings"]["memusage_warning_mb"]
        }
        
        # スパイダータイプ別の設定
        if spider_type == "large_data":
            base_settings.update(self.get_large_data_settings())
        elif spider_type == "mobile":
            base_settings.update(self.get_mobile_settings())
        elif spider_type == "ecommerce":
            base_settings.update(self.get_ecommerce_settings())
        
        return base_settings
    
    def get_large_data_settings(self) -> Dict[str, Any]:
        """大容量データ処理用設定"""
        return {
            'CONCURRENT_REQUESTS': 2,
            'DOWNLOAD_DELAY': 1.0,
            'AUTOTHROTTLE_ENABLED': True,
            'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
            'MEMUSAGE_LIMIT_MB': self.default_settings["large_data_settings"]["memory_limit_mb"],
            'FEEDS': {
                'results.jsonl': {
                    'format': 'jsonl',
                    'encoding': 'utf8',
                    'store_empty': False,
                    'item_export_kwargs': {
                        'ensure_ascii': False
                    }
                }
            }
        }
    
    def get_mobile_settings(self) -> Dict[str, Any]:
        """モバイル用設定"""
        return {
            'PLAYWRIGHT_CONTEXTS': {
                'mobile': {
                    'viewport': {'width': 375, 'height': 667},
                    'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
                    'is_mobile': True,
                    'has_touch': True,
                }
            },
            'USER_AGENT': 'ScrapyUI Mobile Spider 1.0'
        }
    
    def get_ecommerce_settings(self) -> Dict[str, Any]:
        """Eコマース用設定"""
        return {
            'DOWNLOAD_DELAY': 2.0,
            'RANDOMIZE_DOWNLOAD_DELAY': True,
            'AUTOTHROTTLE_ENABLED': True,
            'AUTOTHROTTLE_START_DELAY': 2,
            'AUTOTHROTTLE_MAX_DELAY': 10,
            'USER_AGENT': 'ScrapyUI E-commerce Spider 1.0',
            'COOKIES_ENABLED': True,
            'SESSION_PERSISTENCE': True
        }
    
    def get_export_settings(self) -> Dict[str, Any]:
        """エクスポート設定を取得"""
        return self.default_settings["export_settings"]
    
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
