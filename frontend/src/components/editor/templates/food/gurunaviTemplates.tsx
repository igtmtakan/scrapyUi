import React from 'react'
import { Coffee, MapPin } from 'lucide-react'
import { Template } from '../types'

export const gurunaviTemplates: Template[] = [
  {
    id: 'gurunavi-spider',
    name: 'Gurunavi Restaurant Spider',
    description: 'ぐるなびのレストラン情報を取得するスパイダー（教育用）',
    icon: <Coffee className="w-5 h-5" />,
    category: 'food',
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

class GurunaviSpider(scrapy.Spider):
    name = 'gurunavi_spider'
    allowed_domains = ['r.gnavi.co.jp']
    start_urls = [
        'https://r.gnavi.co.jp/area/tokyo/',  # 東京エリアの例
    ]
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,  # 必ずrobotstxtを遵守
        'DOWNLOAD_DELAY': 2,     # 丁寧にアクセス
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': 2,
        'USER_AGENT': 'ScrapyUI Educational Bot 1.0 (Research Purpose)',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        }
    }
    
    def parse(self, response):
        debug_print(f"Parsing Gurunavi page: {response.url}")
        debug_print(f"Status code: {response.status}")
        
        # エリアページの場合
        if '/area/' in response.url:
            yield from self.parse_area_page(response)
        # レストラン詳細ページの場合
        elif '/restaurant/' in response.url:
            yield from self.parse_restaurant_detail(response)
        else:
            debug_print("Unknown page type, extracting basic info")
            yield self.extract_basic_page_info(response)
    
    def parse_area_page(self, response):
        """エリアページを解析"""
        debug_print("Parsing Gurunavi area page")
        
        # レストランアイテムを取得
        restaurant_items = response.css('.restaurant-list .restaurant-item, .shop-list .shop-item')
        
        debug_print(f"Found {len(restaurant_items)} restaurant items")
        
        for i, item in enumerate(restaurant_items[:15]):  # 最初の15個のみ
            try:
                # レストラン名
                name = item.css('.restaurant-name a::text').get()
                if not name:
                    name = item.css('.shop-name a::text').get()
                
                # レストランURL
                restaurant_url = item.css('.restaurant-name a::attr(href)').get()
                if not restaurant_url:
                    restaurant_url = item.css('.shop-name a::attr(href)').get()
                if restaurant_url:
                    restaurant_url = response.urljoin(restaurant_url)
                
                # 料理ジャンル
                cuisine_type = item.css('.cuisine-type::text').get()
                if not cuisine_type:
                    cuisine_type = item.css('.genre::text').get()
                
                # エリア・住所
                area = item.css('.area::text').get()
                if not area:
                    area = item.css('.address::text').get()
                
                # 評価
                rating = item.css('.rating .score::text').get()
                review_count = item.css('.rating .review-count::text').get()
                
                # 予算
                budget = item.css('.budget::text').get()
                
                # 営業時間
                hours = item.css('.hours::text').get()
                
                # 画像
                image_url = item.css('.restaurant-image img::attr(src)').get()
                
                # 特徴・キャッチコピー
                features = item.css('.features::text').getall()
                catch_copy = item.css('.catch-copy::text').get()
                
                # アクセス情報
                access = item.css('.access::text').get()
                
                restaurant_data = {
                    'item_index': i,
                    'name': name.strip() if name else None,
                    'url': restaurant_url,
                    'cuisine_type': cuisine_type.strip() if cuisine_type else None,
                    'area': area.strip() if area else None,
                    'rating': rating.strip() if rating else None,
                    'review_count': review_count.strip() if review_count else None,
                    'budget': budget.strip() if budget else None,
                    'hours': hours.strip() if hours else None,
                    'image_url': image_url,
                    'features': [f.strip() for f in features if f.strip()],
                    'catch_copy': catch_copy.strip() if catch_copy else None,
                    'access': access.strip() if access else None,
                    'area_url': response.url,
                    'scraped_at': datetime.now().isoformat(),
                    'item_type': 'restaurant_list',
                    'platform': 'gurunavi'
                }
                
                debug_print(f"Restaurant {i+1}: {name}")
                debug_pprint(restaurant_data)
                
                yield restaurant_data
                
                # レストラン詳細ページもクロール（最初の5個のみ）
                if restaurant_url and i < 5:
                    yield response.follow(
                        restaurant_url,
                        callback=self.parse_restaurant_detail,
                        meta={'list_data': restaurant_data}
                    )
                    
            except Exception as e:
                debug_print(f"Error parsing restaurant item {i}: {e}")
                continue
        
        # 次のページへのリンク
        next_page = response.css('.pager .next a::attr(href)').get()
        if next_page:
            debug_print(f"Found next page: {next_page}")
            yield response.follow(next_page, callback=self.parse_area_page)
    
    def parse_restaurant_detail(self, response):
        """レストラン詳細ページを解析"""
        debug_print(f"Parsing Gurunavi restaurant detail: {response.url}")
        
        try:
            # レストラン名
            name = response.css('h1::text').get()
            if not name:
                name = response.css('.restaurant-name::text').get()
            
            # 料理ジャンル
            cuisine_type = response.css('.cuisine-type::text').get()
            
            # 住所
            address = response.css('.address::text').get()
            
            # 電話番号
            phone = response.css('.phone::text').get()
            
            # 営業時間
            hours = response.css('.hours::text').get()
            
            # 定休日
            closed_days = response.css('.closed-days::text').get()
            
            # 予算
            budget_lunch = response.css('.budget-lunch::text').get()
            budget_dinner = response.css('.budget-dinner::text').get()
            
            # 評価情報
            rating = response.css('.rating .score::text').get()
            review_count = response.css('.rating .review-count::text').get()
            
            # アクセス情報
            access = response.css('.access::text').get()
            
            # 座席数
            seats = response.css('.seats::text').get()
            
            # 個室情報
            private_rooms = response.css('.private-rooms::text').get()
            
            # 禁煙・喫煙
            smoking = response.css('.smoking::text').get()
            
            # 駐車場
            parking = response.css('.parking::text').get()
            
            # クレジットカード
            credit_card = response.css('.credit-card::text').get()
            
            # 特徴・サービス
            features = response.css('.features li::text').getall()
            
            # メニュー情報
            menu_items = []
            menu_sections = response.css('.menu-section')
            for section in menu_sections[:3]:  # 最初の3セクションのみ
                section_name = section.css('.section-name::text').get()
                items = section.css('.menu-item')
                for item in items[:5]:  # 各セクション最初の5個のみ
                    item_name = item.css('.item-name::text').get()
                    item_price = item.css('.item-price::text').get()
                    if item_name:
                        menu_items.append({
                            'section': section_name.strip() if section_name else None,
                            'name': item_name.strip(),
                            'price': item_price.strip() if item_price else None
                        })
            
            # 画像
            main_image = response.css('.main-image img::attr(src)').get()
            sub_images = response.css('.sub-images img::attr(src)').getall()
            
            # レビュー（最初の3件のみ）
            reviews = []
            review_items = response.css('.review-item')[:3]
            for review in review_items:
                review_rating = review.css('.review-rating::text').get()
                review_text = review.css('.review-text::text').get()
                review_date = review.css('.review-date::text').get()
                if review_text:
                    reviews.append({
                        'rating': review_rating.strip() if review_rating else None,
                        'text': review_text.strip()[:200],  # 最初の200文字のみ
                        'date': review_date.strip() if review_date else None
                    })
            
            restaurant_detail = {
                'url': response.url,
                'name': name.strip() if name else None,
                'cuisine_type': cuisine_type.strip() if cuisine_type else None,
                'address': address.strip() if address else None,
                'phone': phone.strip() if phone else None,
                'hours': hours.strip() if hours else None,
                'closed_days': closed_days.strip() if closed_days else None,
                'budget_lunch': budget_lunch.strip() if budget_lunch else None,
                'budget_dinner': budget_dinner.strip() if budget_dinner else None,
                'rating': rating.strip() if rating else None,
                'review_count': review_count.strip() if review_count else None,
                'access': access.strip() if access else None,
                'seats': seats.strip() if seats else None,
                'private_rooms': private_rooms.strip() if private_rooms else None,
                'smoking': smoking.strip() if smoking else None,
                'parking': parking.strip() if parking else None,
                'credit_card': credit_card.strip() if credit_card else None,
                'features': [f.strip() for f in features if f.strip()],
                'menu_items': menu_items,
                'main_image': main_image,
                'sub_images': sub_images,
                'reviews': reviews,
                'scraped_at': datetime.now().isoformat(),
                'item_type': 'restaurant_detail',
                'platform': 'gurunavi'
            }
            
            # リストからのメタデータがあれば追加
            list_data = response.meta.get('list_data')
            if list_data:
                restaurant_detail['list_data'] = list_data
            
            debug_print(f"Restaurant detail: {name}")
            debug_pprint(restaurant_detail)
            
            yield restaurant_detail
            
        except Exception as e:
            debug_print(f"Error parsing restaurant detail: {e}")
            yield {
                'url': response.url,
                'error': str(e),
                'item_type': 'error',
                'platform': 'gurunavi',
                'scraped_at': datetime.now().isoformat()
            }
    
    def extract_basic_page_info(self, response):
        """基本的なページ情報を抽出"""
        return {
            'url': response.url,
            'title': response.css('title::text').get(),
            'status_code': response.status,
            'page_type': 'unknown',
            'platform': 'gurunavi',
            'scraped_at': datetime.now().isoformat(),
            'item_type': 'basic_info'
        }
`
  },
  {
    id: 'gurunavi-area-spider',
    name: 'Gurunavi Area Spider',
    description: 'ぐるなびの地域別レストラン情報を取得するスパイダー',
    icon: <MapPin className="w-5 h-5" />,
    category: 'food',
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

class GurunaviAreaSpider(scrapy.Spider):
    name = 'gurunavi_area_spider'
    allowed_domains = ['r.gnavi.co.jp']
    start_urls = [
        'https://r.gnavi.co.jp/area/',  # エリア一覧ページ
    ]
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': 3,
        'USER_AGENT': 'ScrapyUI Educational Area Bot 1.0',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        }
    }
    
    def parse(self, response):
        debug_print(f"Parsing Gurunavi area list: {response.url}")
        
        # 都道府県リストを取得
        prefectures = response.css('.area-list .prefecture, .pref-list a')
        
        debug_print(f"Found {len(prefectures)} prefectures")
        
        for i, prefecture in enumerate(prefectures[:10]):  # 最初の10都道府県のみ
            pref_name = prefecture.css('::text').get()
            pref_url = prefecture.css('::attr(href)').get()
            
            if pref_url and pref_name:
                debug_print(f"Following prefecture: {pref_name}")
                yield response.follow(
                    pref_url,
                    callback=self.parse_prefecture_page,
                    meta={'prefecture_name': pref_name.strip()}
                )
    
    def parse_prefecture_page(self, response):
        """都道府県ページを解析"""
        prefecture_name = response.meta.get('prefecture_name', 'unknown')
        debug_print(f"Parsing prefecture page: {prefecture_name}")
        
        # 市区町村リストを取得
        cities = response.css('.city-list a, .area-list .city')
        
        debug_print(f"Found {len(cities)} cities in {prefecture_name}")
        
        for i, city in enumerate(cities[:5]):  # 最初の5市区町村のみ
            city_name = city.css('::text').get()
            city_url = city.css('::attr(href)').get()
            
            if city_url and city_name:
                debug_print(f"Following city: {city_name}")
                yield response.follow(
                    city_url,
                    callback=self.parse_city_page,
                    meta={
                        'prefecture_name': prefecture_name,
                        'city_name': city_name.strip()
                    }
                )
        
        # 都道府県レベルの統計情報
        pref_stats = {
            'prefecture_name': prefecture_name,
            'total_cities': len(cities),
            'url': response.url,
            'scraped_at': datetime.now().isoformat(),
            'item_type': 'prefecture_stats',
            'platform': 'gurunavi'
        }
        
        yield pref_stats
    
    def parse_city_page(self, response):
        """市区町村ページを解析"""
        prefecture_name = response.meta.get('prefecture_name', 'unknown')
        city_name = response.meta.get('city_name', 'unknown')
        
        debug_print(f"Parsing city page: {city_name}, {prefecture_name}")
        
        # ジャンル別レストラン数を取得
        genres = response.css('.genre-list .genre-item')
        genre_stats = []
        
        for genre in genres:
            genre_name = genre.css('.genre-name::text').get()
            restaurant_count = genre.css('.count::text').get()
            
            if genre_name:
                # 数字を抽出
                count = 0
                if restaurant_count:
                    count_match = re.search(r'(\d+)', restaurant_count)
                    if count_match:
                        count = int(count_match.group(1))
                
                genre_stats.append({
                    'genre_name': genre_name.strip(),
                    'restaurant_count': count
                })
        
        # エリア内のレストランリストを取得
        restaurants = response.css('.restaurant-list .restaurant-item')[:10]  # 最初の10件のみ
        restaurant_list = []
        
        for restaurant in restaurants:
            name = restaurant.css('.name::text').get()
            cuisine = restaurant.css('.cuisine::text').get()
            rating = restaurant.css('.rating::text').get()
            
            if name:
                restaurant_list.append({
                    'name': name.strip(),
                    'cuisine': cuisine.strip() if cuisine else None,
                    'rating': rating.strip() if rating else None
                })
        
        # 市区町村の統計情報
        city_stats = {
            'prefecture_name': prefecture_name,
            'city_name': city_name,
            'total_restaurants': len(restaurants),
            'genre_breakdown': genre_stats,
            'sample_restaurants': restaurant_list,
            'url': response.url,
            'scraped_at': datetime.now().isoformat(),
            'item_type': 'city_stats',
            'platform': 'gurunavi'
        }
        
        debug_print(f"City stats for {city_name}:")
        debug_pprint(city_stats)
        
        yield city_stats
        
        # 人気ジャンルの詳細ページもクロール（最初の3ジャンルのみ）
        for i, genre in enumerate(genres[:3]):
            genre_url = genre.css('a::attr(href)').get()
            genre_name = genre.css('.genre-name::text').get()
            
            if genre_url and genre_name:
                yield response.follow(
                    genre_url,
                    callback=self.parse_genre_page,
                    meta={
                        'prefecture_name': prefecture_name,
                        'city_name': city_name,
                        'genre_name': genre_name.strip()
                    }
                )
    
    def parse_genre_page(self, response):
        """ジャンル別ページを解析"""
        prefecture_name = response.meta.get('prefecture_name', 'unknown')
        city_name = response.meta.get('city_name', 'unknown')
        genre_name = response.meta.get('genre_name', 'unknown')
        
        debug_print(f"Parsing genre page: {genre_name} in {city_name}, {prefecture_name}")
        
        # ジャンル内のレストランを取得
        restaurants = response.css('.restaurant-list .restaurant-item')
        
        for i, restaurant in enumerate(restaurants[:5]):  # 最初の5件のみ
            name = restaurant.css('.name a::text').get()
            url = restaurant.css('.name a::attr(href)').get()
            cuisine = restaurant.css('.cuisine::text').get()
            area = restaurant.css('.area::text').get()
            budget = restaurant.css('.budget::text').get()
            rating = restaurant.css('.rating .score::text').get()
            
            restaurant_data = {
                'prefecture_name': prefecture_name,
                'city_name': city_name,
                'genre_name': genre_name,
                'name': name.strip() if name else None,
                'url': response.urljoin(url) if url else None,
                'cuisine': cuisine.strip() if cuisine else None,
                'area': area.strip() if area else None,
                'budget': budget.strip() if budget else None,
                'rating': rating.strip() if rating else None,
                'genre_page_url': response.url,
                'scraped_at': datetime.now().isoformat(),
                'item_type': 'genre_restaurant',
                'platform': 'gurunavi'
            }
            
            debug_print(f"Genre restaurant {i+1}: {name}")
            debug_pprint(restaurant_data)
            
            yield restaurant_data
`
  }
]
