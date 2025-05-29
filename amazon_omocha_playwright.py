import scrapy
from scrapy_playwright.page import PageMethod
import json
import re
from urllib.parse import urljoin


class OmochaSpider(scrapy.Spider):
    name = "omocha"
    allowed_domains = ["amazon.co.jp"]
    start_urls = ["https://www.amazon.co.jp/gp/bestsellers/toys/ref=zg_bs_nav_toys_0"]
    
    # Playwright専用設定
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        
        # Playwright設定
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        },
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 60000,
        'PLAYWRIGHT_DEFAULT_TIMEOUT': 30000,
        
        # ミドルウェア設定
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_playwright.middleware.ScrapyPlaywrightDownloadHandler': 585,
        },
        
        # ログ設定
        'LOG_LEVEL': 'INFO',
        
        # User Agent
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    def start_requests(self):
        """Playwright専用の開始リクエスト"""
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_ranking_page,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        # ページ読み込み完了まで待機
                        PageMethod('wait_for_load_state', 'networkidle'),
                        PageMethod('wait_for_timeout', 3000),
                        
                        # ページ最下部までスクロール（Playwright JavaScript実行）
                        PageMethod('evaluate', '''
                            async () => {
                                console.log('🔄 Starting scroll to bottom...');
                                
                                // スクロール関数
                                const autoScroll = async () => {
                                    await new Promise((resolve) => {
                                        let totalHeight = 0;
                                        const distance = 200;
                                        const timer = setInterval(() => {
                                            const scrollHeight = document.body.scrollHeight;
                                            window.scrollBy(0, distance);
                                            totalHeight += distance;
                                            
                                            console.log(`📜 Scrolled: ${totalHeight}px / ${scrollHeight}px`);
                                            
                                            if(totalHeight >= scrollHeight - 1000) {
                                                clearInterval(timer);
                                                console.log('✅ Scroll to bottom completed');
                                                resolve();
                                            }
                                        }, 200);
                                    });
                                };
                                
                                await autoScroll();
                                
                                // 追加の待機時間でコンテンツ読み込み完了を確保
                                await new Promise(resolve => setTimeout(resolve, 3000));
                                
                                console.log('🎯 Ready to extract product links');
                                return 'Scroll completed successfully';
                            }
                        '''),
                        
                        # 最終待機
                        PageMethod('wait_for_timeout', 2000)
                    ]
                }
            )

    async def parse_ranking_page(self, response):
        """ランキングページを解析（Playwright使用）"""
        page = response.meta['playwright_page']
        
        try:
            self.logger.info(f'🌐 Processing ranking page: {response.url}')
            
            # Playwrightでページ情報を取得
            page_title = await page.title()
            self.logger.info(f'📄 Page title: {page_title}')
            
            # 商品リンクを抽出（指定されたクラス）
            product_links = response.css('a.a-link-normal.aok-block::attr(href)').getall()
            
            self.logger.info(f'🔗 Found {len(product_links)} product links')
            
            # 各商品ページをスクレイピング（テスト用に3商品）
            for i, link in enumerate(product_links[:3]):
                if link:
                    full_url = urljoin(response.url, link)
                    self.logger.info(f'📦 Processing product {i+1}/3: {full_url}')
                    
                    yield scrapy.Request(
                        url=full_url,
                        callback=self.parse_product,
                        meta={
                            'playwright': True,
                            'playwright_include_page': True,
                            'playwright_page_methods': [
                                # ページ読み込み完了まで待機
                                PageMethod('wait_for_load_state', 'domcontentloaded'),
                                PageMethod('wait_for_timeout', 3000),
                                
                                # 商品ページの要素が読み込まれるまで待機
                                PageMethod('wait_for_selector', '#title, #productTitle', timeout=20000),
                                
                                # 価格情報の読み込み待機
                                PageMethod('wait_for_selector', '.a-price, #priceblock_ourprice, #priceblock_dealprice', timeout=10000),
                                
                                PageMethod('wait_for_timeout', 2000)
                            ]
                        }
                    )
            
            # ページネーション処理（テスト用に無効化）
            # await self.handle_pagination(response, page)
            
        except Exception as e:
            self.logger.error(f'❌ Error in parse_ranking_page: {str(e)}')
        finally:
            await page.close()

    async def parse_product(self, response):
        """商品詳細ページを解析（Playwright使用）"""
        page = response.meta['playwright_page']
        
        try:
            self.logger.info(f'🔍 Parsing product page: {response.url}')
            
            # Playwrightでページタイトルを確認
            page_title = await page.title()
            self.logger.info(f'📄 Product page title: {page_title}')
            
            # タイトル取得（id="title"）
            title = None
            title_selectors = [
                '#title span::text',
                '#productTitle::text',
                'h1#title span::text'
            ]
            
            for selector in title_selectors:
                title_elements = response.css(selector).getall()
                if title_elements:
                    title = ' '.join([t.strip() for t in title_elements if t.strip()])
                    break
            
            if not title:
                title = 'タイトル不明'
            
            # 評価取得
            rating = None
            rating_elements = response.css('span.a-icon-alt::text').getall()
            for rating_text in rating_elements:
                if rating_text and '5つ星のうち' in rating_text:
                    rating_match = re.search(r'([0-9.]+)', rating_text)
                    if rating_match:
                        try:
                            rating = float(rating_match.group(1))
                            break
                        except ValueError:
                            continue
            
            # 税込価格取得
            price = None
            price_selectors = [
                '.a-price-current .a-offscreen::text',
                '.a-price .a-offscreen::text',
                '#priceblock_dealprice::text',
                '#priceblock_ourprice::text'
            ]
            
            for selector in price_selectors:
                price_elements = response.css(selector).getall()
                for price_text in price_elements:
                    if price_text:
                        # 価格から数字を抽出
                        price_clean = price_text.replace('￥', '').replace(',', '').strip()
                        price_match = re.search(r'([0-9,]+)', price_clean)
                        if price_match:
                            try:
                                price = int(price_match.group(1).replace(',', ''))
                                break
                            except ValueError:
                                continue
                if price:
                    break
            
            # レビュー数取得
            review_count = None
            review_selectors = [
                '#acrCustomerReviewText::text',
                'span[data-hook="total-review-count"]::text'
            ]
            
            for selector in review_selectors:
                review_elements = response.css(selector).getall()
                for review_text in review_elements:
                    if review_text and ('個の評価' in review_text or '件のカスタマーレビュー' in review_text):
                        review_match = re.search(r'([0-9,]+)', review_text)
                        if review_match:
                            try:
                                review_count = int(review_match.group(1).replace(',', ''))
                                break
                            except ValueError:
                                continue
                if review_count:
                    break
            
            # 画像URL取得（class="a-dynamic-image a-stretch-vertical"）
            image_url = None
            image_selectors = [
                'img.a-dynamic-image.a-stretch-vertical::attr(src)',
                '#landingImage::attr(src)',
                '.a-dynamic-image::attr(src)'
            ]
            
            for selector in image_selectors:
                image_elements = response.css(selector).getall()
                for url in image_elements:
                    if url and url.startswith('http'):
                        image_url = url
                        break
                if image_url:
                    break
            
            # データアイテムを作成
            item = {
                'title': title,
                'rating': rating,
                'price': price,
                'review_count': review_count,
                'image_url': image_url,
                'product_url': response.url,
                'scraped_at': scrapy.utils.misc.load_object('datetime.datetime').now().isoformat()
            }
            
            self.logger.info(f'✅ Scraped: {title} | Price: ¥{price} | Rating: {rating}⭐ | Reviews: {review_count}')
            yield item
            
        except Exception as e:
            self.logger.error(f'❌ Error parsing product {response.url}: {str(e)}')
        finally:
            await page.close()

    async def handle_pagination(self, response, page):
        """ページネーション処理（Playwright使用）"""
        try:
            # 次のページリンクを探す
            next_selectors = [
                'ul.a-pagination li.a-last a::attr(href)',
                'a[aria-label="次へ"]::attr(href)'
            ]
            
            next_url = None
            for selector in next_selectors:
                next_links = response.css(selector).getall()
                if next_links:
                    next_url = urljoin(response.url, next_links[0])
                    break
            
            if next_url:
                self.logger.info(f'🔄 Following pagination: {next_url}')
                yield scrapy.Request(
                    url=next_url,
                    callback=self.parse_ranking_page,
                    meta={
                        'playwright': True,
                        'playwright_include_page': True,
                        'playwright_page_methods': [
                            PageMethod('wait_for_load_state', 'networkidle'),
                            PageMethod('wait_for_timeout', 3000),
                            PageMethod('evaluate', '''
                                async () => {
                                    const autoScroll = async () => {
                                        await new Promise((resolve) => {
                                            let totalHeight = 0;
                                            const distance = 200;
                                            const timer = setInterval(() => {
                                                const scrollHeight = document.body.scrollHeight;
                                                window.scrollBy(0, distance);
                                                totalHeight += distance;
                                                
                                                if(totalHeight >= scrollHeight - 1000) {
                                                    clearInterval(timer);
                                                    resolve();
                                                }
                                            }, 200);
                                        });
                                    };
                                    
                                    await autoScroll();
                                    await new Promise(resolve => setTimeout(resolve, 3000));
                                    return 'Pagination scroll completed';
                                }
                            '''),
                            PageMethod('wait_for_timeout', 2000)
                        ]
                    }
                )
            else:
                self.logger.info('🏁 No more pagination links found')
                
        except Exception as e:
            self.logger.error(f'❌ Error in pagination: {str(e)}')
