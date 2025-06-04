import React from 'react'
import { Monitor, Smartphone } from 'lucide-react'
import { Template } from '../types'

export const playwrightTemplates: Template[] = [
  {
    id: 'playwright-advanced-spider',
    name: 'Playwright Advanced Spider',
    description: 'Playwright独自メソッドを活用した高度なスパイダー',
    icon: <Monitor className="w-5 h-5" />,
    category: 'playwright',
    code: `import scrapy
from scrapy_playwright.page import PageMethod
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from urllib.parse import urljoin
import asyncio
import json
from datetime import datetime
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class PlaywrightAdvancedSpider(scrapy.Spider):
    name = 'playwright_advanced_spider'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com']

    # 最適化されたPlaywright設定
    custom_settings = {
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
        },
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 10000,
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 0.5,
        'AUTOTHROTTLE_ENABLED': False,
        'ROBOTSTXT_OBEY': True,
        'USER_AGENT': 'ScrapyUI Playwright Spider 1.0',
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_load_state', 'domcontentloaded'),
                    ],
                }
            )

    def parse(self, response):
        # ページが完全に読み込まれた後の処理
        debug_print(f"Processing page: {response.url}")

        # データの抽出
        items = response.css('div.item, article, .product, .content')
        for item in items:
            scrapy_item = {}

            # タイトルの抽出（複数のセレクターを試行）
            title_selectors = ['h1::text', 'h2::text', 'h3::text', '.title::text']
            for selector in title_selectors:
                title = item.css(selector).get()
                if title:
                    scrapy_item['title'] = title.strip()
                    break

            # URLの抽出
            link = item.css('a::attr(href)').get()
            if link:
                scrapy_item['url'] = response.urljoin(link)
            else:
                scrapy_item['url'] = response.url

            # コンテンツの抽出
            content = item.css('p::text, .content::text, .description::text').getall()
            scrapy_item['content'] = ' '.join([text.strip() for text in content if text.strip()])

            # タイムスタンプを追加
            scrapy_item['scraped_at'] = datetime.now().isoformat()

            debug_print(f"Extracted item: {scrapy_item.get('title', 'No title')}")
            yield scrapy_item

        # 次のページへのリンクを探す
        next_page_selectors = [
            'a.next::attr(href)',
            'a[rel="next"]::attr(href)',
            '.pagination a:last-child::attr(href)',
            '.next-page::attr(href)'
        ]

        for selector in next_page_selectors:
            next_page = response.css(selector).get()
            if next_page:
                yield response.follow(
                    next_page,
                    meta={
                        'playwright': True,
                        'playwright_page_methods': [
                            PageMethod('wait_for_load_state', 'domcontentloaded'),
                        ],
                    },
                    callback=self.parse
                )
                break
`
  },
  {
    id: 'puppeteer-spa-scraper',
    name: 'Puppeteer SPA Scraper',
    description: 'Node.js Puppeteerを使用したSPAスクレイピング（改良版）',
    icon: <Monitor className="w-5 h-5" />,
    category: 'puppeteer',
    code: `# Puppeteer SPA Scraping Script (Improved)
# このスクリプトはNode.js統合機能を使用してSPAをスクレイピングします

import asyncio
import json
import aiohttp
import base64
from typing import Dict, Any, Optional

class NodeJSClient:
    """Node.js Puppeteerサービスクライアント"""

    def __init__(self, base_url: str = "http://localhost:3001"):
        self.base_url = base_url.rstrip('/')
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def scrape_spa(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """SPAスクレイピング"""
        url = f"{self.base_url}/api/scraping/spa"

        async with self.session.post(url, json=request_data) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Request failed: {response.status}")

async def scrape_spa():
    """
    Node.js Puppeteerサービスを使用してSPAをスクレイピング
    """
    async with NodeJSClient() as client:
        # スクレイピング設定（改良版）
        request_data = {
            "url": "https://example.com",  # ← ここを変更してください
            "waitFor": "body",  # 基本的な要素を待機
            "timeout": 45000,   # 長めのタイムアウト
            "viewport": {
                "width": 1920,
                "height": 1080
            },
            "extractData": {
                "selectors": {
                    # 複数のセレクターを試行
                    "title": "title, h1, h2",
                    "content": "p, .content, .main, article",
                    "links": "a[href]",
                    "images": "img[src]",
                    "headings": "h1, h2, h3"
                },
                "javascript": '''
                    // より堅牢なデータ抽出
                    function extractPageData() {
                        const data = {
                            pageTitle: document.title,
                            url: window.location.href,
                            loadTime: performance.now(),
                            userAgent: navigator.userAgent,

                            // テキストコンテンツを抽出
                            textContent: [],
                            linkTexts: [],
                            headingTexts: [],

                            // ページ情報
                            hasImages: false,
                            hasLinks: false,
                            elementCounts: {}
                        };

                        // 見出しテキストを抽出
                        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
                        headings.forEach(h => {
                            const text = h.textContent?.trim();
                            if (text && text.length > 0) {
                                data.headingTexts.push(text);
                            }
                        });

                        // リンクテキストを抽出
                        const links = document.querySelectorAll('a');
                        links.forEach(link => {
                            const text = link.textContent?.trim();
                            if (text && text.length > 0 && text.length < 100) {
                                data.linkTexts.push(text);
                            }
                        });

                        // 段落テキストを抽出
                        const paragraphs = document.querySelectorAll('p, .content, .main, article');
                        paragraphs.forEach(p => {
                            const text = p.textContent?.trim();
                            if (text && text.length > 10) {
                                data.textContent.push(text.substring(0, 200));
                            }
                        });

                        // 要素数をカウント
                        data.elementCounts = {
                            divs: document.querySelectorAll('div').length,
                            paragraphs: document.querySelectorAll('p').length,
                            links: document.querySelectorAll('a').length,
                            images: document.querySelectorAll('img').length,
                            headings: document.querySelectorAll('h1, h2, h3, h4, h5, h6').length
                        };

                        data.hasImages = data.elementCounts.images > 0;
                        data.hasLinks = data.elementCounts.links > 0;

                        // 重複を除去
                        data.headingTexts = [...new Set(data.headingTexts)];
                        data.linkTexts = [...new Set(data.linkTexts)];
                        data.textContent = [...new Set(data.textContent)];

                        return data;
                    }

                    // 3秒待ってからデータを抽出
                    return new Promise(resolve => {
                        setTimeout(() => {
                            resolve(extractPageData());
                        }, 3000);
                    });
                '''
            },
            "screenshot": True,
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            print(f"🚀 スクレイピング開始: {request_data['url']}")

            # SPAスクレイピング実行
            response = await client.scrape_spa(request_data)

            if response.get('success'):
                data = response.get('data', {})
                js_data = data.get('javascript', {})

                print(f"✅ スクレイピング成功: {js_data.get('url', 'N/A')}")
                print(f"📄 ページタイトル: {js_data.get('pageTitle', 'N/A')}")
                print(f"⏱️ 読み込み時間: {js_data.get('loadTime', 0):.2f}ms")

                # 抽出されたコンテンツを表示
                headings = js_data.get('headingTexts', [])
                if headings:
                    print(f"📰 見出し ({len(headings)}個):")
                    for i, heading in enumerate(headings[:5]):
                        print(f"   {i+1}. {heading}")

                links = js_data.get('linkTexts', [])
                if links:
                    print(f"🔗 リンク ({len(links)}個):")
                    for i, link in enumerate(links[:5]):
                        print(f"   {i+1}. {link}")

                content = js_data.get('textContent', [])
                if content:
                    print(f"📝 コンテンツ ({len(content)}個):")
                    for i, text in enumerate(content[:3]):
                        print(f"   {i+1}. {text[:100]}...")

                # 要素統計
                counts = js_data.get('elementCounts', {})
                print(f"📊 要素統計: {counts}")

                # スクリーンショットの保存
                if data.get('screenshot'):
                    screenshot_data = base64.b64decode(data['screenshot'])
                    filename = f"screenshot_{int(asyncio.get_event_loop().time())}.png"
                    with open(filename, 'wb') as f:
                        f.write(screenshot_data)
                    print(f"📸 スクリーンショット保存: {filename}")

                return {
                    'url': js_data.get('url'),
                    'title': js_data.get('pageTitle'),
                    'headings_count': len(headings),
                    'links_count': len(links),
                    'content_count': len(content),
                    'element_counts': counts,
                    'has_images': js_data.get('hasImages', False),
                    'has_links': js_data.get('hasLinks', False),
                    'load_time_ms': js_data.get('loadTime', 0)
                }
            else:
                print(f"❌ スクレイピング失敗: {response.get('error')}")
                return None

        except Exception as e:
            print(f"🚨 エラー: {str(e)}")
            return None

# 実行例
if __name__ == "__main__":
    print("🎯 改良版Puppeteerスクレイピングテスト")
    print("💡 ヒント: request_data['url'] を変更して様々なサイトをテストできます")

    result = asyncio.run(scrape_spa())
    if result:
        print("🎉 スクレイピング完了!")
        print(f"📋 結果サマリー: {json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        print("❌ スクレイピング失敗")
`
  },
  {
    id: 'puppeteer-pdf-generator',
    name: 'Puppeteer PDF Generator',
    description: 'WebページからPDFを生成するスクリプト',
    icon: <Monitor className="w-5 h-5" />,
    category: 'puppeteer',
    code: `# Puppeteer PDF Generation Script
# WebページやHTMLコンテンツからPDFを生成

import asyncio
import base64
from scrapy_ui.nodejs_client import get_nodejs_client

async def generate_pdf_from_url():
    """
    URLからPDFを生成
    """
    client = await get_nodejs_client()

    request_data = {
        "url": "https://example.com",
        "options": {
            "format": "A4",
            "landscape": False,
            "margin": {
                "top": "1cm",
                "right": "1cm",
                "bottom": "1cm",
                "left": "1cm"
            },
            "printBackground": True,
            "scale": 1.0,
            "displayHeaderFooter": True,
            "headerTemplate": "<div style='font-size:10px; text-align:center; width:100%;'>Generated by ScrapyUI</div>",
            "footerTemplate": "<div style='font-size:10px; text-align:center; width:100%;'>Page <span class='pageNumber'></span> of <span class='totalPages'></span></div>"
        }
    }

    try:
        response = await client.generate_pdf(request_data)

        if response.success:
            data = response.data
            print(f"✅ PDF生成成功: {data.get('source')}")
            print(f"📄 ファイルサイズ: {data.get('size', 0) / 1024:.2f} KB")

            # PDFファイルの保存
            if data.get('pdf'):
                pdf_data = base64.b64decode(data['pdf'])
                filename = f"generated_{data.get('timestamp', 'unknown').split('T')[0]}.pdf"
                with open(filename, 'wb') as f:
                    f.write(pdf_data)
                print(f"💾 PDFを保存しました: {filename}")

            return data
        else:
            print(f"❌ PDF生成失敗: {response.error}")
            return None

    except Exception as e:
        print(f"🚨 エラー: {str(e)}")
        return None

# 実行例
if __name__ == "__main__":
    result = asyncio.run(generate_pdf_from_url())
    if result:
        print("🎉 PDF生成完了!")
`
  },
  {
    id: 'scrapy-puppeteer-spider',
    name: 'Scrapy + Puppeteer Spider',
    description: 'ScrapyスパイダーでPuppeteerを使用（HTTP API経由）',
    icon: <Monitor className="w-5 h-5" />,
    category: 'puppeteer',
    code: `import scrapy
import json
import aiohttp
import asyncio
import base64

class PuppeteerSpider(scrapy.Spider):
    name = 'puppeteer_spider'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nodejs_url = "http://localhost:3001"

    def start_requests(self):
        """開始リクエスト"""
        urls = [
            'https://example.com',
        ]

        for url in urls:
            # 通常のScrapyリクエストとして開始
            yield scrapy.Request(
                url=url,
                callback=self.parse_with_puppeteer,
                meta={'use_puppeteer': True}
            )

    def parse_with_puppeteer(self, response):
        """Puppeteerを使用してページを解析"""
        if response.meta.get('use_puppeteer'):
            # 非同期でPuppeteerを呼び出し
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(
                    self.scrape_with_puppeteer(response.url)
                )

                if result:
                    yield result

                    # 抽出されたリンクをたどる
                    links = result.get('links', [])
                    for link in links[:3]:  # 最初の3つのリンクのみ
                        if link.startswith('http'):
                            yield scrapy.Request(
                                url=link,
                                callback=self.parse_regular
                            )

            except Exception as e:
                self.logger.error(f"Puppeteer scraping failed: {e}")
                # フォールバック: 通常のスクレイピング
                yield from self.parse_regular(response)
            finally:
                loop.close()
        else:
            yield from self.parse_regular(response)

    async def scrape_with_puppeteer(self, url):
        """Puppeteerサービスを使用してスクレイピング"""
        request_data = {
            "url": url,
            "waitFor": "body",
            "timeout": 30000,
            "extractData": {
                "selectors": {
                    "title": "h1",
                    "content": "p",
                    "links": "a[href]"
                }
            },
            "screenshot": True
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.nodejs_url}/api/scraping/spa",
                    json=request_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get('success'):
                            extracted = data.get('data', {}).get('data', {})

                            # スクリーンショットを保存
                            screenshot_file = None
                            if data.get('data', {}).get('screenshot'):
                                screenshot_file = self.save_screenshot(
                                    data['data']['screenshot'],
                                    url
                                )

                            return {
                                'url': url,
                                'title': extracted.get('title'),
                                'content': extracted.get('content'),
                                'links': extracted.get('links', []),
                                'links_count': len(extracted.get('links', [])),
                                'screenshot_file': screenshot_file,
                                'scraping_method': 'puppeteer'
                            }
                        else:
                            self.logger.error(f"Puppeteer API error: {data.get('error')}")
                            return None
                    else:
                        self.logger.error(f"HTTP error: {response.status}")
                        return None

            except Exception as e:
                self.logger.error(f"Request error: {e}")
                return None

    def parse_regular(self, response):
        """通常のページ解析"""
        yield {
            'url': response.url,
            'title': response.css('title::text').get(),
            'h1': response.css('h1::text').get(),
            'content': ' '.join(response.css('p::text').getall()[:3]),
            'links': response.css('a::attr(href)').getall()[:5],
            'scraping_method': 'regular'
        }

    def save_screenshot(self, screenshot_base64, url):
        """スクリーンショットを保存"""
        try:
            screenshot_data = base64.b64decode(screenshot_base64)
            # URLから安全なファイル名を生成
            safe_name = url.replace('https://', '').replace('http://', '')
            safe_name = safe_name.replace('/', '_').replace(':', '_')
            filename = f"screenshot_{safe_name}.png"

            with open(filename, 'wb') as f:
                f.write(screenshot_data)

            self.logger.info(f"Screenshot saved: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Failed to save screenshot: {e}")
            return None
`
  },
  {
    id: 'puppeteer-ecommerce-spider',
    name: 'E-commerce Puppeteer Spider',
    description: 'ECサイト用のPuppeteerスパイダー',
    icon: <Monitor className="w-5 h-5" />,
    category: 'puppeteer',
    code: `import scrapy
import json
import base64
from scrapy_ui.middlewares.puppeteer_middleware import PuppeteerRequestHelper

class EcommercePuppeteerSpider(scrapy.Spider):
    name = 'ecommerce_puppeteer'

    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_ui.middlewares.puppeteer_middleware.PuppeteerMiddleware': 585,
        },
        'PUPPETEER_ENABLED': True,
        'CONCURRENT_REQUESTS': 1,  # Puppeteerは重いので同時実行数を制限
        'DOWNLOAD_DELAY': 2,
    }

    def start_requests(self):
        """商品ページのスクレイピング開始"""
        product_urls = [
            'https://example-shop.com/product/1',
            'https://example-shop.com/product/2',
        ]

        for url in product_urls:
            yield PuppeteerRequestHelper.spa_request(
                url=url,
                selectors={
                    'name': 'h1.product-title',
                    'price': '.price',
                    'description': '.product-description',
                    'images': 'img.product-image',
                    'availability': '.availability',
                    'reviews': '.review-item',
                    'rating': '.rating-score'
                },
                wait_for='.product-title',
                screenshot=True,
                timeout=30000,
                callback=self.parse_product
            )

    def parse_product(self, response):
        """商品ページの解析"""
        puppeteer_data = response.meta.get('puppeteer_data', {})
        product_data = puppeteer_data.get('data', {})

        # 商品情報を抽出
        product = {
            'url': response.url,
            'name': product_data.get('name'),
            'price': self.clean_price(product_data.get('price')),
            'description': product_data.get('description'),
            'availability': product_data.get('availability'),
            'rating': product_data.get('rating'),
            'review_count': len(product_data.get('reviews', [])),
            'image_count': len(product_data.get('images', [])),
            'scraped_with': 'puppeteer'
        }

        # スクリーンショットを保存
        if 'screenshot' in puppeteer_data:
            screenshot_file = self.save_screenshot(
                puppeteer_data['screenshot'],
                f"product_{product['name']}"
            )
            product['screenshot_file'] = screenshot_file

        yield product

        # 関連商品のリンクを探す
        related_links = product_data.get('related_products', [])
        for link in related_links[:3]:  # 最大3つの関連商品
            if link.startswith('http'):
                yield PuppeteerRequestHelper.spa_request(
                    url=link,
                    selectors={
                        'name': 'h1.product-title',
                        'price': '.price'
                    },
                    wait_for='.product-title',
                    callback=self.parse_related_product
                )

    def parse_related_product(self, response):
        """関連商品の簡易解析"""
        puppeteer_data = response.meta.get('puppeteer_data', {})
        product_data = puppeteer_data.get('data', {})

        yield {
            'url': response.url,
            'name': product_data.get('name'),
            'price': self.clean_price(product_data.get('price')),
            'type': 'related_product'
        }

    def clean_price(self, price_text):
        """価格テキストのクリーニング"""
        if not price_text:
            return None

        import re
        # 数字と小数点のみを抽出
        price_match = re.search(r'[\\d,]+(?:\\.\\d+)?', str(price_text))
        if price_match:
            return float(price_match.group().replace(',', ''))
        return None

    def save_screenshot(self, screenshot_base64, filename_prefix):
        """スクリーンショットを保存"""
        try:
            screenshot_data = base64.b64decode(screenshot_base64)
            filename = f"{filename_prefix}_{self.name}.png"

            with open(filename, 'wb') as f:
                f.write(screenshot_data)

            return filename
        except Exception as e:
            self.logger.error(f"Failed to save screenshot: {e}")
            return None
`
  },
  {
    id: 'yahoo-japan-scraper',
    name: 'Yahoo Japan Scraper',
    description: 'Yahoo.co.jp専用スクレイピングテンプレート',
    icon: <Monitor className="w-5 h-5" />,
    category: 'puppeteer',
    code: `import scrapy
import json
import aiohttp
import asyncio
import base64
import time

class YahooJapanSpider(scrapy.Spider):
    name = 'yahoo_japan_spider'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nodejs_url = "http://localhost:3001"

    def start_requests(self):
        """Yahoo Japan関連のURL"""
        urls = [
            'https://www.yahoo.co.jp/',
            'https://news.yahoo.co.jp/',
            'https://shopping.yahoo.co.jp/',
        ]

        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_yahoo_page,
                meta={'use_puppeteer': True}
            )

    def parse_yahoo_page(self, response):
        """Yahoo.co.jpページの解析"""
        if response.meta.get('use_puppeteer'):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(
                    self.scrape_yahoo_with_puppeteer(response.url)
                )

                if result:
                    yield result

                    # ニュースリンクをたどる
                    news_links = result.get('news_links', [])
                    for link in news_links[:5]:
                        if link and 'news.yahoo.co.jp' in link:
                            yield scrapy.Request(
                                url=link,
                                callback=self.parse_news_article
                            )

            except Exception as e:
                self.logger.error(f"Yahoo Puppeteer scraping failed: {e}")
                yield from self.parse_fallback(response)
            finally:
                loop.close()
        else:
            yield from self.parse_fallback(response)

    async def scrape_yahoo_with_puppeteer(self, url):
        """Yahoo.co.jp専用Puppeteerスクレイピング"""
        # Yahoo.co.jp用の特別な設定
        request_data = {
            "url": url,
            "waitFor": "body",  # 基本的な要素の読み込み待機
            "timeout": 45000,   # 長めのタイムアウト
            "viewport": {
                "width": 1920,
                "height": 1080
            },
            "extractData": {
                "selectors": {
                    # Yahoo.co.jp用のセレクター
                    "title": "title, h1, .topicsListItem_title, .newsFeed_item_title",
                    "news_headlines": ".topicsListItem_title, .newsFeed_item_title, .sc-gJWqzi",
                    "news_links": ".topicsListItem_link, .newsFeed_item_link, a[href*='news.yahoo.co.jp']",
                    "main_content": ".contents, .main, #main, .topicsIndex",
                    "navigation": ".gnav, .header, nav",
                    "search_box": "#srchtxt, .searchbox, input[type='search']",
                    "categories": ".category, .gnav_list, .sc-bwzfXH",
                    "trending": ".ranking, .trend, .popular"
                },
                "javascript": '''
                    // Yahoo.co.jp用のカスタムJavaScript
                    function extractYahooData() {
                        const data = {
                            pageTitle: document.title,
                            url: window.location.href,
                            loadTime: performance.now(),

                            // ニュース見出しを抽出
                            newsHeadlines: [],
                            newsLinks: [],

                            // カテゴリ情報
                            categories: [],

                            // 検索関連
                            hasSearchBox: false,

                            // ページタイプ判定
                            pageType: 'unknown'
                        };

                        // ページタイプを判定
                        if (window.location.href.includes('news.yahoo.co.jp')) {
                            data.pageType = 'news';
                        } else if (window.location.href.includes('shopping.yahoo.co.jp')) {
                            data.pageType = 'shopping';
                        } else if (window.location.href === 'https://www.yahoo.co.jp/') {
                            data.pageType = 'top';
                        }

                        // ニュース見出しを抽出（複数のセレクターを試行）
                        const headlineSelectors = [
                            '.topicsListItem_title',
                            '.newsFeed_item_title',
                            '.sc-gJWqzi',
                            'h3 a',
                            '.ttl a',
                            '[data-cl-params*="headline"]'
                        ];

                        headlineSelectors.forEach(selector => {
                            const elements = document.querySelectorAll(selector);
                            elements.forEach(el => {
                                const text = el.textContent?.trim();
                                const href = el.href || el.closest('a')?.href;

                                if (text && text.length > 5) {
                                    data.newsHeadlines.push(text);
                                    if (href) {
                                        data.newsLinks.push(href);
                                    }
                                }
                            });
                        });

                        // カテゴリ情報を抽出
                        const categorySelectors = [
                            '.gnav_list a',
                            '.category a',
                            'nav a',
                            '.sc-bwzfXH a'
                        ];

                        categorySelectors.forEach(selector => {
                            const elements = document.querySelectorAll(selector);
                            elements.forEach(el => {
                                const text = el.textContent?.trim();
                                if (text && text.length > 0 && text.length < 20) {
                                    data.categories.push(text);
                                }
                            });
                        });

                        // 検索ボックスの存在確認
                        const searchSelectors = ['#srchtxt', '.searchbox', 'input[type="search"]'];
                        data.hasSearchBox = searchSelectors.some(sel =>
                            document.querySelector(sel) !== null
                        );

                        // 重複を除去
                        data.newsHeadlines = [...new Set(data.newsHeadlines)];
                        data.newsLinks = [...new Set(data.newsLinks)];
                        data.categories = [...new Set(data.categories)];

                        return data;
                    }

                    // 少し待ってからデータを抽出
                    return new Promise(resolve => {
                        setTimeout(() => {
                            resolve(extractYahooData());
                        }, 2000);  // 2秒待機
                    });
                '''
            },
            "screenshot": True,
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.nodejs_url}/api/scraping/spa",
                    json=request_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get('success'):
                            extracted = data.get('data', {}).get('data', {})
                            js_data = data.get('data', {}).get('javascript', {})

                            # スクリーンショットを保存
                            screenshot_file = None
                            if data.get('data', {}).get('screenshot'):
                                screenshot_file = self.save_screenshot(
                                    data['data']['screenshot'],
                                    url
                                )

                            return {
                                'url': url,
                                'page_type': js_data.get('pageType', 'unknown'),
                                'title': js_data.get('pageTitle') or extracted.get('title'),
                                'news_headlines': js_data.get('newsHeadlines', []),
                                'news_links': js_data.get('newsLinks', []),
                                'categories': js_data.get('categories', []),
                                'has_search_box': js_data.get('hasSearchBox', False),
                                'load_time_ms': js_data.get('loadTime', 0),
                                'headlines_count': len(js_data.get('newsHeadlines', [])),
                                'links_count': len(js_data.get('newsLinks', [])),
                                'screenshot_file': screenshot_file,
                                'scraping_method': 'puppeteer_yahoo_optimized'
                            }
                        else:
                            self.logger.error(f"Yahoo Puppeteer API error: {data.get('error')}")
                            return None
                    else:
                        self.logger.error(f"HTTP error: {response.status}")
                        return None

            except Exception as e:
                self.logger.error(f"Yahoo request error: {e}")
                return None

    def parse_news_article(self, response):
        """ニュース記事の解析"""
        yield {
            'url': response.url,
            'title': response.css('h1::text, .articleHeader_title::text').get(),
            'content': ' '.join(response.css('.articleBody p::text, .article_body p::text').getall()[:3]),
            'date': response.css('.date, .articleHeader_date::text, time::text').get(),
            'category': response.css('.category, .breadcrumb a::text').get(),
            'scraping_method': 'regular_news'
        }

    def parse_fallback(self, response):
        """フォールバック解析"""
        yield {
            'url': response.url,
            'title': response.css('title::text').get(),
            'content': ' '.join(response.css('h1::text, h2::text, h3::text').getall()[:5]),
            'links': response.css('a::attr(href)').getall()[:10],
            'scraping_method': 'fallback'
        }

    def save_screenshot(self, screenshot_base64, url):
        """スクリーンショットを保存"""
        try:
            screenshot_data = base64.b64decode(screenshot_base64)
            safe_name = url.replace('https://', '').replace('http://', '')
            safe_name = safe_name.replace('/', '_').replace(':', '_').replace('.', '_')
            filename = f"yahoo_{safe_name}_{int(time.time())}.png"

            with open(filename, 'wb') as f:
                f.write(screenshot_data)

            self.logger.info(f"Yahoo screenshot saved: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Failed to save Yahoo screenshot: {e}")
            return None
`
  },
  {
    id: 'rate-limit-safe-puppeteer',
    name: 'Rate Limit Safe Puppeteer',
    description: 'レート制限回避機能付きPuppeteerスクレイパー',
    icon: <Monitor className="w-5 h-5" />,
    category: 'puppeteer',
    code: `import scrapy
import json
import aiohttp
import asyncio
import base64
import time
import random

class RateLimitSafePuppeteerSpider(scrapy.Spider):
    name = 'rate_limit_safe_puppeteer'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nodejs_url = "http://localhost:3001"
        self.request_count = 0
        self.last_request_time = 0
        self.min_delay = 5  # 最小5秒間隔
        self.max_delay = 15  # 最大15秒間隔

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,           # 同時リクエスト数を1に制限
        'DOWNLOAD_DELAY': 10,               # 10秒間隔
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,    # ランダム遅延
        'AUTOTHROTTLE_ENABLED': True,       # 自動スロットリング
        'AUTOTHROTTLE_START_DELAY': 5,      # 開始遅延
        'AUTOTHROTTLE_MAX_DELAY': 30,       # 最大遅延
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.5,  # 目標同時実行数
        'AUTOTHROTTLE_DEBUG': True,         # デバッグ情報表示
        'RETRY_TIMES': 3,                   # リトライ回数
        'RETRY_HTTP_CODES': [429, 500, 502, 503, 504],  # リトライ対象ステータス
    }

    def start_requests(self):
        """レート制限を考慮した開始リクエスト"""
        # テスト用のURL（レート制限が緩いサイト）
        test_urls = [
            'https://httpbin.org/html',      # HTTPテストサイト
            'https://httpbin.org/json',      # JSONテストサイト
        ]

        for i, url in enumerate(test_urls):
            # 各リクエスト間に遅延を追加
            delay = i * self.min_delay

            yield scrapy.Request(
                url=url,
                callback=self.parse_with_safe_puppeteer,
                meta={
                    'use_puppeteer': True,
                    'delay': delay,
                    'retry_count': 0
                },
                dont_filter=True
            )

    def parse_with_safe_puppeteer(self, response):
        """レート制限を考慮したPuppeteer解析"""
        # 遅延実行
        delay = response.meta.get('delay', 0)
        if delay > 0:
            self.logger.info(f"⏳ {delay}秒待機中...")
            time.sleep(delay)

        # リクエスト間隔を確保
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_delay:
            wait_time = self.min_delay - time_since_last
            self.logger.info(f"⏱️ レート制限回避のため{wait_time:.1f}秒待機...")
            time.sleep(wait_time)

        self.last_request_time = time.time()
        self.request_count += 1

        if response.meta.get('use_puppeteer'):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(
                    self.safe_puppeteer_scrape(response.url, response.meta.get('retry_count', 0))
                )

                if result:
                    yield result
                else:
                    # フォールバック: 通常のスクレイピング
                    yield from self.parse_fallback(response)

            except Exception as e:
                self.logger.error(f"Puppeteer scraping failed: {e}")
                yield from self.parse_fallback(response)
            finally:
                loop.close()
        else:
            yield from self.parse_fallback(response)

    async def safe_puppeteer_scrape(self, url, retry_count=0):
        """レート制限対応のPuppeteerスクレイピング"""
        # ランダム遅延を追加
        random_delay = random.uniform(2, 5)
        await asyncio.sleep(random_delay)

        request_data = {
            "url": url,
            "waitFor": "body",
            "timeout": 30000,  # 30秒タイムアウト
            "viewport": {
                "width": 1920,
                "height": 1080
            },
            "extractData": {
                "selectors": {
                    "title": "title, h1",
                    "content": "p, pre, div",
                    "links": "a[href]",
                    "json_data": "pre"  # JSON表示用
                },
                "javascript": '''
                    function extractSafeData() {
                        const data = {
                            pageTitle: document.title,
                            url: window.location.href,
                            loadTime: performance.now(),
                            timestamp: new Date().toISOString(),

                            // 基本コンテンツ
                            headings: [],
                            paragraphs: [],
                            links: [],

                            // JSON データ（httpbin.org/json用）
                            jsonContent: null,

                            // ページ情報
                            elementCounts: {},
                            hasContent: false
                        };

                        try {
                            // 見出しを抽出
                            document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(h => {
                                const text = h.textContent?.trim();
                                if (text) {
                                    data.headings.push(text);
                                }
                            });

                            // 段落を抽出
                            document.querySelectorAll('p').forEach(p => {
                                const text = p.textContent?.trim();
                                if (text && text.length > 10) {
                                    data.paragraphs.push(text.substring(0, 200));
                                }
                            });

                            // リンクを抽出
                            document.querySelectorAll('a[href]').forEach(a => {
                                const href = a.href;
                                const text = a.textContent?.trim();
                                if (href && text) {
                                    data.links.push({
                                        url: href,
                                        text: text
                                    });
                                }
                            });

                            // JSON コンテンツを抽出（httpbin.org/json用）
                            const preElement = document.querySelector('pre');
                            if (preElement) {
                                try {
                                    const jsonText = preElement.textContent?.trim();
                                    if (jsonText && jsonText.startsWith('{')) {
                                        data.jsonContent = JSON.parse(jsonText);
                                    }
                                } catch (e) {
                                    data.jsonParseError = e.message;
                                }
                            }

                            // 要素数をカウント
                            data.elementCounts = {
                                divs: document.querySelectorAll('div').length,
                                paragraphs: document.querySelectorAll('p').length,
                                links: document.querySelectorAll('a').length,
                                headings: document.querySelectorAll('h1, h2, h3, h4, h5, h6').length
                            };

                            data.hasContent = document.body.textContent.length > 100;

                        } catch (error) {
                            data.extractionError = error.message;
                        }

                        return data;
                    }

                    // 2秒待ってからデータを抽出
                    return new Promise(resolve => {
                        setTimeout(() => {
                            resolve(extractSafeData());
                        }, 2000);
                    });
                '''
            },
            "screenshot": True,
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        async with aiohttp.ClientSession() as session:
            try:
                self.logger.info(f"🚀 安全なPuppeteerリクエスト送信: {url}")

                async with session.post(
                    f"{self.nodejs_url}/api/scraping/spa",
                    json=request_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get('success'):
                            extracted = data.get('data', {}).get('javascript', {})

                            # スクリーンショットを保存
                            screenshot_file = None
                            if data.get('data', {}).get('screenshot'):
                                screenshot_file = self.save_screenshot(
                                    data['data']['screenshot'],
                                    url
                                )

                            result = {
                                'url': url,
                                'request_number': self.request_count,
                                'timestamp': extracted.get('timestamp'),
                                'title': extracted.get('pageTitle'),
                                'headings': extracted.get('headings', []),
                                'paragraphs': extracted.get('paragraphs', []),
                                'links': extracted.get('links', []),
                                'json_content': extracted.get('jsonContent'),
                                'element_counts': extracted.get('elementCounts', {}),
                                'has_content': extracted.get('hasContent', False),
                                'load_time_ms': extracted.get('loadTime', 0),
                                'screenshot_file': screenshot_file,
                                'scraping_method': 'safe_puppeteer',
                                'retry_count': retry_count
                            }

                            self.logger.info(f"✅ 安全なPuppeteerスクレイピング成功: {url}")
                            return result
                        else:
                            self.logger.error(f"Puppeteer API error: {data.get('error')}")
                            return None

                    elif response.status == 429:
                        # レート制限の場合
                        self.logger.warning(f"⚠️ レート制限検出 (429): {url}")

                        if retry_count < 3:
                            # 指数バックオフで再試行
                            wait_time = (2 ** retry_count) * 10  # 10, 20, 40秒
                            self.logger.info(f"🔄 {wait_time}秒後に再試行...")
                            await asyncio.sleep(wait_time)

                            return await self.safe_puppeteer_scrape(url, retry_count + 1)
                        else:
                            self.logger.error(f"❌ 最大リトライ回数に達しました: {url}")
                            return None
                    else:
                        self.logger.error(f"HTTP error: {response.status}")
                        return None

            except Exception as e:
                self.logger.error(f"Request error: {e}")
                return None

    def parse_fallback(self, response):
        """フォールバック解析"""
        yield {
            'url': response.url,
            'title': response.css('title::text').get(),
            'content': ' '.join(response.css('p::text, pre::text').getall()[:3]),
            'links': response.css('a::attr(href)').getall()[:5],
            'scraping_method': 'fallback',
            'request_number': self.request_count
        }

    def save_screenshot(self, screenshot_base64, url):
        """スクリーンショットを保存"""
        try:
            screenshot_data = base64.b64decode(screenshot_base64)
            safe_name = url.replace('https://', '').replace('http://', '')
            safe_name = safe_name.replace('/', '_').replace(':', '_').replace('.', '_')
            filename = f"safe_puppeteer_{safe_name}_{int(time.time())}.png"

            with open(filename, 'wb') as f:
                f.write(screenshot_data)

            self.logger.info(f"📸 スクリーンショット保存: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Failed to save screenshot: {e}")
            return None
`
  },
  {
    id: 'optimized-puppeteer-scraper',
    name: 'Optimized Puppeteer Scraper',
    description: 'Yahoo.co.jp成功要因を反映した最適化Puppeteerスクレイパー',
    icon: <Monitor className="w-5 h-5" />,
    category: 'puppeteer',
    code: `import scrapy
import json
import asyncio
import sys
import os

# ScrapyUIのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapy_ui.nodejs_client import NodeJSClient

class OptimizedPuppeteerSpider(scrapy.Spider):
    name = 'optimized_puppeteer_spider'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.success_count = 0
        self.total_count = 0

    def start_requests(self):
        """最適化されたスクレイピング開始"""
        # テスト用URL（成功実績のあるサイト）
        urls = [
            'https://www.yahoo.co.jp/',      # 成功実績あり
            'https://httpbin.org/html',      # テスト用
            'https://httpbin.org/json',      # JSON用
        ]

        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_with_optimized_puppeteer,
                meta={'use_optimized_puppeteer': True},
                dont_filter=True
            )

    def parse_with_optimized_puppeteer(self, response):
        """最適化されたPuppeteerでページを解析"""
        if response.meta.get('use_optimized_puppeteer'):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(
                    self.scrape_with_optimized_client(response.url)
                )

                self.total_count += 1

                if result:
                    self.success_count += 1
                    yield result
                else:
                    # フォールバック: 通常のスクレイピング
                    yield from self.parse_fallback(response)

            except Exception as e:
                self.logger.error(f"Optimized Puppeteer scraping failed: {e}")
                yield from self.parse_fallback(response)
            finally:
                loop.close()
        else:
            yield from self.parse_fallback(response)

    async def scrape_with_optimized_client(self, url):
        """最適化されたクライアントでスクレイピング"""
        async with NodeJSClient() as client:
            try:
                self.logger.info(f"🚀 最適化Puppeteerスクレイピング開始: {url}")

                # Yahoo.co.jp成功要因を反映した最適化スクレイピング
                if 'yahoo.co.jp' in url:
                    # 日本語サイト専用最適化
                    response = await client.scrape_japanese_site(url)
                else:
                    # 一般的な最適化スクレイピング
                    response = await client.scrape_optimized(url)

                if response.success:
                    data = response.data

                    # データ構造の修正: Node.jsサービスは直接セレクター結果を返す
                    if isinstance(data, dict) and 'data' in data:
                        # 新しい構造: {"success": true, "data": {"h1": [...], "title": "..."}}
                        selector_data = data['data']
                    else:
                        # 直接構造: {"h1": [...], "title": "..."}
                        selector_data = data if isinstance(data, dict) else {}

                    # h1要素の詳細解析
                    h1_elements = selector_data.get('h1', [])
                    all_headings = selector_data.get('all_headings', [])

                    result = {
                        'url': url,
                        'scraping_method': 'optimized_puppeteer',
                        'success': True,

                        # 見出し情報（修正版）
                        'h1_count': len(h1_elements) if isinstance(h1_elements, list) else 1 if h1_elements else 0,
                        'h1_elements': h1_elements,
                        'total_headings': len(all_headings) if isinstance(all_headings, list) else 1 if all_headings else 0,

                        # コンテンツ情報
                        'title': selector_data.get('title'),
                        'links_count': len(selector_data.get('links', [])),
                        'images_count': len(selector_data.get('images', [])),

                        # 日本語サイト特有の情報
                        'news_headlines_count': len(selector_data.get('news_headlines', [])),
                        'navigation_count': len(selector_data.get('navigation', [])),

                        # 技術情報
                        'has_screenshot': 'screenshot' in data,
                        'response_keys': list(data.keys()),
                        'optimization_applied': 'japanese_site' if 'yahoo.co.jp' in url else 'general'
                    }

                    # h1要素の詳細ログ（修正版）
                    if h1_elements:
                        # h1_elementsがリストか単一要素かを判定
                        if isinstance(h1_elements, list):
                            h1_count = len(h1_elements)
                            self.logger.info(f"✅ h1要素発見: {h1_count}個")
                            for i, h1 in enumerate(h1_elements[:5]):  # 最初の5個のみログ
                                h1_safe = str(h1).replace('"', "'")
                                self.logger.info(f"   {i+1}. {h1_safe}")
                        else:
                            # 単一要素の場合
                            self.logger.info(f"✅ h1要素発見: 1個")
                            h1_safe = str(h1_elements).replace('"', "'")
                            self.logger.info(f"   1. {h1_safe}")
                    else:
                        self.logger.warning(f"⚠️ h1要素が見つかりませんでした: {url}")

                    # 日本語サイト特有の情報ログ
                    if 'yahoo.co.jp' in url:
                        news_count = len(selector_data.get('news_headlines', []))
                        self.logger.info(f"📰 ニュース見出し: {news_count}個")

                    self.logger.info(f"✅ 最適化Puppeteerスクレイピング成功: {url}")
                    return result
                else:
                    self.logger.error(f"Optimized Puppeteer API error: {response.error}")
                    return None

            except Exception as e:
                self.logger.error(f"Optimized scraping error: {e}")
                return None

    def parse_fallback(self, response):
        """フォールバック解析"""
        self.total_count += 1

        yield {
            'url': response.url,
            'scraping_method': 'fallback',
            'success': True,
            'title': response.css('title::text').get(),
            'h1_count': len(response.css('h1').getall()),
            'h1_elements': response.css('h1::text').getall(),
            'links_count': len(response.css('a::attr(href)').getall()),
            'optimization_applied': 'none'
        }

    def closed(self, reason):
        """スパイダー終了時の統計表示"""
        success_rate = (self.success_count / self.total_count * 100) if self.total_count > 0 else 0

        self.logger.info(f"📊 最適化Puppeteerスクレイピング統計:")
        self.logger.info(f"   成功率: {self.success_count}/{self.total_count} ({success_rate:.1f}%)")
        self.logger.info(f"   適用された最適化: Yahoo.co.jp成功要因反映")
        self.logger.info(f"   終了理由: {reason}")

# テスト実行用のスクリプト
if __name__ == "__main__":
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    print("🚀 最適化Puppeteerスクレイパーのテスト開始")
    print("🎯 Yahoo.co.jp成功要因を反映した機能をテスト")

    # 設定を取得
    settings = get_project_settings()
    settings.set('USER_AGENT', 'ScrapyUI-Optimized-Puppeteer (+http://www.yourdomain.com)')
    settings.set('ROBOTSTXT_OBEY', False)
    settings.set('CONCURRENT_REQUESTS', 1)
    settings.set('DOWNLOAD_DELAY', 3)
    settings.set('LOG_LEVEL', 'INFO')

    # クローラープロセスを作成して実行
    process = CrawlerProcess(settings)
    process.crawl(OptimizedPuppeteerSpider)
    process.start()
`
  }
]
