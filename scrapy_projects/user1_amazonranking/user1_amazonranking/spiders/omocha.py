import scrapy
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs
from ..items import AmazonProductItem


class OmochaSpider(scrapy.Spider):
    name = "omocha"
    allowed_domains = ["amazon.co.jp"]
    start_urls = ["https://www.amazon.co.jp/gp/bestsellers/toys/ref=zg_bs_nav_toys_0"]

    custom_settings = {
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'timeout': 10000,
        },
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 10000,
    }

    def start_requests(self):
        """初期リクエストを生成"""
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse
            )

    def parse(self, response):
        """メインページの解析"""
        self.logger.info(f"Parsing page: {response.url}")

        # 商品リンクを抽出
        product_links = response.css('a.a-link-normal.aok-block::attr(href)').getall()

        self.logger.info(f"Found {len(product_links)} product links")

        # 各商品ページを処理
        for i, link in enumerate(product_links, 1):
            if link:
                product_url = urljoin(response.url, link)
                yield scrapy.Request(
                    url=product_url,
                    callback=self.parse_product,
                    meta={
                        'rank': i,
                        'page_number': self.get_page_number(response.url)
                    }
                )

        # ページネーションリンクを処理
        next_page_links = response.css('a[aria-label*="次のページ"]::attr(href)').getall()
        if not next_page_links:
            # 別のセレクタも試す
            next_page_links = response.css('li.a-last a::attr(href)').getall()

        for next_link in next_page_links:
            if next_link:
                next_url = urljoin(response.url, next_link)
                self.logger.info(f"Following next page: {next_url}")
                yield scrapy.Request(
                    url=next_url,
                    callback=self.parse
                )

    def parse_product(self, response):
        """商品ページの解析"""
        self.logger.info(f"Parsing product: {response.url}")

        item = AmazonProductItem()

        # 商品タイトル（id="title"のテキスト）
        title_element = response.css('#title span::text').get()
        if not title_element:
            title_element = response.css('#productTitle::text').get()
        item['title'] = title_element.strip() if title_element else ''

        # 商品URL
        item['url'] = response.url

        # 評価（星の数）
        rating = self.extract_rating(response)
        item['rating'] = rating

        # 評価数
        rating_count = self.extract_rating_count(response)
        item['rating_count'] = rating_count

        # 税込価格
        price = self.extract_price(response)
        item['price'] = price

        # レビュー数
        review_count = self.extract_review_count(response)
        item['review_count'] = review_count

        # 商品画像URL（class="a-dynamic-image a-stretch-vertical"）
        image_url = response.css('img.a-dynamic-image.a-stretch-vertical::attr(src)').get()
        if not image_url:
            # 別のセレクタも試す
            image_url = response.css('#landingImage::attr(src)').get()
        item['image_url'] = image_url or ''

        # ランキング順位
        item['rank'] = response.meta.get('rank', 0)

        # ページ番号
        item['page_number'] = response.meta.get('page_number', 1)

        # スクレイピング日時
        item['scraped_at'] = datetime.now().isoformat()

        self.logger.info(f"Extracted item: {item['title'][:50]}...")

        yield item

    def extract_rating(self, response):
        """評価（星の数）を抽出"""
        # 複数のセレクタを試す
        rating_selectors = [
            'span.a-icon-alt::text',
            'i[data-hook="average-star-rating"] span.a-icon-alt::text',
            'span[data-hook="rating-out-of-text"]::text',
            '.a-icon-star span.a-icon-alt::text'
        ]

        for selector in rating_selectors:
            rating_text = response.css(selector).get()
            if rating_text:
                # "5つ星のうち4.5" のような形式から数値を抽出
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    return float(rating_match.group(1))

        return 0.0

    def extract_rating_count(self, response):
        """評価数を抽出"""
        rating_count_selectors = [
            'span[data-hook="total-review-count"]::text',
            'a[data-hook="see-all-reviews-link-foot"] span::text',
            '#acrCustomerReviewText::text'
        ]

        for selector in rating_count_selectors:
            count_text = response.css(selector).get()
            if count_text:
                # "1,234個の評価" のような形式から数値を抽出
                count_match = re.search(r'([\d,]+)', count_text.replace(',', ''))
                if count_match:
                    return int(count_match.group(1).replace(',', ''))

        return 0

    def extract_price(self, response):
        """税込価格を抽出"""
        price_selectors = [
            '.a-price-current .a-offscreen::text',
            '.a-price .a-offscreen::text',
            'span.a-price-symbol + span.a-price-whole::text',
            '#price_inside_buybox::text',
            '.a-price-range .a-offscreen::text'
        ]

        for selector in price_selectors:
            price_text = response.css(selector).get()
            if price_text:
                # "￥1,234" のような形式から数値を抽出
                price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                if price_match:
                    return price_match.group(0)

        return ''

    def extract_review_count(self, response):
        """レビュー数を抽出"""
        review_selectors = [
            'a[data-hook="see-all-reviews-link-foot"] span::text',
            '#acrCustomerReviewText::text',
            'span[data-hook="total-review-count"]::text'
        ]

        for selector in review_selectors:
            review_text = response.css(selector).get()
            if review_text:
                # "1,234件のレビュー" のような形式から数値を抽出
                review_match = re.search(r'([\d,]+)', review_text.replace(',', ''))
                if review_match:
                    return int(review_match.group(1).replace(',', ''))

        return 0

    def get_page_number(self, url):
        """URLからページ番号を抽出"""
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)

            # pgパラメータからページ番号を取得
            if 'pg' in query_params:
                return int(query_params['pg'][0])

            # pageパラメータからページ番号を取得
            if 'page' in query_params:
                return int(query_params['page'][0])

        except (ValueError, IndexError):
            pass

        return 1