import scrapy
from scrapy import Request
import re


class AmazonBestsellerSpider(scrapy.Spider):
    name = "amazon_bestseller_fashion"
    allowed_domains = ['amazon.co.jp']
    start_urls = [
        'https://www.amazon.co.jp/gp/bestsellers/fashion/ref=zg_bs_nav_fashion_0'
    ]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'COOKIES_ENABLED': True,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
    }

    def parse(self, response):
        """ベストセラーページの解析"""
        self.logger.info(f'Processing page: {response.url}')
        
        # 商品リンクを取得
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
                    meta={'page_url': response.url}
                )
        
        # ページネーションリンクを取得
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
                self.logger.info(f'Following pagination: {next_url}')
                yield Request(
                    url=next_url,
                    callback=self.parse,
                    meta={'page_url': response.url}
                )

    def parse_product(self, response):
        """商品ページの解析"""
        self.logger.info(f'Processing product: {response.url}')
        
        # 商品名を取得
        product_name = response.css('#productTitle::text').get()
        if not product_name:
            product_name = response.css('h1.a-size-large::text').get()
        if not product_name:
            product_name = response.css('h1 span::text').get()
        
        # 価格を取得
        price = response.css('.a-price-whole::text').get()
        if not price:
            price = response.css('.a-price .a-offscreen::text').get()
        if not price:
            price = response.css('.a-price-range .a-price .a-offscreen::text').get()
        
        # 評価を取得
        rating = response.css('.a-icon-alt::text').re_first(r'5つ星のうち([0-9.]+)')
        if not rating:
            rating = response.css('[data-hook="average-star-rating"] .a-icon-alt::text').re_first(r'5つ星のうち([0-9.]+)')
        
        # レビュー数を取得
        review_count = response.css('#acrCustomerReviewText::text').re_first(r'([0-9,]+)')
        if not review_count:
            review_count = response.css('[data-hook="total-review-count"]::text').re_first(r'([0-9,]+)')
        
        # 商品画像URL
        image_url = response.css('#landingImage::attr(src)').get()
        if not image_url:
            image_url = response.css('.a-dynamic-image::attr(src)').get()
        
        # ランキング情報
        ranking = response.css('#SalesRank::text').re_first(r'([0-9,]+)位')
        if not ranking:
            ranking_text = response.css('.a-list-item:contains("ベストセラー")::text').get()
            if ranking_text:
                ranking = re.search(r'([0-9,]+)位', ranking_text)
                ranking = ranking.group(1) if ranking else None
        
        # ASIN
        asin = response.url.split('/dp/')[-1].split('/')[0] if '/dp/' in response.url else None
        
        # 商品の詳細情報
        availability = response.css('#availability span::text').get()
        if availability:
            availability = availability.strip()
        
        yield {
            'url': response.url,
            'asin': asin,
            'product_name': product_name.strip() if product_name else None,
            'price': price.strip() if price else None,
            'rating': rating,
            'review_count': review_count,
            'ranking': ranking,
            'image_url': image_url,
            'availability': availability,
            'page_url': response.meta.get('page_url'),
            'scraped_at': response.meta.get('scraped_at', ''),
        }
