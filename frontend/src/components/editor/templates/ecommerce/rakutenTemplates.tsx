import React from 'react'
import { Store, Award } from 'lucide-react'
import { Template } from '../types'

export const rakutenTemplates: Template[] = [
  {
    id: 'rakuten-spider',
    name: 'Rakuten Product Spider',
    description: '楽天市場の商品情報を取得するスパイダー（教育用・利用規約遵守）',
    icon: <Store className="w-5 h-5" />,
    category: 'ecommerce',
    code: `import scrapy
from urllib.parse import urljoin, urlparse, parse_qs
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

class RakutenSpider(scrapy.Spider):
    name = 'rakuten_spider'
    allowed_domains = ['search.rakuten.co.jp', 'item.rakuten.co.jp']
    start_urls = [
        'https://search.rakuten.co.jp/search/mall/python+本/',  # 検索結果ページの例
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
        debug_print(f"Parsing Rakuten page: {response.url}")
        debug_print(f"Status code: {response.status}")
        
        # 検索結果ページの場合
        if 'search.rakuten.co.jp' in response.url:
            yield from self.parse_search_results(response)
        # 商品詳細ページの場合
        elif 'item.rakuten.co.jp' in response.url:
            yield from self.parse_product_detail(response)
        else:
            debug_print("Unknown page type, extracting basic info")
            yield self.extract_basic_page_info(response)
    
    def parse_search_results(self, response):
        """検索結果ページを解析"""
        debug_print("Parsing Rakuten search results page")
        
        # 商品アイテムを取得
        product_items = response.css('.searchresultitem')
        
        debug_print(f"Found {len(product_items)} product items")
        
        for i, item in enumerate(product_items[:10]):  # 最初の10個のみ
            try:
                # 商品タイトル
                title = item.css('.content.title h2 a::text').get()
                if not title:
                    title = item.css('.title a::text').get()
                
                # 商品URL
                product_url = item.css('.content.title h2 a::attr(href)').get()
                if not product_url:
                    product_url = item.css('.title a::attr(href)').get()
                
                # 価格情報
                price = item.css('.important::text').get()
                if not price:
                    price = item.css('.price::text').get()
                
                # ショップ名
                shop_name = item.css('.merchant a::text').get()
                
                # 評価情報
                rating = item.css('.ratting .star::text').get()
                review_count = item.css('.ratting .review a::text').get()
                
                # 商品画像
                image_url = item.css('.image img::attr(src)').get()
                
                # 送料情報
                shipping_info = item.css('.postage::text').get()
                
                # ポイント情報
                points = item.css('.point::text').get()
                
                # 商品説明
                description = item.css('.description::text').get()
                
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
                    'points': points.strip() if points else None,
                    'description': description.strip() if description else None,
                    'search_url': response.url,
                    'scraped_at': datetime.now().isoformat(),
                    'item_type': 'search_result',
                    'platform': 'rakuten'
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
        next_page = response.css('.pager .next a::attr(href)').get()
        if next_page:
            debug_print(f"Found next page: {next_page}")
            yield response.follow(next_page, callback=self.parse_search_results)
    
    def parse_product_detail(self, response):
        """商品詳細ページを解析"""
        debug_print(f"Parsing Rakuten product detail: {response.url}")
        
        try:
            # 商品タイトル
            title = response.css('h1::text').get()
            if not title:
                title = response.css('.item_name::text').get()
            
            # 価格情報
            price = response.css('.price2::text').get()
            if not price:
                price = response.css('.price::text').get()
            
            # ショップ情報
            shop_name = response.css('.shop_name a::text').get()
            shop_url = response.css('.shop_name a::attr(href)').get()
            
            # 評価情報
            rating = response.css('.review_rate .star::text').get()
            review_count = response.css('.review_rate .review_count::text').get()
            
            # 商品説明
            description_parts = response.css('.item_desc::text').getall()
            description = ' '.join([desc.strip() for desc in description_parts if desc.strip()])
            
            # 商品画像
            main_image = response.css('.item_image img::attr(src)').get()
            sub_images = response.css('.sub_image img::attr(src)').getall()
            
            # 在庫状況
            availability = response.css('.inventory::text').get()
            
            # 送料情報
            shipping_info = response.css('.postage::text').get()
            
            # ポイント情報
            points = response.css('.point::text').get()
            
            # 商品仕様
            specifications = {}
            spec_rows = response.css('.spec_table tr')
            for row in spec_rows:
                key = row.css('th::text').get()
                value = row.css('td::text').get()
                if key and value:
                    specifications[key.strip()] = value.strip()
            
            # カテゴリ情報（パンくずリスト）
            breadcrumbs = response.css('.breadcrumb a::text').getall()
            
            # 関連商品
            related_products = []
            related_items = response.css('.related_item')[:5]
            for item in related_items:
                related_title = item.css('.title::text').get()
                related_url = item.css('a::attr(href)').get()
                related_price = item.css('.price::text').get()
                if related_title and related_url:
                    related_products.append({
                        'title': related_title.strip(),
                        'url': related_url,
                        'price': related_price.strip() if related_price else None
                    })
            
            product_detail = {
                'url': response.url,
                'title': title.strip() if title else None,
                'price': price.strip() if price else None,
                'shop_name': shop_name.strip() if shop_name else None,
                'shop_url': shop_url,
                'rating': rating.strip() if rating else None,
                'review_count': review_count.strip() if review_count else None,
                'description': description[:500] if description else None,
                'main_image': main_image,
                'sub_images': sub_images,
                'availability': availability.strip() if availability else None,
                'shipping_info': shipping_info.strip() if shipping_info else None,
                'points': points.strip() if points else None,
                'specifications': specifications,
                'breadcrumbs': breadcrumbs,
                'related_products': related_products,
                'scraped_at': datetime.now().isoformat(),
                'item_type': 'product_detail',
                'platform': 'rakuten'
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
                'platform': 'rakuten',
                'scraped_at': datetime.now().isoformat()
            }
    
    def extract_basic_page_info(self, response):
        """基本的なページ情報を抽出"""
        return {
            'url': response.url,
            'title': response.css('title::text').get(),
            'status_code': response.status,
            'page_type': 'unknown',
            'platform': 'rakuten',
            'scraped_at': datetime.now().isoformat(),
            'item_type': 'basic_info'
        }
`
  },
  {
    id: 'rakuten-ranking-spider',
    name: 'Rakuten Ranking Spider',
    description: '楽天市場のランキング情報を取得するスパイダー（教育用）',
    icon: <Award className="w-5 h-5" />,
    category: 'ecommerce',
    code: `import scrapy
from urllib.parse import urljoin
import re
from datetime import datetime
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class RakutenRankingSpider(scrapy.Spider):
    name = 'rakuten_ranking_spider'
    allowed_domains = ['ranking.rakuten.co.jp']
    start_urls = [
        'https://ranking.rakuten.co.jp/',  # 総合ランキング
        'https://ranking.rakuten.co.jp/daily/',  # デイリーランキング
        'https://ranking.rakuten.co.jp/weekly/', # ウィークリーランキング
    ]
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': 3,
        'USER_AGENT': 'ScrapyUI Educational Ranking Bot 1.0',
        'CLOSESPIDER_PAGECOUNT': 30,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        }
    }
    
    def parse(self, response):
        debug_print(f"Parsing Rakuten ranking page: {response.url}")
        
        # ランキングタイプを判定
        ranking_type = self.determine_ranking_type(response.url)
        
        # カテゴリリストを取得
        categories = response.css('.category_list a, .genre_list a')
        
        debug_print(f"Found {len(categories)} categories")
        
        # メインページのランキングを解析
        yield from self.parse_ranking_page(response, ranking_type, 'all')
        
        # 各カテゴリのランキングもクロール（最初の5個のみ）
        for i, category in enumerate(categories[:5]):
            category_name = category.css('::text').get()
            category_url = category.css('::attr(href)').get()
            
            if category_url and category_name:
                debug_print(f"Following category: {category_name}")
                yield response.follow(
                    category_url,
                    callback=self.parse_ranking_page,
                    meta={
                        'ranking_type': ranking_type,
                        'category_name': category_name.strip()
                    }
                )
    
    def determine_ranking_type(self, url):
        """URLからランキングタイプを判定"""
        if 'daily' in url:
            return 'daily'
        elif 'weekly' in url:
            return 'weekly'
        elif 'monthly' in url:
            return 'monthly'
        elif 'realtime' in url:
            return 'realtime'
        else:
            return 'general'
    
    def parse_ranking_page(self, response, ranking_type=None, category_name=None):
        """ランキングページを解析"""
        if ranking_type is None:
            ranking_type = response.meta.get('ranking_type', 'unknown')
        if category_name is None:
            category_name = response.meta.get('category_name', 'unknown')
        
        debug_print(f"Parsing ranking: {ranking_type}, category: {category_name}")
        
        # ランキングアイテムを取得
        ranking_items = response.css('.ranking_list .ranking_item, .item_list .item')
        
        debug_print(f"Found {len(ranking_items)} ranking items")
        
        for i, item in enumerate(ranking_items):
            try:
                # ランキング順位
                rank = item.css('.rank::text').get()
                if rank:
                    rank = re.sub(r'[^0-9]', '', rank)
                    rank = int(rank) if rank.isdigit() else i + 1
                else:
                    rank = i + 1
                
                # 商品タイトル
                title = item.css('.title a::text').get()
                if not title:
                    title = item.css('.item_name::text').get()
                
                # 商品URL
                product_url = item.css('.title a::attr(href)').get()
                if not product_url:
                    product_url = item.css('.item_name a::attr(href)').get()
                
                # 価格情報
                price = item.css('.price::text').get()
                
                # ショップ名
                shop_name = item.css('.shop_name::text').get()
                
                # 評価情報
                rating = item.css('.rating .star::text').get()
                review_count = item.css('.review_count::text').get()
                
                # 商品画像
                image_url = item.css('img::attr(src)').get()
                
                # ランキング変動情報
                ranking_change = item.css('.change::text').get()
                
                # ポイント情報
                points = item.css('.point::text').get()
                
                ranking_data = {
                    'rank': rank,
                    'title': title.strip() if title else None,
                    'url': product_url,
                    'price': price.strip() if price else None,
                    'shop_name': shop_name.strip() if shop_name else None,
                    'rating': rating.strip() if rating else None,
                    'review_count': review_count.strip() if review_count else None,
                    'image_url': image_url,
                    'ranking_change': ranking_change.strip() if ranking_change else None,
                    'points': points.strip() if points else None,
                    'ranking_type': ranking_type,
                    'category_name': category_name,
                    'ranking_url': response.url,
                    'scraped_at': datetime.now().isoformat(),
                    'item_type': 'ranking_item',
                    'platform': 'rakuten'
                }
                
                debug_print(f"Rank {rank}: {title}")
                debug_pprint(ranking_data)
                
                yield ranking_data
                
            except Exception as e:
                debug_print(f"Error parsing ranking item {i}: {e}")
                continue
        
        # ページネーション
        next_page = response.css('.pager .next a::attr(href)').get()
        if next_page:
            debug_print(f"Found next page: {next_page}")
            yield response.follow(
                next_page,
                callback=self.parse_ranking_page,
                meta={
                    'ranking_type': ranking_type,
                    'category_name': category_name
                }
            )
        
        # カテゴリ情報も出力
        category_info = {
            'category_name': category_name,
            'ranking_type': ranking_type,
            'url': response.url,
            'total_items': len(ranking_items),
            'platform': 'rakuten',
            'scraped_at': datetime.now().isoformat(),
            'item_type': 'category_info'
        }
        
        yield category_info
`
  }
]
