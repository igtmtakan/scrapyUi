"""
テンプレート管理サービス
カスタムスパイダーテンプレートとプロジェクトテンプレートを管理
"""
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum


class TemplateType(Enum):
    SPIDER = "spider"
    PROJECT = "project"
    MIDDLEWARE = "middleware"
    PIPELINE = "pipeline"
    ITEM = "item"


@dataclass
class Template:
    id: str
    name: str
    description: str
    type: TemplateType
    content: str
    variables: List[str]  # テンプレート変数のリスト
    tags: List[str]
    author: str
    created_at: str
    updated_at: str
    usage_count: int = 0
    is_public: bool = True
    category: str = "general"


class TemplateService:
    """テンプレート管理サービス"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        self.templates_file = self.templates_dir / "templates.json"
        self.templates: Dict[str, Template] = {}
        self.load_templates()
        self._initialize_default_templates()
    
    def load_templates(self):
        """テンプレートを読み込み"""
        if self.templates_file.exists():
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for template_data in data:
                        template = Template(**template_data)
                        template.type = TemplateType(template.type)
                        self.templates[template.id] = template
            except Exception as e:
                print(f"Error loading templates: {e}")
    
    def save_templates(self):
        """テンプレートを保存"""
        try:
            data = []
            for template in self.templates.values():
                template_dict = asdict(template)
                template_dict['type'] = template.type.value
                data.append(template_dict)
            
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving templates: {e}")
    
    def create_template(
        self,
        name: str,
        description: str,
        template_type: TemplateType,
        content: str,
        variables: List[str] = None,
        tags: List[str] = None,
        author: str = "ScrapyUI",
        category: str = "custom"
    ) -> str:
        """新しいテンプレートを作成"""
        template_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        template = Template(
            id=template_id,
            name=name,
            description=description,
            type=template_type,
            content=content,
            variables=variables or [],
            tags=tags or [],
            author=author,
            created_at=now,
            updated_at=now,
            category=category
        )
        
        self.templates[template_id] = template
        self.save_templates()
        return template_id
    
    def update_template(
        self,
        template_id: str,
        name: str = None,
        description: str = None,
        content: str = None,
        variables: List[str] = None,
        tags: List[str] = None,
        category: str = None
    ) -> bool:
        """テンプレートを更新"""
        if template_id not in self.templates:
            return False
        
        template = self.templates[template_id]
        
        if name is not None:
            template.name = name
        if description is not None:
            template.description = description
        if content is not None:
            template.content = content
        if variables is not None:
            template.variables = variables
        if tags is not None:
            template.tags = tags
        if category is not None:
            template.category = category
        
        template.updated_at = datetime.now().isoformat()
        self.save_templates()
        return True
    
    def delete_template(self, template_id: str) -> bool:
        """テンプレートを削除"""
        if template_id in self.templates:
            del self.templates[template_id]
            self.save_templates()
            return True
        return False
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """テンプレートを取得"""
        return self.templates.get(template_id)
    
    def list_templates(
        self,
        template_type: TemplateType = None,
        category: str = None,
        tags: List[str] = None,
        author: str = None
    ) -> List[Template]:
        """テンプレート一覧を取得"""
        templates = list(self.templates.values())
        
        if template_type:
            templates = [t for t in templates if t.type == template_type]
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]
        
        if author:
            templates = [t for t in templates if t.author == author]
        
        # 使用回数順でソート
        templates.sort(key=lambda t: t.usage_count, reverse=True)
        return templates
    
    def render_template(self, template_id: str, variables: Dict[str, str]) -> Tuple[bool, str]:
        """テンプレートを変数で置換してレンダリング"""
        template = self.get_template(template_id)
        if not template:
            return False, "Template not found"
        
        try:
            content = template.content
            for var_name, var_value in variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                content = content.replace(placeholder, var_value)
            
            # 使用回数を増加
            template.usage_count += 1
            self.save_templates()
            
            return True, content
        except Exception as e:
            return False, f"Error rendering template: {str(e)}"
    
    def extract_variables(self, content: str) -> List[str]:
        """テンプレート内の変数を抽出"""
        import re
        pattern = r'\{\{(\w+)\}\}'
        variables = re.findall(pattern, content)
        return list(set(variables))
    
    def _initialize_default_templates(self):
        """デフォルトテンプレートを初期化"""
        if not self.templates:
            self._create_default_spider_templates()
            self._create_default_middleware_templates()
            self._create_default_pipeline_templates()
            self._create_default_item_templates()
    
    def _create_default_spider_templates(self):
        """デフォルトスパイダーテンプレートを作成"""
        # 基本スパイダーテンプレート（新アーキテクチャ対応）
        basic_spider = '''import scrapy
# 新アーキテクチャ: Playwright専用サービス（ポート8004）を使用
# from scrapy_playwright.page import PageCoroutine  # 削除済み
from {{project_name}}.items import {{item_class}}


class {{spider_class}}(scrapy.Spider):
    name = '{{spider_name}}'
    allowed_domains = [{{allowed_domains}}]
    start_urls = [{{start_urls}}]

    # 新アーキテクチャ: Scrapy-Playwright設定は不要
    # custom_settings = {
    #     "PLAYWRIGHT_BROWSER_TYPE": "chromium",
    #     "DOWNLOAD_HANDLERS": {
    #         "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    #         "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    #     },
    #     "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    # }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_page_coroutines": [
                        PageCoroutine("wait_for_selector", "body"),
                        PageCoroutine("wait_for_timeout", 1000),
                    ],
                },
                callback=self.parse
            )

    async def parse(self, response):
        # データの抽出
        items = response.css('{{item_selector}}')
        for item in items:
            scrapy_item = {{item_class}}()
            scrapy_item['{{field_name}}'] = item.css('{{field_selector}}').get()
            yield scrapy_item

        # 次のページ
        next_page = response.css('{{next_page_selector}}').get()
        if next_page:
            yield response.follow(
                next_page,
                meta={"playwright": True},
                callback=self.parse
            )
'''
        
        self.create_template(
            name="Basic Playwright Spider",
            description="基本的なPlaywright対応スパイダー",
            template_type=TemplateType.SPIDER,
            content=basic_spider,
            variables=["project_name", "item_class", "spider_class", "spider_name", 
                      "allowed_domains", "start_urls", "item_selector", "field_name", 
                      "field_selector", "next_page_selector"],
            tags=["playwright", "basic", "spider"],
            author="ScrapyUI",
            category="default"
        )
        
        # E-commerceスパイダーテンプレート（新アーキテクチャ対応）
        ecommerce_spider = '''import scrapy
# 新アーキテクチャ: Playwright専用サービス（ポート8004）を使用
# from scrapy_playwright.page import PageCoroutine  # 削除済み
from {{project_name}}.items import ProductItem


class {{spider_class}}(scrapy.Spider):
    name = '{{spider_name}}'
    allowed_domains = [{{allowed_domains}}]
    start_urls = [{{start_urls}}]

    # 新アーキテクチャ: Scrapy-Playwright設定は不要
    # custom_settings = {
    #     "PLAYWRIGHT_BROWSER_TYPE": "chromium",
    #     "DOWNLOAD_HANDLERS": {
    #         "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    #         "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    #     },
    #     "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    #     "PLAYWRIGHT_CONTEXTS": {
    #         "default": {
    #             "viewport": {"width": 1280, "height": 800},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
        },
    }

    async def parse(self, response):
        # 商品リストページの解析
        products = response.css('{{product_selector}}')
        for product in products:
            product_url = product.css('{{product_url_selector}}').get()
            if product_url:
                yield response.follow(
                    product_url,
                    meta={"playwright": True},
                    callback=self.parse_product
                )

        # 次のページ
        next_page = response.css('{{next_page_selector}}').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    async def parse_product(self, response):
        # 商品詳細ページの解析
        item = ProductItem()
        item['name'] = response.css('{{product_name_selector}}').get()
        item['price'] = response.css('{{price_selector}}').re_first(r'[\\d,]+')
        item['description'] = response.css('{{description_selector}}').get()
        item['images'] = response.css('{{images_selector}}').getall()
        item['url'] = response.url
        
        yield item
'''
        
        self.create_template(
            name="E-commerce Product Spider",
            description="E-commerce商品スクレイピング用スパイダー",
            template_type=TemplateType.SPIDER,
            content=ecommerce_spider,
            variables=["project_name", "spider_class", "spider_name", "allowed_domains",
                      "start_urls", "product_selector", "product_url_selector",
                      "next_page_selector", "product_name_selector", "price_selector",
                      "description_selector", "images_selector"],
            tags=["playwright", "ecommerce", "product"],
            author="ScrapyUI",
            category="default"
        )

        # Playwright専用サービステンプレート
        playwright_service_spider = self._get_playwright_service_template()
        self.create_template(
            name="Playwright Service Spider",
            description="新アーキテクチャのPlaywright専用サービスを使用したスパイダー",
            template_type=TemplateType.SPIDER,
            content=playwright_service_spider,
            variables=["spider_name", "start_url", "allowed_domains"],
            tags=["playwright", "service", "browser-automation", "new-architecture"],
            author="ScrapyUI",
            category="browser-automation"
        )

        # Amazon Playwright専用サービステンプレート
        amazon_playwright_service_spider = self._get_amazon_playwright_service_template()
        self.create_template(
            name="Amazon Ranking Playwright Service",
            description="Playwright専用サービスを使用したAmazonランキングスパイダー",
            template_type=TemplateType.SPIDER,
            content=amazon_playwright_service_spider,
            variables=["spider_name", "category"],
            tags=["amazon", "playwright", "service", "e-commerce", "ranking"],
            author="ScrapyUI",
            category="e-commerce"
        )
    
    def _create_default_middleware_templates(self):
        """デフォルトミドルウェアテンプレートを作成"""
        user_agent_middleware = '''import random
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware


class {{middleware_class}}(UserAgentMiddleware):
    """ランダムユーザーエージェントミドルウェア"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]

    def process_request(self, request, spider):
        ua = random.choice(self.user_agents)
        request.headers['User-Agent'] = ua
        return None
'''
        
        self.create_template(
            name="Random User Agent Middleware",
            description="ランダムユーザーエージェントミドルウェア",
            template_type=TemplateType.MIDDLEWARE,
            content=user_agent_middleware,
            variables=["middleware_class"],
            tags=["middleware", "user-agent", "random"],
            author="ScrapyUI",
            category="default"
        )
    
    def _create_default_pipeline_templates(self):
        """デフォルトパイプラインテンプレートを作成"""
        json_pipeline = '''import json
from pathlib import Path
from datetime import datetime
from itemadapter import ItemAdapter


class {{pipeline_class}}:
    """JSON出力パイプライン"""
    
    def open_spider(self, spider):
        self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{spider.name}_{timestamp}.json"
        self.file = open(self.output_dir / filename, 'w', encoding='utf-8')
        self.file.write('[\\n')
        self.first_item = True

    def close_spider(self, spider):
        self.file.write('\\n]')
        self.file.close()

    def process_item(self, item, spider):
        if not self.first_item:
            self.file.write(',\\n')
        else:
            self.first_item = False
        
        line = json.dumps(ItemAdapter(item).asdict(), ensure_ascii=False, indent=2)
        self.file.write(line)
        return item
'''
        
        self.create_template(
            name="JSON Export Pipeline",
            description="JSON形式でデータを出力するパイプライン",
            template_type=TemplateType.PIPELINE,
            content=json_pipeline,
            variables=["pipeline_class"],
            tags=["pipeline", "json", "export"],
            author="ScrapyUI",
            category="default"
        )
    
    def _create_default_item_templates(self):
        """デフォルトアイテムテンプレートを作成"""
        basic_item = '''import scrapy
from itemloaders.processors import TakeFirst, MapCompose
from w3lib.html import remove_tags


def clean_text(value):
    """テキストをクリーニング"""
    if value:
        return value.strip().replace('\\n', ' ').replace('\\r', ' ')
    return value


class {{item_class}}(scrapy.Item):
    """{{item_description}}"""
    
    {{fields}}
'''
        
        self.create_template(
            name="Basic Item",
            description="基本的なアイテムクラス",
            template_type=TemplateType.ITEM,
            content=basic_item,
            variables=["item_class", "item_description", "fields"],
            tags=["item", "basic"],
            author="ScrapyUI",
            category="default"
        )

    def _get_playwright_service_template(self):
        """Playwright専用サービステンプレートを取得"""
        return '''#!/usr/bin/env python3
"""
Playwright専用サービス対応スパイダー
新アーキテクチャのPlaywright専用サービスを使用
"""

import scrapy
import json
import requests
from datetime import datetime

def debug_print(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] 🕷️ SPIDER: {message}")

class {{spider_class}}(scrapy.Spider):
    name = "{{spider_name}}"
    allowed_domains = [{{allowed_domains}}]
    start_urls = [{{start_url}}]

    # Playwright専用サービス設定
    playwright_service_url = "http://localhost:8004"

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'FEEDS': {
            'results.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'overwrite': True,
            },
        },
        'ITEM_PIPELINES': {
            'backend.app.pipelines.database_pipeline.DatabasePipeline': 300,
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        debug_print(f"Playwright Service Spider initialized")
        debug_print(f"Playwright Service URL: {self.playwright_service_url}")

    def start_requests(self):
        """Playwright専用サービスを使用したstart_requests"""
        debug_print("Starting spider with Playwright service integration")

        for url in self.start_urls:
            # Playwright専用サービスでページを取得
            content = self.fetch_with_playwright_sync(url)

            if content:
                debug_print("✅ Playwright fetch successful, creating Scrapy response")

                # Scrapyレスポンスを作成
                yield scrapy.http.HtmlResponse(
                    url=url,
                    body=content.encode('utf-8'),
                    encoding='utf-8',
                    request=scrapy.Request(url=url, callback=self.parse)
                )
            else:
                debug_print("❌ Playwright fetch failed, using fallback")
                # フォールバック: 通常のScrapyリクエスト
                yield scrapy.Request(url=url, callback=self.parse_fallback)

    def fetch_with_playwright_sync(self, url: str) -> str:
        """同期版のPlaywright専用サービス呼び出し"""
        debug_print(f"Fetching {url} via Playwright service")

        request_data = {
            "url": url,
            "browser_type": "chromium",
            "headless": True,
            "wait_for": "domcontentloaded",
            "timeout": 30000,
            "javascript_code": "window.scrollTo(0, document.body.scrollHeight);"
        }

        try:
            response = requests.post(
                f"{self.playwright_service_url}/execute",
                json=request_data,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()

                if result.get("success"):
                    debug_print(f"✅ Playwright fetch successful: {result.get('title', 'No title')}")
                    debug_print(f"   Execution time: {result.get('execution_time', 0):.2f}s")
                    debug_print(f"   Content length: {len(result.get('content', ''))}")
                    return result.get("content", "")
                else:
                    debug_print(f"❌ Playwright fetch failed: {result.get('error', 'Unknown error')}")
                    return None
            else:
                debug_print(f"❌ HTTP error: {response.status_code}")
                return None

        except Exception as e:
            debug_print(f"❌ Exception during Playwright fetch: {e}")
            return None

    def parse(self, response):
        """Playwright取得コンテンツの解析"""
        debug_print(f"Parsing Playwright content from: {response.url}")
        debug_print(f"Response length: {len(response.text)}")

        # タイトルを取得
        title = response.css('title::text').get()
        debug_print(f"Page title: {title}")

        # 基本的なデータを抽出
        yield {
            'url': response.url,
            'title': title,
            'method': 'playwright_service',
            'crawl_start_datetime': datetime.now().isoformat(),
            'item_acquired_datetime': datetime.now().isoformat()
        }

        debug_print("✅ Parsing completed")

    def parse_fallback(self, response):
        """フォールバック用のパース関数"""
        debug_print(f"Using fallback parsing for: {response.url}")

        title = response.css('title::text').get()
        debug_print(f"Fallback page title: {title}")

        yield {
            'url': response.url,
            'title': title,
            'method': 'fallback',
            'crawl_start_datetime': datetime.now().isoformat(),
            'item_acquired_datetime': datetime.now().isoformat()
        }

        debug_print("✅ Fallback parsing completed")'''

    def _get_amazon_playwright_service_template(self):
        """Amazon Playwright専用サービステンプレートを取得"""
        return '''#!/usr/bin/env python3
"""
Amazon ランキングスパイダー（Playwright専用サービス版）
新アーキテクチャのPlaywright専用サービスを使用してAmazonランキングを取得
"""

import scrapy
import json
import requests
from datetime import datetime

def debug_print(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] 🛒 AMAZON: {message}")

class {{spider_class}}(scrapy.Spider):
    name = "{{spider_name}}"
    allowed_domains = ["amazon.co.jp"]
    start_urls = ["https://www.amazon.co.jp/gp/bestsellers/{{category}}/"]

    # Playwright専用サービス設定
    playwright_service_url = "http://localhost:8004"

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'FEEDS': {
            'amazon_ranking_results.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'overwrite': True,
            },
        },
        'ITEM_PIPELINES': {
            'backend.app.pipelines.database_pipeline.DatabasePipeline': 300,
        },
    }

    def start_requests(self):
        """Amazon専用のPlaywright設定でリクエスト開始"""
        debug_print("Starting Amazon ranking spider with Playwright service")

        for url in self.start_urls:
            content = self.fetch_amazon_with_playwright(url)

            if content:
                debug_print("✅ Amazon page fetched successfully")
                yield scrapy.http.HtmlResponse(
                    url=url,
                    body=content.encode('utf-8'),
                    encoding='utf-8',
                    request=scrapy.Request(url=url, callback=self.parse_ranking)
                )
            else:
                debug_print("❌ Amazon fetch failed")
                yield scrapy.Request(url=url, callback=self.parse_fallback)

    def fetch_amazon_with_playwright(self, url: str) -> str:
        """Amazon専用のPlaywright設定"""
        debug_print(f"Fetching Amazon page: {url}")

        request_data = {
            "url": url,
            "browser_type": "chromium",
            "headless": True,
            "wait_for": "domcontentloaded",
            "timeout": 30000,
            "javascript_code": "window.scrollTo(0, document.body.scrollHeight); console.log('Amazon page scrolled');"
        }

        try:
            response = requests.post(
                f"{self.playwright_service_url}/execute",
                json=request_data,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    debug_print(f"✅ Amazon fetch successful: {result.get('execution_time', 0):.2f}s")
                    return result.get("content", "")
                else:
                    debug_print(f"❌ Amazon fetch error: {result.get('error')}")

            return None

        except Exception as e:
            debug_print(f"❌ Exception: {e}")
            return None

    def parse_ranking(self, response):
        """Amazonランキングページの解析"""
        debug_print(f"Parsing Amazon ranking page: {response.url}")

        # ランキングアイテムを検索
        ranking_items = response.css('div[data-asin]')
        debug_print(f"Found {len(ranking_items)} ranking items")

        for i, item in enumerate(ranking_items[:60], 1):  # 上位60位まで
            try:
                asin = item.css('::attr(data-asin)').get()
                if not asin:
                    continue

                title = item.css('img::attr(alt)').get() or item.css('a span::text').get()
                image_url = item.css('img::attr(src)').get()
                product_url = item.css('a::attr(href)').get()

                if product_url and product_url.startswith('/'):
                    product_url = f"https://www.amazon.co.jp{product_url}"

                # 価格情報
                price_element = item.css('span.a-price-whole::text').get()
                price = None
                if price_element:
                    try:
                        price = int(price_element.replace(',', ''))
                    except ValueError:
                        pass

                # レビュー情報
                rating_element = item.css('span.a-icon-alt::text').get()
                rating = None
                if rating_element and '5つ星のうち' in rating_element:
                    try:
                        rating = float(rating_element.split('5つ星のうち')[1].split('の')[0])
                    except (IndexError, ValueError):
                        pass

                yield {
                    'rank': i,
                    'asin': asin,
                    'title': title,
                    'price': price,
                    'rating': rating,
                    'image_url': image_url,
                    'product_url': product_url,
                    'category': '{{category}}',
                    'crawl_start_datetime': datetime.now().isoformat(),
                    'item_acquired_datetime': datetime.now().isoformat(),
                    'url': response.url,
                    'method': 'playwright_service'
                }

                debug_print(f"Extracted item {i}: {title[:50] if title else 'No title'}...")

            except Exception as e:
                debug_print(f"❌ Error extracting item {i}: {e}")
                continue

        debug_print(f"✅ Completed Amazon ranking extraction")

    def parse_fallback(self, response):
        """フォールバック解析"""
        debug_print("Using fallback parsing for Amazon")

        yield {
            'title': 'Amazon fallback item',
            'url': response.url,
            'method': 'fallback',
            'crawl_start_datetime': datetime.now().isoformat(),
            'item_acquired_datetime': datetime.now().isoformat()
        }'''
