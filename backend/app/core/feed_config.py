"""
統一FEED設定管理クラス
FeedExporterエラーの根本対応として、すべてのFEED設定を一元管理
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class FeedConfigManager:
    """FEED設定の一元管理クラス"""
    
    # 基本FEED設定テンプレート（indentパラメータを除外）
    BASE_FEED_CONFIGS = {
        'jsonl': {
            'format': 'jsonlines',
            'encoding': 'utf-8',
            'store_empty': False,
            'item_export_kwargs': {
                'ensure_ascii': False
            }
        },
        'json': {
            'format': 'json',
            'encoding': 'utf-8',
            'store_empty': False,
            'item_export_kwargs': {
                'ensure_ascii': False
                # indentパラメータは意図的に除外（競合回避）
            }
        },
        'csv': {
            'format': 'csv',
            'encoding': 'utf-8',
            'store_empty': False
        },
        'xml': {
            'format': 'xml',
            'encoding': 'utf-8',
            'store_empty': False,
            'root_element': 'items',
            'item_element': 'item'
        },
        # XLSX形式は標準Scrapyでサポートされていないため除外
        # 'xlsx': {
        #     'format': 'xlsx',
        #     'encoding': 'utf-8',
        #     'store_empty': False,
        #     'sheet_name': 'Results',
        #     'excel_kwargs': {
        #         'index': False,
        #         'header': True
        #     }
        # }
    }
    
    @classmethod
    def get_standard_feeds(cls, prefix: str = 'results') -> Dict[str, Any]:
        """標準FEED設定を取得"""
        feeds = {}
        
        for format_name, config in cls.BASE_FEED_CONFIGS.items():
            filename = f"{prefix}.{format_name}"
            feeds[filename] = config.copy()
            
        logger.debug(f"Generated standard feeds with prefix '{prefix}': {list(feeds.keys())}")
        return feeds
    
    @classmethod
    def get_spider_feeds(cls, spider_type: str = 'default') -> Dict[str, Any]:
        """スパイダータイプ別のFEED設定を取得"""
        prefix_map = {
            'amazon_ranking': 'ranking_results',
            'puppeteer': 'puppeteer_results',
            'default': 'results'
        }
        
        prefix = prefix_map.get(spider_type, 'results')
        return cls.get_standard_feeds(prefix)
    
    @classmethod
    def get_safe_json_config(cls) -> Dict[str, Any]:
        """安全なJSON設定を取得（indentパラメータなし）"""
        config = cls.BASE_FEED_CONFIGS['json'].copy()
        
        # indentパラメータが存在する場合は削除
        if 'item_export_kwargs' in config:
            config['item_export_kwargs'].pop('indent', None)
            
        return config
    
    @classmethod
    def validate_feed_config(cls, config: Dict[str, Any]) -> tuple[bool, list[str]]:
        """FEED設定の妥当性を検証"""
        errors = []
        
        for filename, feed_config in config.items():
            # 必須フィールドの確認
            if 'format' not in feed_config:
                errors.append(f"Missing 'format' in feed config for {filename}")
                
            if 'encoding' not in feed_config:
                errors.append(f"Missing 'encoding' in feed config for {filename}")
            
            # indentパラメータの競合チェック
            if feed_config.get('format') == 'json':
                item_kwargs = feed_config.get('item_export_kwargs', {})
                if 'indent' in item_kwargs:
                    errors.append(f"Found 'indent' parameter in {filename} - this may cause conflicts")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    @classmethod
    def create_project_feed_settings(cls, project_name: str) -> str:
        """プロジェクト用のFEED設定文字列を生成"""
        feeds = cls.get_standard_feeds()
        
        settings_str = '''
# ===== FEED設定 =====
# 統一FEED設定管理による安全な設定
FEEDS = {'''
        
        for filename, config in feeds.items():
            settings_str += f'''
    '{filename}': {config},'''
        
        settings_str += '''
}

# Feed export encoding
FEED_EXPORT_ENCODING = 'utf-8'
'''
        
        return settings_str


# グローバルインスタンス
feed_config = FeedConfigManager()
