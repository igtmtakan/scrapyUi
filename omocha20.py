import scrapy
import re
from urllib.parse import urljoin
from datetime import datetime


class Omocha20Spider(scrapy.Spider):
    name = "omocha20"
    allowed_domains = ["amazon.co.jp"]
    
    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "FEEDS": {
            "results.jsonl": {
                "format": "jsonlines",
                "encoding": "utf8",
                "store_empty": False,
                "overwrite": True,
            },
            "results.json": {
                "format": "json",
                "encoding": "utf8",
                "store_empty": False,
                "overwrite": True,
            },
            "results.csv": {
                "format": "csv",
                "encoding": "utf8",
                "store_empty": False,
                "overwrite": True,
            },
            "results.xml": {
                "format": "xml",
                "encoding": "utf8",
                "store_empty": False,
                "overwrite": True,
            },
        },
    }

    async def start(self):
        start_url = "https://www.amazon.co.jp/gp/bestsellers/software/ref=zg_bs_nav_software_0"
        yield scrapy.Request(
            url=start_url,
            callback=self.parse,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )

    async def parse(self, response):
        # 商品リンクを抽出（複数のセレクターを試行）
        product_links = []
        
        # Amazonベストセラーページの商品リンクセレクター
        link_selectors = [
            "a[href*='/dp/']",  # 商品詳細ページへのリンク
            "h3 a",  # タイトル内のリンク
            ".a-link-normal[href*='/dp/']",  # 通常のAmazonリンク
            ".s-link-style a",  # 検索結果スタイルのリンク
            "a.a-link-normal.aok-block"  # 元のセレクター
        ]
        
        for selector in link_selectors:
            links = response.css(f"{selector}::attr(href)").getall()
            if links:
                product_links.extend(links)
                self.logger.info(f"Found {len(links)} links with selector: {selector}")
        
        # 重複を除去し、商品ページのみをフィルタ
        unique_links = []
        for link in product_links:
            if link and '/dp/' in link and link not in unique_links:
                unique_links.append(link)
        
        self.logger.info(f"Found {len(unique_links)} unique product links on page: {response.url}")
        
        # 各商品ページを処理（最大50件まで）
        for link in unique_links[:50]:
            full_url = urljoin(response.url, link)
            yield scrapy.Request(
                url=full_url,
                callback=self.parse_product,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )
        
        # ページネーションリンクを探す（改善版）
        next_page_links = []
        
        # 複数のページネーションセレクターを試行
        pagination_selectors = [
            "a[aria-label*='次のページ']",
            "a:contains('次へ')",
            "a[aria-label*='Next']",
            ".a-pagination .a-last a",
            "a[href*='page=2']",
            "a[href*='pg=2']"
        ]
        
        for selector in pagination_selectors:
            links = response.css(f"{selector}::attr(href)").getall()
            if links:
                next_page_links.extend(links)
                self.logger.info(f"Found pagination links with selector: {selector}")
        
        # 最初のページネーションリンクのみを使用
        if next_page_links:
            next_url = urljoin(response.url, next_page_links[0])
            self.logger.info(f"Following pagination link: {next_url}")
            yield scrapy.Request(
                url=next_url,
                callback=self.parse,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )

    async def parse_product(self, response):
        # タイトル抽出（改善版）
        title = None
        title_selectors = [
            "#productTitle::text",
            "h1.a-size-large.a-spacing-none.a-color-base::text",
            "h1[data-automation-id='product-title']::text",
            "h1.a-size-large::text",
            "span#productTitle::text",
            ".product-title::text"
        ]
        
        for selector in title_selectors:
            title = response.css(selector).get()
            if title:
                title = title.strip()
                self.logger.info(f"Title found with CSS {selector}: {title}")
                break

        # まだタイトルが取得できない場合、テキスト内容を直接取得
        if not title:
            try:
                title_texts = response.css("#productTitle *::text").getall()
                if title_texts:
                    title = " ".join([t.strip() for t in title_texts if t.strip()])
                    self.logger.info(f"Title found from text content: {title}")
            except:
                pass

        # 評価抽出（改善版）
        rating = None
        rating_selectors = [
            "span.a-icon-alt::text",
            "[data-hook='rating-out-of-text']::text",
            ".a-star-rating .a-icon-alt::text",
            "i[data-hook='average-star-rating'] .a-icon-alt::text",
            ".cr-original-review-text .a-icon-alt::text"
        ]
        
        for selector in rating_selectors:
            rating_text = response.css(selector).get()
            if rating_text:
                # "5つ星のうち4.2" のような形式から数値を抽出
                rating_match = re.search(r"(\d+\.?\d*)", rating_text)
                if rating_match:
                    rating = rating_match.group(1)
                    self.logger.info(f"Rating found with CSS {selector}: {rating}")
                    break

        # まだ評価が取得できない場合、より広範囲で検索
        if not rating:
            try:
                all_text = response.text
                rating_patterns = [
                    r"(\d+\.?\d*)\s*つ星",
                    r"(\d+\.?\d*)\s*out of 5",
                    r"(\d+\.?\d*)\s*星",
                    r"評価:\s*(\d+\.?\d*)",
                    r"5つ星のうち(\d+\.?\d*)"
                ]
                
                for pattern in rating_patterns:
                    match = re.search(pattern, all_text, re.IGNORECASE)
                    if match:
                        rating = match.group(1)
                        self.logger.info(f"Rating found with pattern {pattern}: {rating}")
                        break
            except:
                pass

        # 税込価格抽出（改善版）
        price = None
        price_selectors = [
            ".a-price .a-offscreen::text",
            ".a-price-whole::text",
            "[data-automation-id='price']::text",
            ".a-price-range .a-offscreen::text"
        ]
        
        for selector in price_selectors:
            price = response.css(selector).get()
            if price and "￥" in price:
                self.logger.info(f"Price found with CSS {selector}: {price}")
                break

        # レビュー数抽出（改善版）
        reviews = None
        review_selectors = [
            "[data-hook='total-review-count']::text",
            "#acrCustomerReviewText::text",
            "a[href*='#customerReviews']::text",
            ".a-link-normal[href*='customerReviews']::text",
            "span[data-hook='total-review-count']::text",
            "#acrCustomerReviewLink::text"
        ]
        
        for selector in review_selectors:
            review_text = response.css(selector).get()
            if review_text:
                review_match = re.search(r"(\d+)", review_text.replace(",", ""))
                if review_match:
                    reviews = review_match.group(1)
                    self.logger.info(f"Reviews found with CSS {selector}: {reviews}")
                    break

        # 画像パス抽出（改善版）
        image_url = None
        image_selectors = [
            "img.a-dynamic-image.a-stretch-vertical::attr(src)",
            "#landingImage::attr(src)",
            "img[data-old-hires]::attr(data-old-hires)",
            ".a-dynamic-image::attr(src)",
            "img.a-dynamic-image::attr(src)"
        ]
        
        for selector in image_selectors:
            image_url = response.css(selector).get()
            if image_url and image_url.startswith("http"):
                self.logger.info(f"Image found with CSS {selector}: {image_url}")
                break

        yield {
            "title": title or "",
            "rating": rating,
            "price": price or "",
            "reviews": reviews,
            "image_url": image_url or "",
            "product_url": response.url,
            "scraped_at": datetime.now().isoformat()
        }
