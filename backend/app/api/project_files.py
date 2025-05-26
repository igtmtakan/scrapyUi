from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import os
import json
from pathlib import Path

from app.database import get_db, Project
from app.models.schemas import ProjectFileCreate, ProjectFileUpdate, ProjectFileResponse

router = APIRouter()

# Scrapyプロジェクトの標準ファイル
SCRAPY_FILES = [
    'scrapy.cfg',
    'settings.py',
    'items.py',
    'pipelines.py',
    'middlewares.py',
    '__init__.py'
]

def get_project_files_dir(project_id: str) -> Path:
    """プロジェクトファイルのディレクトリパスを取得"""
    return Path(f"projects/{project_id}/files")

def ensure_project_files_dir(project_id: str) -> Path:
    """プロジェクトファイルディレクトリを作成"""
    files_dir = get_project_files_dir(project_id)
    files_dir.mkdir(parents=True, exist_ok=True)
    return files_dir

def get_default_file_content(filename: str, project_name: str = "myproject") -> str:
    """デフォルトファイル内容を取得"""
    if filename == 'scrapy.cfg':
        return f"""# Automatically created by: scrapy startproject
#
# For more information about the [deploy] section see:
# https://scrapyd.readthedocs.io/en/latest/deploy.html

[settings]
default = {project_name}.settings

[deploy]
#url = http://localhost:6800/
project = {project_name}
"""
    elif filename == 'settings.py':
        return f"""# Scrapy settings for {project_name} project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = '{project_name}'

SPIDER_MODULES = ['{project_name}.spiders']
NEWSPIDER_MODULE = '{project_name}.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 16
CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {{
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,ja;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}}

# =============================================================================
# SCRAPY-PLAYWRIGHT SETTINGS
# =============================================================================

# Playwright ダウンローダーミドルウェアを有効にする
DOWNLOADER_MIDDLEWARES = {{
    'scrapy_playwright.middleware.ScrapyPlaywrightDownloadHandler': 543,
    # '{project_name}.middlewares.{project_name.capitalize()}SpiderMiddleware': 544,
    # '{project_name}.middlewares.{project_name.capitalize()}DownloaderMiddleware': 545,
}}

# HTTP と HTTPS のダウンロードハンドラーを指定する
DOWNLOAD_HANDLERS = {{
    'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
    'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
}}

# Playwright 設定を有効にする
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'

# Playwright ブラウザ設定
PLAYWRIGHT_BROWSER_TYPE = 'chromium'  # 'chromium', 'firefox', または 'webkit'

# Playwright 起動オプション
PLAYWRIGHT_LAUNCH_OPTIONS = {{
    'headless': True,  # ヘッドレスモード（本番環境では True を推奨）
    'args': [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--disable-gpu',
        '--disable-background-timer-throttling',
        '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding',
    ],
}}

# Playwright コンテキスト設定
PLAYWRIGHT_CONTEXTS = {{
    'default': {{
        'viewport': {{'width': 1280, 'height': 800}},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'locale': 'ja-JP',
        'timezone_id': 'Asia/Tokyo',
    }},
    'mobile': {{
        'viewport': {{'width': 375, 'height': 667}},
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'is_mobile': True,
        'has_touch': True,
        'locale': 'ja-JP',
        'timezone_id': 'Asia/Tokyo',
    }},
    'desktop': {{
        'viewport': {{'width': 1920, 'height': 1080}},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'locale': 'ja-JP',
        'timezone_id': 'Asia/Tokyo',
    }},
}}

# Playwright デフォルトナビゲーションタイムアウト（ミリ秒）
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000

# Playwright ページ読み込み戦略
PLAYWRIGHT_PAGE_GOTO_KWARGS = {{
    'wait_until': 'networkidle',  # 'load', 'domcontentloaded', 'networkidle'
    'timeout': 30000,
}}

# =============================================================================
# SPIDER MIDDLEWARES
# =============================================================================

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {{
#     '{project_name}.middlewares.{project_name.capitalize()}SpiderMiddleware': 543,
# }}

# =============================================================================
# ITEM PIPELINES
# =============================================================================

# Configure pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {{
#     '{project_name}.pipelines.{project_name.capitalize()}Pipeline': 300,
# }}

# =============================================================================
# EXTENSIONS
# =============================================================================

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {{
#     'scrapy.extensions.telnet.TelnetConsole': None,
# }}

# =============================================================================
# AUTOTHROTTLE SETTINGS
# =============================================================================

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 1
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = False

# =============================================================================
# HTTP CACHE SETTINGS
# =============================================================================

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 3600  # 1時間
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = [404, 500, 502, 503, 504]
# HTTPCACHE_STORAGE = 'scrapy.httpcache.FilesystemCacheStorage'

# =============================================================================
# LOGGING SETTINGS
# =============================================================================

# ログレベル設定
LOG_LEVEL = 'INFO'

# ログファイル設定（オプション）
# LOG_FILE = 'scrapy.log'

# =============================================================================
# RETRY SETTINGS
# =============================================================================

# リトライ設定
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# =============================================================================
# FEEDS SETTINGS (データ出力設定)
# =============================================================================

# デフォルトのフィード設定
# FEEDS = {{
#     'output/%(name)s_%(time)s.json': {{
#         'format': 'json',
#         'encoding': 'utf8',
#         'store_empty': False,
#         'item_export_kwargs': {{
#             'ensure_ascii': False,
#         }},
#     }},
#     'output/%(name)s_%(time)s.csv': {{
#         'format': 'csv',
#         'encoding': 'utf8',
#         'store_empty': False,
#     }},
# }}

# =============================================================================
# CUSTOM SETTINGS
# =============================================================================

# カスタム設定（プロジェクト固有の設定をここに追加）
# CUSTOM_SETTINGS = {{
#     'DOWNLOAD_TIMEOUT': 180,
#     'RANDOMIZE_DOWNLOAD_DELAY': True,
#     'COOKIES_ENABLED': True,
#     'COOKIES_DEBUG': False,
# }}

# =============================================================================
# ADDITIONAL SCRAPY-PLAYWRIGHT SETTINGS
# =============================================================================

# Playwright用の追加設定
DOWNLOAD_TIMEOUT = 180
RANDOMIZE_DOWNLOAD_DELAY = True
COOKIES_ENABLED = True
COOKIES_DEBUG = False

# Playwright専用のリクエストメタ設定例
# PLAYWRIGHT_DEFAULT_PAGE_COROUTINES = [
#     PageCoroutine("wait_for_selector", "body"),
#     PageCoroutine("wait_for_timeout", 1000),
# ]

# Playwright用のプロキシ設定例
# PLAYWRIGHT_PROXY = {{
#     'server': 'http://proxy.example.com:8080',
#     'username': 'proxy_user',
#     'password': 'proxy_pass',
# }}

# Playwright用のブラウザ永続化設定例
# PLAYWRIGHT_BROWSER_PERSISTENT_CONTEXT_OPTIONS = {{
#     'user_data_dir': './browser_data',
#     'viewport': {{'width': 1280, 'height': 800}},
# }}
"""
    elif filename == 'items.py':
        return f"""# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags


def clean_text(value):
    \"\"\"テキストをクリーニングする関数\"\"\"
    if value:
        return value.strip().replace('\\n', ' ').replace('\\r', ' ')
    return value


def convert_price(value):
    \"\"\"価格文字列を数値に変換する関数\"\"\"
    if value:
        # 数字以外の文字を除去して数値に変換
        import re
        price_str = re.sub(r'[^0-9.]', '', value)
        try:
            return float(price_str)
        except ValueError:
            return 0.0
    return 0.0


class {project_name.capitalize()}Item(scrapy.Item):
    \"\"\"基本的なスクレイピングアイテム\"\"\"

    # 基本情報
    title = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )

    description = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )

    url = scrapy.Field(
        output_processor=TakeFirst()
    )

    # 日時情報
    published_date = scrapy.Field(
        output_processor=TakeFirst()
    )

    scraped_date = scrapy.Field(
        output_processor=TakeFirst()
    )


class ProductItem({project_name.capitalize()}Item):
    \"\"\"商品情報用のアイテム\"\"\"

    # 商品固有の情報
    product_name = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )

    price = scrapy.Field(
        input_processor=MapCompose(convert_price),
        output_processor=TakeFirst()
    )

    original_price = scrapy.Field(
        input_processor=MapCompose(convert_price),
        output_processor=TakeFirst()
    )

    discount_rate = scrapy.Field(
        output_processor=TakeFirst()
    )

    availability = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )

    brand = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )

    category = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )

    rating = scrapy.Field(
        output_processor=TakeFirst()
    )

    review_count = scrapy.Field(
        output_processor=TakeFirst()
    )

    images = scrapy.Field()

    specifications = scrapy.Field()


class ArticleItem({project_name.capitalize()}Item):
    \"\"\"記事情報用のアイテム\"\"\"

    # 記事固有の情報
    author = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )

    content = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=Join('\\n')
    )

    tags = scrapy.Field()

    category = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )

    view_count = scrapy.Field(
        output_processor=TakeFirst()
    )

    comment_count = scrapy.Field(
        output_processor=TakeFirst()
    )

    featured_image = scrapy.Field(
        output_processor=TakeFirst()
    )


class ContactItem({project_name.capitalize()}Item):
    \"\"\"連絡先情報用のアイテム\"\"\"

    # 連絡先固有の情報
    company_name = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )

    contact_person = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )

    email = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )

    phone = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )

    address = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )

    website = scrapy.Field(
        output_processor=TakeFirst()
    )

    social_media = scrapy.Field()


class ReviewItem({project_name.capitalize()}Item):
    \"\"\"レビュー情報用のアイテム\"\"\"

    # レビュー固有の情報
    reviewer_name = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )

    rating = scrapy.Field(
        output_processor=TakeFirst()
    )

    review_title = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )

    review_content = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )

    review_date = scrapy.Field(
        output_processor=TakeFirst()
    )

    helpful_count = scrapy.Field(
        output_processor=TakeFirst()
    )

    verified_purchase = scrapy.Field(
        output_processor=TakeFirst()
    )
"""
    elif filename == 'middlewares.py':
        return f"""# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import random
import time

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class {project_name.capitalize()}SpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    # Note: custom_settings should be defined in spider classes, not middleware classes

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn't have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class {project_name.capitalize()}DownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    # Note: custom_settings should be defined in spider classes, not middleware classes

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Playwright用のメタデータを追加する例
        if hasattr(spider, 'use_playwright') and spider.use_playwright:
            request.meta.update({{
                'playwright': True,
                'playwright_page_coroutines': [
                    # ページ読み込み完了まで待機
                    # PageCoroutine("wait_for_selector", "body"),
                    # PageCoroutine("wait_for_timeout", 1000),
                ],
            }})

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class PlaywrightUserAgentMiddleware:
    \"\"\"Playwright用のユーザーエージェントローテーションミドルウェア\"\"\"

    # Note: custom_settings should be defined in spider classes, not middleware classes

    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
        ]

    def process_request(self, request, spider):
        # ランダムなユーザーエージェントを設定
        ua = random.choice(self.user_agents)
        request.headers['User-Agent'] = ua

        # Playwright用の設定
        if request.meta.get('playwright'):
            request.meta.setdefault('playwright_context_kwargs', {{}})
            request.meta['playwright_context_kwargs']['user_agent'] = ua

        return None


class PlaywrightDelayMiddleware:
    \"\"\"Playwright用の遅延ミドルウェア\"\"\"

    # Note: custom_settings should be defined in spider classes, not middleware classes

    def __init__(self, delay_min=1, delay_max=3):
        self.delay_min = delay_min
        self.delay_max = delay_max

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        delay_min = settings.getfloat('PLAYWRIGHT_DELAY_MIN', 1)
        delay_max = settings.getfloat('PLAYWRIGHT_DELAY_MAX', 3)
        return cls(delay_min, delay_max)

    def process_request(self, request, spider):
        # Playwrightリクエストの場合のみ遅延を適用
        if request.meta.get('playwright'):
            delay = random.uniform(self.delay_min, self.delay_max)
            time.sleep(delay)
            spider.logger.debug(f'Playwright delay: {{delay:.2f}}s for {{request.url}}')

        return None
"""
    elif filename == 'pipelines.py':
        return f"""# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import json
import sqlite3
import csv
import os
from datetime import datetime
from pathlib import Path

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class {project_name.capitalize()}Pipeline:
    \"\"\"基本的なアイテムパイプライン\"\"\"

    # Note: custom_settings should be defined in spider classes, not pipeline classes

    def process_item(self, item, spider):
        # アイテムの基本的な処理
        adapter = ItemAdapter(item)

        # スクレイピング日時を追加
        adapter['scraped_date'] = datetime.now().isoformat()

        # 必要に応じてデータのクリーニング
        for field_name, value in adapter.items():
            if isinstance(value, str):
                # 空白文字の除去
                adapter[field_name] = value.strip()

        return item


class ValidationPipeline:
    \"\"\"データ検証パイプライン\"\"\"

    # Note: custom_settings should be defined in spider classes, not pipeline classes

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # 必須フィールドの検証
        required_fields = ['title', 'url']
        for field in required_fields:
            if not adapter.get(field):
                spider.logger.warning(f"Missing required field: {{field}} in {{adapter.get('url', 'unknown')}}")
                # 必要に応じてアイテムを破棄
                # raise DropItem(f"Missing required field: {{field}}")

        # URLの検証
        url = adapter.get('url')
        if url and not (url.startswith('http://') or url.startswith('https://')):
            spider.logger.warning(f"Invalid URL format: {{url}}")

        return item


class DuplicatesPipeline:
    \"\"\"重複除去パイプライン\"\"\"

    # Note: custom_settings should be defined in spider classes, not pipeline classes

    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # URLをユニークキーとして使用
        item_id = adapter.get('url')
        if item_id in self.ids_seen:
            spider.logger.info(f"Duplicate item found: {{item_id}}")
            # 重複アイテムを破棄
            # raise DropItem(f"Duplicate item found: {{item_id}}")
        else:
            self.ids_seen.add(item_id)
            return item


class JsonWriterPipeline:
    \"\"\"JSON出力パイプライン\"\"\"

    # Note: custom_settings should be defined in spider classes, not pipeline classes

    def open_spider(self, spider):
        # 出力ディレクトリの作成
        self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)

        # JSONファイルを開く
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{{spider.name}}_{{timestamp}}.json"
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


class CsvWriterPipeline:
    \"\"\"CSV出力パイプライン\"\"\"

    # Note: custom_settings should be defined in spider classes, not pipeline classes

    def open_spider(self, spider):
        # 出力ディレクトリの作成
        self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)

        # CSVファイルを開く
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{{spider.name}}_{{timestamp}}.csv"
        self.file = open(self.output_dir / filename, 'w', newline='', encoding='utf-8')
        self.writer = None

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # 最初のアイテムでヘッダーを書き込み
        if self.writer is None:
            self.writer = csv.DictWriter(self.file, fieldnames=adapter.field_names())
            self.writer.writeheader()

        self.writer.writerow(adapter.asdict())
        return item


class SQLitePipeline:
    \"\"\"SQLite保存パイプライン\"\"\"

    # Note: custom_settings should be defined in spider classes, not pipeline classes

    def open_spider(self, spider):
        # データベースディレクトリの作成
        db_dir = Path('data')
        db_dir.mkdir(exist_ok=True)

        # SQLiteデータベースに接続
        self.connection = sqlite3.connect(db_dir / f"{{spider.name}}.db")
        self.cursor = self.connection.cursor()

        # テーブルの作成（基本的な構造）
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                url TEXT UNIQUE,
                scraped_date TEXT,
                data TEXT
            )
        ''')
        self.connection.commit()

    def close_spider(self, spider):
        self.connection.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        try:
            # アイテムをJSONとして保存
            data_json = json.dumps(adapter.asdict(), ensure_ascii=False)

            self.cursor.execute('''
                INSERT OR REPLACE INTO items (title, description, url, scraped_date, data)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                adapter.get('title'),
                adapter.get('description'),
                adapter.get('url'),
                adapter.get('scraped_date'),
                data_json
            ))
            self.connection.commit()

        except sqlite3.Error as e:
            spider.logger.error(f"Database error: {{e}}")

        return item
"""
    elif filename == '__init__.py':
        return """# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

# ScrapyPlaywrightの設定
custom_settings = {
    "PLAYWRIGHT_BROWSER_TYPE": "chromium",
    "DOWNLOAD_HANDLERS": {
        "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    },
    "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
}

# Playwright用のヘルパー関数
def get_playwright_meta(wait_for_selector=None, wait_for_timeout=1000, context='default'):
    \"\"\"Playwright用のメタデータを生成するヘルパー関数\"\"\"
    meta = {
        'playwright': True,
        'playwright_context': context,
        'playwright_page_coroutines': []
    }

    if wait_for_selector:
        meta['playwright_page_coroutines'].append(
            ('wait_for_selector', wait_for_selector)
        )

    if wait_for_timeout:
        meta['playwright_page_coroutines'].append(
            ('wait_for_timeout', wait_for_timeout)
        )

    return meta


def get_mobile_meta():
    \"\"\"モバイル用のPlaywrightメタデータを取得\"\"\"
    return get_playwright_meta(context='mobile')


def get_desktop_meta():
    \"\"\"デスクトップ用のPlaywrightメタデータを取得\"\"\"
    return get_playwright_meta(context='desktop')
"""
    else:
        return ""

@router.get("/projects/{project_id}/files/", response_model=List[ProjectFileResponse])
async def get_project_files(project_id: str, db: Session = Depends(get_db)):
    """プロジェクトファイル一覧を取得"""
    # プロジェクトの存在確認
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    files_dir = get_project_files_dir(project_id)
    files = []

    for filename in SCRAPY_FILES:
        file_path = files_dir / filename
        if file_path.exists():
            content = file_path.read_text(encoding='utf-8')
        else:
            content = get_default_file_content(filename, project.name)

        files.append({
            "name": filename,
            "path": filename,
            "content": content,
            "size": len(content.encode('utf-8')),
            "modified_at": file_path.stat().st_mtime if file_path.exists() else None
        })

    return files

@router.get("/projects/{project_id}/files/{file_path:path}", response_model=ProjectFileResponse)
async def get_project_file(project_id: str, file_path: str, db: Session = Depends(get_db)):
    """特定のプロジェクトファイルを取得"""
    # プロジェクトの存在確認
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # ファイル名の検証（セキュリティチェック）
    if '..' in file_path or file_path.startswith('/'):
        raise HTTPException(status_code=400, detail="Invalid file path")

    files_dir = get_project_files_dir(project_id)
    file_full_path = files_dir / file_path

    if file_full_path.exists():
        content = file_full_path.read_text(encoding='utf-8')
    else:
        content = get_default_file_content(file_path, project.name)

    return {
        "name": file_path,
        "path": file_path,
        "content": content,
        "size": len(content.encode('utf-8')),
        "modified_at": file_full_path.stat().st_mtime if file_full_path.exists() else None
    }

@router.put("/projects/{project_id}/files/{file_path:path}")
async def update_project_file(
    project_id: str,
    file_path: str,
    file_update: ProjectFileUpdate,
    db: Session = Depends(get_db)
):
    """プロジェクトファイルを更新"""
    # プロジェクトの存在確認
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # ファイル名の検証（セキュリティチェック）
    if '..' in file_path or file_path.startswith('/'):
        raise HTTPException(status_code=400, detail="Invalid file path")

    # 標準ファイル以外も許可するが、拡張子をチェック
    allowed_extensions = ['.py', '.cfg', '.txt', '.md', '.json', '.yaml', '.yml']
    if not any(file_path.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(status_code=400, detail="File type not allowed")

    files_dir = ensure_project_files_dir(project_id)
    file_full_path = files_dir / file_path

    try:
        file_full_path.write_text(file_update.content, encoding='utf-8')
        return {"message": "File updated successfully"}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied to write file")
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"File system error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update file: {str(e)}")

@router.post("/projects/{project_id}/files")
async def create_project_file(
    project_id: str,
    file_create: ProjectFileCreate,
    db: Session = Depends(get_db)
):
    """新しいプロジェクトファイルを作成"""
    # プロジェクトの存在確認
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    files_dir = ensure_project_files_dir(project_id)
    file_full_path = files_dir / file_create.path

    if file_full_path.exists():
        raise HTTPException(status_code=400, detail="File already exists")

    try:
        file_full_path.write_text(file_create.content, encoding='utf-8')
        return {"message": "File created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create file: {str(e)}")

@router.delete("/projects/{project_id}/files/{file_path:path}")
async def delete_project_file(project_id: str, file_path: str, db: Session = Depends(get_db)):
    """プロジェクトファイルを削除"""
    # プロジェクトの存在確認
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # ファイル名の検証
    if file_path not in SCRAPY_FILES:
        raise HTTPException(status_code=400, detail="Invalid file path")

    files_dir = get_project_files_dir(project_id)
    file_full_path = files_dir / file_path

    if not file_full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        file_full_path.unlink()
        return {"message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
