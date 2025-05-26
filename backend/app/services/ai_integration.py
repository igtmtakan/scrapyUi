"""
AI統合サービス
コード生成、最適化提案、バグ検出
"""
import re
import ast
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import openai
from dataclasses import dataclass
import requests
from pathlib import Path


@dataclass
class CodeSuggestion:
    """コード提案"""
    type: str  # 'spider', 'middleware', 'pipeline', 'optimization'
    title: str
    description: str
    code: str
    confidence: float
    reasoning: str
    tags: List[str]


@dataclass
class BugReport:
    """バグレポート"""
    severity: str  # 'low', 'medium', 'high', 'critical'
    category: str  # 'syntax', 'logic', 'performance', 'security'
    line_number: Optional[int]
    description: str
    suggestion: str
    code_snippet: str


class AICodeAnalyzer:
    """AIコード分析クラス"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        if api_key:
            openai.api_key = api_key
        
        # ローカルAI分析ルール
        self.analysis_rules = self._load_analysis_rules()
    
    def _load_analysis_rules(self) -> Dict[str, Any]:
        """分析ルールを読み込み"""
        return {
            'performance_patterns': [
                {
                    'pattern': r'time\.sleep\(\d+\)',
                    'severity': 'medium',
                    'message': 'time.sleep()の代わりにScrapyのDOWNLOAD_DELAYを使用してください',
                    'suggestion': 'custom_settings = {"DOWNLOAD_DELAY": 1}'
                },
                {
                    'pattern': r'requests\.get\(',
                    'severity': 'high',
                    'message': 'requestsライブラリの代わりにScrapyのRequestを使用してください',
                    'suggestion': 'yield scrapy.Request(url, callback=self.parse)'
                }
            ],
            'security_patterns': [
                {
                    'pattern': r'eval\(',
                    'severity': 'critical',
                    'message': 'eval()の使用は危険です',
                    'suggestion': 'ast.literal_eval()を使用してください'
                },
                {
                    'pattern': r'exec\(',
                    'severity': 'critical',
                    'message': 'exec()の使用は危険です',
                    'suggestion': '動的コード実行を避けてください'
                }
            ],
            'scrapy_best_practices': [
                {
                    'pattern': r'def parse\(self, response\):(?!.*yield)',
                    'severity': 'medium',
                    'message': 'parseメソッドでyieldを使用していません',
                    'suggestion': 'アイテムやリクエストをyieldしてください'
                }
            ]
        }
    
    def generate_spider_code(self, requirements: Dict[str, Any]) -> CodeSuggestion:
        """スパイダーコードを生成"""
        spider_name = requirements.get('spider_name', 'example_spider')
        target_url = requirements.get('target_url', 'https://example.com')
        data_fields = requirements.get('data_fields', ['title', 'description'])
        
        # ローカルテンプレートベースの生成
        code = self._generate_spider_template(spider_name, target_url, data_fields)
        
        # AIによる改善（API利用可能な場合）
        if self.api_key:
            enhanced_code = self._enhance_with_ai(code, requirements)
            if enhanced_code:
                code = enhanced_code
        
        return CodeSuggestion(
            type='spider',
            title=f'{spider_name.capitalize()} Spider',
            description=f'{target_url}をスクレイピングするスパイダー',
            code=code,
            confidence=0.85,
            reasoning='テンプレートベースの生成とベストプラクティスの適用',
            tags=['scrapy', 'playwright', 'generated']
        )
    
    def analyze_code_quality(self, code: str, file_type: str = 'spider') -> List[BugReport]:
        """コード品質を分析"""
        bugs = []
        
        # 構文チェック
        syntax_bugs = self._check_syntax(code)
        bugs.extend(syntax_bugs)
        
        # パターンマッチング分析
        pattern_bugs = self._analyze_patterns(code)
        bugs.extend(pattern_bugs)
        
        # Scrapy固有の分析
        if file_type == 'spider':
            scrapy_bugs = self._analyze_scrapy_code(code)
            bugs.extend(scrapy_bugs)
        
        # AIによる高度な分析（API利用可能な場合）
        if self.api_key:
            ai_bugs = self._ai_code_analysis(code)
            bugs.extend(ai_bugs)
        
        return bugs
    
    def suggest_optimizations(self, code: str, performance_data: Dict[str, Any] = None) -> List[CodeSuggestion]:
        """最適化提案を生成"""
        suggestions = []
        
        # パフォーマンスデータに基づく提案
        if performance_data:
            perf_suggestions = self._analyze_performance_data(performance_data)
            suggestions.extend(perf_suggestions)
        
        # コード分析に基づく提案
        code_suggestions = self._analyze_code_for_optimization(code)
        suggestions.extend(code_suggestions)
        
        return suggestions
    
    def generate_middleware_code(self, middleware_type: str, requirements: Dict[str, Any]) -> CodeSuggestion:
        """ミドルウェアコードを生成"""
        templates = {
            'user_agent': self._generate_user_agent_middleware,
            'proxy': self._generate_proxy_middleware,
            'rate_limit': self._generate_rate_limit_middleware,
            'retry': self._generate_retry_middleware
        }
        
        if middleware_type in templates:
            code = templates[middleware_type](requirements)
            
            return CodeSuggestion(
                type='middleware',
                title=f'{middleware_type.replace("_", " ").title()} Middleware',
                description=f'{middleware_type}機能を提供するミドルウェア',
                code=code,
                confidence=0.9,
                reasoning='テンプレートベースの生成',
                tags=['middleware', middleware_type]
            )
        
        return None
    
    def _generate_spider_template(self, spider_name: str, target_url: str, data_fields: List[str]) -> str:
        """スパイダーテンプレートを生成"""
        fields_code = '\n        '.join([
            f"item['{field}'] = response.css('#{field}::text').get()"
            for field in data_fields
        ])
        
        return f'''import scrapy
from scrapy_playwright.page import PageCoroutine


class {spider_name.capitalize()}Spider(scrapy.Spider):
    name = '{spider_name}'
    allowed_domains = ['{self._extract_domain(target_url)}']
    start_urls = ['{target_url}']

    custom_settings = {{
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "DOWNLOAD_HANDLERS": {{
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        }},
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS": 8,
    }}

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={{
                    "playwright": True,
                    "playwright_page_coroutines": [
                        PageCoroutine("wait_for_selector", "body"),
                        PageCoroutine("wait_for_timeout", 1000),
                    ],
                }},
                callback=self.parse
            )

    async def parse(self, response):
        # データの抽出
        items = response.css('div.item')  # セレクターを調整してください
        
        for item_element in items:
            item = {{}}
            {fields_code}
            
            if item.get('title'):  # 必須フィールドのチェック
                yield item

        # 次のページへのリンク
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield response.follow(
                next_page,
                meta={{"playwright": True}},
                callback=self.parse
            )
'''
    
    def _extract_domain(self, url: str) -> str:
        """URLからドメインを抽出"""
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc
    
    def _check_syntax(self, code: str) -> List[BugReport]:
        """構文チェック"""
        bugs = []
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            bugs.append(BugReport(
                severity='critical',
                category='syntax',
                line_number=e.lineno,
                description=f'構文エラー: {e.msg}',
                suggestion='構文を修正してください',
                code_snippet=e.text or ''
            ))
        
        return bugs
    
    def _analyze_patterns(self, code: str) -> List[BugReport]:
        """パターン分析"""
        bugs = []
        lines = code.split('\n')
        
        all_patterns = []
        all_patterns.extend(self.analysis_rules['performance_patterns'])
        all_patterns.extend(self.analysis_rules['security_patterns'])
        all_patterns.extend(self.analysis_rules['scrapy_best_practices'])
        
        for i, line in enumerate(lines, 1):
            for rule in all_patterns:
                if re.search(rule['pattern'], line):
                    bugs.append(BugReport(
                        severity=rule['severity'],
                        category='pattern',
                        line_number=i,
                        description=rule['message'],
                        suggestion=rule['suggestion'],
                        code_snippet=line.strip()
                    ))
        
        return bugs
    
    def _analyze_scrapy_code(self, code: str) -> List[BugReport]:
        """Scrapy固有の分析"""
        bugs = []
        
        # Scrapyのベストプラクティスチェック
        if 'class' in code and 'Spider' in code:
            if 'name =' not in code:
                bugs.append(BugReport(
                    severity='high',
                    category='scrapy',
                    line_number=None,
                    description='スパイダーにnameが定義されていません',
                    suggestion='name = "spider_name" を追加してください',
                    code_snippet=''
                ))
            
            if 'start_urls' not in code and 'start_requests' not in code:
                bugs.append(BugReport(
                    severity='high',
                    category='scrapy',
                    line_number=None,
                    description='start_urlsまたはstart_requestsが定義されていません',
                    suggestion='start_urlsリストまたはstart_requestsメソッドを定義してください',
                    code_snippet=''
                ))
        
        return bugs
    
    def _analyze_performance_data(self, performance_data: Dict[str, Any]) -> List[CodeSuggestion]:
        """パフォーマンスデータ分析"""
        suggestions = []
        
        # CPU使用率が高い場合
        if performance_data.get('cpu_avg', 0) > 80:
            suggestions.append(CodeSuggestion(
                type='optimization',
                title='並行リクエスト数の最適化',
                description='CPU使用率が高いため、並行リクエスト数を減らすことを推奨します',
                code='CONCURRENT_REQUESTS = 4\nCONCURRENT_REQUESTS_PER_DOMAIN = 2',
                confidence=0.8,
                reasoning='高いCPU使用率に基づく推奨',
                tags=['performance', 'cpu']
            ))
        
        # 成功率が低い場合
        if performance_data.get('success_rate', 100) < 90:
            suggestions.append(CodeSuggestion(
                type='optimization',
                title='リトライ設定の改善',
                description='成功率が低いため、リトライ設定を強化することを推奨します',
                code='''RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
RETRY_PRIORITY_ADJUST = -1''',
                confidence=0.85,
                reasoning='低い成功率に基づく推奨',
                tags=['reliability', 'retry']
            ))
        
        return suggestions
    
    def _analyze_code_for_optimization(self, code: str) -> List[CodeSuggestion]:
        """コード最適化分析"""
        suggestions = []
        
        # AutoThrottleの推奨
        if 'AUTOTHROTTLE_ENABLED' not in code:
            suggestions.append(CodeSuggestion(
                type='optimization',
                title='AutoThrottleの有効化',
                description='自動的な遅延調整でサーバー負荷を軽減',
                code='''AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0''',
                confidence=0.9,
                reasoning='AutoThrottleによる自動最適化',
                tags=['performance', 'autothrottle']
            ))
        
        # キャッシュの推奨
        if 'HTTPCACHE_ENABLED' not in code:
            suggestions.append(CodeSuggestion(
                type='optimization',
                title='HTTPキャッシュの有効化',
                description='重複リクエストを避けて効率を向上',
                code='''HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [503, 504, 505, 500, 403, 404, 408]''',
                confidence=0.8,
                reasoning='キャッシュによる効率化',
                tags=['performance', 'cache']
            ))
        
        return suggestions
    
    def _generate_user_agent_middleware(self, requirements: Dict[str, Any]) -> str:
        """ユーザーエージェントミドルウェアを生成"""
        return '''import random
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware


class RandomUserAgentMiddleware(UserAgentMiddleware):
    """ランダムユーザーエージェントミドルウェア"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
        ]

    def process_request(self, request, spider):
        ua = random.choice(self.user_agents)
        request.headers['User-Agent'] = ua
        return None
'''
    
    def _generate_proxy_middleware(self, requirements: Dict[str, Any]) -> str:
        """プロキシミドルウェアを生成"""
        return '''import random
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware


class RotatingProxyMiddleware(HttpProxyMiddleware):
    """ローテーティングプロキシミドルウェア"""
    
    def __init__(self):
        self.proxies = [
            'http://proxy1:8080',
            'http://proxy2:8080',
            'http://proxy3:8080',
        ]

    def process_request(self, request, spider):
        if self.proxies:
            proxy = random.choice(self.proxies)
            request.meta['proxy'] = proxy
        return None
'''
    
    def _generate_rate_limit_middleware(self, requirements: Dict[str, Any]) -> str:
        """レート制限ミドルウェアを生成"""
        return '''import time
from scrapy.downloadermiddlewares.retry import RetryMiddleware


class RateLimitMiddleware:
    """レート制限ミドルウェア"""
    
    def __init__(self, delay=1.0):
        self.delay = delay
        self.last_request_time = 0

    @classmethod
    def from_crawler(cls, crawler):
        delay = crawler.settings.getfloat('RATE_LIMIT_DELAY', 1.0)
        return cls(delay)

    def process_request(self, request, spider):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.delay:
            time.sleep(self.delay - time_since_last)
        
        self.last_request_time = time.time()
        return None
'''
    
    def _generate_retry_middleware(self, requirements: Dict[str, Any]) -> str:
        """リトライミドルウェアを生成"""
        return '''from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message


class SmartRetryMiddleware(RetryMiddleware):
    """スマートリトライミドルウェア"""
    
    def __init__(self, settings):
        super().__init__(settings)
        self.retry_http_codes = settings.getlist('RETRY_HTTP_CODES')
        self.max_retry_times = settings.getint('RETRY_TIMES')

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
            
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
            
        return response

    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) and not request.meta.get('dont_retry', False):
            return self._retry(request, exception, spider)
'''
    
    def _enhance_with_ai(self, code: str, requirements: Dict[str, Any]) -> Optional[str]:
        """AIでコードを改善"""
        # OpenAI APIを使用してコードを改善
        # 実際の実装では、適切なプロンプトエンジニアリングが必要
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a Scrapy expert. Improve the given spider code."},
                    {"role": "user", "content": f"Improve this Scrapy spider code:\n{code}"}
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except:
            return None
    
    def _ai_code_analysis(self, code: str) -> List[BugReport]:
        """AIによるコード分析"""
        # OpenAI APIを使用してコードを分析
        # 実際の実装では、より詳細な分析が必要
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a code reviewer. Find bugs and issues in the given code."},
                    {"role": "user", "content": f"Analyze this code for bugs:\n{code}"}
                ],
                max_tokens=500
            )
            
            # レスポンスを解析してBugReportに変換
            # 簡略化された実装
            analysis = response.choices[0].message.content
            return [BugReport(
                severity='medium',
                category='ai_analysis',
                line_number=None,
                description=analysis,
                suggestion='AIによる提案を確認してください',
                code_snippet=''
            )]
        except:
            return []


# グローバルインスタンス
ai_analyzer = AICodeAnalyzer()
