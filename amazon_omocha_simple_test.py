import scrapy
from scrapy_playwright.page import PageMethod
import json
import re
from urllib.parse import urljoin


class OmochaSpider(scrapy.Spider):
    name = "omocha"
    allowed_domains = ["amazon.co.jp"]
    start_urls = ["https://www.amazon.co.jp/gp/bestsellers/toys/ref=zg_bs_nav_toys_0"]
    
    # 超シンプル設定
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        
        # Playwright必須設定のみ
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'args': ['--no-sandbox', '--disable-dev-shm-usage']
        },
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 30000,
        
        # 全ミドルウェア無効化
        'DOWNLOADER_MIDDLEWARES': {},
        
        'LOG_LEVEL': 'INFO',
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    def start_requests(self):
        """超シンプルな開始リクエスト"""
        self.logger.info('🚀 Starting SIMPLE test spider...')
        
        for url in self.start_urls:
            self.logger.info(f'🔗 Requesting: {url}')
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_load_state', 'domcontentloaded'),
                        PageMethod('wait_for_timeout', 5000),
                    ]
                }
            )

    async def parse(self, response):
        """超シンプルな解析"""
        page = response.meta['playwright_page']
        
        try:
            self.logger.info(f'✅ Successfully loaded page: {response.url}')
            self.logger.info(f'📄 Status: {response.status}')
            self.logger.info(f'📏 Content length: {len(response.text)} chars')
            
            # ページタイトルを取得
            title = response.css('title::text').get()
            self.logger.info(f'📋 Page title: {title}')
            
            # 商品リンクを複数の方法で探す
            # 方法1: 指定されたセレクター
            links1 = response.css('a.a-link-normal.aok-block::attr(href)').getall()
            self.logger.info(f'🔗 Method 1 (a.a-link-normal.aok-block): {len(links1)} links')
            
            # 方法2: Amazon商品ページのパターン
            links2 = response.css('a[href*="/dp/"]::attr(href)').getall()
            self.logger.info(f'🔗 Method 2 (a[href*="/dp/"]): {len(links2)} links')
            
            # 方法3: 全てのリンクからAmazon商品を抽出
            all_links = response.css('a::attr(href)').getall()
            links3 = [link for link in all_links if link and '/dp/' in link]
            self.logger.info(f'🔗 Method 3 (all Amazon product links): {len(links3)} links')
            
            # 方法4: ベストセラーページ特有のセレクター
            links4 = response.css('div[data-testid="zg-item"] a::attr(href)').getall()
            self.logger.info(f'🔗 Method 4 (zg-item): {len(links4)} links')
            
            # 方法5: より広範囲なセレクター
            links5 = response.css('div.zg-item-immersion a::attr(href)').getall()
            self.logger.info(f'🔗 Method 5 (zg-item-immersion): {len(links5)} links')
            
            # 使用するリンクを決定
            product_links = links1 or links2 or links3[:10] or links4 or links5
            self.logger.info(f'📦 Using {len(product_links)} links for processing')
            
            # 最初の1つだけテスト
            if product_links:
                link = product_links[0]
                full_url = urljoin(response.url, link)
                self.logger.info(f'🎯 Testing first product: {full_url}')
                
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_product,
                    meta={
                        'playwright': True,
                        'playwright_include_page': True,
                        'playwright_page_methods': [
                            PageMethod('wait_for_load_state', 'domcontentloaded'),
                            PageMethod('wait_for_timeout', 3000),
                        ]
                    }
                )
            else:
                self.logger.warning('⚠️ No product links found with any method!')
                
                # HTMLの一部をログに出力してデバッグ
                html_snippet = response.text[:2000]
                self.logger.info(f'📄 HTML snippet: {html_snippet}')
            
        except Exception as e:
            self.logger.error(f'❌ Error in parse: {str(e)}')
            import traceback
            self.logger.error(f'📋 Traceback: {traceback.format_exc()}')
        finally:
            await page.close()

    async def parse_product(self, response):
        """超シンプルな商品解析"""
        page = response.meta['playwright_page']
        
        try:
            self.logger.info(f'🔍 Parsing product: {response.url}')
            
            # タイトル取得
            title = None
            title_selectors = [
                '#title span::text',
                '#productTitle::text',
                'h1 span::text'
            ]
            
            for selector in title_selectors:
                elements = response.css(selector).getall()
                if elements:
                    title = ' '.join([t.strip() for t in elements if t.strip()])
                    self.logger.info(f'✅ Title found: {title[:100]}...')
                    break
            
            if not title:
                title = 'タイトル不明'
                self.logger.warning('⚠️ No title found')
            
            # 簡単なアイテムを作成
            item = {
                'title': title,
                'product_url': response.url,
                'scraped_at': scrapy.utils.misc.load_object('datetime.datetime').now().isoformat()
            }
            
            self.logger.info(f'✅ Successfully scraped: {title}')
            yield item
            
        except Exception as e:
            self.logger.error(f'❌ Error parsing product: {str(e)}')
            import traceback
            self.logger.error(f'📋 Traceback: {traceback.format_exc()}')
        finally:
            await page.close()
