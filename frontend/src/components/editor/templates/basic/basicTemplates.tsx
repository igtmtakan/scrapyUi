import React from 'react'
import { FileText, Code, Globe, Database } from 'lucide-react'
import { Template } from '../types'

export const basicTemplates: Template[] = [
  {
    id: 'basic-spider',
    name: 'Basic Spider',
    description: '基本的なスパイダーテンプレート',
    icon: <FileText className="w-5 h-5" />,
    category: 'basic',
    code: `import scrapy
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class BasicSpider(scrapy.Spider):
    name = 'basic_spider'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com']
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'ScrapyUI Basic Spider 1.0',
    }
    
    def parse(self, response):
        debug_print(f"Processing: {response.url}")
        debug_print(f"Status code: {response.status}")
        
        # ページタイトルを取得
        title = response.css('title::text').get()
        
        # すべてのリンクを取得
        links = response.css('a::attr(href)').getall()
        
        # データを構造化
        page_data = {
            'url': response.url,
            'title': title,
            'links_count': len(links),
            'links': links[:10],  # 最初の10個のリンクのみ
        }
        
        debug_print(f"Page title: {title}")
        debug_print(f"Found {len(links)} links")
        debug_pprint(page_data)
        
        yield page_data
        
        # 内部リンクをフォロー（最初の3個のみ）
        for link in links[:3]:
            if link.startswith('/'):
                yield response.follow(link, self.parse)
`
  },
  {
    id: 'basic-http-spider',
    name: 'Basic HTTP Spider',
    description: 'HTTP基本機能を使ったスパイダー',
    icon: <Code className="w-5 h-5" />,
    category: 'basic',
    code: `import scrapy
from scrapy.http import Request
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class BasicHttpSpider(scrapy.Spider):
    name = 'basic_http_spider'
    allowed_domains = ['httpbin.org']
    start_urls = ['https://httpbin.org/']
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'ScrapyUI HTTP Spider 1.0',
    }
    
    def parse(self, response):
        debug_print(f"Processing: {response.url}")
        debug_print(f"Status code: {response.status}")
        
        # HTTPヘッダーを確認
        headers_info = {
            'content_type': response.headers.get('Content-Type', b'').decode(),
            'server': response.headers.get('Server', b'').decode(),
            'content_length': response.headers.get('Content-Length', b'').decode(),
        }
        
        # ページの基本情報
        page_info = {
            'url': response.url,
            'status': response.status,
            'headers': headers_info,
            'body_length': len(response.body),
        }
        
        debug_print("HTTP Response Info:")
        debug_pprint(page_info)
        
        yield page_info
        
        # 異なるHTTPメソッドをテスト
        test_urls = [
            'https://httpbin.org/get',
            'https://httpbin.org/headers',
            'https://httpbin.org/user-agent',
        ]
        
        for url in test_urls:
            yield Request(
                url,
                callback=self.parse_test_endpoint,
                meta={'test_type': url.split('/')[-1]}
            )
    
    def parse_test_endpoint(self, response):
        """テストエンドポイントの解析"""
        test_type = response.meta.get('test_type', 'unknown')
        
        debug_print(f"Testing endpoint: {test_type}")
        
        try:
            import json
            data = json.loads(response.text)
            
            test_result = {
                'test_type': test_type,
                'url': response.url,
                'status': response.status,
                'response_data': data,
            }
            
            debug_print(f"Test result for {test_type}:")
            debug_pprint(test_result)
            
            yield test_result
            
        except json.JSONDecodeError:
            debug_print(f"Failed to parse JSON for {test_type}")
            yield {
                'test_type': test_type,
                'url': response.url,
                'status': response.status,
                'error': 'JSON decode error',
                'raw_response': response.text[:200]
            }
`
  }
]
