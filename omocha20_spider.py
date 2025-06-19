import scrapy
import re
import json
from urllib.parse import urljoin, urlparse


class Omocha20Spider(scrapy.Spider):
    name = "omocha20"
    allowed_domains = ["amazon.co.jp"]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'FEEDS': {
            'results.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'overwrite': True,
            },
            'results.json': {
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'overwrite': True,
            },
            'results.csv': {
                'format': 'csv',
                'encoding': 'utf8',
                'store_empty': False,
                'overwrite': True,
            },
            'results.xml': {
                'format': 'xml',
                'encoding': 'utf8',
                'store_empty': False,
                'overwrite': True,
            },
        },
    }

    def start_requests(self):
        start_url = "https://www.amazon.co.jp/gp/bestsellers/software/ref=zg_bs_nav_software_0"
        yield scrapy.Request(
            url=start_url,
            callback=self.parse
        )

    def parse(self, response):
        # 商品リンクを抽出
        product_links = response.css('a.a-link-normal.aok-block::attr(href)').getall()

        self.logger.info(f"Found {len(product_links)} product links on page: {response.url}")

        # 各商品ページを処理
        for link in product_links:
            if link:
                full_url = urljoin(response.url, link)
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_product
                )

        # ページネーションリンクを探す
        next_page_links = response.css('a[aria-label*="次のページ"]::attr(href), a:contains("次へ")::attr(href)').getall()

        for next_link in next_page_links:
            if next_link:
                next_url = urljoin(response.url, next_link)
                self.logger.info(f"Following pagination link: {next_url}")
                yield scrapy.Request(
                    url=next_url,
                    callback=self.parse
                )

    def parse_product(self, response):
        # タイトル抽出
        title = response.css('#title::text, #productTitle::text').get()
        if title:
            title = title.strip()

        # 評価抽出
        rating = response.css('span.a-icon-alt::text').re_first(r'(\d+\.?\d*)')

        # 税込価格抽出
        price = response.css('.a-price-whole::text, .a-offscreen::text').get()
        if not price:
            price = response.css('span:contains("￥")::text').get()

        # レビュー数抽出
        reviews = response.css('span[data-hook="total-review-count"]::text, a[href*="#customerReviews"]::text').get()
        if reviews:
            reviews = re.search(r'(\d+)', reviews.replace(',', ''))
            reviews = reviews.group(1) if reviews else None

        # 画像パス抽出
        image_url = response.css('img.a-dynamic-image.a-stretch-vertical::attr(src)').get()
        if not image_url:
            image_url = response.css('img[data-old-hires]::attr(data-old-hires)').get()

        yield {
            'title': title,
            'rating': rating,
            'price': price,
            'reviews': reviews,
            'image_url': image_url,
            'product_url': response.url,
            'scraped_at': response.meta.get('download_timestamp')
        }
