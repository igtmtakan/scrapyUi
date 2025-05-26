import React from 'react'
import { Building } from 'lucide-react'
import { Template } from '../types'

export const yahooShoppingTemplates: Template[] = [
  {
    id: 'yahoo-shopping-spider',
    name: 'Yahoo Shopping Spider',
    description: 'Yahoo!ショッピングの商品情報を取得するスパイダー（教育用）',
    icon: <Building className="w-5 h-5" />,
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

class YahooShoppingSpider(scrapy.Spider):
    name = 'yahoo_shopping_spider'
    allowed_domains = ['shopping.yahoo.co.jp']
    start_urls = [
        'https://shopping.yahoo.co.jp/search?p=python+本',  # 検索結果ページの例
    ]
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,  # 必ずrobotstxtを遵守
        'DOWNLOAD_DELAY': 2,     # 丁寧にアクセス
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': 2,
        'USER_AGENT': 'ScrapyUI Educational Bot 1.0 (Research Purpose)',
        'CLOSESPIDER_PAGECOUNT': 25,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        }
    }
    
    def parse(self, response):
        debug_print(f"Parsing Yahoo Shopping page: {response.url}")
        debug_print(f"Status code: {response.status}")
        
        # 検索結果ページの場合
        if '/search?' in response.url:
            yield from self.parse_search_results(response)
        # 商品詳細ページの場合
        elif '/products/' in response.url:
            yield from self.parse_product_detail(response)
        else:
            debug_print("Unknown page type, extracting basic info")
            yield self.extract_basic_page_info(response)
    
    def parse_search_results(self, response):
        """検索結果ページを解析"""
        debug_print("Parsing Yahoo Shopping search results page")
        
        # 商品アイテムを取得
        product_items = response.css('.Product')
        
        debug_print(f"Found {len(product_items)} product items")
        
        for i, item in enumerate(product_items[:10]):  # 最初の10個のみ
            try:
                # 商品タイトル
                title = item.css('.Product__titleLink::text').get()
                if not title:
                    title = item.css('.Product__title a::text').get()
                
                # 商品URL
                product_url = item.css('.Product__titleLink::attr(href)').get()
                if not product_url:
                    product_url = item.css('.Product__title a::attr(href)').get()
                if product_url:
                    product_url = response.urljoin(product_url)
                
                # 価格情報
                price = item.css('.Product__priceValue::text').get()
                if not price:
                    price = item.css('.Product__price::text').get()
                
                # ショップ名
                shop_name = item.css('.Product__seller a::text').get()
                
                # 評価情報
                rating = item.css('.Product__rating .Rating__point::text').get()
                review_count = item.css('.Product__rating .Rating__count::text').get()
                
                # 商品画像
                image_url = item.css('.Product__image img::attr(src)').get()
                
                # 送料情報
                shipping_info = item.css('.Product__shipping::text').get()
                
                # PayPay対応
                is_paypay = bool(item.css('.Product__paypay').get())
                
                # 商品説明
                description = item.css('.Product__description::text').get()
                
                product_data = {
                    'item_index': i,
                    'title': title.strip() if title else None,
                    'url': product_url,
                    'price': price.strip() if price else None,
                    'shop_name': shop_name.strip() if shop_name else None,
                    'rating': rating.strip() if rating else None,
                    'review_count': review_count.strip() if review_count else None,
                    'image_url': image_url,
                    'shipping_info': shipping_info.strip() if shipping_info else None,
                    'is_paypay': is_paypay,
                    'description': description.strip() if description else None,
                    'search_url': response.url,
                    'scraped_at': datetime.now().isoformat(),
                    'item_type': 'search_result',
                    'platform': 'yahoo_shopping'
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
        next_page = response.css('.Pager__item--next a::attr(href)').get()
        if next_page:
            debug_print(f"Found next page: {next_page}")
            yield response.follow(next_page, callback=self.parse_search_results)
    
    def parse_product_detail(self, response):
        """商品詳細ページを解析"""
        debug_print(f"Parsing Yahoo Shopping product detail: {response.url}")
        
        try:
            # 商品タイトル
            title = response.css('h1::text').get()
            if not title:
                title = response.css('.ProductDetail__title::text').get()
            
            # 価格情報
            price = response.css('.ProductDetail__price .Price__value::text').get()
            
            # ショップ情報
            shop_name = response.css('.ProductDetail__seller a::text').get()
            shop_url = response.css('.ProductDetail__seller a::attr(href)').get()
            
            # 評価情報
            rating = response.css('.ProductDetail__rating .Rating__point::text').get()
            review_count = response.css('.ProductDetail__rating .Rating__count::text').get()
            
            # 商品説明
            description_parts = response.css('.ProductDetail__description::text').getall()
            description = ' '.join([desc.strip() for desc in description_parts if desc.strip()])
            
            # 商品画像
            main_image = response.css('.ProductDetail__image img::attr(src)').get()
            sub_images = response.css('.ProductDetail__subImages img::attr(src)').getall()
            
            # 在庫状況
            availability = response.css('.ProductDetail__stock::text').get()
            
            # 送料情報
            shipping_info = response.css('.ProductDetail__shipping::text').get()
            
            # PayPay情報
            paypay_info = response.css('.ProductDetail__paypay::text').get()
            
            # 商品仕様
            specifications = {}
            spec_rows = response.css('.ProductDetail__spec tr')
            for row in spec_rows:
                key = row.css('th::text').get()
                value = row.css('td::text').get()
                if key and value:
                    specifications[key.strip()] = value.strip()
            
            # カテゴリ情報（パンくずリスト）
            breadcrumbs = response.css('.Breadcrumb a::text').getall()
            
            # 関連商品
            related_products = []
            related_items = response.css('.RelatedProducts .Product')[:5]
            for item in related_items:
                related_title = item.css('.Product__title::text').get()
                related_url = item.css('a::attr(href)').get()
                related_price = item.css('.Product__price::text').get()
                if related_title and related_url:
                    related_products.append({
                        'title': related_title.strip(),
                        'url': response.urljoin(related_url),
                        'price': related_price.strip() if related_price else None
                    })
            
            product_detail = {
                'url': response.url,
                'title': title.strip() if title else None,
                'price': price.strip() if price else None,
                'shop_name': shop_name.strip() if shop_name else None,
                'shop_url': response.urljoin(shop_url) if shop_url else None,
                'rating': rating.strip() if rating else None,
                'review_count': review_count.strip() if review_count else None,
                'description': description[:500] if description else None,
                'main_image': main_image,
                'sub_images': sub_images,
                'availability': availability.strip() if availability else None,
                'shipping_info': shipping_info.strip() if shipping_info else None,
                'paypay_info': paypay_info.strip() if paypay_info else None,
                'specifications': specifications,
                'breadcrumbs': breadcrumbs,
                'related_products': related_products,
                'scraped_at': datetime.now().isoformat(),
                'item_type': 'product_detail',
                'platform': 'yahoo_shopping'
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
                'platform': 'yahoo_shopping',
                'scraped_at': datetime.now().isoformat()
            }
    
    def extract_basic_page_info(self, response):
        """基本的なページ情報を抽出"""
        return {
            'url': response.url,
            'title': response.css('title::text').get(),
            'status_code': response.status,
            'page_type': 'unknown',
            'platform': 'yahoo_shopping',
            'scraped_at': datetime.now().isoformat(),
            'item_type': 'basic_info'
        }
`
  }
]
