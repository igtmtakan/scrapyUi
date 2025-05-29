import scrapy
from scrapy_playwright.page import PageMethod
import json
import re
from urllib.parse import urljoin


class OmochaSpider(scrapy.Spider):
    name = "omocha"
    allowed_domains = ["amazon.co.jp"]
    start_urls = ["https://www.amazon.co.jp/gp/bestsellers/toys/ref=zg_bs_nav_toys_0"]
    
    # デバッグ用設定
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': 1.0,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        
        # Playwright必須設定
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'args': ['--no-sandbox', '--disable-dev-shm-usage']
        },
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 60000,
        'PLAYWRIGHT_DEFAULT_TIMEOUT': 30000,
        
        # ミドルウェア設定を完全に除外
        'DOWNLOADER_MIDDLEWARES': {},
        
        'LOG_LEVEL': 'DEBUG',  # デバッグレベルに変更
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    def start_requests(self):
        """デバッグ用開始リクエスト"""
        self.logger.info('🚀 Starting debug spider execution...')
        self.logger.info(f'📋 Spider name: {self.name}')
        self.logger.info(f'🌐 Start URLs: {self.start_urls}')
        
        for url in self.start_urls:
            self.logger.info(f'🔗 Creating request for: {url}')
            yield scrapy.Request(
                url=url,
                callback=self.parse_ranking_page,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        # ページ読み込み完了まで待機
                        PageMethod('wait_for_load_state', 'domcontentloaded'),
                        PageMethod('wait_for_timeout', 5000),
                        
                        # ページ最下部までスクロール
                        PageMethod('evaluate', '''
                            async () => {
                                console.log('🔄 Starting scroll to bottom...');
                                
                                const autoScroll = async () => {
                                    await new Promise((resolve) => {
                                        let totalHeight = 0;
                                        const distance = 300;
                                        const timer = setInterval(() => {
                                            const scrollHeight = document.body.scrollHeight;
                                            window.scrollBy(0, distance);
                                            totalHeight += distance;
                                            
                                            console.log(`📜 Scrolled: ${totalHeight}px / ${scrollHeight}px`);
                                            
                                            if(totalHeight >= scrollHeight - 1000) {
                                                clearInterval(timer);
                                                console.log('✅ Scroll completed');
                                                resolve();
                                            }
                                        }, 300);
                                    });
                                };
                                
                                await autoScroll();
                                await new Promise(resolve => setTimeout(resolve, 3000));
                                
                                console.log('🎯 Ready to extract product links');
                                return 'Scroll completed successfully';
                            }
                        '''),
                        
                        PageMethod('wait_for_timeout', 3000)
                    ]
                }
            )

    async def parse_ranking_page(self, response):
        """デバッグ用ランキングページ解析"""
        page = response.meta['playwright_page']
        
        try:
            self.logger.info(f'🌐 Processing ranking page: {response.url}')
            self.logger.info(f'📄 Response status: {response.status}')
            self.logger.info(f'📏 Response length: {len(response.text)} characters')
            
            # ページタイトルを取得
            page_title = response.css('title::text').get()
            self.logger.info(f'📋 Page title: {page_title}')
            
            # 商品リンクを抽出（指定されたクラス）
            product_links = response.css('a.a-link-normal.aok-block::attr(href)').getall()
            self.logger.info(f'🔗 Found {len(product_links)} product links with selector: a.a-link-normal.aok-block')
            
            # 代替セレクターも試す
            alt_links = response.css('a[href*="/dp/"]::attr(href)').getall()
            self.logger.info(f'🔗 Found {len(alt_links)} product links with alternative selector: a[href*="/dp/"]')
            
            # 全てのリンクを確認
            all_links = response.css('a::attr(href)').getall()
            amazon_links = [link for link in all_links if link and '/dp/' in link]
            self.logger.info(f'🔗 Found {len(amazon_links)} total Amazon product links')
            
            # 使用するリンクを決定
            links_to_use = product_links if product_links else (alt_links if alt_links else amazon_links[:5])
            self.logger.info(f'📦 Using {len(links_to_use)} links for processing')
            
            # 各商品ページをスクレイピング（デバッグ用に2商品）
            for i, link in enumerate(links_to_use[:2]):
                if link:
                    full_url = urljoin(response.url, link)
                    self.logger.info(f'📦 Processing product {i+1}/2: {full_url}')
                    
                    yield scrapy.Request(
                        url=full_url,
                        callback=self.parse_product,
                        meta={
                            'playwright': True,
                            'playwright_include_page': True,
                            'playwright_page_methods': [
                                PageMethod('wait_for_load_state', 'domcontentloaded'),
                                PageMethod('wait_for_timeout', 3000),
                                PageMethod('wait_for_selector', '#title, #productTitle', timeout=20000),
                                PageMethod('wait_for_timeout', 2000)
                            ]
                        }
                    )
            
            # デバッグ用：ページのHTMLの一部を保存
            html_snippet = response.text[:1000]
            self.logger.debug(f'📄 HTML snippet: {html_snippet}')
            
        except Exception as e:
            self.logger.error(f'❌ Error in parse_ranking_page: {str(e)}')
            import traceback
            self.logger.error(f'📋 Traceback: {traceback.format_exc()}')
        finally:
            await page.close()

    async def parse_product(self, response):
        """デバッグ用商品詳細ページ解析"""
        page = response.meta['playwright_page']
        
        try:
            self.logger.info(f'🔍 Parsing product page: {response.url}')
            self.logger.info(f'📄 Response status: {response.status}')
            
            # ページタイトルを取得
            page_title = response.css('title::text').get()
            self.logger.info(f'📋 Page title: {page_title}')
            
            # タイトル取得（id="title"）
            title = None
            title_selectors = [
                '#title span::text',
                '#productTitle::text',
                'h1#title span::text',
                'h1 span::text'
            ]
            
            for selector in title_selectors:
                title_elements = response.css(selector).getall()
                self.logger.debug(f'🔍 Selector {selector}: found {len(title_elements)} elements')
                if title_elements:
                    title = ' '.join([t.strip() for t in title_elements if t.strip()])
                    self.logger.info(f'✅ Title found with selector {selector}: {title[:50]}...')
                    break
            
            if not title:
                title = 'タイトル不明'
                self.logger.warning('⚠️ No title found with any selector')
            
            # 評価取得
            rating = None
            rating_elements = response.css('span.a-icon-alt::text').getall()
            self.logger.debug(f'🔍 Rating elements found: {len(rating_elements)}')
            for rating_text in rating_elements:
                if rating_text and '5つ星のうち' in rating_text:
                    rating_match = re.search(r'([0-9.]+)', rating_text)
                    if rating_match:
                        try:
                            rating = float(rating_match.group(1))
                            self.logger.info(f'✅ Rating found: {rating}')
                            break
                        except ValueError:
                            continue
            
            if not rating:
                self.logger.warning('⚠️ No rating found')
            
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
                self.logger.debug(f'🔍 Price selector {selector}: found {len(price_elements)} elements')
                for price_text in price_elements:
                    if price_text:
                        price_clean = price_text.replace('￥', '').replace(',', '').strip()
                        price_match = re.search(r'([0-9,]+)', price_clean)
                        if price_match:
                            try:
                                price = int(price_match.group(1).replace(',', ''))
                                self.logger.info(f'✅ Price found: ¥{price}')
                                break
                            except ValueError:
                                continue
                if price:
                    break
            
            if not price:
                self.logger.warning('⚠️ No price found')
            
            # レビュー数取得
            review_count = None
            review_selectors = [
                '#acrCustomerReviewText::text',
                'span[data-hook="total-review-count"]::text'
            ]
            
            for selector in review_selectors:
                review_elements = response.css(selector).getall()
                self.logger.debug(f'🔍 Review selector {selector}: found {len(review_elements)} elements')
                for review_text in review_elements:
                    if review_text and ('個の評価' in review_text or '件のカスタマーレビュー' in review_text):
                        review_match = re.search(r'([0-9,]+)', review_text)
                        if review_match:
                            try:
                                review_count = int(review_match.group(1).replace(',', ''))
                                self.logger.info(f'✅ Review count found: {review_count}')
                                break
                            except ValueError:
                                continue
                if review_count:
                    break
            
            if not review_count:
                self.logger.warning('⚠️ No review count found')
            
            # 画像URL取得（class="a-dynamic-image a-stretch-vertical"）
            image_url = None
            image_selectors = [
                'img.a-dynamic-image.a-stretch-vertical::attr(src)',
                '#landingImage::attr(src)',
                '.a-dynamic-image::attr(src)'
            ]
            
            for selector in image_selectors:
                image_elements = response.css(selector).getall()
                self.logger.debug(f'🔍 Image selector {selector}: found {len(image_elements)} elements')
                for url in image_elements:
                    if url and url.startswith('http'):
                        image_url = url
                        self.logger.info(f'✅ Image URL found: {image_url[:50]}...')
                        break
                if image_url:
                    break
            
            if not image_url:
                self.logger.warning('⚠️ No image URL found')
            
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
            
            self.logger.info(f'✅ Scraped item: {title} | Price: ¥{price} | Rating: {rating}⭐ | Reviews: {review_count}')
            yield item
            
        except Exception as e:
            self.logger.error(f'❌ Error parsing product {response.url}: {str(e)}')
            import traceback
            self.logger.error(f'📋 Traceback: {traceback.format_exc()}')
        finally:
            await page.close()
