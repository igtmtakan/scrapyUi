import scrapy
from scrapy import Request
import re


class Omocha20Spider(scrapy.Spider):
    name = "omocha20"
    allowed_domains = ['amazon.co.jp']
    start_urls = [
        'https://www.amazon.co.jp/gp/bestsellers/toys/ref=zg_bs_nav_toys_0'
    ]

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'HTTPCACHE_ENABLED': True,
        'HTTPCACHE_DIR': 'httpcache',
        'HTTPCACHE_EXPIRATION_SECS': 86400,
        'FEED_EXPORT_ENCODING': 'utf-8',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache',
        }
    }

    def start_requests(self):
        """リクエスト開始"""
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                }
            )

    def parse(self, response):
        """おもちゃベストセラーページの解析"""
        self.logger.info(f'Processing page: {response.url}')

        # 商品リンクを取得 (class="a-link-normal aok-block")
        product_links = response.css('a.a-link-normal.aok-block::attr(href)').getall()
        
        self.logger.info(f'Found {len(product_links)} product links')

        # 各商品ページを処理
        for link in product_links:
            if link:
                # 相対URLを絶対URLに変換
                full_url = response.urljoin(link)
                yield Request(
                    url=full_url,
                    callback=self.parse_product,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        'page_url': response.url
                    }
                )

        # ページネーションリンクを取得（再帰的に巡る）
        next_page_links = response.css('a[aria-label="次のページに移動"]::attr(href)').getall()
        if not next_page_links:
            # 別のセレクタも試す
            next_page_links = response.css('a.s-pagination-next::attr(href)').getall()
        if not next_page_links:
            # さらに別のセレクタ
            next_page_links = response.css('li.a-last a::attr(href)').getall()

        for next_link in next_page_links:
            if next_link:
                next_url = response.urljoin(next_link)
                self.logger.info(f'Following next page: {next_url}')
                yield Request(
                    url=next_url,
                    callback=self.parse,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        'page_url': response.url
                    }
                )

    def parse_product(self, response):
        """商品詳細ページの解析"""
        self.logger.info(f'Processing product: {response.url}')

        # 商品タイトル (id="title")
        title = response.css('#title span::text').get()
        if not title:
            title = response.css('#title::text').get()
        if title:
            title = title.strip()

        # 評価を取得
        rating = None
        rating_text = response.css('span.a-icon-alt::text').get()
        if rating_text:
            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
            if rating_match:
                rating = rating_match.group(1)

        # 税込価格を取得
        price = None
        price_selectors = [
            '.a-price-whole::text',
            '.a-price .a-offscreen::text',
            '.a-price-current .a-offscreen::text',
            '.a-price-range .a-offscreen::text'
        ]
        for selector in price_selectors:
            price_text = response.css(selector).get()
            if price_text:
                price = price_text.strip()
                break

        # レビュー数を取得
        review_count = None
        review_selectors = [
            '#acrCustomerReviewText::text',
            'span[data-hook="total-review-count"]::text',
            '.a-size-base.a-link-normal::text'
        ]
        for selector in review_selectors:
            review_text = response.css(selector).get()
            if review_text and ('レビュー' in review_text or 'review' in review_text.lower()):
                review_count = review_text.strip()
                break

        # 画像パス (class="a-dynamic-image a-stretch-vertical")
        image_url = response.css('img.a-dynamic-image.a-stretch-vertical::attr(src)').get()
        if not image_url:
            # 代替セレクタ
            image_url = response.css('#landingImage::attr(src)').get()

        # データを返す
        item_data = {
            'title': title,
            'rating': rating,
            'price': price,
            'review_count': review_count,
            'image_url': image_url,
            'product_url': response.url,
            'source_page': response.meta.get('page_url', ''),
            'scraped_at': response.headers.get('Date', '').decode('utf-8') if response.headers.get('Date') else ''
        }

        self.logger.info(f"✅ Item: {title or 'No title'} - Price: {price or 'N/A'} - Rating: {rating or 'N/A'}")

        yield item_data
