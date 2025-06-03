import React from 'react'
import { Chrome, Zap } from 'lucide-react'
import { Template } from '../types'

export const puppeteerTemplates: Template[] = [
  {
    id: 'puppeteer-basic',
    name: 'Puppeteer Basic Spider',
    description: 'Node.js Puppeteerを使用した基本的なスパイダー（JavaScript重要サイト対応）',
    icon: <Chrome className="w-5 h-5" />,
    category: 'browser-automation',
    code: `import scrapy
import json
from urllib.parse import urljoin
from datetime import datetime


class PuppeteerSpider(scrapy.Spider):
    """
    Node.js Puppeteerを使用したスパイダー
    JavaScript重要なSPAサイトやダイナミックコンテンツの取得に使用
    """

    name = 'puppeteer_spider'
    allowed_domains = []
    start_urls = [
        'https://example.com'
    ]

    # Puppeteerサービスの設定
    puppeteer_service_url = 'http://localhost:3001'

    # デフォルト設定
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,

        # フィード設定
        'FEEDS': {
            'results/%(name)s_%(time)s.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'overwrite': True,
            },
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # クロールスタート日時を記録
        self.crawl_start_time = datetime.now()

    def make_puppeteer_request(self, url, **kwargs):
        """
        Puppeteerサービスを使用してリクエストを作成
        """
        # デフォルトのPuppeteerデータ
        puppeteer_data = {
            'url': url,
            'viewport': {'width': 1920, 'height': 1080},
            'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'timeout': 30000,
            'waitFor': 3000,
            'extractData': {
                'selectors': {
                    'title': 'title, h1, .title',
                    'content': 'main, .content, article, body',
                    'links': 'a[href]',
                    'images': 'img[src]'
                },
                'javascript': '''
                    return {
                        pageHeight: document.body.scrollHeight,
                        linkCount: document.querySelectorAll('a').length,
                        imageCount: document.querySelectorAll('img').length,
                        loadTime: performance.now(),
                        currentUrl: window.location.href,
                        title: document.title
                    };
                '''
            },
            'screenshot': False,
            'fullPage': False
        }

        return scrapy.Request(
            url=f"{self.puppeteer_service_url}/api/scraping/spa",
            method='POST',
            headers={
                'Content-Type': 'application/json',
                'x-api-key': 'scrapyui-nodejs-service-key-2024'
            },
            body=json.dumps(puppeteer_data),
            callback=self.parse_puppeteer_response,
            meta={
                'original_url': url,
                'puppeteer_data': puppeteer_data,
                **kwargs.get('meta', {})
            }
        )

    def parse_puppeteer_response(self, response):
        """
        Puppeteerサービスからのレスポンスを解析
        """
        try:
            data = json.loads(response.text)
            
            if not data.get('success'):
                self.logger.error(f"Puppeteer request failed: {data.get('message', 'Unknown error')}")
                return
            
            # 元のURLとPuppeteerデータを取得
            original_url = response.meta.get('original_url')
            
            # レスポンスデータを解析
            result_data = data.get('data', {})
            extracted_data = result_data.get('extractedData', {})
            custom_data = result_data.get('customData', {})
            page_info = result_data.get('pageInfo', {})
            
            # アイテムを作成
            item = {}
            
            # 基本情報
            item['url'] = original_url
            item['scraped_at'] = datetime.now().isoformat()
            item['crawl_start_time'] = self.crawl_start_time.isoformat()
            
            # ページ情報
            item['page_title'] = page_info.get('title', '')
            item['final_url'] = page_info.get('url', original_url)
            
            # 抽出されたデータ
            item['title'] = extracted_data.get('title', '')
            item['content'] = extracted_data.get('content', '')
            item['links'] = extracted_data.get('links', [])
            item['images'] = extracted_data.get('images', [])
            
            # カスタムJavaScriptデータ
            item['page_height'] = custom_data.get('pageHeight', 0)
            item['link_count'] = custom_data.get('linkCount', 0)
            item['image_count'] = custom_data.get('imageCount', 0)
            item['load_time'] = custom_data.get('loadTime', 0)
            
            self.logger.info(f"Successfully scraped: {original_url}")
            yield item
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
        except Exception as e:
            self.logger.error(f"Error processing Puppeteer response: {e}")

    def start_requests(self):
        """
        開始リクエストを生成（互換性のため）
        """
        for url in self.start_urls:
            yield self.make_puppeteer_request(url)
    
    async def start(self):
        """
        開始リクエストを生成（新しいasyncメソッド）
        """
        for url in self.start_urls:
            yield self.make_puppeteer_request(url)
`
  },
  {
    id: 'puppeteer-spa',
    name: 'Puppeteer SPA Spider',
    description: 'SPA（Single Page Application）対応のPuppeteerスパイダー',
    icon: <Zap className="w-5 h-5" />,
    category: 'browser-automation',
    code: `import scrapy
import json
from urllib.parse import urljoin
from datetime import datetime


class SPAPuppeteerSpider(scrapy.Spider):
    """
    SPA（Single Page Application）対応のPuppeteerスパイダー
    """

    name = 'spa_puppeteer'
    allowed_domains = []
    start_urls = [
        'https://example-spa.com'
    ]

    # Puppeteerサービスの設定
    puppeteer_service_url = 'http://localhost:3001'

    def start_requests(self):
        """
        SPA用の設定でリクエストを開始
        """
        for url in self.start_urls:
            yield self.make_spa_request(url)

    def make_spa_request(self, url):
        """
        SPA用のPuppeteerリクエストを作成
        """
        puppeteer_data = {
            'url': url,
            'viewport': {'width': 1920, 'height': 1080},
            'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'timeout': 60000,
            'waitFor': 5000,
            'extractData': {
                'selectors': {
                    'content': '.app, #app, main, .main-content',
                    'navigation': 'nav, .nav, .navigation',
                    'dynamic_items': '.item, .card, .product',
                    'buttons': 'button, .btn',
                    'forms': 'form, .form'
                }
            },
            'screenshot': True,
            'fullPage': True
        }

        return scrapy.Request(
            url=f"{self.puppeteer_service_url}/api/scraping/spa",
            method='POST',
            headers={
                'Content-Type': 'application/json',
                'x-api-key': 'scrapyui-nodejs-service-key-2024'
            },
            body=json.dumps(puppeteer_data),
            callback=self.parse_spa_response,
            meta={'original_url': url}
        )

    def parse_spa_response(self, response):
        """
        SPAレスポンスを解析
        """
        try:
            data = json.loads(response.text)
            
            if data.get('success'):
                result_data = data.get('data', {})
                original_url = response.meta.get('original_url')
                
                item = {
                    'url': original_url,
                    'spa_content': result_data.get('extractedData', {}),
                    'screenshot': result_data.get('screenshot'),
                    'scraped_at': datetime.now().isoformat()
                }
                
                yield item
                
        except Exception as e:
            self.logger.error(f"Error parsing SPA response: {e}")
`
  }
]
