"""
Scrapy設定検証サービス
settings.pyの設定値を検証し、最適化提案を行う
"""
import ast
import re
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


@dataclass
class ValidationResult:
    level: ValidationLevel
    message: str
    line_number: Optional[int] = None
    setting_name: Optional[str] = None
    suggestion: Optional[str] = None


class ScrapyConfigValidator:
    """Scrapy設定検証クラス"""
    
    def __init__(self):
        self.required_settings = {
            'BOT_NAME': str,
            'SPIDER_MODULES': list,
            'NEWSPIDER_MODULE': str,
        }
        
        self.recommended_settings = {
            'ROBOTSTXT_OBEY': bool,
            'DOWNLOAD_DELAY': (int, float),
            'CONCURRENT_REQUESTS': int,
            'CONCURRENT_REQUESTS_PER_DOMAIN': int,
        }
        
        self.playwright_settings = {
            'PLAYWRIGHT_BROWSER_TYPE': str,
            'DOWNLOAD_HANDLERS': dict,
            'TWISTED_REACTOR': str,
            'PLAYWRIGHT_LAUNCH_OPTIONS': dict,
            'PLAYWRIGHT_CONTEXTS': dict,
        }
        
        self.dangerous_settings = {
            'ROBOTSTXT_OBEY': False,  # robots.txtを無視するのは危険
            'DOWNLOAD_DELAY': 0,      # 遅延なしは危険
            'CONCURRENT_REQUESTS': lambda x: x > 32,  # 高すぎる並行リクエスト
        }
    
    def validate_settings_file(self, content: str) -> List[ValidationResult]:
        """settings.pyファイル全体を検証"""
        results = []
        
        try:
            # Python構文チェック
            tree = ast.parse(content)
            
            # 設定値を抽出
            settings = self._extract_settings(tree)
            
            # 各種検証を実行
            results.extend(self._validate_required_settings(settings))
            results.extend(self._validate_recommended_settings(settings))
            results.extend(self._validate_playwright_settings(settings))
            results.extend(self._validate_dangerous_settings(settings))
            results.extend(self._validate_setting_types(settings))
            results.extend(self._validate_performance_settings(settings))
            results.extend(self._validate_security_settings(settings))
            
        except SyntaxError as e:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Python構文エラー: {e.msg}",
                line_number=e.lineno
            ))
        
        return results
    
    def _extract_settings(self, tree: ast.AST) -> Dict[str, Any]:
        """ASTから設定値を抽出"""
        settings = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        setting_name = target.id
                        try:
                            # 設定値を評価（安全な値のみ）
                            if isinstance(node.value, (ast.Constant, ast.Str, ast.Num)):
                                settings[setting_name] = ast.literal_eval(node.value)
                            elif isinstance(node.value, (ast.List, ast.Dict, ast.Tuple)):
                                settings[setting_name] = ast.literal_eval(node.value)
                            elif isinstance(node.value, ast.NameConstant):
                                settings[setting_name] = node.value.value
                        except (ValueError, TypeError):
                            # 評価できない複雑な値はスキップ
                            pass
        
        return settings
    
    def _validate_required_settings(self, settings: Dict[str, Any]) -> List[ValidationResult]:
        """必須設定の検証"""
        results = []
        
        for setting_name, expected_type in self.required_settings.items():
            if setting_name not in settings:
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"必須設定 '{setting_name}' が見つかりません",
                    setting_name=setting_name,
                    suggestion=f"{setting_name} = '適切な値を設定してください'"
                ))
            elif not isinstance(settings[setting_name], expected_type):
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"'{setting_name}' の型が正しくありません。{expected_type.__name__}型である必要があります",
                    setting_name=setting_name
                ))
        
        return results
    
    def _validate_recommended_settings(self, settings: Dict[str, Any]) -> List[ValidationResult]:
        """推奨設定の検証"""
        results = []
        
        for setting_name, expected_type in self.recommended_settings.items():
            if setting_name not in settings:
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    message=f"推奨設定 '{setting_name}' が設定されていません",
                    setting_name=setting_name,
                    suggestion=self._get_default_suggestion(setting_name)
                ))
        
        return results
    
    def _validate_playwright_settings(self, settings: Dict[str, Any]) -> List[ValidationResult]:
        """Playwright設定の検証"""
        results = []
        
        # Playwrightが使用されているかチェック
        has_playwright = any(
            'playwright' in str(settings.get(key, '')).lower()
            for key in ['DOWNLOAD_HANDLERS', 'DOWNLOADER_MIDDLEWARES']
        )
        
        if has_playwright:
            for setting_name, expected_type in self.playwright_settings.items():
                if setting_name not in settings:
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        message=f"Playwright使用時は '{setting_name}' の設定を推奨します",
                        setting_name=setting_name,
                        suggestion=self._get_playwright_suggestion(setting_name)
                    ))
            
            # Twisted Reactorの確認
            if settings.get('TWISTED_REACTOR') != 'twisted.internet.asyncioreactor.AsyncioSelectorReactor':
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message="PlaywrightにはAsyncioSelectorReactorが必要です",
                    setting_name='TWISTED_REACTOR',
                    suggestion="TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'"
                ))
        
        return results
    
    def _validate_dangerous_settings(self, settings: Dict[str, Any]) -> List[ValidationResult]:
        """危険な設定の検証"""
        results = []
        
        for setting_name, dangerous_value in self.dangerous_settings.items():
            if setting_name in settings:
                current_value = settings[setting_name]
                
                if callable(dangerous_value):
                    if dangerous_value(current_value):
                        results.append(ValidationResult(
                            level=ValidationLevel.WARNING,
                            message=f"'{setting_name}' の値 ({current_value}) は推奨されません",
                            setting_name=setting_name,
                            suggestion=self._get_safe_suggestion(setting_name)
                        ))
                elif current_value == dangerous_value:
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        message=f"'{setting_name}' = {dangerous_value} は推奨されません",
                        setting_name=setting_name,
                        suggestion=self._get_safe_suggestion(setting_name)
                    ))
        
        return results
    
    def _validate_setting_types(self, settings: Dict[str, Any]) -> List[ValidationResult]:
        """設定値の型検証"""
        results = []
        
        type_checks = {
            'DOWNLOAD_DELAY': (int, float),
            'CONCURRENT_REQUESTS': int,
            'CONCURRENT_REQUESTS_PER_DOMAIN': int,
            'CONCURRENT_REQUESTS_PER_IP': int,
            'DOWNLOAD_TIMEOUT': (int, float),
            'RETRY_TIMES': int,
            'ROBOTSTXT_OBEY': bool,
        }
        
        for setting_name, expected_types in type_checks.items():
            if setting_name in settings:
                if not isinstance(settings[setting_name], expected_types):
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"'{setting_name}' の型が正しくありません",
                        setting_name=setting_name,
                        suggestion=f"適切な型: {expected_types}"
                    ))
        
        return results
    
    def _validate_performance_settings(self, settings: Dict[str, Any]) -> List[ValidationResult]:
        """パフォーマンス設定の検証"""
        results = []
        
        # 並行リクエスト数の確認
        concurrent_requests = settings.get('CONCURRENT_REQUESTS', 16)
        download_delay = settings.get('DOWNLOAD_DELAY', 0)
        
        if concurrent_requests > 32 and download_delay < 1:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="高い並行リクエスト数には適切な遅延設定を推奨します",
                suggestion="DOWNLOAD_DELAY = 1 以上を設定してください"
            ))
        
        # AutoThrottle設定の確認
        if not settings.get('AUTOTHROTTLE_ENABLED'):
            results.append(ValidationResult(
                level=ValidationLevel.INFO,
                message="AutoThrottleの使用を検討してください",
                suggestion="AUTOTHROTTLE_ENABLED = True"
            ))
        
        return results
    
    def _validate_security_settings(self, settings: Dict[str, Any]) -> List[ValidationResult]:
        """セキュリティ設定の検証"""
        results = []
        
        # robots.txt遵守の確認
        if not settings.get('ROBOTSTXT_OBEY', True):
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="robots.txtを無視する設定になっています",
                setting_name='ROBOTSTXT_OBEY',
                suggestion="ROBOTSTXT_OBEY = True を推奨します"
            ))
        
        # User-Agentの確認
        default_request_headers = settings.get('DEFAULT_REQUEST_HEADERS', {})
        if 'User-Agent' not in default_request_headers:
            results.append(ValidationResult(
                level=ValidationLevel.INFO,
                message="カスタムUser-Agentの設定を推奨します",
                suggestion="DEFAULT_REQUEST_HEADERS に User-Agent を追加してください"
            ))
        
        return results
    
    def _get_default_suggestion(self, setting_name: str) -> str:
        """デフォルト設定の提案"""
        suggestions = {
            'ROBOTSTXT_OBEY': 'ROBOTSTXT_OBEY = True',
            'DOWNLOAD_DELAY': 'DOWNLOAD_DELAY = 3',
            'CONCURRENT_REQUESTS': 'CONCURRENT_REQUESTS = 16',
            'CONCURRENT_REQUESTS_PER_DOMAIN': 'CONCURRENT_REQUESTS_PER_DOMAIN = 8',
        }
        return suggestions.get(setting_name, f"{setting_name} = '適切な値'")
    
    def _get_playwright_suggestion(self, setting_name: str) -> str:
        """Playwright設定の提案"""
        suggestions = {
            'PLAYWRIGHT_BROWSER_TYPE': "PLAYWRIGHT_BROWSER_TYPE = 'chromium'",
            'DOWNLOAD_HANDLERS': '''DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}''',
            'TWISTED_REACTOR': "TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'",
            'PLAYWRIGHT_LAUNCH_OPTIONS': '''PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "args": ["--no-sandbox", "--disable-setuid-sandbox"],
}''',
            'PLAYWRIGHT_CONTEXTS': '''PLAYWRIGHT_CONTEXTS = {
    "default": {
        "viewport": {"width": 1280, "height": 800},
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    },
}''',
        }
        return suggestions.get(setting_name, f"{setting_name} = '適切な値'")
    
    def _get_safe_suggestion(self, setting_name: str) -> str:
        """安全な設定の提案"""
        suggestions = {
            'ROBOTSTXT_OBEY': 'ROBOTSTXT_OBEY = True',
            'DOWNLOAD_DELAY': 'DOWNLOAD_DELAY = 1  # 最低1秒の遅延を推奨',
            'CONCURRENT_REQUESTS': 'CONCURRENT_REQUESTS = 16  # 適度な並行数',
        }
        return suggestions.get(setting_name, f"{setting_name} = '安全な値'")
    
    def generate_optimization_report(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """最適化レポートを生成"""
        report = {
            'performance_score': 0,
            'security_score': 0,
            'compatibility_score': 0,
            'recommendations': [],
            'summary': {}
        }
        
        # パフォーマンススコア計算
        performance_factors = [
            ('AUTOTHROTTLE_ENABLED', 20),
            ('DOWNLOAD_DELAY', 15),
            ('CONCURRENT_REQUESTS', 15),
            ('HTTPCACHE_ENABLED', 10),
        ]
        
        for setting, weight in performance_factors:
            if setting in settings:
                if setting == 'AUTOTHROTTLE_ENABLED' and settings[setting]:
                    report['performance_score'] += weight
                elif setting == 'DOWNLOAD_DELAY' and settings[setting] > 0:
                    report['performance_score'] += weight
                elif setting == 'CONCURRENT_REQUESTS' and 8 <= settings[setting] <= 32:
                    report['performance_score'] += weight
                elif setting == 'HTTPCACHE_ENABLED' and settings[setting]:
                    report['performance_score'] += weight
        
        # セキュリティスコア計算
        security_factors = [
            ('ROBOTSTXT_OBEY', 30),
            ('DEFAULT_REQUEST_HEADERS', 20),
            ('DOWNLOAD_DELAY', 15),
        ]
        
        for setting, weight in security_factors:
            if setting in settings:
                if setting == 'ROBOTSTXT_OBEY' and settings[setting]:
                    report['security_score'] += weight
                elif setting == 'DEFAULT_REQUEST_HEADERS' and 'User-Agent' in settings[setting]:
                    report['security_score'] += weight
                elif setting == 'DOWNLOAD_DELAY' and settings[setting] >= 1:
                    report['security_score'] += weight
        
        # 互換性スコア計算（Playwright対応）
        playwright_factors = [
            ('TWISTED_REACTOR', 25),
            ('DOWNLOAD_HANDLERS', 25),
            ('PLAYWRIGHT_BROWSER_TYPE', 15),
        ]
        
        for setting, weight in playwright_factors:
            if setting in settings:
                if setting == 'TWISTED_REACTOR' and 'asyncio' in str(settings[setting]):
                    report['compatibility_score'] += weight
                elif setting == 'DOWNLOAD_HANDLERS' and 'playwright' in str(settings[setting]):
                    report['compatibility_score'] += weight
                elif setting == 'PLAYWRIGHT_BROWSER_TYPE':
                    report['compatibility_score'] += weight
        
        # 推奨事項の生成
        if report['performance_score'] < 50:
            report['recommendations'].append("パフォーマンス設定の最適化を推奨します")
        if report['security_score'] < 50:
            report['recommendations'].append("セキュリティ設定の強化を推奨します")
        if report['compatibility_score'] < 50:
            report['recommendations'].append("Playwright互換性の向上を推奨します")
        
        return report
