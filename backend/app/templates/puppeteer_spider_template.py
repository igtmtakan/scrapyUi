"""
Puppeteerスパイダーテンプレート
Node.js Puppeteerサービスを使用したWebスクレイピング
"""

import scrapy
import json
import requests
from urllib.parse import urljoin
from datetime import datetime


class PuppeteerSpider(scrapy.Spider):
    """
    Puppeteerを使用したスパイダーのベースクラス
    JavaScript重要なSPAサイトやダイナミックコンテンツの取得に使用
    """
    
    name = 'puppeteer_spider'
    
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
        self.puppeteer_config = {
            'viewport': {'width': 1920, 'height': 1080},
            'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'timeout': 30000,
            'waitFor': 3000,  # デフォルト待機時間
        }
    
    def start_requests(self):
        """
        開始リクエストを生成
        サブクラスでオーバーライドして使用
        """
        urls = getattr(self, 'start_urls', [])
        for url in urls:
            yield self.make_puppeteer_request(url)
    
    def make_puppeteer_request(self, url, **kwargs):
        """
        Puppeteerを使用したリクエストを作成
        """
        # Puppeteer設定をマージ
        config = {**self.puppeteer_config, **kwargs}
        
        # Puppeteerサービスへのリクエストデータ
        puppeteer_data = {
            'url': url,
            'viewport': config.get('viewport'),
            'userAgent': config.get('userAgent'),
            'timeout': config.get('timeout'),
            'waitFor': config.get('waitFor'),
            'extractData': config.get('extractData'),
            'screenshot': config.get('screenshot', False),
            'fullPage': config.get('fullPage', False),
        }
        
        # 不要なNone値を削除
        puppeteer_data = {k: v for k, v in puppeteer_data.items() if v is not None}
        
        return scrapy.Request(
            url=f"{self.puppeteer_service_url}/api/scraping/spa",
            method='POST',
            headers={'Content-Type': 'application/json'},
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
                self.logger.error(f"Puppeteer scraping failed: {data.get('message', 'Unknown error')}")
                return
            
            scraping_data = data.get('data', {})
            original_url = response.meta.get('original_url')
            
            # 基本的なアイテムデータ
            item = {
                'url': original_url,
                'scraped_url': scraping_data.get('url'),
                'title': scraping_data.get('pageInfo', {}).get('title'),
                'timestamp': scraping_data.get('timestamp'),
                'scraped_at': datetime.now().isoformat(),
            }
            
            # 抽出されたデータを追加
            if 'extractedData' in scraping_data:
                item.update(scraping_data['extractedData'])
            
            # カスタムJavaScriptの結果を追加
            if 'customData' in scraping_data:
                item['custom_data'] = scraping_data['customData']
            
            # スクリーンショットデータを追加
            if 'screenshot' in scraping_data:
                item['screenshot'] = scraping_data['screenshot']
            
            yield item
            
            # 追加のリンクを抽出する場合
            yield from self.extract_additional_links(scraping_data, response)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Puppeteer response: {e}")
        except Exception as e:
            self.logger.error(f"Error processing Puppeteer response: {e}")
    
    def extract_additional_links(self, scraping_data, response):
        """
        スクレイピングデータから追加のリンクを抽出
        サブクラスでオーバーライドして使用
        """
        return []
    
    def make_dynamic_request(self, url, actions, extract_after=None, **kwargs):
        """
        動的コンテンツ用のPuppeteerリクエストを作成
        """
        config = {**self.puppeteer_config, **kwargs}
        
        puppeteer_data = {
            'url': url,
            'actions': actions,
            'extractAfter': extract_after,
            'timeout': config.get('timeout'),
        }
        
        return scrapy.Request(
            url=f"{self.puppeteer_service_url}/api/scraping/dynamic",
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(puppeteer_data),
            callback=self.parse_dynamic_response,
            meta={
                'original_url': url,
                'puppeteer_data': puppeteer_data,
                **kwargs.get('meta', {})
            }
        )
    
    def parse_dynamic_response(self, response):
        """
        動的コンテンツのレスポンスを解析
        """
        try:
            data = json.loads(response.text)
            
            if not data.get('success'):
                self.logger.error(f"Dynamic scraping failed: {data.get('message', 'Unknown error')}")
                return
            
            original_url = response.meta.get('original_url')
            
            item = {
                'url': original_url,
                'scraped_url': data.get('url'),
                'title': data.get('pageInfo', {}).get('title'),
                'timestamp': data.get('timestamp'),
                'actions_executed': data.get('actionsExecuted', 0),
                'scraped_at': datetime.now().isoformat(),
            }
            
            # 抽出されたデータを追加
            if 'data' in data:
                item.update(data['data'])
            
            # カスタムJavaScriptの結果を追加
            if 'customData' in data:
                item['custom_data'] = data['customData']
            
            yield item
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse dynamic response: {e}")
        except Exception as e:
            self.logger.error(f"Error processing dynamic response: {e}")


class ExamplePuppeteerSpider(PuppeteerSpider):
    """
    Puppeteerスパイダーの使用例
    """
    
    name = 'example_puppeteer'
    start_urls = ['https://example.com']
    
    def start_requests(self):
        """
        カスタムデータ抽出設定でリクエストを開始
        """
        for url in self.start_urls:
            yield self.make_puppeteer_request(
                url=url,
                extractData={
                    'selectors': {
                        'title': 'h1',
                        'description': 'p',
                        'links': 'a[href]'
                    },
                    'javascript': '''
                        return {
                            pageHeight: document.body.scrollHeight,
                            linkCount: document.querySelectorAll('a').length,
                            imageCount: document.querySelectorAll('img').length
                        };
                    '''
                },
                screenshot=True,
                waitFor='h1'  # h1要素が表示されるまで待機
            )


class DynamicContentSpider(PuppeteerSpider):
    """
    動的コンテンツ用スパイダーの例
    """
    
    name = 'dynamic_content'
    start_urls = ['https://example.com/search']
    
    def start_requests(self):
        """
        動的アクション付きリクエストを開始
        """
        for url in self.start_urls:
            actions = [
                {'type': 'type', 'selector': 'input[name="q"]', 'value': 'search term'},
                {'type': 'click', 'selector': 'button[type="submit"]'},
                {'type': 'wait', 'delay': 3000},
                {'type': 'scroll'}
            ]
            
            extract_after = {
                'selectors': {
                    'results': '.search-result h3',
                    'descriptions': '.search-result p'
                }
            }
            
            yield self.make_dynamic_request(
                url=url,
                actions=actions,
                extract_after=extract_after
            )
