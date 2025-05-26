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
        'CLOSESPIDER_PAGECOUNT': 20,
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
  }
]
