# Scrapy-Playwright対応のスパイダーテンプレート

def get_basic_spider_template(spider_name: str, project_name: str, start_urls: list = None) -> str:
    """基本的なPlaywright対応スパイダーテンプレート（最適化済み）"""
    if start_urls is None:
        start_urls = ["https://example.com"]

    urls_str = ",\n        ".join([f'"{url}"' for url in start_urls])

    return f"""import scrapy
from scrapy_playwright.page import PageMethod
from {project_name}.items import {project_name.capitalize()}Item


class {spider_name.capitalize()}Spider(scrapy.Spider):
    name = '{spider_name}'
    allowed_domains = []
    start_urls = [
        {urls_str}
    ]

    # 最適化されたPlaywright設定
    custom_settings = {{
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {{
            'headless': True,
        }},
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 10000,
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 0.5,
        'AUTOTHROTTLE_ENABLED': False,
    }}

    # 新しいstart()メソッド（Scrapy 2.13.0+対応）
    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={{
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_load_state', 'domcontentloaded'),
                    ],
                }},
                callback=self.parse
            )

    # 後方互換性のためのstart_requests()メソッド（非推奨）
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={{
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_load_state', 'domcontentloaded'),
                    ],
                }},
                callback=self.parse
            )

    async def parse(self, response):
        # ページが完全に読み込まれた後の処理
        self.logger.info(f'Parsing {{response.url}}')

        # データの抽出例
        items = response.css('div.item')
        for item in items:
            scrapy_item = {project_name.capitalize()}Item()
            scrapy_item['title'] = item.css('h2::text').get()
            scrapy_item['description'] = item.css('p::text').get()
            scrapy_item['url'] = response.url
            yield scrapy_item

        # 次のページへのリンクを辿る例
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield response.follow(
                next_page,
                meta={{
                    "playwright": True,
                    "playwright_page_coroutines": [
                        PageCoroutine("wait_for_selector", "body"),
                    ],
                }},
                callback=self.parse
            )
"""


def get_advanced_spider_template(spider_name: str, project_name: str, start_urls: list = None) -> str:
    """高度なPlaywright対応スパイダーテンプレート（最適化済み）"""
    if start_urls is None:
        start_urls = ["https://example.com"]

    urls_str = ",\n        ".join([f'"{url}"' for url in start_urls])

    return f"""import scrapy
from scrapy_playwright.page import PageMethod
from {project_name}.items import {project_name.capitalize()}Item
from urllib.parse import urljoin
import re


class {spider_name.capitalize()}Spider(scrapy.Spider):
    name = '{spider_name}'
    allowed_domains = []
    start_urls = [
        {urls_str}
    ]

    # 最適化されたPlaywright設定（高度版）
    custom_settings = {{
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {{
            'headless': True,
        }},
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 10000,
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 0.5,
        'AUTOTHROTTLE_ENABLED': False,
        'ROBOTSTXT_OBEY': True,
        'USER_AGENT': 'ScrapyUI Advanced Spider 1.0',
    }}

    # 新しいstart()メソッド（Scrapy 2.13.0+対応）
    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={{
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_load_state', 'domcontentloaded'),
                        PageMethod('wait_for_timeout', 500),
                    ],
                }},
                callback=self.parse
            )

    # 後方互換性のためのstart_requests()メソッド（非推奨）
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={{
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_load_state', 'domcontentloaded'),
                        PageMethod('wait_for_timeout', 500),
                    ],
                }},
                callback=self.parse
            )

    def parse(self, response):
        # ページが完全に読み込まれた後の処理
        self.logger.info(f'Parsing {{response.url}}')

        # データの抽出
        items = response.css('div.item, article, .product')
        for item in items:
            scrapy_item = {project_name.capitalize()}Item()

            # タイトルの抽出（複数のセレクターを試行）
            title_selectors = ['h1::text', 'h2::text', 'h3::text', '.title::text']
            for selector in title_selectors:
                title = item.css(selector).get()
                if title:
                    scrapy_item['title'] = title.strip()
                    break

            # URLの抽出
            link = item.css('a::attr(href)').get()
            if link:
                scrapy_item['url'] = urljoin(response.url, link)
            else:
                scrapy_item['url'] = response.url

            # コンテンツの抽出
            content = item.css('p::text, .content::text, .description::text').getall()
            scrapy_item['content'] = ' '.join([text.strip() for text in content if text.strip()])

            yield scrapy_item

        # 次のページへのリンクを探す
        next_page_selectors = [
            'a.next::attr(href)',
            'a[rel="next"]::attr(href)',
            '.pagination a:last-child::attr(href)',
            '.next-page::attr(href)'
        ]

        for selector in next_page_selectors:
            next_page = response.css(selector).get()
            if next_page:
                yield response.follow(
                    next_page,
                    meta={{
                        'playwright': True,
                        'playwright_page_methods': [
                            PageMethod('wait_for_load_state', 'domcontentloaded'),
                        ],
                    }},
                    callback=self.parse
                )
                break

"""


def get_mobile_spider_template(spider_name: str, project_name: str, start_urls: list = None) -> str:
    """モバイル対応スパイダーテンプレート（最適化済み）"""
    if start_urls is None:
        start_urls = ["https://example.com"]

    urls_str = ",\n        ".join([f'"{url}"' for url in start_urls])

    return f"""import scrapy
from scrapy_playwright.page import PageMethod
from {project_name}.items import {project_name.capitalize()}Item


class {spider_name.capitalize()}Spider(scrapy.Spider):
    name = '{spider_name}'
    allowed_domains = []
    start_urls = [
        {urls_str}
    ]

    # 最適化されたPlaywright設定（モバイル用）
    custom_settings = {{
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {{
            'headless': True,
        }},
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 10000,
        'PLAYWRIGHT_CONTEXTS': {{
            'mobile': {{
                'viewport': {{'width': 375, 'height': 667}},
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
                'is_mobile': True,
                'has_touch': True,
            }},
        }},
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 0.5,
        'AUTOTHROTTLE_ENABLED': False,
        'USER_AGENT': 'ScrapyUI Mobile Spider 1.0',
    }}

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={{
                    'playwright': True,
                    'playwright_context': 'mobile',
                    'playwright_page_methods': [
                        PageMethod('wait_for_load_state', 'domcontentloaded'),
                    ],
                }},
                callback=self.parse
            )

    def parse(self, response):
        # モバイルページの解析
        self.logger.info(f'Parsing mobile page: {{response.url}}')

        # データの抽出（モバイル用セレクター）
        mobile_selectors = [
            'div.mobile-item',
            '.mobile-content',
            'article',
            '.item',
            '.card'
        ]

        items = []
        for selector in mobile_selectors:
            found_items = response.css(selector)
            if found_items:
                items = found_items
                break

        for item in items:
            scrapy_item = {project_name.capitalize()}Item()

            # タイトルの抽出
            title_selectors = ['h1::text', 'h2::text', 'h3::text', '.title::text', '.name::text']
            for selector in title_selectors:
                title = item.css(selector).get()
                if title:
                    scrapy_item['title'] = title.strip()
                    break

            # コンテンツの抽出
            content = item.css('p::text, .description::text, .content::text').getall()
            scrapy_item['content'] = ' '.join([text.strip() for text in content if text.strip()])

            scrapy_item['url'] = response.url
            yield scrapy_item

        # 次のページ（モバイル用）
        next_selectors = [
            'a.next::attr(href)',
            '.pagination-next::attr(href)',
            'button[data-next]::attr(data-next)',
            '.load-more::attr(href)'
        ]

        for selector in next_selectors:
            next_page = response.css(selector).get()
            if next_page:
                yield response.follow(
                    next_page,
                    meta={{
                        'playwright': True,
                        'playwright_context': 'mobile',
                        'playwright_page_methods': [
                            PageMethod('wait_for_load_state', 'domcontentloaded'),
                        ],
                    }},
                    callback=self.parse
                )
                break
"""
