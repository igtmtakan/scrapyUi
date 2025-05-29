import scrapy
from scrapy_playwright.page import PageMethod
import json
import re
from urllib.parse import urljoin


class OmochaSpider(scrapy.Spider):
    name = "omocha"
    allowed_domains = ["amazon.co.jp"]
    start_urls = ["https://www.amazon.co.jp/gp/bestsellers/toys/ref=zg_bs_nav_toys_0"]
    
    # Playwright最適化設定（ミドルウェア問題を回避）
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': 1.0,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps'
            ]
        },
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 60000,
        'PLAYWRIGHT_DEFAULT_TIMEOUT': 30000,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # 問題のあるミドルウェアを無効化
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_playwright.middleware.ScrapyPlaywrightDownloadHandler': 585,
        },
        # ログレベルを調整
        'LOG_LEVEL': 'INFO'
    }

    # 新しいstart()メソッドを使用（非推奨警告を回避）
    async def start(self):
        """開始メソッド - ランキングページをスクロールして全商品を読み込み"""
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_ranking_page,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        # ページ読み込み待機
                        PageMethod('wait_for_load_state', 'domcontentloaded'),
                        PageMethod('wait_for_timeout', 5000),
                        
                        # 最下部までスクロール
                        PageMethod('evaluate', '''
                            async () => {
                                console.log('Starting scroll to bottom...');
                                
                                const scrollToBottom = () => {
                                    return new Promise((resolve) => {
                                        let totalHeight = 0;
                                        const distance = 300;
                                        const timer = setInterval(() => {
                                            const scrollHeight = document.body.scrollHeight;
                                            window.scrollBy(0, distance);
                                            totalHeight += distance;
                                            
                                            console.log(`Scrolled: ${totalHeight}/${scrollHeight}`);
                                            
                                            if(totalHeight >= scrollHeight - 1000) {
                                                clearInterval(timer);
                                                console.log('Scroll completed');
                                                resolve();
                                            }
                                        }, 300);
                                    });
                                };
                                
                                await scrollToBottom();
                                
                                // 追加の待機時間
                                await new Promise(resolve => setTimeout(resolve, 3000));
                                
                                return 'Scroll completed';
                            }
                        '''),
                        
                        # 最終的な待機
                        PageMethod('wait_for_timeout', 3000)
                    ]
                }
            )

    async def parse_ranking_page(self, response):
        """ランキングページを解析して商品リンクを抽出"""
        page = response.meta['playwright_page']
        
        try:
            self.logger.info(f'Processing ranking page: {response.url}')
            
            # 商品リンクを抽出 (指定されたクラス)
            product_links = response.css('a.a-link-normal.aok-block::attr(href)').getall()
            
            self.logger.info(f'Found {len(product_links)} product links on ranking page')
            
            # 各商品ページをスクレイピング（テスト用に5商品に制限）
            for i, link in enumerate(product_links[:5]):
                if link:
                    full_url = urljoin(response.url, link)
                    self.logger.info(f'Processing product {i+1}/5: {full_url}')
                    
                    yield scrapy.Request(
                        url=full_url,
                        callback=self.parse_product,
                        meta={
                            'playwright': True,
                            'playwright_include_page': True,
                            'playwright_page_methods': [
                                PageMethod('wait_for_load_state', 'domcontentloaded'),
                                PageMethod('wait_for_timeout', 3000),
                                # タイトル要素の読み込み待機
                                PageMethod('wait_for_selector', '#title, #productTitle', timeout=20000),
                                PageMethod('wait_for_timeout', 2000)
                            ]
                        }
                    )
            
            # ページネーション処理（テスト用に無効化）
            # await self.handle_pagination(response, page)
            
        except Exception as e:
            self.logger.error(f'Error in parse_ranking_page: {str(e)}')
        finally:
            await page.close()

    async def parse_product(self, response):
        """商品詳細ページを解析"""
        page = response.meta['playwright_page']
        
        try:
            self.logger.info(f'Parsing product page: {response.url}')
            
            # タイトル取得 (id="title")
            title = None
            title_selectors = [
                '#title span::text',
                '#productTitle::text',
                'h1#title span::text',
                '.product-title::text'
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
            rating_selectors = [
                'span.a-icon-alt::text',
                '.a-star-rating span.a-icon-alt::text',
                '[data-hook="rating-out-of-text"]::text'
            ]
            
            for selector in rating_selectors:
                rating_texts = response.css(selector).getall()
                for rating_text in rating_texts:
                    if rating_text and '5つ星のうち' in rating_text:
                        rating_match = re.search(r'([\\d.]+)', rating_text)
                        if rating_match:
                            rating = float(rating_match.group(1))
                            break
                if rating:
                    break
            
            # 税込価格取得
            price = None
            price_selectors = [
                '.a-price-current .a-offscreen::text',
                '.a-price .a-offscreen::text',
                '#priceblock_dealprice::text',
                '#priceblock_ourprice::text',
                '.a-price-range .a-offscreen::text',
                '[data-testid="price"] .a-offscreen::text'
            ]
            
            for selector in price_selectors:
                price_texts = response.css(selector).getall()
                for price_text in price_texts:
                    if price_text:
                        # 価格から数字を抽出
                        price_match = re.search(r'([\\d,]+)', price_text.replace('￥', '').replace(',', ''))
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
                'span[data-hook="total-review-count"]::text',
                '.a-size-base.a-link-normal::text',
                '#averageCustomerReviews span.a-size-base::text'
            ]
            
            for selector in review_selectors:
                review_texts = response.css(selector).getall()
                for review_text in review_texts:
                    if review_text and ('個の評価' in review_text or '件のカスタマーレビュー' in review_text):
                        review_match = re.search(r'([\\d,]+)', review_text)
                        if review_match:
                            try:
                                review_count = int(review_match.group(1).replace(',', ''))
                                break
                            except ValueError:
                                continue
                if review_count:
                    break
            
            # 画像URL取得 (class="a-dynamic-image a-stretch-vertical")
            image_url = None
            image_selectors = [
                'img.a-dynamic-image.a-stretch-vertical::attr(src)',
                '#landingImage::attr(src)',
                '.a-dynamic-image::attr(src)',
                '#imgTagWrapperId img::attr(src)'
            ]
            
            for selector in image_selectors:
                image_urls = response.css(selector).getall()
                for url in image_urls:
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
            
            self.logger.info(f'Scraped product: {title} - Price: {price} - Rating: {rating}')
            yield item
            
        except Exception as e:
            self.logger.error(f'Error parsing product {response.url}: {str(e)}')
        finally:
            await page.close()
