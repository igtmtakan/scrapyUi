import React from 'react'
import { ShoppingCart, Trophy } from 'lucide-react'
import { Template } from '../types'

export const amazonTemplates: Template[] = [
  {
    id: 'amazon-spider',
    name: 'Amazon Product Spider',
    description: 'Amazon商品情報を取得するスパイダー（教育用・利用規約遵守）',
    icon: <ShoppingCart className="w-5 h-5" />,
    category: 'ecommerce',
    code: `import scrapy
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
import json
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class AmazonSpider(scrapy.Spider):
    name = 'amazon_spider'
    allowed_domains = ['amazon.co.jp']
    start_urls = [
        'https://www.amazon.co.jp/s?k=python+book',  # 検索結果ページの例
    ]
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,  # 必ずrobotstxtを遵守
        'DOWNLOAD_DELAY': 3,     # 丁寧にアクセス
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': 2,
        'USER_AGENT': 'ScrapyUI Educational Bot 1.0 (Research Purpose)',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache',
        }
    }
    
    def parse(self, response):
        debug_print(f"Parsing Amazon page: {response.url}")
        debug_print(f"Status code: {response.status}")
        
        # 検索結果ページの場合
        if '/s?' in response.url:
            yield from self.parse_search_results(response)
        # 商品詳細ページの場合
        elif '/dp/' in response.url or '/gp/product/' in response.url:
            yield from self.parse_product_detail(response)
        else:
            debug_print("Unknown page type, extracting basic info")
            yield self.extract_basic_page_info(response)
    
    def parse_search_results(self, response):
        """検索結果ページを解析"""
        debug_print("Parsing search results page")
        
        # 商品アイテムを取得（Amazonの構造に基づく）
        product_items = response.css('[data-component-type="s-search-result"]')
        
        debug_print(f"Found {len(product_items)} product items")
        
        for i, item in enumerate(product_items[:10]):  # 最初の10個のみ
            try:
                # 商品タイトル
                title = item.css('h2 a span::text').get() or item.css('.s-title-instructions-style span::text').get()
                
                # 商品URL
                product_url = item.css('h2 a::attr(href)').get()
                if product_url:
                    product_url = response.urljoin(product_url)
                
                # 価格情報
                price = item.css('.a-price-whole::text').get()
                price_fraction = item.css('.a-price-fraction::text').get()
                if price and price_fraction:
                    full_price = f"{price}.{price_fraction}"
                else:
                    full_price = item.css('.a-price .a-offscreen::text').get()
                
                # 評価
                rating = item.css('.a-icon-alt::text').get()
                review_count = item.css('.a-size-base::text').get()
                
                # 画像URL
                image_url = item.css('.s-image::attr(src)').get()
                
                # 配送情報
                delivery_info = item.css('.a-color-base.a-text-bold::text').get()
                
                # Prime対応
                is_prime = bool(item.css('.a-icon-prime').get())
                
                product_data = {
                    'item_index': i,
                    'title': title,
                    'url': product_url,
                    'price': full_price,
                    'rating': rating,
                    'review_count': review_count,
                    'image_url': image_url,
                    'delivery_info': delivery_info,
                    'is_prime': is_prime,
                    'search_url': response.url,
                    'scraped_at': datetime.now().isoformat(),
                    'item_type': 'search_result'
                }
                
                debug_print(f"Product {i+1}: {title}")
                debug_pprint(product_data)
                
                yield product_data
                
                # 商品詳細ページもクロール（最初の3個のみ）
                if product_url and i < 3:
                    yield response.follow(
                        product_url,
                        callback=self.parse_product_detail,
                        meta={'search_result_data': product_data}
                    )
                    
            except Exception as e:
                debug_print(f"Error parsing product item {i}: {e}")
                continue
        
        # 次のページへのリンク
        next_page = response.css('.s-pagination-next::attr(href)').get()
        if next_page:
            debug_print(f"Found next page: {next_page}")
            yield response.follow(next_page, callback=self.parse_search_results)
    
    def parse_product_detail(self, response):
        """商品詳細ページを解析"""
        debug_print(f"Parsing product detail: {response.url}")
        
        try:
            # 商品タイトル
            title = response.css('#productTitle::text').get()
            if title:
                title = title.strip()
            
            # 価格情報
            price_whole = response.css('.a-price-whole::text').get()
            price_fraction = response.css('.a-price-fraction::text').get()
            if price_whole and price_fraction:
                price = f"{price_whole}.{price_fraction}"
            else:
                price = response.css('.a-price .a-offscreen::text').get()
            
            # 評価情報
            rating = response.css('.a-icon-alt::text').get()
            review_count = response.css('#acrCustomerReviewText::text').get()
            
            # 商品説明
            description = response.css('#feature-bullets ul li span::text').getall()
            description_text = ' '.join([desc.strip() for desc in description if desc.strip()])
            
            # 商品画像
            main_image = response.css('#landingImage::attr(src)').get()
            
            # 在庫状況
            availability = response.css('#availability span::text').get()
            if availability:
                availability = availability.strip()
            
            # ブランド情報
            brand = response.css('#bylineInfo::text').get()
            
            # カテゴリ情報（パンくずリスト）
            breadcrumbs = response.css('#wayfinding-breadcrumbs_feature_div a::text').getall()
            
            # 商品仕様
            specifications = {}
            spec_rows = response.css('#productDetails_techSpec_section_1 tr')
            for row in spec_rows:
                key = row.css('td:first-child::text').get()
                value = row.css('td:last-child::text').get()
                if key and value:
                    specifications[key.strip()] = value.strip()
            
            # ASIN
            asin = response.css('#ASIN::attr(value)').get()
            
            product_detail = {
                'url': response.url,
                'title': title,
                'price': price,
                'rating': rating,
                'review_count': review_count,
                'description': description_text[:500] if description_text else None,
                'main_image': main_image,
                'availability': availability,
                'brand': brand,
                'breadcrumbs': breadcrumbs,
                'specifications': specifications,
                'asin': asin,
                'scraped_at': datetime.now().isoformat(),
                'item_type': 'product_detail'
            }
            
            # 検索結果からのメタデータがあれば追加
            search_result_data = response.meta.get('search_result_data')
            if search_result_data:
                product_detail['search_result_data'] = search_result_data
            
            debug_print(f"Product detail: {title}")
            debug_pprint(product_detail)
            
            yield product_detail
            
        except Exception as e:
            debug_print(f"Error parsing product detail: {e}")
            yield {
                'url': response.url,
                'error': str(e),
                'item_type': 'error',
                'scraped_at': datetime.now().isoformat()
            }
    
    def extract_basic_page_info(self, response):
        """基本的なページ情報を抽出"""
        return {
            'url': response.url,
            'title': response.css('title::text').get(),
            'status_code': response.status,
            'page_type': 'unknown',
            'scraped_at': datetime.now().isoformat(),
            'item_type': 'basic_info'
        }
`
  },
  {
    id: 'amazon-ranking60',
    name: 'AmazonRanking60',
    description: 'Amazonランキング上位60商品を効率的に取得するスパイダー（2ページ×30商品）',
    icon: <Trophy className="w-5 h-5" />,
    category: 'ecommerce',
    code: `import scrapy
# 新アーキテクチャ: Playwright専用サービス（ポート8004）を使用
# from scrapy_playwright.page import PageMethod  # 削除済み
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
import json
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class AmazonRanking60Spider(scrapy.Spider):
    name = 'amazon_ranking60'
    allowed_domains = ['amazon.co.jp']
    start_urls = [
        'https://www.amazon.co.jp/gp/bestsellers/',  # ベストセラーランキング
    ]

    # 取得する商品数の設定
    target_items_per_page = 100  # 1ページあたりの目標商品数
    target_pages = 10           # 取得するページ数
    total_target_items = target_items_per_page * target_pages  # 合計60商品

    # 新アーキテクチャ: Scrapy-Playwright設定は不要
    custom_settings = {
        # 'DOWNLOAD_HANDLERS': {  # 削除済み - 標準HTTPダウンローダーを使用
        #     'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        #     'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        # },
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': 3,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        },
        # 'PLAYWRIGHT_BROWSER_TYPE': 'chromium',  # 削除済み
        # 'PLAYWRIGHT_LAUNCH_OPTIONS': {  # 削除済み
        #     'headless': True,
        #     'timeout': 30000,
        # },
        # 'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 30000,  # 削除済み
        # 'PLAYWRIGHT_PROCESS_REQUEST_HEADERS': None,  # 削除済み
        'FEEDS': {
            'ranking_results.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'item_export_kwargs': {
                    'ensure_ascii': False,
                },
            },
        },
        'FEED_EXPORT_ENCODING': 'utf-8',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_start_datetime = datetime.now().isoformat()
        self.items_scraped = 0
        self.pages_scraped = 0
        debug_print(f"Spider initialized. Target: {self.total_target_items} items from {self.target_pages} pages")

    async def start(self):
        """新しいstart()メソッド（Scrapy 2.13.0+対応）"""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                # 新アーキテクチャ: Playwright専用サービス（ポート8004）を使用
                # meta={
                #     'playwright': True,
                #     'playwright_page_methods': [
                #         PageMethod('wait_for_load_state', 'domcontentloaded'),
                #         PageMethod('wait_for_timeout', 2000),
                #         PageMethod('evaluate', 'window.scrollTo(0, document.body.scrollHeight)'),
                #         PageMethod('wait_for_timeout', 1000),
                #     ],
                # },
                callback=self.parse_ranking_page
            )

    def parse_ranking_page(self, response):
        """ランキングページを解析"""
        debug_print(f"Parsing ranking page: {response.url}")
        self.pages_scraped += 1

        # ランキング商品のセレクタ（複数パターンに対応）
        product_selectors = [
            'div[data-component-type="s-search-result"]',  # 検索結果形式
            '.s-result-item[data-component-type="s-search-result"]',  # 検索結果アイテム
            '.zg-item-immersion',  # ベストセラー形式
            '.a-carousel-card',    # カルーセル形式
            '.p13n-sc-uncoverable-faceout',  # おすすめ商品形式
        ]

        products_found = []
        for selector in product_selectors:
            products = response.css(selector)
            if products:
                debug_print(f"Found {len(products)} products with selector: {selector}")
                products_found = products
                break

        if not products_found:
            debug_print("No products found with any selector, trying alternative approach")
            # フォールバック: リンクベースの検索
            product_links = response.css('a[href*="/dp/"]::attr(href)').getall()
            debug_print(f"Found {len(product_links)} product links as fallback")

            for i, link in enumerate(product_links[:self.target_items_per_page]):
                if self.items_scraped >= self.total_target_items:
                    break

                product_url = urljoin(response.url, link)
                yield scrapy.Request(
                    product_url,
                    meta={
                        'playwright': True,
                        'playwright_page_methods': [
                            PageMethod('wait_for_load_state', 'domcontentloaded'),
                        ],
                        'ranking_position': i + 1 + (self.pages_scraped - 1) * self.target_items_per_page,
                        'page_number': self.pages_scraped,
                    },
                    callback=self.parse_product_detail
                )
            return

        # 商品情報を抽出
        for i, product in enumerate(products_found[:self.target_items_per_page]):
            if self.items_scraped >= self.total_target_items:
                break

            # 商品リンクを取得
            product_link = product.css('a[href*="/dp/"]::attr(href)').get()
            if not product_link:
                product_link = product.css('a::attr(href)').get()

            if product_link:
                product_url = urljoin(response.url, product_link)
                ranking_position = i + 1 + (self.pages_scraped - 1) * self.target_items_per_page

                # 基本情報を先に抽出
                title = product.css('h2 a span::text, .s-size-mini span::text, .p13n-sc-truncate::text').get()
                if title:
                    title = title.strip()

                # 価格情報
                price = product.css('.a-price .a-offscreen::text, .p13n-sc-price::text').get()

                # 評価
                rating = product.css('.a-icon-alt::text').get()

                # 画像URL
                image_url = product.css('img::attr(src)').get()

                # レビュー数
                review_count = product.css('.a-size-base::text').get()

                basic_data = {
                    'ranking_position': ranking_position,
                    'page_number': self.pages_scraped,
                    'title': title,
                    'price': price,
                    'rating': rating,
                    'review_count': review_count,
                    'image_url': image_url,
                    'product_url': product_url,
                    'source_url': response.url,
                    'scraped_at': datetime.now().isoformat(),
                    'crawl_start_datetime': self.crawl_start_datetime,
                    'item_type': 'ranking_product'
                }

                debug_print(f"Rank {ranking_position}: {title}")
                yield basic_data
                self.items_scraped += 1

                # 詳細ページも取得（オプション）
                yield scrapy.Request(
                    product_url,
                    meta={
                        'playwright': True,
                        'playwright_page_methods': [
                            PageMethod('wait_for_load_state', 'domcontentloaded'),
                        ],
                        'basic_data': basic_data,
                    },
                    callback=self.parse_product_detail,
                    dont_filter=True
                )

        # 次のページへ（目標ページ数まで）
        if self.pages_scraped < self.target_pages and self.items_scraped < self.total_target_items:
            next_page_selectors = [
                '.s-pagination-next::attr(href)',
                'a[aria-label="次へ"]::attr(href)',
                '.a-pagination .a-last a::attr(href)',
            ]

            next_page = None
            for selector in next_page_selectors:
                next_page = response.css(selector).get()
                if next_page:
                    break

            if next_page:
                next_page_url = urljoin(response.url, next_page)
                debug_print(f"Moving to next page ({self.pages_scraped + 1}/{self.target_pages}): {next_page_url}")
                yield scrapy.Request(
                    next_page_url,
                    meta={
                        'playwright': True,
                        'playwright_page_methods': [
                            PageMethod('wait_for_load_state', 'domcontentloaded'),
                            PageMethod('wait_for_timeout', 2000),
                            PageMethod('evaluate', 'window.scrollTo(0, document.body.scrollHeight)'),
                            PageMethod('wait_for_timeout', 1000),
                        ],
                    },
                    callback=self.parse_ranking_page
                )
            else:
                debug_print("No next page found or target pages reached")

    def parse_product_detail(self, response):
        """商品詳細ページを解析（ランキング情報付き）"""
        debug_print(f"Parsing product detail: {response.url}")

        basic_data = response.meta.get('basic_data', {})

        try:
            # 商品タイトル
            title = response.css('#productTitle::text').get()
            if title:
                title = title.strip()

            # 価格情報（複数パターン対応）
            price_selectors = [
                '.a-price .a-offscreen::text',
                '.a-price-whole::text',
                '#priceblock_dealprice::text',
                '#priceblock_ourprice::text',
                '.a-price-range .a-offscreen::text',
            ]

            price = None
            for selector in price_selectors:
                price = response.css(selector).get()
                if price:
                    break

            # 評価情報
            rating = response.css('.a-icon-alt::text').get()
            review_count = response.css('#acrCustomerReviewText::text').get()

            # ASIN
            asin = response.css('#ASIN::attr(value)').get()

            # ブランド
            brand = response.css('#bylineInfo::text').get()

            # 在庫状況
            availability = response.css('#availability span::text').get()
            if availability:
                availability = availability.strip()

            # カテゴリ（パンくずリスト）
            breadcrumbs = response.css('#wayfinding-breadcrumbs_feature_div a::text').getall()

            # 商品画像
            main_image = response.css('#landingImage::attr(src)').get()

            # 商品の特徴
            features = response.css('#feature-bullets ul li span::text').getall()
            features_text = [f.strip() for f in features if f.strip()]

            detailed_data = {
                **basic_data,  # 基本データをマージ
                'title_detail': title,
                'price_detail': price,
                'rating_detail': rating,
                'review_count_detail': review_count,
                'asin': asin,
                'brand': brand,
                'availability': availability,
                'breadcrumbs': breadcrumbs,
                'main_image': main_image,
                'features': features_text[:5] if features_text else [],  # 上位5つの特徴
                'detail_scraped_at': datetime.now().isoformat(),
                'item_type': 'ranking_product_detail'
            }

            debug_print(f"Detailed rank {basic_data.get('ranking_position', 'N/A')}: {title}")
            yield detailed_data

        except Exception as e:
            debug_print(f"Error parsing product detail: {e}")
            error_data = {
                **basic_data,
                'error': str(e),
                'item_type': 'ranking_error',
                'error_scraped_at': datetime.now().isoformat()
            }
            yield error_data

    def closed(self, reason):
        """スパイダー終了時の処理"""
        debug_print(f"Spider closed. Reason: {reason}")
        debug_print(f"Total items scraped: {self.items_scraped}")
        debug_print(f"Total pages scraped: {self.pages_scraped}")
        debug_print(f"Target was: {self.total_target_items} items from {self.target_pages} pages")
`
  }
]
