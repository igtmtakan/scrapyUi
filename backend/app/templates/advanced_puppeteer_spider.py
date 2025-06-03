"""
高度なPuppeteerスパイダーテンプレート
実用的なWebスクレイピングシナリオに対応
"""

def get_puppeteer_spider_template(spider_name: str, project_name: str, start_urls: list = None) -> str:
    """Node.js Puppeteer対応スパイダーテンプレート"""
    if start_urls is None:
        start_urls = ["https://example.com"]

    urls_str = ",\n        ".join([f'"{url}"' for url in start_urls])

    return f"""import scrapy
import json
from urllib.parse import urljoin
from datetime import datetime
from {project_name}.items import {project_name.capitalize()}Item


class {spider_name.capitalize()}Spider(scrapy.Spider):
    \"\"\"
    Node.js Puppeteerを使用したスパイダー
    JavaScript重要なSPAサイトやダイナミックコンテンツの取得に使用
    \"\"\"

    name = '{spider_name}'
    allowed_domains = []
    start_urls = [
        {urls_str}
    ]

    # Puppeteerサービスの設定
    puppeteer_service_url = 'http://localhost:3001'

    # デフォルト設定
    custom_settings = {{
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,

        # ScrapyUI データベースパイプライン設定
        'ITEM_PIPELINES': {{
            '{project_name}.pipelines.ScrapyUIDatabasePipeline': 100,
            '{project_name}.pipelines.ScrapyUIJSONPipeline': 200,
        }},
        'SCRAPYUI_DATABASE_URL': None,  # 実行時に設定
        'SCRAPYUI_TASK_ID': None,       # 実行時に設定
        'SCRAPYUI_JSON_FILE': None,     # 実行時に設定

        # フィード設定
        'FEEDS': {{
            'results/%(name)s_%(time)s.jsonl': {{
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'overwrite': True,
            }},
        }},
    }}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # クロールスタート日時を記録
        self.crawl_start_time = datetime.now()

    def make_puppeteer_request(self, url, **kwargs):
        \"\"\"
        Puppeteerサービスを使用してリクエストを作成
        \"\"\"
        # デフォルトのPuppeteerデータ
        puppeteer_data = {{
            'url': url,
            'viewport': {{'width': 1920, 'height': 1080}},
            'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'timeout': 30000,
            'waitFor': 3000,
            'extractData': {{
                'selectors': {{
                    'title': 'title, h1, .title',
                    'content': 'main, .content, article, body',
                    'links': 'a[href]',
                    'images': 'img[src]'
                }},
                'javascript': '''
                    return {{
                        pageHeight: document.body.scrollHeight,
                        linkCount: document.querySelectorAll('a').length,
                        imageCount: document.querySelectorAll('img').length,
                        loadTime: performance.now(),
                        currentUrl: window.location.href,
                        title: document.title
                    }};
                '''
            }},
            'screenshot': False,
            'fullPage': False
        }}

        # カスタムデータで上書き
        if 'extractData' in kwargs:
            puppeteer_data['extractData'].update(kwargs['extractData'])
        if 'viewport' in kwargs:
            puppeteer_data['viewport'].update(kwargs['viewport'])
        if 'timeout' in kwargs:
            puppeteer_data['timeout'] = kwargs['timeout']
        if 'waitFor' in kwargs:
            puppeteer_data['waitFor'] = kwargs['waitFor']
        if 'screenshot' in kwargs:
            puppeteer_data['screenshot'] = kwargs['screenshot']

        # デバッグ用ログ出力
        self.logger.info(f"Making Puppeteer request to: {{self.puppeteer_service_url}}/api/scraping/spa")
        self.logger.info(f"Request headers: {{'Content-Type': 'application/json', 'x-api-key': 'scrapyui-nodejs-service-key-2024'}}")
        self.logger.info(f"Request body: {{json.dumps(puppeteer_data, indent=2)}}")

        return scrapy.Request(
            url=f"{{self.puppeteer_service_url}}/api/scraping/spa",
            method='POST',
            headers={{
                'Content-Type': 'application/json',
                'x-api-key': 'scrapyui-nodejs-service-key-2024'
            }},
            body=json.dumps(puppeteer_data),
            callback=self.parse_puppeteer_response,
            meta={{
                'original_url': url,
                'puppeteer_data': puppeteer_data,
                **kwargs.get('meta', {{}})
            }}
        )

    def parse_puppeteer_response(self, response):
        \"\"\"
        Puppeteerサービスからのレスポンスを解析
        \"\"\"
        # デバッグ用ログ出力
        self.logger.info(f"Received response: status={{response.status}}, url={{response.url}}")
        self.logger.info(f"Response headers: {{dict(response.headers)}}")
        self.logger.info(f"Response body: {{response.text[:500]}}...")  # 最初の500文字のみ

        try:
            data = json.loads(response.text)

            if not data.get('success'):
                self.logger.error(f"Puppeteer request failed: {{data.get('message', 'Unknown error')}}")
                return

            # 元のURLとPuppeteerデータを取得
            original_url = response.meta.get('original_url')
            puppeteer_data = response.meta.get('puppeteer_data', {{}})

            # レスポンスデータを解析
            result_data = data.get('data', {{}})
            extracted_data = result_data.get('extractedData', {{}})
            custom_data = result_data.get('customData', {{}})
            page_info = result_data.get('pageInfo', {{}})

            # アイテムを作成
            item = {project_name.capitalize()}Item()

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

            self.logger.info(f"Successfully scraped: {{original_url}}")
            yield item

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {{e}}")
        except Exception as e:
            self.logger.error(f"Error processing Puppeteer response: {{e}}")

    def start_requests(self):
        \"\"\"
        開始リクエストを生成（互換性のため）
        \"\"\"
        for url in self.start_urls:
            yield self.make_puppeteer_request(url)

    async def start(self):
        \"\"\"
        開始リクエストを生成（新しいasyncメソッド）
        \"\"\"
        for url in self.start_urls:
            yield self.make_puppeteer_request(url)
"""


import scrapy
import json
import requests
from urllib.parse import urljoin, urlparse
from datetime import datetime
import time
import re


class AdvancedPuppeteerSpider(scrapy.Spider):
    """
    高度なPuppeteer機能を使用したスパイダー
    SPA、動的コンテンツ、認証が必要なサイトに対応
    """
    
    name = 'advanced_puppeteer'
    
    # Puppeteerサービスの設定
    puppeteer_service_url = 'http://localhost:3001'
    
    # デフォルト設定
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 15,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'FEEDS': {
            'results/%(name)s_%(time)s.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'overwrite': True,
            },
            'results/%(name)s_%(time)s.csv': {
                'format': 'csv',
                'encoding': 'utf8',
                'store_empty': False,
                'overwrite': True,
            },
        },
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Puppeteer設定
        self.puppeteer_config = {
            'viewport': {'width': 1920, 'height': 1080},
            'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'timeout': 60000,  # 60秒タイムアウト
            'waitFor': 5000,   # 5秒待機
            'headless': True,
            'devtools': False,
        }
        
        # 認証情報（必要に応じて設定）
        self.auth_config = {
            'username': kwargs.get('username'),
            'password': kwargs.get('password'),
            'login_url': kwargs.get('login_url'),
        }
        
        # スクレイピング統計
        self.stats = {
            'pages_scraped': 0,
            'items_extracted': 0,
            'errors': 0,
            'start_time': time.time()
        }
    
    def start_requests(self):
        """
        開始リクエストを生成
        認証が必要な場合は先にログインを実行
        """
        if self.auth_config.get('login_url'):
            # 認証が必要な場合
            yield self.make_login_request()
        else:
            # 通常のスクレイピング開始
            urls = getattr(self, 'start_urls', [])
            for url in urls:
                yield self.make_puppeteer_request(url)
    
    def make_login_request(self):
        """
        ログインリクエストを作成
        """
        login_actions = [
            {'type': 'wait', 'selector': 'input[type="email"], input[name="username"], input[name="email"]', 'timeout': 10000},
            {'type': 'type', 'selector': 'input[type="email"], input[name="username"], input[name="email"]', 'value': self.auth_config['username']},
            {'type': 'type', 'selector': 'input[type="password"], input[name="password"]', 'value': self.auth_config['password']},
            {'type': 'click', 'selector': 'button[type="submit"], input[type="submit"], .login-button'},
            {'type': 'wait', 'delay': 3000},  # ログイン処理完了を待機
        ]
        
        return self.make_dynamic_request(
            url=self.auth_config['login_url'],
            actions=login_actions,
            callback=self.after_login,
            meta={'login_attempt': True}
        )
    
    def after_login(self, response):
        """
        ログイン後の処理
        """
        try:
            data = json.loads(response.text)
            if data.get('success'):
                self.logger.info("Login successful, starting main scraping")
                # ログイン成功後、メインのスクレイピングを開始
                urls = getattr(self, 'start_urls', [])
                for url in urls:
                    yield self.make_puppeteer_request(url)
            else:
                self.logger.error(f"Login failed: {data.get('message', 'Unknown error')}")
        except Exception as e:
            self.logger.error(f"Error processing login response: {e}")
    
    def make_puppeteer_request(self, url, **kwargs):
        """
        Puppeteerを使用したリクエストを作成
        """
        config = {**self.puppeteer_config, **kwargs}
        
        # 高度な抽出設定
        extract_data = kwargs.get('extractData', {
            'selectors': {
                'title': 'title, h1, .title, .page-title',
                'content': 'main, .content, .main-content, article, .article',
                'links': 'a[href]',
                'images': 'img[src]',
                'meta_description': 'meta[name="description"]',
                'meta_keywords': 'meta[name="keywords"]',
            },
            'javascript': '''
                return {
                    pageHeight: document.body.scrollHeight,
                    pageWidth: document.body.scrollWidth,
                    linkCount: document.querySelectorAll('a').length,
                    imageCount: document.querySelectorAll('img').length,
                    formCount: document.querySelectorAll('form').length,
                    loadTime: performance.now(),
                    userAgent: navigator.userAgent,
                    currentUrl: window.location.href,
                    referrer: document.referrer,
                    cookies: document.cookie,
                    localStorage: JSON.stringify(localStorage),
                    sessionStorage: JSON.stringify(sessionStorage)
                };
            '''
        })
        
        puppeteer_data = {
            'url': url,
            'viewport': config.get('viewport'),
            'userAgent': config.get('userAgent'),
            'timeout': config.get('timeout'),
            'waitFor': config.get('waitFor'),
            'extractData': extract_data,
            'screenshot': config.get('screenshot', False),
            'fullPage': config.get('fullPage', True),
            'pdf': config.get('pdf', False),
        }
        
        # 不要なNone値を削除
        puppeteer_data = {k: v for k, v in puppeteer_data.items() if v is not None}
        
        return scrapy.Request(
            url=f"{self.puppeteer_service_url}/api/scraping/spa",
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(puppeteer_data),
            callback=kwargs.get('callback', self.parse_puppeteer_response),
            meta={
                'original_url': url,
                'puppeteer_data': puppeteer_data,
                **kwargs.get('meta', {})
            }
        )
    
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
            callback=kwargs.get('callback', self.parse_dynamic_response),
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
                self.stats['errors'] += 1
                return
            
            scraping_data = data.get('data', {})
            original_url = response.meta.get('original_url')
            
            # 基本的なアイテムデータ
            item = {
                'url': original_url,
                'scraped_url': scraping_data.get('url'),
                'title': self.clean_text(scraping_data.get('pageInfo', {}).get('title')),
                'timestamp': scraping_data.get('timestamp'),
                'scraped_at': datetime.now().isoformat(),
                'spider_name': self.name,
            }
            
            # 抽出されたデータを追加
            if 'extractedData' in scraping_data:
                extracted = scraping_data['extractedData']
                
                # セレクターで抽出されたデータ
                if 'selectors' in extracted:
                    selectors_data = extracted['selectors']
                    item.update({
                        'content': self.clean_text(selectors_data.get('content')),
                        'meta_description': self.clean_text(selectors_data.get('meta_description')),
                        'meta_keywords': self.clean_text(selectors_data.get('meta_keywords')),
                        'links': self.extract_links(selectors_data.get('links', [])),
                        'images': self.extract_images(selectors_data.get('images', [])),
                    })
                
                # JavaScriptで抽出されたデータ
                if 'javascript' in extracted:
                    js_data = extracted['javascript']
                    item.update({
                        'page_metrics': {
                            'height': js_data.get('pageHeight'),
                            'width': js_data.get('pageWidth'),
                            'link_count': js_data.get('linkCount'),
                            'image_count': js_data.get('imageCount'),
                            'form_count': js_data.get('formCount'),
                            'load_time': js_data.get('loadTime'),
                        },
                        'browser_info': {
                            'user_agent': js_data.get('userAgent'),
                            'current_url': js_data.get('currentUrl'),
                            'referrer': js_data.get('referrer'),
                        }
                    })
            
            # スクリーンショットデータを追加
            if 'screenshot' in scraping_data:
                item['screenshot'] = scraping_data['screenshot']
            
            # PDFデータを追加
            if 'pdf' in scraping_data:
                item['pdf'] = scraping_data['pdf']
            
            self.stats['pages_scraped'] += 1
            self.stats['items_extracted'] += 1
            
            yield item
            
            # 追加のリンクを抽出する場合
            yield from self.extract_additional_links(scraping_data, response)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Puppeteer response: {e}")
            self.stats['errors'] += 1
        except Exception as e:
            self.logger.error(f"Error processing Puppeteer response: {e}")
            self.stats['errors'] += 1
    
    def parse_dynamic_response(self, response):
        """
        動的コンテンツのレスポンスを解析
        """
        try:
            data = json.loads(response.text)
            
            if not data.get('success'):
                self.logger.error(f"Dynamic scraping failed: {data.get('message', 'Unknown error')}")
                self.stats['errors'] += 1
                return
            
            original_url = response.meta.get('original_url')
            
            item = {
                'url': original_url,
                'scraped_url': data.get('url'),
                'title': self.clean_text(data.get('pageInfo', {}).get('title')),
                'timestamp': data.get('timestamp'),
                'actions_executed': data.get('actionsExecuted', 0),
                'scraped_at': datetime.now().isoformat(),
                'spider_name': self.name,
                'scraping_type': 'dynamic',
            }
            
            # 抽出されたデータを追加
            if 'data' in data:
                item.update(data['data'])
            
            self.stats['pages_scraped'] += 1
            self.stats['items_extracted'] += 1
            
            yield item
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse dynamic response: {e}")
            self.stats['errors'] += 1
        except Exception as e:
            self.logger.error(f"Error processing dynamic response: {e}")
            self.stats['errors'] += 1
    
    def extract_additional_links(self, scraping_data, response):
        """
        スクレイピングデータから追加のリンクを抽出
        """
        # サブクラスでオーバーライドして使用
        return []
    
    def clean_text(self, text):
        """
        テキストをクリーンアップ
        """
        if not text:
            return None
        
        # HTMLタグを除去
        text = re.sub(r'<[^>]+>', '', str(text))
        # 余分な空白を除去
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text if text else None
    
    def extract_links(self, links_data):
        """
        リンクデータを抽出・整理
        """
        if not links_data:
            return []
        
        links = []
        for link in links_data:
            if isinstance(link, dict):
                href = link.get('href')
                text = self.clean_text(link.get('text', ''))
                if href:
                    links.append({
                        'url': href,
                        'text': text,
                        'absolute_url': urljoin(response.meta.get('original_url', ''), href)
                    })
        
        return links
    
    def extract_images(self, images_data):
        """
        画像データを抽出・整理
        """
        if not images_data:
            return []
        
        images = []
        for img in images_data:
            if isinstance(img, dict):
                src = img.get('src')
                alt = self.clean_text(img.get('alt', ''))
                if src:
                    images.append({
                        'url': src,
                        'alt': alt,
                        'absolute_url': urljoin(response.meta.get('original_url', ''), src)
                    })
        
        return images
    
    def closed(self, reason):
        """
        スパイダー終了時の処理
        """
        end_time = time.time()
        duration = end_time - self.stats['start_time']
        
        self.logger.info(f"Spider closed: {reason}")
        self.logger.info(f"Statistics:")
        self.logger.info(f"  - Pages scraped: {self.stats['pages_scraped']}")
        self.logger.info(f"  - Items extracted: {self.stats['items_extracted']}")
        self.logger.info(f"  - Errors: {self.stats['errors']}")
        self.logger.info(f"  - Duration: {duration:.2f} seconds")
        self.logger.info(f"  - Average time per page: {duration/max(self.stats['pages_scraped'], 1):.2f} seconds")


# 使用例クラス

class EcommercePuppeteerSpider(AdvancedPuppeteerSpider):
    """
    ECサイト用Puppeteerスパイダー
    """
    
    name = 'ecommerce_puppeteer'
    start_urls = ['https://example-shop.com/products']
    
    def start_requests(self):
        """
        商品一覧ページから開始
        """
        for url in self.start_urls:
            yield self.make_puppeteer_request(
                url=url,
                extractData={
                    'selectors': {
                        'products': '.product-item',
                        'product_titles': '.product-title',
                        'product_prices': '.product-price',
                        'product_images': '.product-image img',
                        'product_links': '.product-link',
                        'pagination': '.pagination a',
                    },
                    'javascript': '''
                        const products = Array.from(document.querySelectorAll('.product-item')).map(item => ({
                            title: item.querySelector('.product-title')?.textContent?.trim(),
                            price: item.querySelector('.product-price')?.textContent?.trim(),
                            image: item.querySelector('.product-image img')?.src,
                            link: item.querySelector('.product-link')?.href,
                            rating: item.querySelector('.rating')?.textContent?.trim(),
                            availability: item.querySelector('.availability')?.textContent?.trim()
                        }));
                        return { products };
                    '''
                },
                screenshot=True
            )
    
    def extract_additional_links(self, scraping_data, response):
        """
        商品詳細ページのリンクを抽出
        """
        extracted = scraping_data.get('extractedData', {})
        
        # JavaScriptで抽出された商品データから詳細ページリンクを取得
        if 'javascript' in extracted and 'products' in extracted['javascript']:
            products = extracted['javascript']['products']
            for product in products:
                if product.get('link'):
                    yield self.make_puppeteer_request(
                        url=product['link'],
                        extractData={
                            'selectors': {
                                'title': 'h1, .product-title',
                                'description': '.product-description',
                                'price': '.price, .product-price',
                                'images': '.product-images img',
                                'specifications': '.specifications',
                                'reviews': '.review',
                            }
                        },
                        meta={'product_detail': True}
                    )


class NewsSitePuppeteerSpider(AdvancedPuppeteerSpider):
    """
    ニュースサイト用Puppeteerスパイダー
    """
    
    name = 'news_puppeteer'
    start_urls = ['https://example-news.com']
    
    def start_requests(self):
        """
        ニュース一覧から記事を抽出
        """
        for url in self.start_urls:
            # 無限スクロールに対応
            scroll_actions = [
                {'type': 'wait', 'selector': '.article-list', 'timeout': 10000},
                {'type': 'scroll', 'direction': 'down', 'distance': 1000},
                {'type': 'wait', 'delay': 2000},
                {'type': 'scroll', 'direction': 'down', 'distance': 1000},
                {'type': 'wait', 'delay': 2000},
                {'type': 'scroll', 'direction': 'down', 'distance': 1000},
                {'type': 'wait', 'delay': 2000},
            ]
            
            extract_after = {
                'selectors': {
                    'articles': '.article-item',
                    'headlines': '.article-title',
                    'summaries': '.article-summary',
                    'dates': '.article-date',
                    'authors': '.article-author',
                    'categories': '.article-category',
                    'article_links': '.article-link',
                }
            }
            
            yield self.make_dynamic_request(
                url=url,
                actions=scroll_actions,
                extract_after=extract_after
            )
