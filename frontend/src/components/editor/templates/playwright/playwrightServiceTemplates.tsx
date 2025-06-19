import React from 'react'
import { Globe, Zap, ShoppingCart, Search } from 'lucide-react'
import { Template } from '../types'

export const playwrightServiceTemplates: Template[] = [
  {
    id: 'playwright-service-basic',
    name: 'Playwright Service Basic Spider',
    description: '新アーキテクチャのPlaywright専用サービスを使用した基本スパイダー',
    icon: <Globe className="w-5 h-5" />,
    category: 'browser-automation',
    code: `#!/usr/bin/env python3
"""
Playwright専用サービス対応スパイダー
新アーキテクチャのPlaywright専用サービスを使用
"""

import scrapy
import json
import requests
from datetime import datetime

def debug_print(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] 🕷️ SPIDER: {message}")

class PlaywrightServiceSpider(scrapy.Spider):
    name = "playwright_service_spider"
    allowed_domains = ["example.com"]
    start_urls = ["https://example.com"]
    
    # Playwright専用サービス設定
    playwright_service_url = "http://localhost:8004"
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'FEEDS': {
            'results.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'overwrite': True,
            },
        },
        'ITEM_PIPELINES': {
            'backend.app.pipelines.database_pipeline.DatabasePipeline': 300,
        },
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        debug_print(f"Playwright Service Spider initialized")
        debug_print(f"Playwright Service URL: {self.playwright_service_url}")
    
    def start_requests(self):
        """Playwright専用サービスを使用したstart_requests"""
        debug_print("Starting spider with Playwright service integration")
        
        for url in self.start_urls:
            # Playwright専用サービスでページを取得
            content = self.fetch_with_playwright_sync(url)
            
            if content:
                debug_print("✅ Playwright fetch successful, creating Scrapy response")
                
                # Scrapyレスポンスを作成
                yield scrapy.http.HtmlResponse(
                    url=url,
                    body=content.encode('utf-8'),
                    encoding='utf-8',
                    request=scrapy.Request(url=url, callback=self.parse)
                )
            else:
                debug_print("❌ Playwright fetch failed, using fallback")
                # フォールバック: 通常のScrapyリクエスト
                yield scrapy.Request(url=url, callback=self.parse_fallback)
    
    def fetch_with_playwright_sync(self, url: str) -> str:
        """同期版のPlaywright専用サービス呼び出し"""
        debug_print(f"Fetching {url} via Playwright service")
        
        request_data = {
            "url": url,
            "browser_type": "chromium",
            "headless": True,
            "wait_for": "domcontentloaded",
            "timeout": 30000,
            "javascript_code": "window.scrollTo(0, document.body.scrollHeight);"
        }
        
        try:
            response = requests.post(
                f"{self.playwright_service_url}/execute",
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    debug_print(f"✅ Playwright fetch successful: {result.get('title', 'No title')}")
                    debug_print(f"   Execution time: {result.get('execution_time', 0):.2f}s")
                    debug_print(f"   Content length: {len(result.get('content', ''))}")
                    return result.get("content", "")
                else:
                    debug_print(f"❌ Playwright fetch failed: {result.get('error', 'Unknown error')}")
                    return None
            else:
                debug_print(f"❌ HTTP error: {response.status_code}")
                return None
                
        except Exception as e:
            debug_print(f"❌ Exception during Playwright fetch: {e}")
            return None
    
    def parse(self, response):
        """Playwright取得コンテンツの解析"""
        debug_print(f"Parsing Playwright content from: {response.url}")
        debug_print(f"Response length: {len(response.text)}")
        
        # タイトルを取得
        title = response.css('title::text').get()
        debug_print(f"Page title: {title}")
        
        # 基本的なデータを抽出
        yield {
            'url': response.url,
            'title': title,
            'method': 'playwright_service',
            'crawl_start_datetime': datetime.now().isoformat(),
            'item_acquired_datetime': datetime.now().isoformat()
        }
        
        debug_print("✅ Parsing completed")
    
    def parse_fallback(self, response):
        """フォールバック用のパース関数"""
        debug_print(f"Using fallback parsing for: {response.url}")
        
        title = response.css('title::text').get()
        debug_print(f"Fallback page title: {title}")
        
        yield {
            'url': response.url,
            'title': title,
            'method': 'fallback',
            'crawl_start_datetime': datetime.now().isoformat(),
            'item_acquired_datetime': datetime.now().isoformat()
        }
        
        debug_print("✅ Fallback parsing completed")`
  },
  {
    id: 'playwright-service-amazon',
    name: 'Amazon Ranking Spider (Playwright Service)',
    description: 'Playwright専用サービスを使用したAmazonランキングスパイダー',
    icon: <ShoppingCart className="w-5 h-5" />,
    category: 'e-commerce',
    code: `#!/usr/bin/env python3
"""
Amazon ランキングスパイダー（Playwright専用サービス版）
新アーキテクチャのPlaywright専用サービスを使用してAmazonランキングを取得
"""

import scrapy
import json
import requests
from datetime import datetime

def debug_print(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] 🛒 AMAZON: {message}")

class AmazonRankingPlaywrightSpider(scrapy.Spider):
    name = "amazon_ranking_playwright"
    allowed_domains = ["amazon.co.jp"]
    start_urls = ["https://www.amazon.co.jp/gp/bestsellers/toys/"]
    
    # Playwright専用サービス設定
    playwright_service_url = "http://localhost:8004"
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'FEEDS': {
            'amazon_ranking_results.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'overwrite': True,
            },
        },
        'ITEM_PIPELINES': {
            'backend.app.pipelines.database_pipeline.DatabasePipeline': 300,
        },
    }
    
    def start_requests(self):
        """Amazon専用のPlaywright設定でリクエスト開始"""
        debug_print("Starting Amazon ranking spider with Playwright service")
        
        for url in self.start_urls:
            content = self.fetch_amazon_with_playwright(url)
            
            if content:
                debug_print("✅ Amazon page fetched successfully")
                yield scrapy.http.HtmlResponse(
                    url=url,
                    body=content.encode('utf-8'),
                    encoding='utf-8',
                    request=scrapy.Request(url=url, callback=self.parse_ranking)
                )
            else:
                debug_print("❌ Amazon fetch failed")
                yield scrapy.Request(url=url, callback=self.parse_fallback)
    
    def fetch_amazon_with_playwright(self, url: str) -> str:
        """Amazon専用のPlaywright設定"""
        debug_print(f"Fetching Amazon page: {url}")
        
        request_data = {
            "url": url,
            "browser_type": "chromium",
            "headless": True,
            "wait_for": "domcontentloaded",
            "timeout": 30000,
            "javascript_code": """
                // ページを下にスクロール
                window.scrollTo(0, document.body.scrollHeight);
                
                // 少し待機
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // 再度スクロール
                window.scrollTo(0, document.body.scrollHeight);
                
                console.log('Amazon page scrolled and loaded');
            """
        }
        
        try:
            response = requests.post(
                f"{self.playwright_service_url}/execute",
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    debug_print(f"✅ Amazon fetch successful: {result.get('execution_time', 0):.2f}s")
                    return result.get("content", "")
                else:
                    debug_print(f"❌ Amazon fetch error: {result.get('error')}")
            
            return None
            
        except Exception as e:
            debug_print(f"❌ Exception: {e}")
            return None
    
    def parse_ranking(self, response):
        """Amazonランキングページの解析"""
        debug_print(f"Parsing Amazon ranking page: {response.url}")
        
        # ランキングアイテムを検索
        ranking_items = response.css('div[data-asin]')
        debug_print(f"Found {len(ranking_items)} ranking items")
        
        for i, item in enumerate(ranking_items[:60], 1):  # 上位60位まで
            try:
                asin = item.css('::attr(data-asin)').get()
                if not asin:
                    continue
                
                title = item.css('img::attr(alt)').get() or item.css('a span::text').get()
                image_url = item.css('img::attr(src)').get()
                product_url = item.css('a::attr(href)').get()
                
                if product_url and product_url.startswith('/'):
                    product_url = f"https://www.amazon.co.jp{product_url}"
                
                # 価格情報
                price_element = item.css('span.a-price-whole::text').get()
                price = None
                if price_element:
                    try:
                        price = int(price_element.replace(',', ''))
                    except ValueError:
                        pass
                
                # レビュー情報
                rating_element = item.css('span.a-icon-alt::text').get()
                rating = None
                if rating_element and '5つ星のうち' in rating_element:
                    try:
                        rating = float(rating_element.split('5つ星のうち')[1].split('の')[0])
                    except (IndexError, ValueError):
                        pass
                
                yield {
                    'rank': i,
                    'asin': asin,
                    'title': title,
                    'price': price,
                    'rating': rating,
                    'image_url': image_url,
                    'product_url': product_url,
                    'category': 'toys',
                    'crawl_start_datetime': datetime.now().isoformat(),
                    'item_acquired_datetime': datetime.now().isoformat(),
                    'url': response.url,
                    'method': 'playwright_service'
                }
                
                debug_print(f"Extracted item {i}: {title[:50] if title else 'No title'}...")
                
            except Exception as e:
                debug_print(f"❌ Error extracting item {i}: {e}")
                continue
        
        debug_print(f"✅ Completed Amazon ranking extraction")
    
    def parse_fallback(self, response):
        """フォールバック解析"""
        debug_print("Using fallback parsing for Amazon")
        
        yield {
            'title': 'Amazon fallback item',
            'url': response.url,
            'method': 'fallback',
            'crawl_start_datetime': datetime.now().isoformat(),
            'item_acquired_datetime': datetime.now().isoformat()
        }`
  }
]
