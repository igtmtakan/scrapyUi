# Scrapy-Playwright対応のスパイダーテンプレート

def get_basic_spider_template(spider_name: str, project_name: str, start_urls: list = None) -> str:
    """基本的なPlaywright対応スパイダーテンプレート（最適化済み）"""
    if start_urls is None:
        start_urls = ["https://example.com"]

    urls_str = ",\n        ".join([f'"{url}"' for url in start_urls])

    return f"""import scrapy
from scrapy_playwright.page import PageMethod
from {project_name}.items import {project_name.capitalize()}Item
from datetime import datetime


class {spider_name.capitalize()}Spider(scrapy.Spider):
    name = '{spider_name}'
    allowed_domains = []
    start_urls = [
        {urls_str}
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # クロールスタート日時を記録
        self.crawl_start_datetime = datetime.now().isoformat()

    # 最適化されたPlaywright設定（JSONL形式対応）
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
        'FEED_EXPORT_ENCODING': 'utf-8',
        'FEEDS': {{
            'results.jsonl': {{
                'format': 'jsonl',
                'encoding': 'utf8',
                'store_empty': False,
                'item_export_kwargs': {{
                    'ensure_ascii': False
                }}
            }},
            'results.json': {{
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'item_export_kwargs': {{
                    'ensure_ascii': False
                }}
            }},
            'results.csv': {{
                'format': 'csv',
                'encoding': 'utf8',
                'store_empty': False
            }},
            'results.xml': {{
                'format': 'xml',
                'encoding': 'utf8',
                'store_empty': False
            }}
        }},
        # ScrapyUI データベースパイプライン設定
        'ITEM_PIPELINES': {{
            '{project_name}.pipelines.ScrapyUIDatabasePipeline': 100,
            '{project_name}.pipelines.ScrapyUIJSONPipeline': 200,
        }},
        'SCRAPYUI_DATABASE_URL': None,  # 実行時に設定
        'SCRAPYUI_TASK_ID': None,       # 実行時に設定
        'SCRAPYUI_JSON_FILE': None,     # 実行時に設定
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
            # 日時フィールドを追加
            scrapy_item['crawl_start_datetime'] = self.crawl_start_datetime
            scrapy_item['item_acquired_datetime'] = datetime.now().isoformat()
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
from datetime import datetime
import re


class {spider_name.capitalize()}Spider(scrapy.Spider):
    name = '{spider_name}'
    allowed_domains = []
    start_urls = [
        {urls_str}
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # クロールスタート日時を記録
        self.crawl_start_datetime = datetime.now().isoformat()

    # 最適化されたPlaywright設定（高度版・JSONL形式対応）
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
        'FEED_EXPORT_ENCODING': 'utf-8',
        'FEEDS': {{
            'results.jsonl': {{
                'format': 'jsonl',
                'encoding': 'utf8',
                'store_empty': False,
                'item_export_kwargs': {{
                    'ensure_ascii': False
                }}
            }},
            'results.json': {{
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'item_export_kwargs': {{
                    'ensure_ascii': False
                }}
            }},
            'results.csv': {{
                'format': 'csv',
                'encoding': 'utf8',
                'store_empty': False
            }},
            'results.xml': {{
                'format': 'xml',
                'encoding': 'utf8',
                'store_empty': False
            }}
        }},
        # ScrapyUI データベースパイプライン設定
        'ITEM_PIPELINES': {{
            '{project_name}.pipelines.ScrapyUIDatabasePipeline': 100,
            '{project_name}.pipelines.ScrapyUIJSONPipeline': 200,
        }},
        'SCRAPYUI_DATABASE_URL': None,  # 実行時に設定
        'SCRAPYUI_TASK_ID': None,       # 実行時に設定
        'SCRAPYUI_JSON_FILE': None,     # 実行時に設定
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

            # 日時フィールドを追加
            scrapy_item['crawl_start_datetime'] = self.crawl_start_datetime
            scrapy_item['item_acquired_datetime'] = datetime.now().isoformat()

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
from datetime import datetime


class {spider_name.capitalize()}Spider(scrapy.Spider):
    name = '{spider_name}'
    allowed_domains = []
    start_urls = [
        {urls_str}
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # クロールスタート日時を記録
        self.crawl_start_datetime = datetime.now().isoformat()

    # 最適化されたPlaywright設定（モバイル用・JSONL形式対応）
    custom_settings = {{
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {{
            'headless': True,
        }},
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 10000,
        'PLAYWRIGHT_CONTEXTS': {{
            'mobile': {{
                'viewport': {{'width': 375, 'height': 667}},
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
                'is_mobile': True,
                'has_touch': True,
            }},
        }},
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 0.5,
        'AUTOTHROTTLE_ENABLED': False,
        'USER_AGENT': 'ScrapyUI Mobile Spider 1.0',
        'FEED_EXPORT_ENCODING': 'utf-8',
        'FEEDS': {{
            'results.jsonl': {{
                'format': 'jsonl',
                'encoding': 'utf8',
                'store_empty': False,
                'item_export_kwargs': {{
                    'ensure_ascii': False
                }}
            }},
            'results.json': {{
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'item_export_kwargs': {{
                    'ensure_ascii': False
                }}
            }},
            'results.csv': {{
                'format': 'csv',
                'encoding': 'utf8',
                'store_empty': False
            }},
            'results.xml': {{
                'format': 'xml',
                'encoding': 'utf8',
                'store_empty': False
            }}
        }},
        # ScrapyUI データベースパイプライン設定
        'ITEM_PIPELINES': {{
            '{project_name}.pipelines.ScrapyUIDatabasePipeline': 100,
            '{project_name}.pipelines.ScrapyUIJSONPipeline': 200,
        }},
        'SCRAPYUI_DATABASE_URL': None,  # 実行時に設定
        'SCRAPYUI_TASK_ID': None,       # 実行時に設定
        'SCRAPYUI_JSON_FILE': None,     # 実行時に設定
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
            # 日時フィールドを追加
            scrapy_item['crawl_start_datetime'] = self.crawl_start_datetime
            scrapy_item['item_acquired_datetime'] = datetime.now().isoformat()
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


def get_amazon_ranking60_template(spider_name: str, project_name: str, start_urls: list = None) -> str:
    """AmazonRanking60スパイダーテンプレート（ランキング上位60商品取得）"""
    if start_urls is None:
        start_urls = ["https://www.amazon.co.jp/gp/bestsellers/"]

    urls_str = ",\n        ".join([f'"{url}"' for url in start_urls])

    return f"""import scrapy
from scrapy_playwright.page import PageMethod
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
import json
import pprint

def debug_print(message):
    \"\"\"デバッグ用のprint関数\"\"\"
    print(f"[DEBUG] {{message}}")

def debug_pprint(data):
    \"\"\"デバッグ用のpprint関数\"\"\"
    print("[DEBUG] Data:")
    pprint.pprint(data)

class {spider_name.capitalize()}Spider(scrapy.Spider):
    name = '{spider_name}'
    allowed_domains = ['amazon.co.jp']
    start_urls = [
        {urls_str}
    ]

    # 取得する商品数の設定
    target_items_per_page = 30  # 1ページあたりの目標商品数
    target_pages = 2           # 取得するページ数
    total_target_items = target_items_per_page * target_pages  # 合計60商品

    custom_settings = {{
        'DOWNLOAD_HANDLERS': {{
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        }},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': 3,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'CLOSESPIDER_PAGECOUNT': 10,
        'CLOSESPIDER_ITEMCOUNT': 70,  # 目標より少し多めに設定
        'DEFAULT_REQUEST_HEADERS': {{
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }},
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {{
            'headless': True,
            'timeout': 30000,
        }},
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 30000,
        'PLAYWRIGHT_PROCESS_REQUEST_HEADERS': None,
        'FEEDS': {{
            'ranking_results.jsonl': {{
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'item_export_kwargs': {{
                    'ensure_ascii': False,
                }},
            }},
        }},
        'FEED_EXPORT_ENCODING': 'utf-8',
        # ScrapyUI データベースパイプライン設定
        'ITEM_PIPELINES': {{
            '{project_name}.pipelines.ScrapyUIDatabasePipeline': 100,
            '{project_name}.pipelines.ScrapyUIJSONPipeline': 200,
        }},
        'SCRAPYUI_DATABASE_URL': None,  # 実行時に設定
        'SCRAPYUI_TASK_ID': None,       # 実行時に設定
        'SCRAPYUI_JSON_FILE': None,     # 実行時に設定
    }}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_start_datetime = datetime.now().isoformat()
        self.items_scraped = 0
        self.pages_scraped = 0
        debug_print(f"Spider initialized. Target: {{self.total_target_items}} items from {{self.target_pages}} pages")

    async def start(self):
        \"\"\"新しいstart()メソッド（Scrapy 2.13.0+対応）\"\"\"
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={{
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_load_state', 'domcontentloaded'),
                        PageMethod('wait_for_timeout', 2000),
                        PageMethod('evaluate', 'window.scrollTo(0, document.body.scrollHeight)'),
                        PageMethod('wait_for_timeout', 1000),
                    ],
                }},
                callback=self.parse_ranking_page
            )

    def parse_ranking_page(self, response):
        \"\"\"ランキングページを解析\"\"\"
        debug_print(f"Parsing ranking page: {{response.url}}")
        self.pages_scraped += 1

        # ランキング商品のセレクタ（複数パターンに対応）
        product_selectors = [
            'div[data-component-type="s-search-result"]',  # 検索結果形式
            '.s-result-item[data-component-type="s-search-result"]',  # 検索結果アイテム
            '.zg-item-immersion',  # ベストセラー形式
            '.a-carousel-card',    # カルーセル形式
            '.p13n-sc-uncoverable-faceout',  # おすすめ商品形式
        ]

        products_found = []
        for selector in product_selectors:
            products = response.css(selector)
            if products:
                debug_print(f"Found {{len(products)}} products with selector: {{selector}}")
                products_found = products
                break

        if not products_found:
            debug_print("No products found with any selector, trying alternative approach")
            # フォールバック: リンクベースの検索
            product_links = response.css('a[href*="/dp/"]::attr(href)').getall()
            debug_print(f"Found {{len(product_links)}} product links as fallback")

            for i, link in enumerate(product_links[:self.target_items_per_page]):
                if self.items_scraped >= self.total_target_items:
                    break

                product_url = urljoin(response.url, link)
                yield scrapy.Request(
                    product_url,
                    meta={{
                        'playwright': True,
                        'playwright_page_methods': [
                            PageMethod('wait_for_load_state', 'domcontentloaded'),
                        ],
                        'ranking_position': i + 1 + (self.pages_scraped - 1) * self.target_items_per_page,
                        'page_number': self.pages_scraped,
                    }},
                    callback=self.parse_product_detail
                )
            return

        # 商品情報を抽出
        for i, product in enumerate(products_found[:self.target_items_per_page]):
            if self.items_scraped >= self.total_target_items:
                break

            # 商品リンクを取得
            product_link = product.css('a[href*="/dp/"]::attr(href)').get()
            if not product_link:
                product_link = product.css('a::attr(href)').get()

            if product_link:
                product_url = urljoin(response.url, product_link)
                ranking_position = i + 1 + (self.pages_scraped - 1) * self.target_items_per_page

                # 基本情報を先に抽出
                title = product.css('h2 a span::text, .s-size-mini span::text, .p13n-sc-truncate::text').get()
                if title:
                    title = title.strip()

                # 価格情報
                price = product.css('.a-price .a-offscreen::text, .p13n-sc-price::text').get()

                # 評価
                rating = product.css('.a-icon-alt::text').get()

                # 画像URL
                image_url = product.css('img::attr(src)').get()

                # レビュー数
                review_count = product.css('.a-size-base::text').get()

                basic_data = {{
                    'ranking_position': ranking_position,
                    'page_number': self.pages_scraped,
                    'title': title,
                    'price': price,
                    'rating': rating,
                    'review_count': review_count,
                    'image_url': image_url,
                    'product_url': product_url,
                    'source_url': response.url,
                    'scraped_at': datetime.now().isoformat(),
                    'crawl_start_datetime': self.crawl_start_datetime,
                    'item_type': 'ranking_product'
                }}

                debug_print(f"Rank {{ranking_position}}: {{title}}")
                yield basic_data
                self.items_scraped += 1

                # 詳細ページも取得（オプション）
                yield scrapy.Request(
                    product_url,
                    meta={{
                        'playwright': True,
                        'playwright_page_methods': [
                            PageMethod('wait_for_load_state', 'domcontentloaded'),
                        ],
                        'basic_data': basic_data,
                    }},
                    callback=self.parse_product_detail,
                    dont_filter=True
                )

        # 次のページへ（目標ページ数まで）
        if self.pages_scraped < self.target_pages and self.items_scraped < self.total_target_items:
            next_page_selectors = [
                '.s-pagination-next::attr(href)',
                'a[aria-label="次へ"]::attr(href)',
                '.a-pagination .a-last a::attr(href)',
            ]

            next_page = None
            for selector in next_page_selectors:
                next_page = response.css(selector).get()
                if next_page:
                    break

            if next_page:
                next_page_url = urljoin(response.url, next_page)
                debug_print(f"Moving to next page ({{self.pages_scraped + 1}}/{{self.target_pages}}): {{next_page_url}}")
                yield scrapy.Request(
                    next_page_url,
                    meta={{
                        'playwright': True,
                        'playwright_page_methods': [
                            PageMethod('wait_for_load_state', 'domcontentloaded'),
                            PageMethod('wait_for_timeout', 2000),
                            PageMethod('evaluate', 'window.scrollTo(0, document.body.scrollHeight)'),
                            PageMethod('wait_for_timeout', 1000),
                        ],
                    }},
                    callback=self.parse_ranking_page
                )
            else:
                debug_print("No next page found or target pages reached")

    def parse_product_detail(self, response):
        \"\"\"商品詳細ページを解析（ランキング情報付き）\"\"\"
        debug_print(f"Parsing product detail: {{response.url}}")

        basic_data = response.meta.get('basic_data', {{}})

        try:
            # 商品タイトル
            title = response.css('#productTitle::text').get()
            if title:
                title = title.strip()

            # 価格情報（複数パターン対応）
            price_selectors = [
                '.a-price .a-offscreen::text',
                '.a-price-whole::text',
                '#priceblock_dealprice::text',
                '#priceblock_ourprice::text',
                '.a-price-range .a-offscreen::text',
            ]

            price = None
            for selector in price_selectors:
                price = response.css(selector).get()
                if price:
                    break

            # 評価情報
            rating = response.css('.a-icon-alt::text').get()
            review_count = response.css('#acrCustomerReviewText::text').get()

            # ASIN
            asin = response.css('#ASIN::attr(value)').get()

            # ブランド
            brand = response.css('#bylineInfo::text').get()

            # 在庫状況
            availability = response.css('#availability span::text').get()
            if availability:
                availability = availability.strip()

            # カテゴリ（パンくずリスト）
            breadcrumbs = response.css('#wayfinding-breadcrumbs_feature_div a::text').getall()

            # 商品画像
            main_image = response.css('#landingImage::attr(src)').get()

            # 商品の特徴
            features = response.css('#feature-bullets ul li span::text').getall()
            features_text = [f.strip() for f in features if f.strip()]

            detailed_data = {{
                **basic_data,  # 基本データをマージ
                'title_detail': title,
                'price_detail': price,
                'rating_detail': rating,
                'review_count_detail': review_count,
                'asin': asin,
                'brand': brand,
                'availability': availability,
                'breadcrumbs': breadcrumbs,
                'main_image': main_image,
                'features': features_text[:5] if features_text else [],  # 上位5つの特徴
                'detail_scraped_at': datetime.now().isoformat(),
                'item_type': 'ranking_product_detail'
            }}

            debug_print(f"Detailed rank {{basic_data.get('ranking_position', 'N/A')}}: {{title}}")
            yield detailed_data

        except Exception as e:
            debug_print(f"Error parsing product detail: {{e}}")
            error_data = {{
                **basic_data,
                'error': str(e),
                'item_type': 'ranking_error',
                'error_scraped_at': datetime.now().isoformat()
            }}
            yield error_data

    def closed(self, reason):
        \"\"\"スパイダー終了時の処理\"\"\"
        debug_print(f"Spider closed. Reason: {{reason}}")
        debug_print(f"Total items scraped: {{self.items_scraped}}")
        debug_print(f"Total pages scraped: {{self.pages_scraped}}")
        debug_print(f"Target was: {{self.total_target_items}} items from {{self.target_pages}} pages")
"""
