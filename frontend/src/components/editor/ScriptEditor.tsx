'use client'

import React, { useRef, useEffect, useState } from 'react'
import Editor from '@monaco-editor/react'
import { Play, Save, FileText, Settings, Bug, Download, FileCode, Copy, X, RotateCcw } from 'lucide-react'

interface ScriptEditorProps {
  value: string
  onChange: (value: string) => void
  language?: string
  theme?: 'vs-dark' | 'light'
  readOnly?: boolean
  onSave?: () => void
  onRun?: () => void
  onTest?: () => void
  fileName?: string
  className?: string
}

export function ScriptEditor({
  value,
  onChange,
  language = 'python',
  theme = 'vs-dark',
  readOnly = false,
  onSave,
  onRun,
  onTest,
  fileName = 'spider.py',
  className = ''
}: ScriptEditorProps) {
  const editorRef = useRef<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errors, setErrors] = useState<any[]>([])
  const [showSettingsSnippet, setShowSettingsSnippet] = useState(false)
  const [showRestoreConfirm, setShowRestoreConfirm] = useState(false)

  // ファイルタイプを判定
  const getFileType = () => {
    const name = fileName.toLowerCase()
    if (name.includes('scrapy.cfg')) return 'scrapy_cfg'
    if (name.includes('__init__.py')) return 'init'
    if (name.includes('settings')) return 'settings'
    if (name.includes('items')) return 'items'
    if (name.includes('pipelines')) return 'pipelines'
    if (name.includes('middlewares')) return 'middlewares'
    return 'spider'
  }

  // スニペット生成（ファイルタイプに応じて）
  const generateSnippet = () => {
    const fileType = getFileType()

    // プロジェクト名を正しく取得
    let projectName = fileName.replace('.py', '').toLowerCase()

    // scrapy.cfgの場合は、URLからプロジェクト名を取得
    if (fileType === 'scrapy_cfg') {
      // URLパラメータからprojectPathを取得
      const urlParams = new URLSearchParams(window.location.search)
      const projectPath = urlParams.get('projectPath')
      if (projectPath) {
        projectName = projectPath.toLowerCase()
      } else {
        // フォールバック: demo_demoomochaproject
        projectName = 'demo_demoomochaproject'
      }
    }

    const capitalizedProjectName = projectName.charAt(0).toUpperCase() + projectName.slice(1)

    switch (fileType) {
      case 'scrapy_cfg':
        return generateScrapyCfgSnippet(projectName)
      case 'init':
        return generateInitSnippet(projectName)
      case 'settings':
        return generateSettingsSnippet(projectName)
      case 'items':
        return generateItemsSnippet(projectName, capitalizedProjectName)
      case 'pipelines':
        return generatePipelinesSnippet(projectName, capitalizedProjectName)
      case 'middlewares':
        return generateMiddlewaresSnippet(projectName, capitalizedProjectName)
      default:
        return generateSpiderSnippet(projectName, capitalizedProjectName)
    }
  }

  // scrapy.cfgスニペット生成
  const generateScrapyCfgSnippet = (projectName: string) => {
    return `# Automatically created by: scrapy startproject
#
# For more information about the [deploy] section see:
# https://scrapyd.readthedocs.io/en/latest/deploy.html

[settings]
default = ${projectName}.settings

[deploy]
#url = http://localhost:6800/
project = ${projectName}
`
  }

  // __init__.pyスニペット生成
  const generateInitSnippet = (projectName: string) => {
    // ファイルパスに基づいてスニペットを判定
    const filePath = fileName.toLowerCase()

    if (filePath.includes('/spiders/__init__.py') || filePath.includes('\\spiders\\__init__.py')) {
      // spiders/__init__.py用のスニペット
      return `# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
`
    } else {
      // プロジェクトルートの__init__.py用のスニペット（通常は空）
      return `# ${projectName} package
`
    }
  }

  // settings.pyスニペット生成
  const generateSettingsSnippet = (projectName: string) => {
    return `# Scrapy settings for ${projectName} project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = '${projectName}'

SPIDER_MODULES = ['${projectName}.spiders']
NEWSPIDER_MODULE = '${projectName}.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    '${projectName}.middlewares.${projectName.charAt(0).toUpperCase() + projectName.slice(1)}SpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    '${projectName}.middlewares.${projectName.charAt(0).toUpperCase() + projectName.slice(1)}DownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    '${projectName}.pipelines.${projectName.charAt(0).toUpperCase() + projectName.slice(1)}Pipeline': 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 1
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = 'utf-8'

# Custom settings (commented out for standard Scrapy configuration)
# DOWNLOAD_DELAY = 1
# RANDOMIZE_DOWNLOAD_DELAY = 0.5
# CONCURRENT_REQUESTS = 16
# CONCURRENT_REQUESTS_PER_DOMAIN = 8
# CONCURRENT_REQUESTS_PER_IP = 16
# COOKIES_ENABLED = True
# TELNETCONSOLE_ENABLED = False
# RETRY_ENABLED = True
# RETRY_TIMES = 2
# RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
# DEFAULT_REQUEST_HEADERS = {
#     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#     'Accept-Language': 'ja',
#     'User-Agent': '${projectName} (+http://www.yourdomain.com)',
# }
# HTTPCACHE_ENABLED = True
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_EXPIRATION_SECS = 86400  # 1 day

# ========================================
# Scrapy-Playwright Settings (Optional)
# ========================================
# Uncomment the following settings to enable Playwright support

# Download handlers for Playwright
#DOWNLOAD_HANDLERS = {
#    'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
#    'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
#}

# Playwright browser configuration
#PLAYWRIGHT_BROWSER_TYPE = 'chromium'  # Options: 'chromium', 'firefox', 'webkit'
#PLAYWRIGHT_LAUNCH_OPTIONS = {
#    'headless': True,
#    'args': ['--no-sandbox', '--disable-dev-shm-usage']
#}

# Playwright page configuration
#PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000  # 30 seconds
#PLAYWRIGHT_ABORT_REQUEST = lambda req: req.resource_type in ['image', 'stylesheet', 'font']

# Playwright context configuration
#PLAYWRIGHT_CONTEXTS = {
#    'default': {
#        'viewport': {'width': 1920, 'height': 1080},
#        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
#    },
#    'mobile': {
#        'viewport': {'width': 375, 'height': 667},
#        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
#    }
#}

# Playwright process configuration
#PLAYWRIGHT_PROCESS_REQUEST_TIMEOUT = 30
#PLAYWRIGHT_MAX_CONTEXTS = 15
#PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 1

# Proxy settings (optional - configure as needed)
# DOWNLOADER_MIDDLEWARES = {
#     'scrapy_proxies.RandomProxy': 350,
# }`
  }

  // items.pyスニペット生成
  const generateItemsSnippet = (projectName: string, capitalizedProjectName: string) => {
    return `# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags


def clean_text(value):
    """テキストをクリーニングする関数"""
    if value:
        return value.strip().replace('\\n', ' ').replace('\\r', ' ')
    return value


def convert_price(value):
    """価格文字列を数値に変換する関数"""
    if value:
        # 数字以外の文字を除去して数値に変換
        import re
        price_str = re.sub(r'[^0-9.]', '', value)
        try:
            return float(price_str)
        except ValueError:
            return 0.0
    return 0.0


class ${capitalizedProjectName}Item(scrapy.Item):
    """基本的なスクレイピングアイテム"""

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


class ProductItem(${capitalizedProjectName}Item):
    """商品情報用のアイテム"""

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

    image_urls = scrapy.Field()

    images = scrapy.Field()


class NewsItem(${capitalizedProjectName}Item):
    """ニュース記事用のアイテム"""

    # ニュース固有の情報
    headline = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )

    author = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )

    content = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )

    tags = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text)
    )

    source = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
`
  }

  // pipelines.pyスニペット生成
  const generatePipelinesSnippet = (projectName: string, capitalizedProjectName: string) => {
    return `# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import json
import sqlite3
import logging
from datetime import datetime, timezone
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class ${capitalizedProjectName}Pipeline:
    """基本的なアイテムパイプライン"""

    def process_item(self, item, spider):
        """アイテムを処理する"""
        adapter = ItemAdapter(item)

        # 必須フィールドの検証
        if not adapter.get('title'):
            raise DropItem(f"Missing title in {item}")

        # スクレイピング日時を追加
        adapter['scraped_date'] = datetime.now(timezone.utc).isoformat()

        return item


class ValidationPipeline:
    """データ検証パイプライン"""

    def process_item(self, item, spider):
        """アイテムの検証を行う"""
        adapter = ItemAdapter(item)

        # URLの検証
        if adapter.get('url') and not adapter['url'].startswith(('http://', 'https://')):
            raise DropItem(f"Invalid URL in {item}")

        # テキストフィールドの長さ制限
        if adapter.get('title') and len(adapter['title']) > 500:
            adapter['title'] = adapter['title'][:500] + '...'

        if adapter.get('description') and len(adapter['description']) > 2000:
            adapter['description'] = adapter['description'][:2000] + '...'

        return item


class DuplicatesPipeline:
    """重複除去パイプライン"""

    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        """重複アイテムを除去する"""
        adapter = ItemAdapter(item)

        # URLをユニークキーとして使用
        item_id = adapter.get('url')
        if item_id in self.ids_seen:
            raise DropItem(f"Duplicate item found: {item}")
        else:
            self.ids_seen.add(item_id)
            return item


class JsonWriterPipeline:
    """JSONファイル出力パイプライン"""

    def open_spider(self, spider):
        """スパイダー開始時にファイルを開く"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.file = open(f'{spider.name}_{timestamp}.json', 'w', encoding='utf-8')

    def close_spider(self, spider):
        """スパイダー終了時にファイルを閉じる"""
        self.file.close()

    def process_item(self, item, spider):
        """アイテムをJSONファイルに書き込む"""
        line = json.dumps(ItemAdapter(item).asdict(), ensure_ascii=False) + "\\n"
        self.file.write(line)
        return item


class SQLitePipeline:
    """SQLiteデータベース保存パイプライン"""

    def __init__(self, sqlite_db):
        self.sqlite_db = sqlite_db

    @classmethod
    def from_crawler(cls, crawler):
        """設定からデータベースパスを取得"""
        db_settings = crawler.settings.getdict("DATABASE")
        if db_settings:
            sqlite_db = db_settings.get('sqlite_db', 'scrapy_data.db')
        else:
            sqlite_db = 'scrapy_data.db'
        return cls(sqlite_db=sqlite_db)

    def open_spider(self, spider):
        """スパイダー開始時にデータベース接続を開く"""
        self.connection = sqlite3.connect(self.sqlite_db)
        self.cursor = self.connection.cursor()

        # テーブル作成
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                url TEXT UNIQUE,
                scraped_date TEXT,
                spider_name TEXT
            )
        ''')
        self.connection.commit()

    def close_spider(self, spider):
        """スパイダー終了時にデータベース接続を閉じる"""
        self.connection.close()

    def process_item(self, item, spider):
        """アイテムをデータベースに保存"""
        adapter = ItemAdapter(item)

        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO items (title, description, url, scraped_date, spider_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                adapter.get('title'),
                adapter.get('description'),
                adapter.get('url'),
                adapter.get('scraped_date'),
                spider.name
            ))
            self.connection.commit()
            logging.info(f"Item saved to database: {adapter.get('title')}")
        except sqlite3.Error as e:
            logging.error(f"Error saving item to database: {e}")
            raise DropItem(f"Error saving item: {e}")

        return item


class ImagesPipeline:
    """画像ダウンロードパイプライン"""

    def process_item(self, item, spider):
        """画像URLを処理する"""
        adapter = ItemAdapter(item)

        # 画像URLの正規化
        if adapter.get('image_urls'):
            normalized_urls = []
            for url in adapter['image_urls']:
                if url.startswith('//'):
                    url = 'https:' + url
                elif url.startswith('/'):
                    # 相対URLを絶対URLに変換
                    base_url = adapter.get('url', '')
                    if base_url:
                        from urllib.parse import urljoin
                        url = urljoin(base_url, url)
                normalized_urls.append(url)
            adapter['image_urls'] = normalized_urls

        return item
`
  }

  // middlewares.pyスニペット生成
  const generateMiddlewaresSnippet = (projectName: string, capitalizedProjectName: string) => {
    return `# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import random
import logging
from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message


class ${capitalizedProjectName}SpiderMiddleware:
    """スパイダーミドルウェア"""

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        """スパイダーの入力を処理"""
        return None

    def process_spider_output(self, response, result, spider):
        """スパイダーの出力を処理"""
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        """スパイダーの例外を処理"""
        pass

    def process_start_requests(self, start_requests, spider):
        """開始リクエストを処理"""
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        """スパイダー開始時の処理"""
        spider.logger.info('Spider opened: %s' % spider.name)


class ${capitalizedProjectName}DownloaderMiddleware:
    """ダウンローダーミドルウェア"""

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        """リクエストを処理"""
        return None

    def process_response(self, request, response, spider):
        """レスポンスを処理"""
        return response

    def process_exception(self, request, exception, spider):
        """例外を処理"""
        pass

    def spider_opened(self, spider):
        """スパイダー開始時の処理"""
        spider.logger.info('Spider opened: %s' % spider.name)


class UserAgentMiddleware:
    """ユーザーエージェントローテーションミドルウェア"""

    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
        ]

    def process_request(self, request, spider):
        """ランダムなユーザーエージェントを設定"""
        ua = random.choice(self.user_agents)
        request.headers['User-Agent'] = ua
        return None


class ProxyMiddleware:
    """プロキシミドルウェア"""

    def __init__(self):
        self.proxies = [
            # プロキシリストをここに追加
            # 'http://proxy1:port',
            # 'http://proxy2:port',
        ]

    def process_request(self, request, spider):
        """ランダムなプロキシを設定"""
        if self.proxies:
            proxy = random.choice(self.proxies)
            request.meta['proxy'] = proxy
        return None


class CustomRetryMiddleware(RetryMiddleware):
    """カスタムリトライミドルウェア"""

    def __init__(self, settings):
        super().__init__(settings)
        self.retry_http_codes = set(int(x) for x in settings.getlist('RETRY_HTTP_CODES'))

    def process_response(self, request, response, spider):
        """レスポンスに基づいてリトライを判定"""
        if request.meta.get('dont_retry', False):
            return response


class LoggingMiddleware:
    """ログ出力ミドルウェア"""

    def process_request(self, request, spider):
        """リクエストをログに記録"""
        spider.logger.info(f'Processing request: {request.url}')
        return None

    def process_response(self, request, response, spider):
        """レスポンスをログに記録"""
        spider.logger.info(f'Response received: {response.status} for {request.url}')
        return response


# ========================================
# Playwright Middlewares (Optional)
# ========================================
# Uncomment the following middlewares to enable Playwright support

#import asyncio
#from scrapy_playwright.page import PageCoroutine

#class PlaywrightUserAgentMiddleware:
#    """Playwright用のユーザーエージェントローテーションミドルウェア"""
#
#    def __init__(self):
#        self.user_agents = [
#            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#        ]
#
#    def process_request(self, request, spider):
#        """ランダムなユーザーエージェントを設定"""
#        if request.meta.get('playwright'):
#            ua = random.choice(self.user_agents)
#            request.meta.setdefault('playwright_context_kwargs', {})
#            request.meta['playwright_context_kwargs']['user_agent'] = ua
#        return None

#class PlaywrightDelayMiddleware:
#    """Playwright用の遅延ミドルウェア"""
#
#    def __init__(self, delay_min=1, delay_max=3):
#        self.delay_min = delay_min
#        self.delay_max = delay_max
#
#    @classmethod
#    def from_crawler(cls, crawler):
#        settings = crawler.settings
#        delay_min = settings.getfloat('PLAYWRIGHT_DELAY_MIN', 1)
#        delay_max = settings.getfloat('PLAYWRIGHT_DELAY_MAX', 3)
#        return cls(delay_min, delay_max)
#
#    def process_request(self, request, spider):
#        """Playwrightリクエストの場合のみ遅延を適用"""
#        if request.meta.get('playwright'):
#            delay = random.uniform(self.delay_min, self.delay_max)
#            request.meta.setdefault('playwright_page_coroutines', [])
#            request.meta['playwright_page_coroutines'].append(
#                PageCoroutine('wait_for_timeout', delay * 1000)
#            )
#        return None

#class PlaywrightScrollMiddleware:
#    """Playwright用のスクロールミドルウェア"""
#
#    def process_request(self, request, spider):
#        """ページを最下部までスクロール"""
#        if request.meta.get('playwright') and request.meta.get('scroll_to_bottom'):
#            request.meta.setdefault('playwright_page_coroutines', [])
#            request.meta['playwright_page_coroutines'].extend([
#                PageCoroutine('evaluate', '''
#                    async () => {
#                        await new Promise((resolve) => {
#                            let totalHeight = 0;
#                            const distance = 100;
#                            const timer = setInterval(() => {
#                                const scrollHeight = document.body.scrollHeight;
#                                window.scrollBy(0, distance);
#                                totalHeight += distance;
#                                if(totalHeight >= scrollHeight){
#                                    clearInterval(timer);
#                                    resolve();
#                                }
#                            }, 100);
#                        });
#                    }
#                '''),
#                PageCoroutine('wait_for_timeout', 1000)
#            ])
#        return None

        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response

        return response

    def process_exception(self, request, exception, spider):
        """例外に基づいてリトライを判定"""
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) and not request.meta.get('dont_retry', False):
            return self._retry(request, exception, spider)


class LoggingMiddleware:
    """ログ出力ミドルウェア"""

    def process_request(self, request, spider):
        """リクエストをログ出力"""
        spider.logger.info(f'Processing request: {request.url}')
        return None

    def process_response(self, request, response, spider):
        """レスポンスをログ出力"""
        spider.logger.info(f'Received response: {response.status} for {request.url}')
        return response

    def process_exception(self, request, exception, spider):
        """例外をログ出力"""
        spider.logger.error(f'Exception occurred: {exception} for {request.url}')
        pass
`
  }

  // spider用スニペット生成
  const generateSpiderSnippet = (projectName: string, capitalizedProjectName: string) => {
    return `import scrapy
from scrapy import Request
from ${projectName}.items import ${capitalizedProjectName}Item

# Playwright imports (uncomment when using Playwright)
# from scrapy_playwright.page import PageCoroutine


class ${capitalizedProjectName}Spider(scrapy.Spider):
    """${capitalizedProjectName} Spider"""

    name = '${projectName}'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com']

    # カスタム設定
    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
    }

    def parse(self, response):
        """メインのパース関数"""
        # ページ内のリンクを抽出
        links = response.css('a::attr(href)').getall()

        for link in links:
            if link:
                # 相対URLを絶対URLに変換
                absolute_url = response.urljoin(link)
                yield Request(
                    url=absolute_url,
                    callback=self.parse_item,
                    meta={'page_url': response.url}
                )

        # 次のページへのリンクを処理
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield Request(
                url=response.urljoin(next_page),
                callback=self.parse
            )

    def parse_item(self, response):
        """個別アイテムのパース"""
        item = ${capitalizedProjectName}Item()

        # 基本情報を抽出
        item['title'] = response.css('h1::text').get()
        item['description'] = response.css('.description::text').get()
        item['url'] = response.url

        # メタ情報を追加
        item['page_url'] = response.meta.get('page_url')

        # デバッグ情報を出力
        self.logger.info(f'Scraped item: {item["title"]} from {response.url}')

        yield item

    def parse_with_css(self, response):
        """CSSセレクターを使用したパース例"""
        items = response.css('.item')

        for item_selector in items:
            item = ${capitalizedProjectName}Item()

            item['title'] = item_selector.css('.title::text').get()
            item['description'] = item_selector.css('.description::text').get()
            item['url'] = item_selector.css('a::attr(href)').get()

            if item['url']:
                item['url'] = response.urljoin(item['url'])

            yield item

    def parse_with_xpath(self, response):
        """XPathを使用したパース例"""
        items = response.xpath('//div[@class="item"]')

        for item_selector in items:
            item = ${capitalizedProjectName}Item()

            item['title'] = item_selector.xpath('.//h2/text()').get()
            item['description'] = item_selector.xpath('.//p[@class="description"]/text()').get()
            item['url'] = item_selector.xpath('.//a/@href').get()

            if item['url']:
                item['url'] = response.urljoin(item['url'])

            yield item

    def start_requests(self):
        """開始リクエストをカスタマイズ"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for url in self.start_urls:
            yield Request(
                url=url,
                headers=headers,
                callback=self.parse,
                meta={'download_timeout': 30}
            )

    def closed(self, reason):
        """スパイダー終了時の処理"""
        self.logger.info(f'Spider closed: {reason}')


# ========================================
# Playwright Spider Examples (Optional)
# ========================================
# Uncomment the following class to enable Playwright support

# class ${capitalizedProjectName}PlaywrightSpider(scrapy.Spider):
#     """Playwright対応スパイダー"""
#
#     name = '${projectName}_playwright'
#     allowed_domains = ['example.com']
#     start_urls = ['https://example.com']
#
#     # Playwright用のカスタム設定
#     custom_settings = {
#         'DOWNLOAD_HANDLERS': {
#             'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
#             'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
#         },
#         'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
#         'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
#         'PLAYWRIGHT_LAUNCH_OPTIONS': {
#             'headless': True,
#         },
#     }
#
#     def start_requests(self):
#         """Playwright用の開始リクエスト"""
#         for url in self.start_urls:
#             yield scrapy.Request(
#                 url=url,
#                 meta={
#                     'playwright': True,
#                     'playwright_page_coroutines': [
#                         PageCoroutine('wait_for_selector', 'body'),
#                         PageCoroutine('wait_for_timeout', 2000),
#                     ],
#                 },
#                 callback=self.parse
#             )
#
#     def parse(self, response):
#         """Playwrightレスポンスのパース"""
#         # ページが完全に読み込まれた後の処理
#         items = response.css('.item')
#
#         for item_selector in items:
#             item = ${capitalizedProjectName}Item()
#             item['title'] = item_selector.css('.title::text').get()
#             item['description'] = item_selector.css('.description::text').get()
#             item['url'] = response.url
#             yield item
#
#         # 次のページへのリンク（JavaScript処理が必要な場合）
#         next_page_button = response.css('button.next-page')
#         if next_page_button:
#             yield scrapy.Request(
#                 url=response.url,
#                 meta={
#                     'playwright': True,
#                     'playwright_page_coroutines': [
#                         PageCoroutine('click', 'button.next-page'),
#                         PageCoroutine('wait_for_selector', '.item'),
#                         PageCoroutine('wait_for_timeout', 1000),
#                     ],
#                 },
#                 callback=self.parse,
#                 dont_filter=True
#             )
#
#     def parse_with_scroll(self, response):
#         """スクロールが必要なページの処理"""
#         yield scrapy.Request(
#             url=response.url,
#             meta={
#                 'playwright': True,
#                 'playwright_page_coroutines': [
#                     PageCoroutine('evaluate', '''
#                         async () => {
#                             await new Promise((resolve) => {
#                                 let totalHeight = 0;
#                                 const distance = 100;
#                                 const timer = setInterval(() => {
#                                     const scrollHeight = document.body.scrollHeight;
#                                     window.scrollBy(0, distance);
#                                     totalHeight += distance;
#                                     if(totalHeight >= scrollHeight){
#                                         clearInterval(timer);
#                                         resolve();
#                                     }
#                                 }, 100);
#                             });
#                         }
#                     '''),
#                     PageCoroutine('wait_for_timeout', 2000),
#                 ],
#             },
#             callback=self.parse_scrolled_content
#         )
#
#     def parse_scrolled_content(self, response):
#         """スクロール後のコンテンツを処理"""
#         items = response.css('.dynamic-item')
#         for item_selector in items:
#             item = ${capitalizedProjectName}Item()
#             item['title'] = item_selector.css('.title::text').get()
#             item['url'] = response.url
#             yield item
`
  }

  const copySnippet = () => {
    const snippet = generateSnippet()
    navigator.clipboard.writeText(snippet)
  }

  const restoreDefaultCode = () => {
    setShowRestoreConfirm(true)
  }

  const confirmRestoreDefaultCode = () => {
    const defaultCode = generateSnippet()
    onChange(defaultCode)
    setShowRestoreConfirm(false)
  }

  const downloadSnippet = () => {
    const snippet = generateSnippet()
    const fileType = getFileType()
    const projectName = fileName.replace(/\.(py|cfg)$/, '').replace('__init__', 'init').toLowerCase()
    const blob = new Blob([snippet], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url

    // ファイル拡張子を適切に設定
    let extension = '.py'
    if (fileType === 'scrapy_cfg') {
      extension = '.cfg'
    } else if (fileType === 'init') {
      extension = '.py'
    }

    a.download = `${projectName}_${fileType}${extension}`

    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const getSnippetTitle = () => {
    const fileType = getFileType()
    const filePath = fileName.toLowerCase()

    switch (fileType) {
      case 'scrapy_cfg': return 'Scrapy.cfg Snippet'
      case 'init':
        if (filePath.includes('/spiders/__init__.py') || filePath.includes('\\spiders\\__init__.py')) {
          return 'Spiders __init__.py Snippet'
        } else {
          return '__init__.py Snippet'
        }
      case 'settings': return 'Settings.py Snippet'
      case 'items': return 'Items.py Snippet'
      case 'pipelines': return 'Pipelines.py Snippet'
      case 'middlewares': return 'Middlewares.py Snippet'
      default: return 'Spider.py Snippet'
    }
  }

  const getSnippetDescription = () => {
    const fileType = getFileType()
    const filePath = fileName.toLowerCase()

    switch (fileType) {
      case 'scrapy_cfg':
        return {
          usage: 'このスニペットをプロジェクトルートの scrapy.cfg ファイルにコピーしてください',
          config: 'プロジェクト名とsettingsモジュールの設定が含まれています',
          standard: 'Scrapy標準のプロジェクト設定ファイルです'
        }
      case 'init':
        if (filePath.includes('/spiders/__init__.py') || filePath.includes('\\spiders\\__init__.py')) {
          return {
            usage: 'このスニペットをspidersディレクトリの __init__.py ファイルにコピーしてください',
            config: 'スパイダーパッケージの初期化ファイルです',
            standard: 'Scrapy標準のスパイダーパッケージ設定です'
          }
        } else {
          return {
            usage: 'このスニペットをプロジェクトの __init__.py ファイルにコピーしてください',
            config: 'プロジェクトパッケージの初期化ファイルです',
            standard: 'Python標準のパッケージ初期化ファイルです'
          }
        }
      case 'settings':
        return {
          usage: 'このスニペットをプロジェクトの settings.py ファイルにコピーしてください',
          config: 'Scrapy標準設定とPlaywright設定（コメントアウト）が含まれています',
          standard: 'Scrapy標準設定のみが有効で、Playwright設定はコメントアウトされています'
        }
      case 'items':
        return {
          usage: 'このスニペットをプロジェクトの items.py ファイルにコピーしてください',
          config: '基本アイテム、商品アイテム、ニュースアイテムのクラスが含まれています',
          standard: 'ItemLoaderとプロセッサーを使用したデータクリーニング機能付きです'
        }
      case 'pipelines':
        return {
          usage: 'このスニペットをプロジェクトの pipelines.py ファイルにコピーしてください',
          config: '検証、重複除去、JSON出力、SQLite保存などのパイプラインが含まれています',
          standard: 'settings.pyのITEM_PIPELINESに追加して有効化してください'
        }
      case 'middlewares':
        return {
          usage: 'このスニペットをプロジェクトの middlewares.py ファイルにコピーしてください',
          config: 'ユーザーエージェント、プロキシ、リトライ、Playwrightミドルウェア（コメントアウト）が含まれています',
          standard: 'settings.pyのMIDDLEWARESに追加して有効化してください'
        }
      default:
        return {
          usage: 'このスニペットを新しいスパイダーファイルにコピーしてください',
          config: 'CSS、XPath、カスタムリクエスト、Playwrightスパイダー（コメントアウト）の実装例が含まれています',
          standard: 'プロジェクトのitemsとの連携とPlaywright対応が設定されています'
        }
    }
  }

  const handleEditorDidMount = (editor: any, monaco: any) => {
    editorRef.current = editor
    setIsLoading(false)

    // Python言語設定の拡張
    if (language === 'python') {
      monaco.languages.setLanguageConfiguration('python', {
        comments: {
          lineComment: '#',
          blockComment: ['"""', '"""']
        },
        brackets: [
          ['{', '}'],
          ['[', ']'],
          ['(', ')']
        ],
        autoClosingPairs: [
          { open: '{', close: '}' },
          { open: '[', close: ']' },
          { open: '(', close: ')' },
          { open: '"', close: '"' },
          { open: "'", close: "'" }
        ],
        surroundingPairs: [
          { open: '{', close: '}' },
          { open: '[', close: ']' },
          { open: '(', close: ')' },
          { open: '"', close: '"' },
          { open: "'", close: "'" }
        ]
      })

      // Scrapy固有のキーワードとクラスの追加
      monaco.languages.registerCompletionItemProvider('python', {
        provideCompletionItems: (model: any, position: any) => {
          const suggestions = [
            {
              label: 'scrapy.Spider',
              kind: monaco.languages.CompletionItemKind.Class,
              insertText: 'scrapy.Spider',
              documentation: 'Base Spider class'
            },
            {
              label: 'start_urls',
              kind: monaco.languages.CompletionItemKind.Property,
              insertText: 'start_urls = []',
              documentation: 'List of URLs to start crawling from'
            },
            {
              label: 'parse',
              kind: monaco.languages.CompletionItemKind.Method,
              insertText: [
                'def parse(self, response):',
                '    """Parse the response and extract data."""',
                '    pass'
              ].join('\n'),
              documentation: 'Default callback method for parsing responses'
            },
            {
              label: 'scrapy.Request',
              kind: monaco.languages.CompletionItemKind.Class,
              insertText: 'scrapy.Request(url, callback=self.parse)',
              documentation: 'Create a new request'
            },
            {
              label: 'response.css',
              kind: monaco.languages.CompletionItemKind.Method,
              insertText: 'response.css("selector")',
              documentation: 'CSS selector for extracting data'
            },
            {
              label: 'response.xpath',
              kind: monaco.languages.CompletionItemKind.Method,
              insertText: 'response.xpath("//xpath")',
              documentation: 'XPath selector for extracting data'
            },
            {
              label: 'yield',
              kind: monaco.languages.CompletionItemKind.Keyword,
              insertText: 'yield',
              documentation: 'Yield items or requests'
            }
          ]
          return { suggestions }
        }
      })
    }

    // キーボードショートカット
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      onSave?.()
    })

    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
      onRun?.()
    })
  }

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      onChange(value)
    }
  }

  const formatCode = () => {
    if (editorRef.current) {
      editorRef.current.getAction('editor.action.formatDocument').run()
    }
  }

  const downloadCode = () => {
    const blob = new Blob([value], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className={`flex flex-col h-full bg-gray-900 ${className}`}>
      {/* ファイル名とメインアクションボタン */}
      <div className="flex items-center justify-between p-3 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center space-x-2">
          <FileText className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-300">{fileName}</span>
        </div>

        <div className="flex items-center space-x-2">
          {onSave && (
            <button
              onClick={onSave}
              className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors flex items-center space-x-1"
              title="Save (Ctrl+S)"
            >
              <Save className="w-4 h-4" />
              <span className="text-sm">Save</span>
            </button>
          )}

          {onTest && (
            <button
              onClick={onTest}
              className="px-3 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded transition-colors flex items-center space-x-1"
              title="Quick Test"
            >
              <Bug className="w-4 h-4" />
              <span className="text-sm">Test</span>
            </button>
          )}

          {onRun && (
            <button
              onClick={onRun}
              className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition-colors flex items-center space-x-1"
              title="Run (Ctrl+Enter)"
            >
              <Play className="w-4 h-4" />
              <span className="text-sm">Run</span>
            </button>
          )}
        </div>
      </div>

      {/* ツールバー */}
      <div className="flex items-center justify-end p-2 bg-gray-750 border-b border-gray-700">
        <div className="flex items-center space-x-1">
          <button
            onClick={formatCode}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
            title="Format Code (Shift+Alt+F)"
          >
            <Settings className="w-4 h-4" />
          </button>

          <button
            onClick={downloadCode}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
            title="Download"
          >
            <Download className="w-4 h-4" />
          </button>

          <button
            onClick={() => setShowSettingsSnippet(true)}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
            title={getSnippetTitle()}
          >
            <FileCode className="w-4 h-4" />
          </button>

          <button
            onClick={restoreDefaultCode}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
            title="Restore Default Code"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* エディター */}
      <div className="flex-1 relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
            <div className="text-gray-400">Loading editor...</div>
          </div>
        )}

        <Editor
          height="100%"
          language={language}
          theme={theme}
          value={value}
          onChange={handleEditorChange}
          onMount={handleEditorDidMount}
          options={{
            readOnly,
            minimap: { enabled: true },
            fontSize: 14,
            lineNumbers: 'on',
            roundedSelection: false,
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 4,
            insertSpaces: true,
            wordWrap: 'on',
            folding: true,
            foldingStrategy: 'indentation',
            showFoldingControls: 'always',
            bracketPairColorization: { enabled: true },
            guides: {
              bracketPairs: true,
              indentation: true
            },
            suggest: {
              showKeywords: true,
              showSnippets: true,
              showClasses: true,
              showFunctions: true,
              showVariables: true
            },
            quickSuggestions: {
              other: true,
              comments: false,
              strings: false
            },
            parameterHints: {
              enabled: true
            },
            hover: {
              enabled: true
            }
          }}
        />
      </div>

      {/* エラー表示 */}
      {errors.length > 0 && (
        <div className="p-3 bg-red-900 border-t border-red-700">
          <div className="flex items-center space-x-2 mb-2">
            <Bug className="w-4 h-4 text-red-400" />
            <span className="text-sm text-red-300 font-medium">Errors</span>
          </div>
          <div className="space-y-1">
            {errors.map((error, index) => (
              <div key={index} className="text-sm text-red-200">
                Line {error.line}: {error.message}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Settings.py スニペットモーダル */}
      {showSettingsSnippet && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] flex flex-col">
            {/* ヘッダー */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <div className="flex items-center space-x-2">
                <FileCode className="w-5 h-5 text-blue-400" />
                <h3 className="text-lg font-semibold text-white">{getSnippetTitle()}</h3>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={copySnippet}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors flex items-center space-x-1"
                  title="Copy to Clipboard"
                >
                  <Copy className="w-4 h-4" />
                  <span>Copy</span>
                </button>
                <button
                  onClick={downloadSnippet}
                  className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors flex items-center space-x-1"
                  title="Download File"
                >
                  <Download className="w-4 h-4" />
                  <span>Download</span>
                </button>
                <button
                  onClick={() => setShowSettingsSnippet(false)}
                  className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
                  title="Close"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* コンテンツ */}
            <div className="flex-1 overflow-hidden">
              <Editor
                height="70vh"
                language={getFileType() === 'scrapy_cfg' ? 'ini' : 'python'}
                theme="vs-dark"
                value={generateSnippet()}
                options={{
                  readOnly: true,
                  minimap: { enabled: false },
                  fontSize: 13,
                  lineNumbers: 'on',
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  wordWrap: 'on',
                  folding: true,
                  bracketPairColorization: { enabled: true },
                  guides: {
                    bracketPairs: true,
                    indentation: true
                  }
                }}
              />
            </div>

            {/* フッター */}
            <div className="p-4 border-t border-gray-700 bg-gray-750">
              <div className="text-sm text-gray-400">
                <p className="mb-1">
                  <strong className="text-gray-300">📝 使用方法:</strong> {getSnippetDescription().usage}
                </p>
                <p className="mb-1">
                  <strong className="text-gray-300">⚙️ 設定:</strong> {getSnippetDescription().config}
                </p>
                <p>
                  <strong className="text-gray-300">🔧 標準準拠:</strong> {getSnippetDescription().standard}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* デフォルトコード復旧確認ダイアログ */}
      {showRestoreConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4">
            {/* ヘッダー */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <div className="flex items-center space-x-2">
                <RotateCcw className="w-5 h-5 text-orange-400" />
                <h3 className="text-lg font-semibold text-white">デフォルトコード復旧</h3>
              </div>
            </div>

            {/* コンテンツ */}
            <div className="p-4">
              <p className="text-gray-300 mb-4">
                現在のコードを削除して、デフォルトの{getSnippetTitle().replace(' Snippet', '')}コードに復旧しますか？
              </p>
              <div className="bg-yellow-900 border border-yellow-700 rounded p-3 mb-4">
                <div className="flex items-center space-x-2">
                  <span className="text-yellow-400">⚠️</span>
                  <span className="text-yellow-200 text-sm font-medium">注意</span>
                </div>
                <p className="text-yellow-200 text-sm mt-1">
                  この操作は元に戻せません。現在の変更内容は失われます。
                </p>
              </div>
            </div>

            {/* フッター */}
            <div className="flex items-center justify-end space-x-3 p-4 border-t border-gray-700">
              <button
                onClick={() => setShowRestoreConfirm(false)}
                className="px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded transition-colors"
              >
                キャンセル
              </button>
              <button
                onClick={confirmRestoreDefaultCode}
                className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded transition-colors flex items-center space-x-2"
              >
                <RotateCcw className="w-4 h-4" />
                <span>復旧する</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
