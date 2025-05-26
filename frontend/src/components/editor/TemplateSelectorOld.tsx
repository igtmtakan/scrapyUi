'use client'

import React, { useState, useEffect } from 'react'
import {
  FileText, Code, Globe, ShoppingCart, Database, Zap, Search, Rss, Image, Table, Link, BookOpen,
  TrendingUp, MessageSquare, Shield, Clock, Download, Upload, Settings, Users, Mail, Phone,
  MapPin, Calendar, Star, Heart, Eye, Lock, Key, Wifi, Server, Cloud, Smartphone, Monitor,
  Camera, Video, Music, Archive, Folder, Tag, Filter, RefreshCw, Target, Flag, Bookmark,
  Hash, AtSign, DollarSign, AlertTriangle, Info, MessageCircle, Send, Share, Copy, Edit,
  ExternalLink, Home, Building, Store, Factory, Truck, Car, Plane, Ship, Train, Bus, Bike,
  Map, Navigation, Compass, Route, Grid, Layout, Trophy, Award, Medal, Gamepad2, Radio, Tv,
  Coffee, Pizza, Gift, Cake, Apple, Banana, Grape, Cherry, Carrot, Corn, Tomato, Pepper,
  Mushroom, Broccoli, Fish, Chicken, Beef, Egg, Milk, Cheese, Bread, Rice, Pasta, Wine,
  Beer, Cocktail, Cookie, Candy, Umbrella, Briefcase, Backpack, Handbag, Watch, Ring,
  Shirt, Pants, Shoe, Hat, Glasses, Sunglasses, Crown, Gem, Palette, Brush, Scissors,
  Ruler, Compass as CompassIcon, Layers, Maximize, Minimize, ZoomIn, ZoomOut, RotateCcw,
  RotateCw, FlipHorizontal, FlipVertical, Crop, PenTool, Pipette, Square, Circle, Triangle,
  Hexagon, Diamond, Pentagon, Smile, Frown, Meh, Angry, Surprised, Confused, Mask,
  Headphones, Mic, Speaker, Volume2, Play, Pause, Stop, SkipForward, SkipBack, Radio as RadioIcon,
  Tv as TvIcon, Gamepad2 as GamepadIcon, Joystick, Trophy as TrophyIcon, Award as AwardIcon,
  Medal as MedalIcon, Target as TargetIcon, Flag as FlagIcon, Bookmark as BookmarkIcon,
  Hash as HashIcon, AtSign as AtSignIcon, DollarSign as DollarSignIcon, Percent, Plus, Minus,
  X, Check, AlertTriangle as AlertTriangleIcon, Info as InfoIcon, HelpCircle, MessageCircle as MessageCircleIcon,
  Send as SendIcon, Share as ShareIcon, Copy as CopyIcon, Edit as EditIcon, Trash, Save, Print
} from 'lucide-react'

interface Template {
  id: string
  name: string
  description: string
  icon: React.ReactNode
  code: string
  category: 'basic' | 'ecommerce' | 'news' | 'api' | 'advanced' | 'social' | 'data' | 'monitoring' | 'security' | 'performance' | 'testing' | 'automation' | 'integration' | 'mobile' | 'media' | 'finance' | 'travel' | 'food' | 'real-estate' | 'job' | 'education' | 'health' | 'sports' | 'gaming' | 'weather' | 'government' | 'legal' | 'nonprofit' | 'playwright'
}

interface TemplateSelectorProps {
  onSelectTemplate: (template: Template) => void
  onClose: () => void
}

const templates: Template[] = [
  {
    id: 'basic-spider',
    name: 'Basic Spider',
    description: 'シンプルなWebスクレイピングスパイダー',
    icon: <FileText className="w-5 h-5" />,
    category: 'basic',
    code: `import scrapy
from scrapy_playwright.page import PageMethod

class BasicSpider(scrapy.Spider):
    name = 'basic_spider'
    start_urls = ['https://example.com']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
        },
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "body"),
                    ],
                }
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]

        # ページタイトルを取得
        title = await page.title()

        # データを抽出
        yield {
            'url': response.url,
            'title': title,
            'content': response.css('body::text').get()
        }

        await page.close()
`
  },
  {
    id: 'basic-http-spider',
    name: 'Basic HTTP Spider',
    description: '基本的なHTTPリクエストを使ったシンプルなスクレイピング',
    icon: <Code className="w-5 h-5" />,
    category: 'basic',
    code: `import scrapy

class BasicSpider(scrapy.Spider):
    name = 'basic_spider'
    start_urls = ['https://httpbin.org/json']

    def parse(self, response):
        debug_print(f"Parsing response from {response.url}")

        # レスポンスの基本情報を取得
        debug_print(f"Status code: {response.status}")
        debug_print(f"Content type: {response.headers.get('content-type', b'').decode()}")

        # JSONレスポンスの場合
        if 'json' in response.headers.get('content-type', b'').decode().lower():
            try:
                json_data = response.json()
                debug_print("JSON data received:")
                debug_pprint(json_data)

                yield {
                    'url': response.url,
                    'status': response.status,
                    'content_type': response.headers.get('content-type', b'').decode(),
                    'data': json_data
                }
            except Exception as e:
                debug_print(f"Error parsing JSON: {e}")
                yield {
                    'url': response.url,
                    'status': response.status,
                    'error': str(e)
                }
        else:
            # HTMLレスポンスの場合
            title = response.css('title::text').get()
            debug_print(f"Extracted title: {title}")

            # 基本的なデータを抽出
            data = {
                'url': response.url,
                'status': response.status,
                'title': title,
                'content_length': len(response.text)
            }

            debug_print("Yielding extracted data:")
            debug_pprint(data)

            yield data
`
  },
  {
    id: 'html-spider',
    name: 'HTML Parser Spider',
    description: 'Scrapyの標準セレクターを使ったHTMLパース',
    icon: <Code className="w-5 h-5" />,
    category: 'basic',
    code: `import scrapy

class HtmlSpider(scrapy.Spider):
    name = 'html_spider'
    start_urls = ['https://quotes.toscrape.com/']

    def parse(self, response):
        debug_print(f"Parsing response from {response.url}")

        # ページタイトルを取得
        title = response.css('title::text').get()
        debug_print(f"Page title: {title}")

        # 引用文を抽出
        quotes = []
        for quote in response.css('div.quote'):
            text = quote.css('span.text::text').get()
            author = quote.css('small.author::text').get()
            tags = quote.css('div.tags a.tag::text').getall()

            quote_data = {
                'text': text,
                'author': author,
                'tags': tags
            }
            quotes.append(quote_data)
            debug_print(f"Extracted quote by {author}")

        # メタ情報を取得
        meta_description = response.css('meta[name="description"]::attr(content)').get()

        # リンクを取得
        links = []
        for link in response.css('a'):
            href = link.css('::attr(href)').get()
            text = link.css('::text').get()
            if href and text:
                links.append({
                    'href': href,
                    'text': text.strip()
                })

        data = {
            'url': response.url,
            'title': title,
            'meta_description': meta_description,
            'quotes': quotes,
            'links': links[:10],  # 最初の10個のリンクのみ
            'quote_count': len(quotes)
        }

        debug_print("Yielding extracted data:")
        debug_pprint(data)
        yield data

        # 次のページへのリンクを探す
        next_page = response.css('li.next a::attr(href)').get()
        if next_page:
            debug_print(f"Following next page: {next_page}")
            yield response.follow(next_page, self.parse)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "body"),
                    ],
                }
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]

        # ページのHTMLを取得
        html_content = await page.content()

        # BeautifulSoupでHTMLをパース
        soup = BeautifulSoup(html_content, 'html.parser')

        # タイトルを取得
        title = soup.title.string if soup.title else ''

        # メタ情報を取得
        meta_description = ''
        meta_keywords = ''
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            meta_description = meta_desc.get('content', '')

        meta_key = soup.find('meta', attrs={'name': 'keywords'})
        if meta_key:
            meta_keywords = meta_key.get('content', '')

        # 見出しを取得
        headings = []
        for tag in soup.find_all(re.compile(r'^h[1-6]$')):
            headings.append({
                'level': tag.name,
                'text': tag.get_text(strip=True),
                'id': tag.get('id', ''),
                'class': ' '.join(tag.get('class', []))
            })

        # リンクを取得
        links = []
        for link in soup.find_all('a', href=True):
            links.append({
                'text': link.get_text(strip=True),
                'href': link['href'],
                'title': link.get('title', ''),
                'target': link.get('target', '')
            })

        # 画像を取得
        images = []
        for img in soup.find_all('img', src=True):
            images.append({
                'src': img['src'],
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'width': img.get('width', ''),
                'height': img.get('height', '')
            })

        # テーブルデータを取得
        tables = []
        for table in soup.find_all('table'):
            table_data = {
                'headers': [],
                'rows': []
            }

            # ヘッダーを取得
            header_row = table.find('tr')
            if header_row:
                headers = header_row.find_all(['th', 'td'])
                table_data['headers'] = [h.get_text(strip=True) for h in headers]

            # データ行を取得
            rows = table.find_all('tr')[1:]  # ヘッダー行をスキップ
            for row in rows:
                cells = row.find_all(['td', 'th'])
                table_data['rows'].append([cell.get_text(strip=True) for cell in cells])

            tables.append(table_data)

        # フォームを取得
        forms = []
        for form in soup.find_all('form'):
            form_data = {
                'action': form.get('action', ''),
                'method': form.get('method', 'get'),
                'inputs': []
            }

            for input_tag in form.find_all('input'):
                form_data['inputs'].append({
                    'type': input_tag.get('type', 'text'),
                    'name': input_tag.get('name', ''),
                    'value': input_tag.get('value', ''),
                    'placeholder': input_tag.get('placeholder', '')
                })

            forms.append(form_data)

        # テキストコンテンツを取得（スクリプトとスタイルを除外）
        for script in soup(["script", "style"]):
            script.decompose()

        text_content = soup.get_text()
        # 複数の空白を単一のスペースに変換
        clean_text = re.sub(r'\\s+', ' ', text_content).strip()

        yield {
            'url': response.url,
            'title': title,
            'meta_description': meta_description,
            'meta_keywords': meta_keywords,
            'headings': headings,
            'links': links,
            'images': images,
            'tables': tables,
            'forms': forms,
            'text_content': clean_text[:1000],  # 最初の1000文字
            'word_count': len(clean_text.split()),
            'link_count': len(links),
            'image_count': len(images)
        }

        await page.close()
`
  },
  {
    id: 'pyquery-advanced-spider',
    name: 'PyQuery Advanced Spider',
    description: 'PyQueryを使った高度なHTMLパースとデータ抽出',
    icon: <Database className="w-5 h-5" />,
    category: 'advanced',
    code: `import scrapy
from scrapy_playwright.page import PageMethod
from pyquery import PyQuery as pq

class PyQueryAdvancedSpider(scrapy.Spider):
    name = 'pyquery_advanced_spider'
    start_urls = ['https://example.com']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
        },
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "body"),
                    ],
                }
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]

        # ページのHTMLを取得
        html_content = await page.content()

        # PyQueryでHTMLをパース
        doc = pq(html_content)

        # jQueryライクな記法でデータを抽出
        title = doc('title').text()

        # 見出しを取得
        headings = []
        for i in range(1, 7):
            doc(f'h{i}').each(lambda idx, elem: headings.append({
                'level': f'h{i}',
                'text': pq(elem).text(),
                'id': pq(elem).attr('id') or '',
                'class': pq(elem).attr('class') or ''
            }))

        # リンクを取得
        links = []
        doc('a[href]').each(lambda idx, elem: links.append({
            'text': pq(elem).text(),
            'href': pq(elem).attr('href'),
            'title': pq(elem).attr('title') or ''
        }))

        # 画像を取得
        images = []
        doc('img[src]').each(lambda idx, elem: images.append({
            'src': pq(elem).attr('src'),
            'alt': pq(elem).attr('alt') or '',
            'title': pq(elem).attr('title') or ''
        }))

        # CSSセレクターを使った高度な抽出
        articles = []
        doc('article, .article, .post').each(lambda idx, elem: articles.append({
            'title': pq(elem).find('h1, h2, h3, .title').text(),
            'content': pq(elem).find('.content, .body, p').text()[:200],
            'author': pq(elem).find('.author, .by').text(),
            'date': pq(elem).find('.date, .published, time').text()
        }))

        yield {
            'url': response.url,
            'title': title,
            'headings': headings,
            'links': links,
            'images': images,
            'articles': articles,
            'meta_description': doc('meta[name="description"]').attr('content') or '',
            'meta_keywords': doc('meta[name="keywords"]').attr('content') or '',
            'social_links': [
                pq(elem).attr('href') for elem in
                doc('a[href*="facebook"], a[href*="twitter"], a[href*="instagram"], a[href*="linkedin"]')
            ]
        }

        await page.close()
`
  },
  {
    id: 'ecommerce-spider',
    name: 'E-commerce Spider (bs4)',
    description: 'BeautifulSoup4を使ったECサイト商品情報スクレイピング',
    icon: <ShoppingCart className="w-5 h-5" />,
    category: 'ecommerce',
    code: `import scrapy
from scrapy_playwright.page import PageMethod
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

class EcommerceSpider(scrapy.Spider):
    name = 'ecommerce_spider'
    start_urls = ['https://example-shop.com/products']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
        },
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", ".product-list, .products, .items"),
                        PageMethod("wait_for_load_state", "networkidle"),
                    ],
                }
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]

        # ページのHTMLを取得
        html_content = await page.content()
        soup = BeautifulSoup(html_content, 'html.parser')

        # 商品リンクを取得（複数のセレクターパターンに対応）
        product_selectors = [
            '.product-item a', '.product a', '.item a',
            'a[href*="/product/"]', 'a[href*="/item/"]',
            '.product-card a', '.product-tile a'
        ]

        product_links = []
        for selector in product_selectors:
            # CSSセレクターをBeautifulSoupで使用
            if '.' in selector or '#' in selector:
                # 簡単なクラス/IDセレクター
                class_name = selector.replace('.', '').replace(' a', '')
                links = soup.find_all('a', class_=re.compile(class_name))
                product_links.extend(links)
            elif '[href*=' in selector:
                # href属性を含むリンク
                href_pattern = selector.split('"')[1]
                links = soup.find_all('a', href=re.compile(href_pattern))
                product_links.extend(links)

        # 重複を除去
        unique_links = list(set([link.get('href') for link in product_links if link.get('href')]))

        for href in unique_links[:20]:  # 最初の20商品に制限
            absolute_url = urljoin(response.url, href)
            yield response.follow(
                absolute_url,
                callback=self.parse_product,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                }
            )

        # 次のページへのリンクを探す
        next_page_selectors = [
            '.pagination .next', '.pager .next',
            'a[rel="next"]', '.next-page', '.load-more'
        ]

        for selector in next_page_selectors:
            next_link = soup.select_one(selector)
            if next_link and next_link.get('href'):
                next_url = urljoin(response.url, next_link['href'])
                yield response.follow(next_url, callback=self.parse)
                break

        await page.close()

    async def parse_product(self, response):
        page = response.meta["playwright_page"]

        # ページのHTMLを取得
        html_content = await page.content()
        soup = BeautifulSoup(html_content, 'html.parser')

        # 商品名を取得（複数のパターンに対応）
        name_selectors = [
            'h1', '.product-name', '.product-title',
            '.item-name', '.title', '[data-testid="product-name"]'
        ]
        name = self.extract_text_by_selectors(soup, name_selectors)

        # 価格を取得
        price_selectors = [
            '.price', '.product-price', '.cost', '.amount',
            '[data-testid="price"]', '.price-current', '.sale-price'
        ]
        price = self.extract_text_by_selectors(soup, price_selectors)

        # 元の価格（割引前）を取得
        original_price_selectors = [
            '.original-price', '.was-price', '.list-price',
            '.price-original', '.regular-price'
        ]
        original_price = self.extract_text_by_selectors(soup, original_price_selectors)

        # 商品説明を取得
        description_selectors = [
            '.description', '.product-description', '.product-details',
            '.item-description', '.summary', '.overview'
        ]
        description = self.extract_text_by_selectors(soup, description_selectors)

        # 画像URLを取得
        image_selectors = [
            '.product-image img', '.item-image img', '.main-image img',
            '.product-photo img', '[data-testid="product-image"] img'
        ]
        image_url = self.extract_image_by_selectors(soup, image_selectors, response.url)

        # 在庫状況を取得
        stock_selectors = [
            '.stock', '.availability', '.in-stock', '.out-of-stock',
            '[data-testid="stock"]', '.inventory'
        ]
        stock_status = self.extract_text_by_selectors(soup, stock_selectors)

        # レビュー評価を取得
        rating_selectors = [
            '.rating', '.stars', '.review-score', '.product-rating'
        ]
        rating = self.extract_text_by_selectors(soup, rating_selectors)

        # ブランド情報を取得
        brand_selectors = [
            '.brand', '.manufacturer', '.vendor', '.product-brand'
        ]
        brand = self.extract_text_by_selectors(soup, brand_selectors)

        # SKU/商品コードを取得
        sku_selectors = [
            '.sku', '.product-code', '.item-code', '[data-sku]'
        ]
        sku = self.extract_text_by_selectors(soup, sku_selectors)

        yield {
            'name': name,
            'price': price,
            'original_price': original_price,
            'description': description[:500] if description else '',  # 500文字に制限
            'image_url': image_url,
            'stock_status': stock_status,
            'rating': rating,
            'brand': brand,
            'sku': sku,
            'url': response.url,
            'domain': response.url.split('/')[2] if '/' in response.url else ''
        }

        await page.close()

    def extract_text_by_selectors(self, soup, selectors):
        """複数のセレクターを試してテキストを抽出"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text:
                    return text
        return ''

    def extract_image_by_selectors(self, soup, selectors, base_url):
        """複数のセレクターを試して画像URLを抽出"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                src = element.get('src') or element.get('data-src')
                if src:
                    return urljoin(base_url, src)
        return ''
`
  },
  {
    id: 'quotes-spider',
    name: 'Quotes Spider',
    description: '名言サイトから名言を収集するスパイダー（教育用）',
    icon: <BookOpen className="w-5 h-5" />,
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

class QuotesSpider(scrapy.Spider):
    name = 'quotes_spider'
    allowed_domains = ['quotes.toscrape.com']
    start_urls = [
        'https://quotes.toscrape.com/',
        'https://quotes.toscrape.com/page/2/'
    ]

    # 軽量で安全な設定
    custom_settings = {
        'DOWNLOAD_HANDLERS': {},  # Playwrightハンドラーを無効化
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'ScrapyUI Educational Bot 1.0'
    }

    def parse(self, response):
        debug_print(f"Parsing response from {response.url}")
        debug_print(f"Status code: {response.status}")

        # 名言を抽出
        quotes = response.css('div.quote')
        debug_print(f"Found {len(quotes)} quotes on this page")

        for quote in quotes:
            text = quote.css('span.text::text').get()
            author = quote.css('small.author::text').get()
            tags = quote.css('div.tags a.tag::text').getall()

            data = {
                'url': response.url,
                'text': text,
                'author': author,
                'tags': tags,
                'page_title': response.css('title::text').get()
            }

            debug_print(f"Extracted quote by {author}")
            debug_pprint(data)

            yield data

        # 次のページへのリンクを取得
        next_page = response.css('li.next a::attr(href)').get()
        if next_page:
            debug_print(f"Following next page: {next_page}")
            yield response.follow(next_page, self.parse)
`
  },
  {
    id: 'news-spider',
    name: 'News Spider (bs4)',
    description: 'BeautifulSoup4を使ったニュースサイトの記事スクレイピング',
    icon: <Globe className="w-5 h-5" />,
    category: 'news',
    code: `import scrapy
from scrapy_playwright.page import PageMethod
from bs4 import BeautifulSoup
from datetime import datetime
import re
from urllib.parse import urljoin

class NewsSpider(scrapy.Spider):
    name = 'news_spider'
    start_urls = ['https://example-news.com']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
        },
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", ".article-list, .news-list, .posts"),
                    ],
                }
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]

        # ページのHTMLを取得
        html_content = await page.content()
        soup = BeautifulSoup(html_content, 'html.parser')

        # 記事リンクを取得（複数のパターンに対応）
        article_selectors = [
            '.article-item a', '.news-item a', '.post a',
            'article a', '.entry a', '.story a',
            'a[href*="/article/"]', 'a[href*="/news/"]', 'a[href*="/post/"]'
        ]

        article_links = []
        for selector in article_selectors:
            if '[href*=' in selector:
                # href属性を含むリンク
                href_pattern = selector.split('"')[1]
                links = soup.find_all('a', href=re.compile(href_pattern))
                article_links.extend(links)
            else:
                # CSSセレクターをBeautifulSoupで使用
                links = soup.select(selector)
                article_links.extend(links)

        # 重複を除去
        unique_links = list(set([link.get('href') for link in article_links if link.get('href')]))

        for href in unique_links[:15]:  # 最初の15記事に制限
            absolute_url = urljoin(response.url, href)
            yield response.follow(
                absolute_url,
                callback=self.parse_article,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                }
            )

        # 次のページへのリンクを探す
        next_page_selectors = [
            '.pagination .next', '.pager .next',
            'a[rel="next"]', '.next-page', '.load-more'
        ]

        for selector in next_page_selectors:
            next_link = soup.select_one(selector)
            if next_link and next_link.get('href'):
                next_url = urljoin(response.url, next_link['href'])
                yield response.follow(next_url, callback=self.parse)
                break

        await page.close()

    async def parse_article(self, response):
        page = response.meta["playwright_page"]

        # ページのHTMLを取得
        html_content = await page.content()
        soup = BeautifulSoup(html_content, 'html.parser')

        # タイトルを取得
        title_selectors = [
            'h1', '.article-title', '.post-title', '.entry-title',
            '.news-title', '.headline', '[data-testid="headline"]'
        ]
        title = self.extract_text_by_selectors(soup, title_selectors)

        # 著者を取得
        author_selectors = [
            '.author', '.byline', '.writer', '.journalist',
            '.post-author', '.article-author', '[rel="author"]'
        ]
        author = self.extract_text_by_selectors(soup, author_selectors)

        # 日付を取得
        date_selectors = [
            '.date', '.published', '.post-date', '.article-date',
            'time', '.timestamp', '[datetime]'
        ]
        date = self.extract_text_by_selectors(soup, date_selectors)

        # 記事本文を取得
        content_selectors = [
            '.article-content', '.post-content', '.entry-content',
            '.news-content', '.story-body', '.article-body'
        ]
        content = self.extract_text_by_selectors(soup, content_selectors)

        # 要約/リードを取得
        summary_selectors = [
            '.summary', '.excerpt', '.lead', '.intro',
            '.article-summary', '.post-excerpt'
        ]
        summary = self.extract_text_by_selectors(soup, summary_selectors)

        # カテゴリを取得
        category_selectors = [
            '.category', '.section', '.topic', '.genre',
            '.article-category', '.post-category'
        ]
        category = self.extract_text_by_selectors(soup, category_selectors)

        # タグを取得
        tags = []
        tag_selectors = [
            '.tags .tag', '.keywords .keyword', '.labels .label',
            '.article-tags a', '.post-tags a'
        ]

        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            for tag_element in tag_elements:
                tag_text = tag_element.get_text(strip=True)
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)

        # 画像を取得
        image_selectors = [
            '.article-image img', '.post-image img', '.featured-image img',
            '.hero-image img', '.main-image img'
        ]
        image_url = self.extract_image_by_selectors(soup, image_selectors, response.url)

        # ソーシャルシェア数を取得（もしあれば）
        social_shares = {}
        share_selectors = {
            'facebook': ['.fb-share', '.facebook-share', '[data-social="facebook"]'],
            'twitter': ['.twitter-share', '[data-social="twitter"]'],
            'linkedin': ['.linkedin-share', '[data-social="linkedin"]']
        }

        for platform, selectors in share_selectors.items():
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    share_count = re.search(r'\\d+', element.get_text())
                    if share_count:
                        social_shares[platform] = int(share_count.group())
                    break

        yield {
            'title': title,
            'author': author,
            'date': date,
            'category': category,
            'summary': summary[:300] if summary else '',  # 300文字に制限
            'content': content[:2000] if content else '',  # 2000文字に制限
            'tags': tags,
            'image_url': image_url,
            'social_shares': social_shares,
            'url': response.url,
            'domain': response.url.split('/')[2] if '/' in response.url else '',
            'scraped_at': datetime.now().isoformat(),
            'word_count': len(content.split()) if content else 0
        }

        await page.close()

    def extract_text_by_selectors(self, soup, selectors):
        """複数のセレクターを試してテキストを抽出"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text:
                    return text
        return ''

    def extract_image_by_selectors(self, soup, selectors, base_url):
        """複数のセレクターを試して画像URLを抽出"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                src = element.get('src') or element.get('data-src')
                if src:
                    return urljoin(base_url, src)
        return ''
`
  },
  {
    id: 'api-spider',
    name: 'API Spider',
    description: 'API経由でのデータ取得',
    icon: <Database className="w-5 h-5" />,
    category: 'api',
    code: `import scrapy
import json

class ApiSpider(scrapy.Spider):
    name = 'api_spider'
    start_urls = ['https://api.example.com/data']

    def start_requests(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; ScrapyBot)',
            'Accept': 'application/json',
            'Authorization': 'Bearer YOUR_API_TOKEN'  # 必要に応じて設定
        }

        for url in self.start_urls:
            yield scrapy.Request(
                url,
                headers=headers,
                callback=self.parse_api
            )

    def parse_api(self, response):
        try:
            data = json.loads(response.text)

            # APIレスポンスからデータを抽出
            if 'results' in data:
                for item in data['results']:
                    yield {
                        'id': item.get('id'),
                        'name': item.get('name'),
                        'description': item.get('description'),
                        'created_at': item.get('created_at'),
                        'source': 'api'
                    }

            # ページネーション処理
            if 'next' in data and data['next']:
                yield scrapy.Request(
                    data['next'],
                    callback=self.parse_api,
                    headers=response.request.headers
                )

        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse JSON from {response.url}")
`
  },
  {
    id: 'advanced-spider',
    name: 'Advanced Spider',
    description: 'ログイン機能付き高度なスパイダー',
    icon: <Zap className="w-5 h-5" />,
    category: 'advanced',
    code: `import scrapy
from scrapy_playwright.page import PageMethod

class AdvancedSpider(scrapy.Spider):
    name = 'advanced_spider'
    start_urls = ['https://example.com/login']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
        },
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.login,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "#login-form"),
                    ],
                }
            )

    async def login(self, response):
        page = response.meta["playwright_page"]

        # ログインフォームに入力
        await page.fill('#username', 'your_username')
        await page.fill('#password', 'your_password')

        # ログインボタンをクリック
        await page.click('#login-button')

        # ページ遷移を待機
        await page.wait_for_url('**/dashboard')

        # ダッシュボードページをスクレイピング
        yield scrapy.Request(
            page.url,
            callback=self.parse_dashboard,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page": page,  # ページオブジェクトを引き継ぎ
            }
        )

    async def parse_dashboard(self, response):
        page = response.meta["playwright_page"]

        # ダッシュボードからデータを抽出
        user_info = await page.text_content('.user-info')
        notifications = await page.query_selector_all('.notification')

        notification_data = []
        for notification in notifications:
            text = await notification.text_content()
            notification_data.append(text.strip())

        yield {
            'user_info': user_info,
            'notifications': notification_data,
            'url': response.url
        }

        # 他のページへのリンクを辿る
        links = await page.query_selector_all('a[href*="/data/"]')
        for link in links:
            href = await link.get_attribute('href')
            if href:
                yield response.follow(
                    href,
                    callback=self.parse_data,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                    }
                )

        await page.close()

    async def parse_data(self, response):
        page = response.meta["playwright_page"]

        # データページから情報を抽出
        title = await page.text_content('h1')
        content = await page.text_content('.content')

        yield {
            'title': title,
            'content': content,
            'url': response.url
        }

        await page.close()
`
  },
  {
    id: 'json-api-spider',
    name: 'JSON API Spider',
    description: 'REST APIからJSONデータを取得するスパイダー',
    icon: <Database className="w-5 h-5" />,
    category: 'api',
    code: `import scrapy
import json
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class ApiSpider(scrapy.Spider):
    name = 'api_spider'
    allowed_domains = ['httpbin.org', 'jsonplaceholder.typicode.com']
    start_urls = [
        'https://httpbin.org/json',
        'https://jsonplaceholder.typicode.com/posts/1',
        'https://jsonplaceholder.typicode.com/users/1'
    ]

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},  # 通常のHTTPリクエストを使用
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 2,
        'USER_AGENT': 'ScrapyUI API Bot 1.0',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
    }

    def parse(self, response):
        debug_print(f"Parsing API response from {response.url}")
        debug_print(f"Status code: {response.status}")
        debug_print(f"Content type: {response.headers.get('content-type', b'').decode()}")

        try:
            # JSONレスポンスをパース
            data = json.loads(response.text)
            debug_print("Successfully parsed JSON data")
            debug_pprint(data)

            # データの種類に応じて処理
            if 'slideshow' in data:
                # httpbin.org/json のレスポンス
                yield {
                    'source': 'httpbin',
                    'url': response.url,
                    'slideshow_title': data['slideshow']['title'],
                    'slideshow_author': data['slideshow']['author'],
                    'slides_count': len(data['slideshow']['slides']),
                    'raw_data': data
                }
            elif 'title' in data and 'body' in data:
                # JSONPlaceholder posts のレスポンス
                yield {
                    'source': 'jsonplaceholder_post',
                    'url': response.url,
                    'post_id': data.get('id'),
                    'user_id': data.get('userId'),
                    'title': data.get('title'),
                    'body': data.get('body'),
                    'body_length': len(data.get('body', '')),
                    'raw_data': data
                }
            elif 'name' in data and 'email' in data:
                # JSONPlaceholder users のレスポンス
                yield {
                    'source': 'jsonplaceholder_user',
                    'url': response.url,
                    'user_id': data.get('id'),
                    'name': data.get('name'),
                    'username': data.get('username'),
                    'email': data.get('email'),
                    'phone': data.get('phone'),
                    'website': data.get('website'),
                    'company': data.get('company', {}).get('name'),
                    'address': f"{data.get('address', {}).get('city')}, {data.get('address', {}).get('zipcode')}",
                    'raw_data': data
                }
            else:
                # その他のJSONデータ
                yield {
                    'source': 'unknown',
                    'url': response.url,
                    'data_keys': list(data.keys()) if isinstance(data, dict) else [],
                    'raw_data': data
                }

        except json.JSONDecodeError as e:
            debug_print(f"Failed to parse JSON: {e}")
            yield {
                'source': 'error',
                'url': response.url,
                'error': str(e),
                'raw_text': response.text[:500]  # 最初の500文字
            }
`
  },
  {
    id: 'table-spider',
    name: 'Table Scraper',
    description: 'HTMLテーブルからデータを抽出するスパイダー',
    icon: <Table className="w-5 h-5" />,
    category: 'data',
    code: `import scrapy
import pandas as pd
from io import StringIO
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class TableSpider(scrapy.Spider):
    name = 'table_spider'
    allowed_domains = ['example.com']
    start_urls = [
        'https://en.wikipedia.org/wiki/List_of_countries_by_population',
        'https://www.w3schools.com/html/html_tables.asp'
    ]

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'ScrapyUI Table Scraper 1.0'
    }

    def parse(self, response):
        debug_print(f"Parsing tables from {response.url}")
        debug_print(f"Status code: {response.status}")

        # すべてのテーブルを取得
        tables = response.css('table')
        debug_print(f"Found {len(tables)} tables on this page")

        for i, table in enumerate(tables):
            debug_print(f"Processing table {i+1}")

            # テーブルのヘッダーを取得
            headers = []
            header_rows = table.css('thead tr, tr:first-child')
            if header_rows:
                headers = header_rows[0].css('th::text, td::text').getall()
                headers = [h.strip() for h in headers if h.strip()]

            debug_print(f"Table headers: {headers}")

            # テーブルの行を取得
            rows = []
            data_rows = table.css('tbody tr, tr')[1:] if headers else table.css('tbody tr, tr')

            for row in data_rows[:10]:  # 最初の10行のみ処理
                cells = row.css('td::text, th::text').getall()
                cells = [cell.strip() for cell in cells if cell.strip()]
                if cells:
                    rows.append(cells)

            debug_print(f"Extracted {len(rows)} data rows")

            # テーブルデータを構造化
            table_data = {
                'url': response.url,
                'table_index': i + 1,
                'headers': headers,
                'row_count': len(rows),
                'column_count': len(headers) if headers else (len(rows[0]) if rows else 0),
                'sample_rows': rows[:5],  # 最初の5行をサンプルとして保存
            }

            # ヘッダーがある場合は辞書形式でも保存
            if headers and rows:
                structured_rows = []
                for row in rows[:5]:  # 最初の5行のみ
                    if len(row) >= len(headers):
                        row_dict = {}
                        for j, header in enumerate(headers):
                            if j < len(row):
                                row_dict[header] = row[j]
                        structured_rows.append(row_dict)
                table_data['structured_data'] = structured_rows

            debug_print(f"Table {i+1} data:")
            debug_pprint(table_data)

            yield table_data

        # ページ内のリンクをフォロー（同じドメインのみ）
        links = response.css('a[href]::attr(href)').getall()
        for link in links[:3]:  # 最初の3つのリンクのみ
            if link.startswith('/') or response.urljoin(link).startswith(response.url):
                debug_print(f"Following link: {link}")
                yield response.follow(link, self.parse)
`
  },
  {
    id: 'link-spider',
    name: 'Link Crawler',
    description: 'ウェブサイトのリンク構造を分析するスパイダー',
    icon: <Link className="w-5 h-5" />,
    category: 'monitoring',
    code: `import scrapy
from urllib.parse import urljoin, urlparse
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class LinkSpider(scrapy.Spider):
    name = 'link_spider'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': 2,  # 最大2階層まで
        'USER_AGENT': 'ScrapyUI Link Crawler 1.0'
    }

    def parse(self, response):
        debug_print(f"Analyzing links on {response.url}")
        debug_print(f"Status code: {response.status}")

        # ページの基本情報
        page_info = {
            'url': response.url,
            'title': response.css('title::text').get(),
            'status_code': response.status,
            'content_length': len(response.text),
            'depth': response.meta.get('depth', 0)
        }

        # すべてのリンクを取得
        links = response.css('a[href]')
        internal_links = []
        external_links = []
        broken_links = []

        for link in links:
            href = link.css('::attr(href)').get()
            text = link.css('::text').get() or ''
            text = text.strip()

            if href:
                absolute_url = urljoin(response.url, href)
                parsed_url = urlparse(absolute_url)

                link_data = {
                    'href': href,
                    'absolute_url': absolute_url,
                    'text': text,
                    'title': link.css('::attr(title)').get() or ''
                }

                # 内部リンクか外部リンクかを判定
                if parsed_url.netloc == urlparse(response.url).netloc:
                    internal_links.append(link_data)
                else:
                    external_links.append(link_data)

        # 画像リンクも取得
        images = []
        for img in response.css('img[src]'):
            src = img.css('::attr(src)').get()
            alt = img.css('::attr(alt)').get() or ''
            if src:
                images.append({
                    'src': urljoin(response.url, src),
                    'alt': alt,
                    'title': img.css('::attr(title)').get() or ''
                })

        # メタ情報を取得
        meta_info = {
            'description': response.css('meta[name="description"]::attr(content)').get() or '',
            'keywords': response.css('meta[name="keywords"]::attr(content)').get() or '',
            'robots': response.css('meta[name="robots"]::attr(content)').get() or '',
            'canonical': response.css('link[rel="canonical"]::attr(href)').get() or ''
        }

        page_analysis = {
            **page_info,
            'internal_links_count': len(internal_links),
            'external_links_count': len(external_links),
            'images_count': len(images),
            'internal_links': internal_links[:10],  # 最初の10個のみ
            'external_links': external_links[:10],  # 最初の10個のみ
            'images': images[:5],  # 最初の5個のみ
            'meta_info': meta_info,
            'headings': {
                'h1': response.css('h1::text').getall(),
                'h2': response.css('h2::text').getall()[:5],  # 最初の5個のみ
                'h3': response.css('h3::text').getall()[:5]   # 最初の5個のみ
            }
        }

        debug_print(f"Page analysis for {response.url}:")
        debug_pprint(page_analysis)

        yield page_analysis

        # 内部リンクをフォロー（深度制限内で）
        current_depth = response.meta.get('depth', 0)
        if current_depth < 2:  # 最大2階層まで
            for link in internal_links[:5]:  # 最初の5つのリンクのみフォロー
                debug_print(f"Following internal link: {link['absolute_url']}")
                yield response.follow(link['absolute_url'], self.parse)
`
  },
  {
    id: 'form-spider',
    name: 'Form Analyzer',
    description: 'ウェブフォームの構造を分析するスパイダー',
    icon: <Search className="w-5 h-5" />,
    category: 'monitoring',
    code: `import scrapy
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class FormSpider(scrapy.Spider):
    name = 'form_spider'
    allowed_domains = ['example.com']
    start_urls = [
        'https://httpbin.org/forms/post',
        'https://www.w3schools.com/html/html_forms.asp'
    ]

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'ScrapyUI Form Analyzer 1.0'
    }

    def parse(self, response):
        debug_print(f"Analyzing forms on {response.url}")
        debug_print(f"Status code: {response.status}")

        # すべてのフォームを取得
        forms = response.css('form')
        debug_print(f"Found {len(forms)} forms on this page")

        for i, form in enumerate(forms):
            debug_print(f"Analyzing form {i+1}")

            # フォームの基本属性
            form_data = {
                'url': response.url,
                'form_index': i + 1,
                'action': form.css('::attr(action)').get() or '',
                'method': form.css('::attr(method)').get() or 'GET',
                'enctype': form.css('::attr(enctype)').get() or '',
                'name': form.css('::attr(name)').get() or '',
                'id': form.css('::attr(id)').get() or '',
                'class': form.css('::attr(class)').get() or ''
            }

            # フォーム内の入力フィールドを分析
            inputs = []
            for input_elem in form.css('input'):
                input_data = {
                    'type': input_elem.css('::attr(type)').get() or 'text',
                    'name': input_elem.css('::attr(name)').get() or '',
                    'id': input_elem.css('::attr(id)').get() or '',
                    'placeholder': input_elem.css('::attr(placeholder)').get() or '',
                    'value': input_elem.css('::attr(value)').get() or '',
                    'required': input_elem.css('::attr(required)').get() is not None,
                    'disabled': input_elem.css('::attr(disabled)').get() is not None
                }
                inputs.append(input_data)

            # セレクトボックスを分析
            selects = []
            for select_elem in form.css('select'):
                options = []
                for option in select_elem.css('option'):
                    options.append({
                        'value': option.css('::attr(value)').get() or '',
                        'text': option.css('::text').get() or '',
                        'selected': option.css('::attr(selected)').get() is not None
                    })

                select_data = {
                    'name': select_elem.css('::attr(name)').get() or '',
                    'id': select_elem.css('::attr(id)').get() or '',
                    'multiple': select_elem.css('::attr(multiple)').get() is not None,
                    'required': select_elem.css('::attr(required)').get() is not None,
                    'options': options
                }
                selects.append(select_data)

            # テキストエリアを分析
            textareas = []
            for textarea in form.css('textarea'):
                textarea_data = {
                    'name': textarea.css('::attr(name)').get() or '',
                    'id': textarea.css('::attr(id)').get() or '',
                    'placeholder': textarea.css('::attr(placeholder)').get() or '',
                    'rows': textarea.css('::attr(rows)').get() or '',
                    'cols': textarea.css('::attr(cols)').get() or '',
                    'required': textarea.css('::attr(required)').get() is not None,
                    'text': textarea.css('::text').get() or ''
                }
                textareas.append(textarea_data)

            # ボタンを分析
            buttons = []
            for button in form.css('button, input[type="submit"], input[type="button"], input[type="reset"]'):
                button_data = {
                    'type': button.css('::attr(type)').get() or 'button',
                    'name': button.css('::attr(name)').get() or '',
                    'value': button.css('::attr(value)').get() or '',
                    'text': button.css('::text').get() or ''
                }
                buttons.append(button_data)

            # フォームデータを統合
            form_analysis = {
                **form_data,
                'inputs_count': len(inputs),
                'selects_count': len(selects),
                'textareas_count': len(textareas),
                'buttons_count': len(buttons),
                'inputs': inputs,
                'selects': selects,
                'textareas': textareas,
                'buttons': buttons,
                'has_file_upload': any(inp['type'] == 'file' for inp in inputs),
                'has_required_fields': any(inp['required'] for inp in inputs) or any(sel['required'] for sel in selects) or any(ta['required'] for ta in textareas)
            }

            debug_print(f"Form {i+1} analysis:")
            debug_pprint(form_analysis)

            yield form_analysis
`
  },
  {
    id: 'crawl-spider',
    name: 'CrawlSpider with Rules',
    description: 'Rule(LinkExtractor)を使った自動リンクフォロー型スパイダー',
    icon: <TrendingUp className="w-5 h-5" />,
    category: 'advanced',
    code: `import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class CrawlSpiderWithRules(CrawlSpider):
    name = 'crawl_spider'
    allowed_domains = ['quotes.toscrape.com']
    start_urls = ['https://quotes.toscrape.com/']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},  # 通常のHTTPリクエストを使用
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': 3,  # 最大3階層まで
        'USER_AGENT': 'ScrapyUI CrawlSpider 1.0',
        'CLOSESPIDER_PAGECOUNT': 20,  # 最大20ページまで
    }

    # ルール定義：どのリンクをフォローするかを指定
    rules = (
        # ページネーションリンクをフォロー（次のページ）
        Rule(
            LinkExtractor(
                restrict_css='li.next a',  # 「次へ」ボタンのみ
                attrs=['href']
            ),
            callback='parse_quotes',
            follow=True,
            cb_kwargs={'page_type': 'pagination'}
        ),

        # 著者ページへのリンクをフォロー
        Rule(
            LinkExtractor(
                restrict_css='small.author a',  # 著者名のリンク
                attrs=['href']
            ),
            callback='parse_author',
            follow=False,  # 著者ページからはさらにフォローしない
            cb_kwargs={'page_type': 'author'}
        ),

        # タグページへのリンクをフォロー
        Rule(
            LinkExtractor(
                restrict_css='div.tags a.tag',  # タグのリンク
                attrs=['href']
            ),
            callback='parse_tag',
            follow=True,  # タグページからもフォロー
            cb_kwargs={'page_type': 'tag'}
        ),
    )

    def parse_start_url(self, response):
        """開始URLの処理"""
        debug_print(f"Processing start URL: {response.url}")
        return self.parse_quotes(response, page_type='start')

    def parse_quotes(self, response, page_type='unknown'):
        """名言ページの解析"""
        debug_print(f"Parsing quotes page: {response.url} (type: {page_type})")
        debug_print(f"Status code: {response.status}")

        # ページ情報
        page_info = {
            'url': response.url,
            'page_type': page_type,
            'title': response.css('title::text').get(),
            'depth': response.meta.get('depth', 0)
        }

        # 名言を抽出
        quotes = response.css('div.quote')
        debug_print(f"Found {len(quotes)} quotes on this page")

        for quote in quotes:
            text = quote.css('span.text::text').get()
            author = quote.css('small.author::text').get()
            tags = quote.css('div.tags a.tag::text').getall()
            author_url = quote.css('small.author a::attr(href)').get()

            quote_data = {
                **page_info,
                'item_type': 'quote',
                'text': text,
                'author': author,
                'author_url': response.urljoin(author_url) if author_url else None,
                'tags': tags,
                'tags_count': len(tags)
            }

            debug_print(f"Extracted quote by {author}")
            debug_pprint(quote_data)

            yield quote_data

        # ページ統計情報も出力
        page_stats = {
            **page_info,
            'item_type': 'page_stats',
            'quotes_count': len(quotes),
            'unique_authors': len(set(q.css('small.author::text').get() for q in quotes)),
            'total_tags': sum(len(q.css('div.tags a.tag::text').getall()) for q in quotes)
        }

        debug_print(f"Page statistics:")
        debug_pprint(page_stats)

        yield page_stats

    def parse_author(self, response, page_type='author'):
        """著者ページの解析"""
        debug_print(f"Parsing author page: {response.url}")
        debug_print(f"Status code: {response.status}")

        # 著者情報を抽出
        author_name = response.css('h3.author-title::text').get()
        birth_date = response.css('span.author-born-date::text').get()
        birth_location = response.css('span.author-born-location::text').get()
        description = response.css('div.author-description::text').get()

        author_data = {
            'url': response.url,
            'page_type': page_type,
            'item_type': 'author',
            'name': author_name,
            'birth_date': birth_date,
            'birth_location': birth_location,
            'description': description.strip() if description else None,
            'depth': response.meta.get('depth', 0)
        }

        debug_print(f"Extracted author: {author_name}")
        debug_pprint(author_data)

        yield author_data

    def parse_tag(self, response, page_type='tag'):
        """タグページの解析"""
        debug_print(f"Parsing tag page: {response.url}")
        debug_print(f"Status code: {response.status}")

        # タグ情報を抽出
        tag_name = response.url.split('/')[-2] if response.url.endswith('/') else response.url.split('/')[-1]

        # このタグの名言を取得
        quotes = response.css('div.quote')
        authors_with_tag = [q.css('small.author::text').get() for q in quotes]

        tag_data = {
            'url': response.url,
            'page_type': page_type,
            'item_type': 'tag',
            'tag_name': tag_name,
            'quotes_count': len(quotes),
            'authors_with_tag': list(set(authors_with_tag)),
            'authors_count': len(set(authors_with_tag)),
            'depth': response.meta.get('depth', 0)
        }

        debug_print(f"Extracted tag: {tag_name}")
        debug_pprint(tag_data)

        yield tag_data

        # タグページの名言も処理
        for item in self.parse_quotes(response, page_type='tag_quotes'):
            yield item
`
  },
  {
    id: 'news-crawl-spider',
    name: 'News CrawlSpider',
    description: 'ニュースサイト用の高度なCrawlSpider（カテゴリ別クロール）',
    icon: <Rss className="w-5 h-5" />,
    category: 'news',
    code: `import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from urllib.parse import urljoin, urlparse
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

class NewsCrawlSpider(CrawlSpider):
    name = 'news_crawl_spider'
    allowed_domains = ['example-news.com']  # 実際のニュースサイトに変更してください
    start_urls = [
        'https://example-news.com/',
        'https://example-news.com/politics/',
        'https://example-news.com/technology/',
        'https://example-news.com/sports/'
    ]

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,  # ニュースサイトには丁寧に
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': 3,
        'USER_AGENT': 'ScrapyUI News Crawler 1.0',
        'CLOSESPIDER_PAGECOUNT': 50,
    }

    rules = (
        # 記事ページへのリンクをフォロー
        Rule(
            LinkExtractor(
                allow=[
                    r'/article/\\d+/',  # /article/123/ 形式
                    r'/news/\\d{4}/\\d{2}/\\d{2}/',  # /news/2024/01/15/ 形式
                    r'/\\d{4}/\\d{2}/\\d{2}/.+',  # /2024/01/15/article-title 形式
                ],
                deny=[
                    r'/tag/',
                    r'/author/',
                    r'/search/',
                    r'/login',
                    r'/register'
                ],
                restrict_css=[
                    'article a',
                    '.article-list a',
                    '.news-item a',
                    'h2 a',
                    'h3 a'
                ]
            ),
            callback='parse_article',
            follow=False,
            cb_kwargs={'content_type': 'article'}
        ),

        # カテゴリページをフォロー
        Rule(
            LinkExtractor(
                allow=[
                    r'/politics/',
                    r'/technology/',
                    r'/sports/',
                    r'/business/',
                    r'/entertainment/'
                ],
                restrict_css=[
                    'nav a',
                    '.category-nav a',
                    '.menu a'
                ]
            ),
            callback='parse_category',
            follow=True,
            cb_kwargs={'content_type': 'category'}
        ),

        # ページネーション
        Rule(
            LinkExtractor(
                allow=[r'/page/\\d+/', r'\\?page=\\d+'],
                restrict_css=[
                    '.pagination a',
                    '.next-page',
                    'a[rel="next"]'
                ]
            ),
            callback='parse_category',
            follow=True,
            cb_kwargs={'content_type': 'pagination'}
        ),
    )

    def parse_start_url(self, response):
        """開始URLの処理"""
        debug_print(f"Processing start URL: {response.url}")
        return self.parse_category(response, content_type='homepage')

    def parse_category(self, response, content_type='category'):
        """カテゴリページの解析"""
        debug_print(f"Parsing category page: {response.url} (type: {content_type})")
        debug_print(f"Status code: {response.status}")

        # カテゴリ情報を抽出
        category_name = self.extract_category_name(response.url)

        # 記事リストを取得
        article_links = response.css('article a, .article-item a, .news-item a')

        category_data = {
            'url': response.url,
            'content_type': content_type,
            'item_type': 'category',
            'category_name': category_name,
            'articles_count': len(article_links),
            'title': response.css('title::text').get(),
            'depth': response.meta.get('depth', 0),
            'scraped_at': datetime.now().isoformat()
        }

        debug_print(f"Category: {category_name}, Articles found: {len(article_links)}")
        debug_pprint(category_data)

        yield category_data

    def parse_article(self, response, content_type='article'):
        """記事ページの解析"""
        debug_print(f"Parsing article: {response.url}")
        debug_print(f"Status code: {response.status}")

        # 記事の基本情報を抽出
        title = self.extract_title(response)
        content = self.extract_content(response)
        author = self.extract_author(response)
        publish_date = self.extract_publish_date(response)
        category = self.extract_category_name(response.url)
        tags = self.extract_tags(response)

        # 記事の統計情報
        word_count = len(content.split()) if content else 0
        paragraph_count = len(response.css('p').getall())
        image_count = len(response.css('img').getall())

        article_data = {
            'url': response.url,
            'content_type': content_type,
            'item_type': 'article',
            'title': title,
            'content': content[:1000] if content else None,  # 最初の1000文字
            'content_length': len(content) if content else 0,
            'word_count': word_count,
            'paragraph_count': paragraph_count,
            'image_count': image_count,
            'author': author,
            'publish_date': publish_date,
            'category': category,
            'tags': tags,
            'depth': response.meta.get('depth', 0),
            'scraped_at': datetime.now().isoformat()
        }

        debug_print(f"Article: {title}")
        debug_pprint(article_data)

        yield article_data

    def extract_title(self, response):
        """記事タイトルを抽出"""
        selectors = [
            'h1::text',
            '.article-title::text',
            '.entry-title::text',
            'title::text'
        ]

        for selector in selectors:
            title = response.css(selector).get()
            if title:
                return title.strip()
        return None

    def extract_content(self, response):
        """記事本文を抽出"""
        selectors = [
            '.article-content',
            '.entry-content',
            '.post-content',
            'article .content',
            '.article-body'
        ]

        for selector in selectors:
            content_elem = response.css(selector)
            if content_elem:
                # テキストのみを抽出
                text = ' '.join(content_elem.css('::text').getall())
                return re.sub(r'\\s+', ' ', text).strip()
        return None

    def extract_author(self, response):
        """著者名を抽出"""
        selectors = [
            '.author::text',
            '.byline::text',
            '.article-author::text',
            '[rel="author"]::text'
        ]

        for selector in selectors:
            author = response.css(selector).get()
            if author:
                return author.strip()
        return None

    def extract_publish_date(self, response):
        """公開日を抽出"""
        selectors = [
            'time::attr(datetime)',
            '.publish-date::text',
            '.article-date::text',
            '[property="article:published_time"]::attr(content)'
        ]

        for selector in selectors:
            date = response.css(selector).get()
            if date:
                return date.strip()
        return None

    def extract_category_name(self, url):
        """URLからカテゴリ名を抽出"""
        path = urlparse(url).path
        segments = [s for s in path.split('/') if s]

        # 一般的なカテゴリパターン
        categories = ['politics', 'technology', 'sports', 'business', 'entertainment']
        for segment in segments:
            if segment in categories:
                return segment

        return segments[0] if segments else 'general'

    def extract_tags(self, response):
        """タグを抽出"""
        selectors = [
            '.tags a::text',
            '.article-tags a::text',
            '.tag-list a::text'
        ]

        tags = []
        for selector in selectors:
            tags.extend(response.css(selector).getall())

        return [tag.strip() for tag in tags if tag.strip()]
`
  },
  {
    id: 'ecommerce-crawl-spider',
    name: 'E-commerce CrawlSpider',
    description: 'ECサイト用のCrawlSpider（商品カテゴリとページネーション対応）',
    icon: <ShoppingCart className="w-5 h-5" />,
    category: 'ecommerce',
    code: `import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from urllib.parse import urljoin, urlparse
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

class EcommerceCrawlSpider(CrawlSpider):
    name = 'ecommerce_crawl_spider'
    allowed_domains = ['example-shop.com']  # 実際のECサイトに変更してください
    start_urls = [
        'https://example-shop.com/',
        'https://example-shop.com/categories/',
        'https://example-shop.com/products/'
    ]

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,  # ECサイトには丁寧に
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': 4,
        'USER_AGENT': 'ScrapyUI E-commerce Crawler 1.0',
        'CLOSESPIDER_PAGECOUNT': 100,
        'CLOSESPIDER_ITEMCOUNT': 500,  # 最大500商品まで
    }

    rules = (
        # 商品詳細ページへのリンクをフォロー
        Rule(
            LinkExtractor(
                allow=[
                    r'/product/\\d+/',  # /product/123/ 形式
                    r'/item/\\d+/',     # /item/123/ 形式
                    r'/p/[\\w-]+/',     # /p/product-name/ 形式
                ],
                deny=[
                    r'/cart/',
                    r'/checkout/',
                    r'/login',
                    r'/register',
                    r'/account/',
                    r'/admin/',
                    r'/api/'
                ],
                restrict_css=[
                    '.product-item a',
                    '.product-list a',
                    '.product-grid a',
                    'h2 a',
                    'h3 a',
                    '.product-title a'
                ]
            ),
            callback='parse_product',
            follow=False,
            cb_kwargs={'content_type': 'product'}
        ),

        # カテゴリページをフォロー
        Rule(
            LinkExtractor(
                allow=[
                    r'/category/[\\w-]+/',
                    r'/categories/[\\w-]+/',
                    r'/c/[\\w-]+/'
                ],
                deny=[
                    r'/search/',
                    r'/filter/',
                    r'/sort/'
                ],
                restrict_css=[
                    '.category-nav a',
                    '.categories a',
                    '.menu a',
                    'nav a'
                ]
            ),
            callback='parse_category',
            follow=True,
            cb_kwargs={'content_type': 'category'}
        ),

        # ページネーション
        Rule(
            LinkExtractor(
                allow=[
                    r'/page/\\d+/',
                    r'\\?page=\\d+',
                    r'\\?p=\\d+'
                ],
                restrict_css=[
                    '.pagination a',
                    '.next-page',
                    'a[rel="next"]',
                    '.page-numbers a'
                ]
            ),
            callback='parse_category',
            follow=True,
            cb_kwargs={'content_type': 'pagination'}
        ),

        # ブランドページをフォロー
        Rule(
            LinkExtractor(
                allow=[r'/brand/[\\w-]+/'],
                restrict_css=['.brand-list a', '.brands a']
            ),
            callback='parse_brand',
            follow=True,
            cb_kwargs={'content_type': 'brand'}
        ),
    )

    def parse_start_url(self, response):
        """開始URLの処理"""
        debug_print(f"Processing start URL: {response.url}")
        return self.parse_category(response, content_type='homepage')

    def parse_category(self, response, content_type='category'):
        """カテゴリページの解析"""
        debug_print(f"Parsing category page: {response.url} (type: {content_type})")
        debug_print(f"Status code: {response.status}")

        # カテゴリ情報を抽出
        category_name = self.extract_category_name(response.url)

        # 商品リストを取得
        product_links = response.css('.product-item a, .product-list a, .product-grid a')

        # カテゴリの統計情報
        total_products = self.extract_total_products(response)
        price_range = self.extract_price_range(response)

        category_data = {
            'url': response.url,
            'content_type': content_type,
            'item_type': 'category',
            'category_name': category_name,
            'products_on_page': len(product_links),
            'total_products': total_products,
            'price_range': price_range,
            'title': response.css('title::text').get(),
            'breadcrumbs': response.css('.breadcrumb a::text').getall(),
            'depth': response.meta.get('depth', 0),
            'scraped_at': datetime.now().isoformat()
        }

        debug_print(f"Category: {category_name}, Products on page: {len(product_links)}")
        debug_pprint(category_data)

        yield category_data

    def parse_product(self, response, content_type='product'):
        """商品ページの解析"""
        debug_print(f"Parsing product: {response.url}")
        debug_print(f"Status code: {response.status}")

        # 商品の基本情報を抽出
        name = self.extract_product_name(response)
        price = self.extract_price(response)
        original_price = self.extract_original_price(response)
        description = self.extract_description(response)
        brand = self.extract_brand(response)
        category = self.extract_category_name(response.url)
        sku = self.extract_sku(response)
        availability = self.extract_availability(response)
        rating = self.extract_rating(response)
        review_count = self.extract_review_count(response)
        images = self.extract_images(response)
        specifications = self.extract_specifications(response)

        # 価格情報の計算
        discount_percentage = None
        if price and original_price:
            try:
                price_num = float(re.sub(r'[^\\d.]', '', price))
                original_price_num = float(re.sub(r'[^\\d.]', '', original_price))
                if original_price_num > price_num:
                    discount_percentage = round(((original_price_num - price_num) / original_price_num) * 100, 2)
            except (ValueError, ZeroDivisionError):
                pass

        product_data = {
            'url': response.url,
            'content_type': content_type,
            'item_type': 'product',
            'name': name,
            'price': price,
            'original_price': original_price,
            'discount_percentage': discount_percentage,
            'description': description[:500] if description else None,  # 最初の500文字
            'brand': brand,
            'category': category,
            'sku': sku,
            'availability': availability,
            'rating': rating,
            'review_count': review_count,
            'images_count': len(images),
            'images': images[:3],  # 最初の3つの画像
            'specifications': specifications,
            'breadcrumbs': response.css('.breadcrumb a::text').getall(),
            'depth': response.meta.get('depth', 0),
            'scraped_at': datetime.now().isoformat()
        }

        debug_print(f"Product: {name} - {price}")
        debug_pprint(product_data)

        yield product_data

    def parse_brand(self, response, content_type='brand'):
        """ブランドページの解析"""
        debug_print(f"Parsing brand page: {response.url}")

        brand_name = self.extract_brand_name(response.url)
        product_count = len(response.css('.product-item, .product-list-item'))

        brand_data = {
            'url': response.url,
            'content_type': content_type,
            'item_type': 'brand',
            'brand_name': brand_name,
            'products_count': product_count,
            'description': response.css('.brand-description::text').get(),
            'depth': response.meta.get('depth', 0),
            'scraped_at': datetime.now().isoformat()
        }

        debug_print(f"Brand: {brand_name}")
        debug_pprint(brand_data)

        yield brand_data

    def extract_product_name(self, response):
        """商品名を抽出"""
        selectors = [
            'h1::text',
            '.product-title::text',
            '.product-name::text',
            '.item-title::text'
        ]

        for selector in selectors:
            name = response.css(selector).get()
            if name:
                return name.strip()
        return None

    def extract_price(self, response):
        """現在価格を抽出"""
        selectors = [
            '.price::text',
            '.current-price::text',
            '.sale-price::text',
            '.product-price::text'
        ]

        for selector in selectors:
            price = response.css(selector).get()
            if price:
                return price.strip()
        return None

    def extract_original_price(self, response):
        """元の価格を抽出"""
        selectors = [
            '.original-price::text',
            '.regular-price::text',
            '.was-price::text',
            '.list-price::text'
        ]

        for selector in selectors:
            price = response.css(selector).get()
            if price:
                return price.strip()
        return None

    def extract_description(self, response):
        """商品説明を抽出"""
        selectors = [
            '.product-description',
            '.description',
            '.product-details',
            '.item-description'
        ]

        for selector in selectors:
            desc_elem = response.css(selector)
            if desc_elem:
                text = ' '.join(desc_elem.css('::text').getall())
                return re.sub(r'\\s+', ' ', text).strip()
        return None

    def extract_brand(self, response):
        """ブランド名を抽出"""
        selectors = [
            '.brand::text',
            '.product-brand::text',
            '.manufacturer::text'
        ]

        for selector in selectors:
            brand = response.css(selector).get()
            if brand:
                return brand.strip()
        return None

    def extract_sku(self, response):
        """SKUを抽出"""
        selectors = [
            '.sku::text',
            '.product-code::text',
            '.item-code::text'
        ]

        for selector in selectors:
            sku = response.css(selector).get()
            if sku:
                return sku.strip()
        return None

    def extract_availability(self, response):
        """在庫状況を抽出"""
        selectors = [
            '.availability::text',
            '.stock-status::text',
            '.in-stock::text'
        ]

        for selector in selectors:
            availability = response.css(selector).get()
            if availability:
                return availability.strip()
        return None

    def extract_rating(self, response):
        """評価を抽出"""
        selectors = [
            '.rating::text',
            '.stars::attr(data-rating)',
            '.review-rating::text'
        ]

        for selector in selectors:
            rating = response.css(selector).get()
            if rating:
                return rating.strip()
        return None

    def extract_review_count(self, response):
        """レビュー数を抽出"""
        selectors = [
            '.review-count::text',
            '.reviews-count::text',
            '.rating-count::text'
        ]

        for selector in selectors:
            count = response.css(selector).get()
            if count:
                return count.strip()
        return None

    def extract_images(self, response):
        """商品画像を抽出"""
        images = []
        selectors = [
            '.product-images img::attr(src)',
            '.product-gallery img::attr(src)',
            '.item-images img::attr(src)'
        ]

        for selector in selectors:
            imgs = response.css(selector).getall()
            for img in imgs:
                if img:
                    images.append(response.urljoin(img))

        return list(set(images))  # 重複を除去

    def extract_specifications(self, response):
        """仕様を抽出"""
        specs = {}
        spec_rows = response.css('.specifications tr, .specs tr, .product-specs tr')

        for row in spec_rows:
            key = row.css('td:first-child::text, th::text').get()
            value = row.css('td:last-child::text').get()
            if key and value:
                specs[key.strip()] = value.strip()

        return specs

    def extract_category_name(self, url):
        """URLからカテゴリ名を抽出"""
        path = urlparse(url).path
        segments = [s for s in path.split('/') if s]

        # カテゴリキーワードを探す
        category_keywords = ['category', 'categories', 'c']
        for i, segment in enumerate(segments):
            if segment in category_keywords and i + 1 < len(segments):
                return segments[i + 1]

        return segments[0] if segments else 'general'

    def extract_brand_name(self, url):
        """URLからブランド名を抽出"""
        path = urlparse(url).path
        segments = [s for s in path.split('/') if s]

        # ブランドキーワードを探す
        brand_keywords = ['brand', 'brands', 'b']
        for i, segment in enumerate(segments):
            if segment in brand_keywords and i + 1 < len(segments):
                return segments[i + 1]

        return segments[-1] if segments else 'unknown'

    def extract_total_products(self, response):
        """総商品数を抽出"""
        selectors = [
            '.total-products::text',
            '.results-count::text',
            '.product-count::text'
        ]

        for selector in selectors:
            count = response.css(selector).get()
            if count:
                # 数字のみを抽出
                numbers = re.findall(r'\\d+', count)
                if numbers:
                    return int(numbers[0])
        return None

    def extract_price_range(self, response):
        """価格帯を抽出"""
        prices = []
        price_elements = response.css('.price::text, .product-price::text').getall()

        for price_text in price_elements:
            # 価格から数字を抽出
            numbers = re.findall(r'\\d+\\.?\\d*', price_text)
            if numbers:
                try:
                    prices.append(float(numbers[0]))
                except ValueError:
                    continue

        if prices:
            return {
                'min': min(prices),
                'max': max(prices),
                'avg': round(sum(prices) / len(prices), 2)
            }
        return None
`
  },
  {
    id: 'security-spider',
    name: 'Security Scanner Spider',
    description: 'セキュリティ脆弱性をチェックするスパイダー（教育用）',
    icon: <Shield className="w-5 h-5" />,
    category: 'security',
    code: `import scrapy
from scrapy.http import Request
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
import hashlib
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class SecuritySpider(scrapy.Spider):
    name = 'security_spider'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,  # セキュリティスキャンは丁寧に
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': 2,
        'USER_AGENT': 'ScrapyUI Security Scanner 1.0 (Educational Purpose)',
        'CLOSESPIDER_PAGECOUNT': 20,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en',
        }
    }

    def parse(self, response):
        debug_print(f"Security scanning: {response.url}")
        debug_print(f"Status code: {response.status}")

        # セキュリティヘッダーをチェック
        security_headers = self.check_security_headers(response)

        # フォームのセキュリティをチェック
        form_security = self.check_form_security(response)

        # リンクのセキュリティをチェック
        link_security = self.check_link_security(response)

        # JavaScriptライブラリの脆弱性をチェック
        js_vulnerabilities = self.check_js_vulnerabilities(response)

        # HTTPSの使用状況をチェック
        https_usage = self.check_https_usage(response)

        # Cookieのセキュリティをチェック
        cookie_security = self.check_cookie_security(response)

        # セキュリティスコアを計算
        security_score = self.calculate_security_score(
            security_headers, form_security, link_security,
            js_vulnerabilities, https_usage, cookie_security
        )

        security_report = {
            'url': response.url,
            'scan_timestamp': datetime.now().isoformat(),
            'security_score': security_score,
            'security_headers': security_headers,
            'form_security': form_security,
            'link_security': link_security,
            'js_vulnerabilities': js_vulnerabilities,
            'https_usage': https_usage,
            'cookie_security': cookie_security,
            'recommendations': self.generate_recommendations(security_score, security_headers, form_security)
        }

        debug_print(f"Security report for {response.url}:")
        debug_pprint(security_report)

        yield security_report

        # 内部リンクをフォロー（セキュリティスキャンのため）
        for link in response.css('a[href]::attr(href)').getall()[:5]:
            if link.startswith('/') or response.urljoin(link).startswith(response.url):
                yield response.follow(link, self.parse)

    def check_security_headers(self, response):
        """セキュリティヘッダーをチェック"""
        headers = response.headers
        security_headers = {
            'X-Frame-Options': headers.get('X-Frame-Options', b'').decode(),
            'X-Content-Type-Options': headers.get('X-Content-Type-Options', b'').decode(),
            'X-XSS-Protection': headers.get('X-XSS-Protection', b'').decode(),
            'Strict-Transport-Security': headers.get('Strict-Transport-Security', b'').decode(),
            'Content-Security-Policy': headers.get('Content-Security-Policy', b'').decode(),
            'Referrer-Policy': headers.get('Referrer-Policy', b'').decode(),
            'Permissions-Policy': headers.get('Permissions-Policy', b'').decode(),
        }

        # セキュリティヘッダーの評価
        header_score = 0
        for header, value in security_headers.items():
            if value:
                header_score += 1

        return {
            'headers': security_headers,
            'score': header_score,
            'max_score': len(security_headers),
            'missing_headers': [h for h, v in security_headers.items() if not v]
        }

    def check_form_security(self, response):
        """フォームのセキュリティをチェック"""
        forms = response.css('form')
        form_issues = []

        for i, form in enumerate(forms):
            action = form.css('::attr(action)').get() or ''
            method = form.css('::attr(method)').get() or 'GET'

            # HTTPS使用チェック
            if action.startswith('http://'):
                form_issues.append(f"Form {i+1}: Uses HTTP instead of HTTPS")

            # CSRF保護チェック
            csrf_token = form.css('input[name*="csrf"], input[name*="token"]').get()
            if not csrf_token and method.upper() == 'POST':
                form_issues.append(f"Form {i+1}: Missing CSRF protection")

            # パスワードフィールドのチェック
            password_fields = form.css('input[type="password"]')
            if password_fields and not response.url.startswith('https://'):
                form_issues.append(f"Form {i+1}: Password field over HTTP")

        return {
            'total_forms': len(forms),
            'issues': form_issues,
            'secure_forms': len(forms) - len(form_issues)
        }

    def check_link_security(self, response):
        """リンクのセキュリティをチェック"""
        external_links = []
        insecure_links = []

        for link in response.css('a[href]'):
            href = link.css('::attr(href)').get()
            if href:
                absolute_url = urljoin(response.url, href)
                parsed = urlparse(absolute_url)

                # 外部リンクのチェック
                if parsed.netloc and parsed.netloc != urlparse(response.url).netloc:
                    external_links.append(absolute_url)

                    # rel="noopener"のチェック
                    rel = link.css('::attr(rel)').get() or ''
                    if 'noopener' not in rel:
                        insecure_links.append(f"External link without noopener: {absolute_url}")

                # HTTPリンクのチェック
                if absolute_url.startswith('http://'):
                    insecure_links.append(f"HTTP link: {absolute_url}")

        return {
            'external_links_count': len(external_links),
            'insecure_links': insecure_links,
            'external_links': external_links[:10]  # 最初の10個のみ
        }

    def check_js_vulnerabilities(self, response):
        """JavaScriptライブラリの脆弱性をチェック"""
        js_libraries = []
        potential_vulnerabilities = []

        # スクリプトタグを検索
        for script in response.css('script[src]'):
            src = script.css('::attr(src)').get()
            if src:
                js_libraries.append(src)

                # 古いjQueryバージョンのチェック
                if 'jquery' in src.lower():
                    version_match = re.search(r'jquery[.-]?(\\d+\\.\\d+\\.\\d+)', src.lower())
                    if version_match:
                        version = version_match.group(1)
                        if version < '3.5.0':
                            potential_vulnerabilities.append(f"Outdated jQuery version: {version}")

        return {
            'js_libraries': js_libraries,
            'potential_vulnerabilities': potential_vulnerabilities,
            'libraries_count': len(js_libraries)
        }

    def check_https_usage(self, response):
        """HTTPS使用状況をチェック"""
        is_https = response.url.startswith('https://')
        mixed_content = []

        # 混合コンテンツのチェック
        if is_https:
            for resource in response.css('img[src], script[src], link[href]'):
                src = resource.css('::attr(src)').get() or resource.css('::attr(href)').get()
                if src and src.startswith('http://'):
                    mixed_content.append(src)

        return {
            'is_https': is_https,
            'mixed_content': mixed_content,
            'mixed_content_count': len(mixed_content)
        }

    def check_cookie_security(self, response):
        """Cookieのセキュリティをチェック"""
        cookies = response.headers.getlist('Set-Cookie')
        cookie_issues = []

        for cookie in cookies:
            cookie_str = cookie.decode()

            # Secure属性のチェック
            if 'Secure' not in cookie_str and response.url.startswith('https://'):
                cookie_issues.append("Cookie missing Secure attribute")

            # HttpOnly属性のチェック
            if 'HttpOnly' not in cookie_str:
                cookie_issues.append("Cookie missing HttpOnly attribute")

            # SameSite属性のチェック
            if 'SameSite' not in cookie_str:
                cookie_issues.append("Cookie missing SameSite attribute")

        return {
            'total_cookies': len(cookies),
            'issues': cookie_issues,
            'secure_cookies': len(cookies) - len(cookie_issues)
        }

    def calculate_security_score(self, security_headers, form_security, link_security, js_vulnerabilities, https_usage, cookie_security):
        """セキュリティスコアを計算（0-100）"""
        score = 0

        # セキュリティヘッダー（30点）
        if security_headers['max_score'] > 0:
            score += (security_headers['score'] / security_headers['max_score']) * 30

        # HTTPS使用（20点）
        if https_usage['is_https']:
            score += 20
            if https_usage['mixed_content_count'] == 0:
                score += 5

        # フォームセキュリティ（20点）
        if form_security['total_forms'] > 0:
            score += (form_security['secure_forms'] / form_security['total_forms']) * 20
        else:
            score += 20  # フォームがない場合は満点

        # リンクセキュリティ（15点）
        if len(link_security['insecure_links']) == 0:
            score += 15

        # JavaScriptライブラリ（10点）
        if len(js_vulnerabilities['potential_vulnerabilities']) == 0:
            score += 10

        # Cookieセキュリティ（5点）
        if cookie_security['total_cookies'] > 0:
            score += (cookie_security['secure_cookies'] / cookie_security['total_cookies']) * 5
        else:
            score += 5  # Cookieがない場合は満点

        return round(score, 2)

    def generate_recommendations(self, score, security_headers, form_security):
        """セキュリティ改善の推奨事項を生成"""
        recommendations = []

        if score < 70:
            recommendations.append("Overall security score is low. Consider implementing the following improvements:")

        if len(security_headers['missing_headers']) > 0:
            recommendations.append(f"Add missing security headers: {', '.join(security_headers['missing_headers'])}")

        if len(form_security['issues']) > 0:
            recommendations.append("Fix form security issues: implement CSRF protection and use HTTPS")

        if score >= 90:
            recommendations.append("Excellent security posture! Keep monitoring for new vulnerabilities.")
        elif score >= 70:
            recommendations.append("Good security posture with room for improvement.")

        return recommendations
`
  },
  {
    id: 'performance-spider',
    name: 'Performance Monitor Spider',
    description: 'ウェブサイトのパフォーマンスを監視・測定するスパイダー',
    icon: <Clock className="w-5 h-5" />,
    category: 'performance',
    code: `import scrapy
from scrapy.http import Request
from scrapy.downloadermiddlewares.stats import DownloaderStats
from urllib.parse import urljoin, urlparse
import time
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

class PerformanceSpider(scrapy.Spider):
    name = 'performance_spider'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': 2,
        'USER_AGENT': 'ScrapyUI Performance Monitor 1.0',
        'CLOSESPIDER_PAGECOUNT': 10,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.stats.DownloaderStats': 850,
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = time.time()
        self.page_metrics = []

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url,
                callback=self.parse,
                meta={'start_time': time.time()},
                dont_filter=True
            )

    def parse(self, response):
        # レスポンス時間を計算
        start_time = response.meta.get('start_time', time.time())
        response_time = time.time() - start_time

        debug_print(f"Performance analysis for: {response.url}")
        debug_print(f"Response time: {response_time:.3f}s")

        # ページサイズを計算
        page_size = len(response.body)

        # リソースを分析
        resources = self.analyze_resources(response)

        # SEOパフォーマンスを分析
        seo_metrics = self.analyze_seo_performance(response)

        # 画像最適化を分析
        image_optimization = self.analyze_image_optimization(response)

        # CSS/JS最適化を分析
        asset_optimization = self.analyze_asset_optimization(response)

        # キャッシュ設定を分析
        cache_analysis = self.analyze_cache_headers(response)

        # パフォーマンススコアを計算
        performance_score = self.calculate_performance_score(
            response_time, page_size, resources, seo_metrics,
            image_optimization, asset_optimization
        )

        performance_report = {
            'url': response.url,
            'timestamp': datetime.now().isoformat(),
            'response_time': round(response_time, 3),
            'page_size_bytes': page_size,
            'page_size_kb': round(page_size / 1024, 2),
            'performance_score': performance_score,
            'resources': resources,
            'seo_metrics': seo_metrics,
            'image_optimization': image_optimization,
            'asset_optimization': asset_optimization,
            'cache_analysis': cache_analysis,
            'recommendations': self.generate_performance_recommendations(
                response_time, page_size, resources, image_optimization, asset_optimization
            )
        }

        debug_print(f"Performance report:")
        debug_pprint(performance_report)

        yield performance_report

        # 内部リンクをフォロー（パフォーマンステストのため）
        for link in response.css('a[href]::attr(href)').getall()[:3]:
            if link.startswith('/') or response.urljoin(link).startswith(response.url):
                yield Request(
                    response.urljoin(link),
                    callback=self.parse,
                    meta={'start_time': time.time()},
                    dont_filter=True
                )

    def analyze_resources(self, response):
        """ページリソースを分析"""
        images = response.css('img[src]::attr(src)').getall()
        css_files = response.css('link[rel="stylesheet"]::attr(href)').getall()
        js_files = response.css('script[src]::attr(src)').getall()

        # 外部リソースをカウント
        external_images = [img for img in images if img.startswith('http') and not img.startswith(response.url)]
        external_css = [css for css in css_files if css.startswith('http') and not css.startswith(response.url)]
        external_js = [js for js in js_files if js.startswith('http') and not js.startswith(response.url)]

        return {
            'total_images': len(images),
            'total_css_files': len(css_files),
            'total_js_files': len(js_files),
            'external_images': len(external_images),
            'external_css': len(external_css),
            'external_js': len(external_js),
            'total_requests': len(images) + len(css_files) + len(js_files) + 1,  # +1 for HTML
            'external_requests': len(external_images) + len(external_css) + len(external_js)
        }

    def analyze_seo_performance(self, response):
        """SEOパフォーマンスを分析"""
        title = response.css('title::text').get() or ''
        meta_description = response.css('meta[name="description"]::attr(content)').get() or ''
        h1_tags = response.css('h1::text').getall()
        h2_tags = response.css('h2::text').getall()

        # 構造化データの確認
        structured_data = response.css('script[type="application/ld+json"]').getall()

        # 画像のalt属性確認
        images_without_alt = response.css('img:not([alt])').getall()

        return {
            'title_length': len(title),
            'meta_description_length': len(meta_description),
            'h1_count': len(h1_tags),
            'h2_count': len(h2_tags),
            'has_structured_data': len(structured_data) > 0,
            'structured_data_count': len(structured_data),
            'images_without_alt': len(images_without_alt),
            'title_optimal': 30 <= len(title) <= 60,
            'meta_description_optimal': 120 <= len(meta_description) <= 160
        }

    def analyze_image_optimization(self, response):
        """画像最適化を分析"""
        images = response.css('img')
        large_images = []
        unoptimized_formats = []
        missing_lazy_loading = []

        for img in images:
            src = img.css('::attr(src)').get()
            loading = img.css('::attr(loading)').get()

            if src:
                # 画像フォーマットをチェック
                if src.lower().endswith(('.bmp', '.tiff')):
                    unoptimized_formats.append(src)

                # lazy loadingをチェック
                if not loading or loading != 'lazy':
                    missing_lazy_loading.append(src)

                # 大きな画像をチェック（推測）
                if 'large' in src.lower() or 'big' in src.lower():
                    large_images.append(src)

        return {
            'total_images': len(images),
            'unoptimized_formats': len(unoptimized_formats),
            'missing_lazy_loading': len(missing_lazy_loading),
            'potentially_large_images': len(large_images),
            'optimization_score': max(0, 100 - (len(unoptimized_formats) * 10) - (len(missing_lazy_loading) * 5))
        }

    def analyze_asset_optimization(self, response):
        """CSS/JS最適化を分析"""
        inline_css = response.css('style').getall()
        inline_js = response.css('script:not([src])').getall()

        # インラインスタイルの総サイズ
        inline_css_size = sum(len(css) for css in inline_css)
        inline_js_size = sum(len(js) for js in inline_js)

        # 外部ファイルの数
        external_css = response.css('link[rel="stylesheet"]').getall()
        external_js = response.css('script[src]').getall()

        return {
            'inline_css_count': len(inline_css),
            'inline_js_count': len(inline_js),
            'inline_css_size': inline_css_size,
            'inline_js_size': inline_js_size,
            'external_css_count': len(external_css),
            'external_js_count': len(external_js),
            'total_asset_requests': len(external_css) + len(external_js),
            'optimization_needed': inline_css_size > 10000 or inline_js_size > 10000 or len(external_css) > 5 or len(external_js) > 5
        }

    def analyze_cache_headers(self, response):
        """キャッシュヘッダーを分析"""
        headers = response.headers

        cache_control = headers.get('Cache-Control', b'').decode()
        expires = headers.get('Expires', b'').decode()
        etag = headers.get('ETag', b'').decode()
        last_modified = headers.get('Last-Modified', b'').decode()

        return {
            'has_cache_control': bool(cache_control),
            'has_expires': bool(expires),
            'has_etag': bool(etag),
            'has_last_modified': bool(last_modified),
            'cache_control': cache_control,
            'expires': expires,
            'cache_score': sum([bool(cache_control), bool(expires), bool(etag), bool(last_modified)]) * 25
        }

    def calculate_performance_score(self, response_time, page_size, resources, seo_metrics, image_optimization, asset_optimization):
        """パフォーマンススコア（0-100）を計算"""
        score = 100

        # レスポンス時間（30点）
        if response_time > 3:
            score -= 30
        elif response_time > 2:
            score -= 20
        elif response_time > 1:
            score -= 10

        # ページサイズ（20点）
        page_size_mb = page_size / (1024 * 1024)
        if page_size_mb > 5:
            score -= 20
        elif page_size_mb > 3:
            score -= 15
        elif page_size_mb > 1:
            score -= 10

        # リクエスト数（20点）
        if resources['total_requests'] > 100:
            score -= 20
        elif resources['total_requests'] > 50:
            score -= 15
        elif resources['total_requests'] > 30:
            score -= 10

        # SEO最適化（15点）
        seo_score = 0
        if seo_metrics['title_optimal']:
            seo_score += 5
        if seo_metrics['meta_description_optimal']:
            seo_score += 5
        if seo_metrics['h1_count'] > 0:
            seo_score += 3
        if seo_metrics['images_without_alt'] == 0:
            seo_score += 2
        score = score - 15 + seo_score

        # 画像最適化（10点）
        score = score - 10 + (image_optimization['optimization_score'] / 10)

        # アセット最適化（5点）
        if not asset_optimization['optimization_needed']:
            score += 5

        return max(0, round(score, 2))

    def generate_performance_recommendations(self, response_time, page_size, resources, image_optimization, asset_optimization):
        """パフォーマンス改善の推奨事項を生成"""
        recommendations = []

        if response_time > 2:
            recommendations.append(f"Improve server response time (current: {response_time:.3f}s)")

        if page_size > 1024 * 1024:  # 1MB
            recommendations.append(f"Reduce page size (current: {page_size / 1024:.1f}KB)")

        if resources['total_requests'] > 50:
            recommendations.append(f"Reduce HTTP requests (current: {resources['total_requests']})")

        if image_optimization['unoptimized_formats'] > 0:
            recommendations.append("Optimize image formats (use WebP, AVIF)")

        if image_optimization['missing_lazy_loading'] > 0:
            recommendations.append("Implement lazy loading for images")

        if asset_optimization['optimization_needed']:
            recommendations.append("Minify and combine CSS/JS files")

        if resources['external_requests'] > 10:
            recommendations.append("Reduce external resource dependencies")

        if not recommendations:
            recommendations.append("Great performance! Keep monitoring for regressions.")

        return recommendations
`
  },
  {
    id: 'testing-spider',
    name: 'A/B Testing Spider',
    description: 'A/Bテストやユーザビリティテストのためのスパイダー',
    icon: <Target className="w-5 h-5" />,
    category: 'testing',
    code: `import scrapy
from scrapy.http import Request
from urllib.parse import urljoin, urlparse
import random
import time
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

class TestingSpider(scrapy.Spider):
    name = 'testing_spider'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': 2,
        'USER_AGENT': 'ScrapyUI Testing Bot 1.0',
        'CLOSESPIDER_PAGECOUNT': 20,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en,ja;q=0.9',
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_variants = ['A', 'B', 'C']
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        self.test_results = []

    def start_requests(self):
        for url in self.start_urls:
            for variant in self.test_variants:
                yield Request(
                    url,
                    callback=self.parse,
                    meta={
                        'test_variant': variant,
                        'start_time': time.time(),
                        'user_agent': random.choice(self.user_agents)
                    },
                    headers={'User-Agent': random.choice(self.user_agents)},
                    dont_filter=True
                )

    def parse(self, response):
        variant = response.meta.get('test_variant', 'A')
        start_time = response.meta.get('start_time', time.time())
        load_time = time.time() - start_time

        debug_print(f"Testing variant {variant} on {response.url}")
        debug_print(f"Load time: {load_time:.3f}s")

        # ページの基本メトリクスを収集
        page_metrics = self.collect_page_metrics(response)

        # ユーザビリティ要素をテスト
        usability_test = self.test_usability(response)

        # フォームのテスト
        form_test = self.test_forms(response)

        # ナビゲーションのテスト
        navigation_test = self.test_navigation(response)

        # レスポンシブデザインのテスト
        responsive_test = self.test_responsive_elements(response)

        # アクセシビリティのテスト
        accessibility_test = self.test_accessibility(response)

        # パフォーマンスメトリクス
        performance_metrics = self.collect_performance_metrics(response, load_time)

        test_result = {
            'url': response.url,
            'test_variant': variant,
            'timestamp': datetime.now().isoformat(),
            'load_time': round(load_time, 3),
            'user_agent': response.meta.get('user_agent', ''),
            'page_metrics': page_metrics,
            'usability_test': usability_test,
            'form_test': form_test,
            'navigation_test': navigation_test,
            'responsive_test': responsive_test,
            'accessibility_test': accessibility_test,
            'performance_metrics': performance_metrics,
            'overall_score': self.calculate_overall_score(
                usability_test, form_test, navigation_test,
                responsive_test, accessibility_test, performance_metrics
            )
        }

        debug_print(f"Test result for variant {variant}:")
        debug_pprint(test_result)

        yield test_result

        # 内部リンクをテスト
        for link in response.css('a[href]::attr(href)').getall()[:3]:
            if link.startswith('/') or response.urljoin(link).startswith(response.url):
                yield Request(
                    response.urljoin(link),
                    callback=self.parse,
                    meta={
                        'test_variant': variant,
                        'start_time': time.time(),
                        'user_agent': response.meta.get('user_agent', '')
                    },
                    headers={'User-Agent': response.meta.get('user_agent', '')},
                    dont_filter=True
                )

    def collect_page_metrics(self, response):
        """ページの基本メトリクスを収集"""
        title = response.css('title::text').get() or ''
        h1_tags = response.css('h1::text').getall()
        images = response.css('img').getall()
        links = response.css('a[href]').getall()
        forms = response.css('form').getall()

        return {
            'title': title,
            'title_length': len(title),
            'h1_count': len(h1_tags),
            'image_count': len(images),
            'link_count': len(links),
            'form_count': len(forms),
            'page_size': len(response.body),
            'status_code': response.status
        }

    def test_usability(self, response):
        """ユーザビリティ要素をテスト"""
        issues = []
        score = 100

        # タイトルの長さをチェック
        title = response.css('title::text').get() or ''
        if len(title) < 10 or len(title) > 60:
            issues.append("Title length not optimal")
            score -= 10

        # H1タグの存在をチェック
        h1_tags = response.css('h1').getall()
        if len(h1_tags) == 0:
            issues.append("Missing H1 tag")
            score -= 15
        elif len(h1_tags) > 1:
            issues.append("Multiple H1 tags")
            score -= 5

        # ナビゲーションメニューの存在をチェック
        nav_elements = response.css('nav, .navigation, .menu, #menu').getall()
        if len(nav_elements) == 0:
            issues.append("No navigation menu found")
            score -= 20

        # 検索機能の存在をチェック
        search_elements = response.css('input[type="search"], .search, #search').getall()
        if len(search_elements) == 0:
            issues.append("No search functionality found")
            score -= 10

        # フッターの存在をチェック
        footer_elements = response.css('footer, .footer, #footer').getall()
        if len(footer_elements) == 0:
            issues.append("No footer found")
            score -= 5

        return {
            'score': max(0, score),
            'issues': issues,
            'total_issues': len(issues)
        }

    def test_forms(self, response):
        """フォームのテスト"""
        forms = response.css('form')
        form_issues = []
        score = 100

        for i, form in enumerate(forms):
            # ラベルの存在をチェック
            labels = form.css('label').getall()
            inputs = form.css('input, textarea, select').getall()

            if len(inputs) > len(labels):
                form_issues.append(f"Form {i+1}: Missing labels for some inputs")
                score -= 10

            # 必須フィールドの表示をチェック
            required_inputs = form.css('input[required], textarea[required], select[required]').getall()
            for required_input in required_inputs:
                # 必須マークの確認（*, required, 等）
                if '*' not in form.get() and 'required' not in form.get().lower():
                    form_issues.append(f"Form {i+1}: Required fields not clearly marked")
                    score -= 5
                    break

            # 送信ボタンの存在をチェック
            submit_buttons = form.css('input[type="submit"], button[type="submit"], button:not([type])').getall()
            if len(submit_buttons) == 0:
                form_issues.append(f"Form {i+1}: No submit button found")
                score -= 15

        return {
            'total_forms': len(forms),
            'score': max(0, score) if len(forms) > 0 else 100,
            'issues': form_issues,
            'total_issues': len(form_issues)
        }

    def test_navigation(self, response):
        """ナビゲーションのテスト"""
        issues = []
        score = 100

        # パンくずリストの存在をチェック
        breadcrumbs = response.css('.breadcrumb, .breadcrumbs, nav[aria-label*="breadcrumb"]').getall()
        if len(breadcrumbs) == 0:
            issues.append("No breadcrumb navigation found")
            score -= 10

        # メインナビゲーションのリンク数をチェック
        main_nav_links = response.css('nav a, .navigation a, .menu a').getall()
        if len(main_nav_links) > 10:
            issues.append("Too many navigation links (cognitive overload)")
            score -= 5
        elif len(main_nav_links) < 3:
            issues.append("Too few navigation links")
            score -= 5

        # ホームページへのリンクをチェック
        home_links = response.css('a[href="/"], a[href="./"], a[href*="home"]').getall()
        if len(home_links) == 0:
            issues.append("No clear home page link")
            score -= 10

        # 404ページの処理をチェック（リンク切れの検出）
        broken_links = []
        for link in response.css('a[href]')[:10]:  # 最初の10個のリンクのみチェック
            href = link.css('::attr(href)').get()
            if href and href.startswith('#'):
                # アンカーリンクの場合、対応する要素があるかチェック
                anchor_id = href[1:]
                if not response.css(f'#{anchor_id}, [name="{anchor_id}"]').get():
                    broken_links.append(href)

        if len(broken_links) > 0:
            issues.append(f"Broken anchor links found: {len(broken_links)}")
            score -= len(broken_links) * 2

        return {
            'score': max(0, score),
            'issues': issues,
            'total_issues': len(issues),
            'main_nav_links_count': len(main_nav_links),
            'broken_links': broken_links
        }

    def test_responsive_elements(self, response):
        """レスポンシブデザイン要素のテスト"""
        issues = []
        score = 100

        # ビューポートメタタグの存在をチェック
        viewport_meta = response.css('meta[name="viewport"]').get()
        if not viewport_meta:
            issues.append("Missing viewport meta tag")
            score -= 20

        # レスポンシブ画像の使用をチェック
        images = response.css('img')
        responsive_images = 0
        for img in images:
            if img.css('::attr(srcset)').get() or img.css('::attr(sizes)').get():
                responsive_images += 1

        if len(images) > 0 and responsive_images == 0:
            issues.append("No responsive images found")
            score -= 15

        # CSSメディアクエリの存在をチェック
        css_content = ' '.join(response.css('style::text').getall())
        if '@media' not in css_content:
            issues.append("No CSS media queries found in inline styles")
            score -= 10

        # フレキシブルレイアウトの使用をチェック
        if 'flex' not in css_content and 'grid' not in css_content:
            issues.append("No modern layout methods (flexbox/grid) detected")
            score -= 10

        return {
            'score': max(0, score),
            'issues': issues,
            'total_issues': len(issues),
            'has_viewport_meta': bool(viewport_meta),
            'responsive_images_ratio': responsive_images / len(images) if len(images) > 0 else 0
        }

    def test_accessibility(self, response):
        """アクセシビリティのテスト"""
        issues = []
        score = 100

        # 画像のalt属性をチェック
        images_without_alt = response.css('img:not([alt])').getall()
        if len(images_without_alt) > 0:
            issues.append(f"{len(images_without_alt)} images missing alt attributes")
            score -= len(images_without_alt) * 2

        # フォームラベルの関連付けをチェック
        inputs_without_labels = response.css('input:not([aria-label]):not([aria-labelledby])').getall()
        labels = response.css('label').getall()
        if len(inputs_without_labels) > len(labels):
            issues.append("Some form inputs lack proper labels")
            score -= 10

        # 見出しの階層をチェック
        headings = []
        for i in range(1, 7):
            headings.extend([(i, h) for h in response.css(f'h{i}').getall()])

        if len(headings) > 1:
            heading_levels = [h[0] for h in headings]
            if heading_levels[0] != 1:
                issues.append("Page doesn't start with H1")
                score -= 10

            # 見出しレベルのスキップをチェック
            for i in range(1, len(heading_levels)):
                if heading_levels[i] - heading_levels[i-1] > 1:
                    issues.append("Heading levels skip (bad hierarchy)")
                    score -= 5
                    break

        # カラーコントラストの基本チェック（CSSから推測）
        css_content = ' '.join(response.css('style::text').getall())
        if 'color:' in css_content and 'background' in css_content:
            # 基本的な色の使用をチェック（詳細な分析は困難）
            if '#fff' in css_content and '#000' not in css_content:
                issues.append("Potential color contrast issues")
                score -= 5

        # キーボードナビゲーションのサポートをチェック
        focusable_elements = response.css('a, button, input, textarea, select, [tabindex]').getall()
        if len(focusable_elements) == 0:
            issues.append("No focusable elements found")
            score -= 15

        return {
            'score': max(0, score),
            'issues': issues,
            'total_issues': len(issues),
            'images_without_alt': len(images_without_alt),
            'focusable_elements_count': len(focusable_elements)
        }

    def collect_performance_metrics(self, response, load_time):
        """パフォーマンスメトリクスを収集"""
        page_size = len(response.body)
        image_count = len(response.css('img').getall())
        css_count = len(response.css('link[rel="stylesheet"]').getall())
        js_count = len(response.css('script[src]').getall())

        return {
            'load_time': load_time,
            'page_size_kb': round(page_size / 1024, 2),
            'total_requests': 1 + image_count + css_count + js_count,
            'image_count': image_count,
            'css_files': css_count,
            'js_files': js_count,
            'performance_grade': self.grade_performance(load_time, page_size)
        }

    def grade_performance(self, load_time, page_size):
        """パフォーマンスをグレード評価"""
        score = 100

        # ロード時間の評価
        if load_time > 3:
            score -= 30
        elif load_time > 2:
            score -= 20
        elif load_time > 1:
            score -= 10

        # ページサイズの評価
        page_size_mb = page_size / (1024 * 1024)
        if page_size_mb > 2:
            score -= 20
        elif page_size_mb > 1:
            score -= 10

        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def calculate_overall_score(self, usability_test, form_test, navigation_test, responsive_test, accessibility_test, performance_metrics):
        """総合スコアを計算"""
        scores = [
            usability_test['score'] * 0.25,      # 25%
            form_test['score'] * 0.15,           # 15%
            navigation_test['score'] * 0.20,     # 20%
            responsive_test['score'] * 0.15,     # 15%
            accessibility_test['score'] * 0.25   # 25%
        ]

        overall_score = sum(scores)

        # パフォーマンスグレードによる調整
        performance_grade = performance_metrics['performance_grade']
        if performance_grade == 'A':
            overall_score += 0
        elif performance_grade == 'B':
            overall_score -= 5
        elif performance_grade == 'C':
            overall_score -= 10
        elif performance_grade == 'D':
            overall_score -= 15
        else:  # F
            overall_score -= 20

        return max(0, round(overall_score, 2))
`
  },
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

    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'args': ['--no-sandbox', '--disable-dev-shm-usage']
        },
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 30000,
        'PLAYWRIGHT_DEFAULT_TIMEOUT': 10000,
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
        'CLOSESPIDER_PAGECOUNT': 10,
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        # ページロード完了まで待機
                        PageMethod("wait_for_load_state", "networkidle"),
                        # 特定の要素が表示されるまで待機
                        PageMethod("wait_for_selector", "body", timeout=10000),
                        # JavaScriptを実行してページの準備完了を確認
                        PageMethod("evaluate", "() => document.readyState === 'complete'"),
                    ],
                }
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]

        debug_print(f"Processing page: {response.url}")
        debug_print(f"Page title: {await page.title()}")

        # ページの基本情報を取得
        page_info = await self.get_page_info(page, response.url)

        # スクリーンショットを撮影
        screenshot_data = await self.take_screenshot(page)

        # ページのパフォーマンス情報を取得
        performance_data = await self.get_performance_metrics(page)

        # ネットワークリクエストを監視
        network_data = await self.monitor_network_requests(page)

        # JavaScriptエラーを監視
        js_errors = await self.monitor_js_errors(page)

        # ページの可視性を確認
        visibility_data = await self.check_element_visibility(page)

        # フォームとの相互作用をテスト
        form_interaction = await self.test_form_interactions(page)

        # モバイルビューポートをテスト
        mobile_test = await self.test_mobile_viewport(page)

        # ページデータを収集
        page_data = {
            'url': response.url,
            'timestamp': datetime.now().isoformat(),
            'page_info': page_info,
            'screenshot': screenshot_data,
            'performance': performance_data,
            'network': network_data,
            'js_errors': js_errors,
            'visibility': visibility_data,
            'form_interaction': form_interaction,
            'mobile_test': mobile_test
        }

        debug_print("Page analysis complete:")
        debug_pprint(page_data)

        yield page_data

        # 動的に生成されたリンクを取得
        dynamic_links = await self.get_dynamic_links(page)

        # 内部リンクをフォロー
        for link_url in dynamic_links[:3]:
            yield scrapy.Request(
                link_url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "networkidle"),
                        PageMethod("wait_for_selector", "body"),
                    ],
                }
            )

        await page.close()

    async def get_page_info(self, page, url):
        """ページの基本情報を取得"""
        try:
            title = await page.title()
            viewport = page.viewport_size
            user_agent = await page.evaluate("() => navigator.userAgent")

            # メタタグ情報を取得
            meta_description = await page.get_attribute('meta[name="description"]', 'content') or ''
            meta_keywords = await page.get_attribute('meta[name="keywords"]', 'content') or ''

            # ページの言語を取得
            page_lang = await page.get_attribute('html', 'lang') or ''

            # ページのエンコーディングを取得
            charset = await page.get_attribute('meta[charset]', 'charset') or \
                     await page.get_attribute('meta[http-equiv="Content-Type"]', 'content') or ''

            return {
                'title': title,
                'url': url,
                'viewport': viewport,
                'user_agent': user_agent,
                'meta_description': meta_description,
                'meta_keywords': meta_keywords,
                'language': page_lang,
                'charset': charset,
                'title_length': len(title),
                'meta_description_length': len(meta_description)
            }
        except Exception as e:
            debug_print(f"Error getting page info: {e}")
            return {'error': str(e)}

    async def take_screenshot(self, page):
        """スクリーンショットを撮影"""
        try:
            # フルページスクリーンショット
            screenshot_full = await page.screenshot(full_page=True, type='png')

            # ビューポートスクリーンショット
            screenshot_viewport = await page.screenshot(full_page=False, type='png')

            return {
                'full_page_size': len(screenshot_full),
                'viewport_size': len(screenshot_viewport),
                'screenshot_taken': True,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            debug_print(f"Error taking screenshot: {e}")
            return {'error': str(e), 'screenshot_taken': False}

    async def get_performance_metrics(self, page):
        """パフォーマンスメトリクスを取得"""
        try:
            # Navigation Timing APIを使用
            performance_data = await page.evaluate("""
                () => {
                    const perfData = performance.getEntriesByType('navigation')[0];
                    const paintEntries = performance.getEntriesByType('paint');

                    return {
                        // Navigation Timing
                        dns_lookup: perfData.domainLookupEnd - perfData.domainLookupStart,
                        tcp_connect: perfData.connectEnd - perfData.connectStart,
                        request_time: perfData.responseStart - perfData.requestStart,
                        response_time: perfData.responseEnd - perfData.responseStart,
                        dom_loading: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                        page_load: perfData.loadEventEnd - perfData.loadEventStart,
                        total_time: perfData.loadEventEnd - perfData.navigationStart,

                        // Paint Timing
                        first_paint: paintEntries.find(entry => entry.name === 'first-paint')?.startTime || 0,
                        first_contentful_paint: paintEntries.find(entry => entry.name === 'first-contentful-paint')?.startTime || 0,

                        // Resource Timing
                        resource_count: performance.getEntriesByType('resource').length,

                        // Memory (if available)
                        memory: performance.memory ? {
                            used: performance.memory.usedJSHeapSize,
                            total: performance.memory.totalJSHeapSize,
                            limit: performance.memory.jsHeapSizeLimit
                        } : null
                    };
                }
            """)

            return performance_data
        except Exception as e:
            debug_print(f"Error getting performance metrics: {e}")
            return {'error': str(e)}

    async def monitor_network_requests(self, page):
        """ネットワークリクエストを監視"""
        try:
            # ネットワークイベントをリッスン
            requests = []
            responses = []

            async def handle_request(request):
                requests.append({
                    'url': request.url,
                    'method': request.method,
                    'resource_type': request.resource_type,
                    'headers': dict(request.headers)
                })

            async def handle_response(response):
                responses.append({
                    'url': response.url,
                    'status': response.status,
                    'headers': dict(response.headers),
                    'size': len(await response.body()) if response.status < 400 else 0
                })

            page.on('request', handle_request)
            page.on('response', handle_response)

            # 少し待機してリクエストを収集
            await asyncio.sleep(2)

            return {
                'total_requests': len(requests),
                'total_responses': len(responses),
                'failed_requests': len([r for r in responses if r['status'] >= 400]),
                'request_types': list(set([r['resource_type'] for r in requests])),
                'total_size': sum([r['size'] for r in responses]),
                'requests': requests[:10],  # 最初の10個のみ
                'responses': responses[:10]  # 最初の10個のみ
            }
        except Exception as e:
            debug_print(f"Error monitoring network: {e}")
            return {'error': str(e)}

    async def monitor_js_errors(self, page):
        """JavaScriptエラーを監視"""
        try:
            js_errors = []
            console_messages = []

            async def handle_console(msg):
                console_messages.append({
                    'type': msg.type,
                    'text': msg.text,
                    'location': msg.location
                })

            async def handle_page_error(error):
                js_errors.append({
                    'message': str(error),
                    'timestamp': datetime.now().isoformat()
                })

            page.on('console', handle_console)
            page.on('pageerror', handle_page_error)

            # 少し待機してエラーを収集
            await asyncio.sleep(1)

            return {
                'js_errors': js_errors,
                'console_messages': console_messages,
                'error_count': len(js_errors),
                'console_count': len(console_messages)
            }
        except Exception as e:
            debug_print(f"Error monitoring JS errors: {e}")
            return {'error': str(e)}

    async def check_element_visibility(self, page):
        """要素の可視性をチェック"""
        try:
            # 重要な要素の可視性をチェック
            visibility_checks = await page.evaluate("""
                () => {
                    const elements = {
                        'navigation': document.querySelector('nav, .navigation, .menu'),
                        'main_content': document.querySelector('main, .main, .content, #content'),
                        'footer': document.querySelector('footer, .footer'),
                        'header': document.querySelector('header, .header'),
                        'search': document.querySelector('input[type="search"], .search'),
                        'logo': document.querySelector('.logo, #logo, [alt*="logo"]')
                    };

                    const results = {};
                    for (const [name, element] of Object.entries(elements)) {
                        if (element) {
                            const rect = element.getBoundingClientRect();
                            const style = window.getComputedStyle(element);
                            results[name] = {
                                visible: rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none',
                                in_viewport: rect.top >= 0 && rect.left >= 0 && rect.bottom <= window.innerHeight && rect.right <= window.innerWidth,
                                dimensions: { width: rect.width, height: rect.height },
                                position: { top: rect.top, left: rect.left }
                            };
                        } else {
                            results[name] = { exists: false };
                        }
                    }
                    return results;
                }
            """)

            return visibility_checks
        except Exception as e:
            debug_print(f"Error checking visibility: {e}")
            return {'error': str(e)}

    async def test_form_interactions(self, page):
        """フォームとの相互作用をテスト"""
        try:
            forms = await page.query_selector_all('form')
            form_tests = []

            for i, form in enumerate(forms):
                # フォーム内の入力要素を取得
                inputs = await form.query_selector_all('input, textarea, select')

                form_data = {
                    'form_index': i,
                    'input_count': len(inputs),
                    'action': await form.get_attribute('action'),
                    'method': await form.get_attribute('method'),
                    'inputs': []
                }

                # 各入力要素をテスト
                for input_elem in inputs[:3]:  # 最初の3つのみテスト
                    input_type = await input_elem.get_attribute('type')
                    input_name = await input_elem.get_attribute('name')

                    if input_type in ['text', 'email', 'password']:
                        # テキスト入力をテスト
                        try:
                            await input_elem.fill('test_value')
                            value = await input_elem.input_value()
                            form_data['inputs'].append({
                                'type': input_type,
                                'name': input_name,
                                'fillable': True,
                                'test_value': value
                            })
                        except Exception:
                            form_data['inputs'].append({
                                'type': input_type,
                                'name': input_name,
                                'fillable': False
                            })

                form_tests.append(form_data)

            return {
                'total_forms': len(forms),
                'form_tests': form_tests
            }
        except Exception as e:
            debug_print(f"Error testing forms: {e}")
            return {'error': str(e)}

    async def test_mobile_viewport(self, page):
        """モバイルビューポートをテスト"""
        try:
            # 現在のビューポートを保存
            original_viewport = page.viewport_size

            # モバイルビューポートに変更
            await page.set_viewport_size({"width": 375, "height": 667})  # iPhone SE

            # モバイルビューでの要素の可視性をチェック
            mobile_visibility = await page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('nav, .navigation, .menu, .sidebar');
                    const results = [];

                    elements.forEach((element, index) => {
                        const rect = element.getBoundingClientRect();
                        const style = window.getComputedStyle(element);
                        results.push({
                            index: index,
                            visible: rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none',
                            in_viewport: rect.top >= 0 && rect.left >= 0 && rect.bottom <= window.innerHeight && rect.right <= window.innerWidth,
                            overflow: rect.right > window.innerWidth || rect.bottom > window.innerHeight
                        });
                    });

                    return {
                        viewport: { width: window.innerWidth, height: window.innerHeight },
                        elements: results,
                        has_horizontal_scroll: document.body.scrollWidth > window.innerWidth
                    };
                }
            """)

            # 元のビューポートに戻す
            await page.set_viewport_size(original_viewport)

            return {
                'mobile_test_completed': True,
                'mobile_viewport': mobile_visibility,
                'original_viewport': original_viewport
            }
        except Exception as e:
            debug_print(f"Error testing mobile viewport: {e}")
            return {'error': str(e)}

    async def get_dynamic_links(self, page):
        """動的に生成されたリンクを取得"""
        try:
            # JavaScriptで動的に生成されたリンクを取得
            links = await page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href]'));
                    return links
                        .map(link => link.href)
                        .filter(href => href.startsWith(window.location.origin))
                        .slice(0, 10);  // 最初の10個のみ
                }
            """)

            return links
        except Exception as e:
            debug_print(f"Error getting dynamic links: {e}")
            return []
`
  },
  {
    id: 'playwright-spa-spider',
    name: 'Playwright SPA Spider',
    description: 'SPA（Single Page Application）専用のPlaywrightスパイダー',
    icon: <Smartphone className="w-5 h-5" />,
    category: 'playwright',
    code: `import scrapy
from scrapy_playwright.page import PageMethod
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
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

class PlaywrightSPASpider(scrapy.Spider):
    name = 'playwright_spa_spider'
    allowed_domains = ['example-spa.com']
    start_urls = ['https://example-spa.com']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'args': ['--no-sandbox', '--disable-dev-shm-usage']
        },
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 60000,  # SPAは時間がかかる
        'PLAYWRIGHT_DEFAULT_TIMEOUT': 30000,
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 1,
        'CLOSESPIDER_PAGECOUNT': 15,
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        # SPAの初期ロードを待機
                        PageMethod("wait_for_load_state", "networkidle"),
                        # React/Vue/Angularアプリの準備完了を待機
                        PageMethod("wait_for_function", "() => window.React || window.Vue || window.ng || document.querySelector('[data-reactroot]') || document.querySelector('#app') || document.querySelector('.app')", timeout=30000),
                        # 動的コンテンツの読み込み完了を待機
                        PageMethod("wait_for_timeout", 3000),
                    ],
                }
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]

        debug_print(f"Processing SPA: {response.url}")

        # SPAフレームワークを検出
        framework_info = await self.detect_spa_framework(page)

        # 初期状態のデータを収集
        initial_data = await self.collect_initial_spa_data(page)

        # ルーティングをテスト
        routing_test = await self.test_spa_routing(page)

        # 動的コンテンツの読み込みをテスト
        dynamic_content = await self.test_dynamic_content_loading(page)

        # 状態管理をテスト
        state_management = await self.test_state_management(page)

        # APIコールを監視
        api_calls = await self.monitor_api_calls(page)

        # パフォーマンスメトリクスを収集
        performance_metrics = await self.collect_spa_performance(page)

        spa_data = {
            'url': response.url,
            'timestamp': datetime.now().isoformat(),
            'framework_info': framework_info,
            'initial_data': initial_data,
            'routing_test': routing_test,
            'dynamic_content': dynamic_content,
            'state_management': state_management,
            'api_calls': api_calls,
            'performance_metrics': performance_metrics
        }

        debug_print("SPA analysis complete:")
        debug_pprint(spa_data)

        yield spa_data

        await page.close()

    async def detect_spa_framework(self, page):
        """SPAフレームワークを検出"""
        try:
            framework_detection = await page.evaluate("""
                () => {
                    const frameworks = {
                        react: !!(window.React || document.querySelector('[data-reactroot]') || document.querySelector('[data-react-helmet]')),
                        vue: !!(window.Vue || document.querySelector('[data-v-]') || document.querySelector('#app')),
                        angular: !!(window.ng || window.angular || document.querySelector('[ng-app]') || document.querySelector('app-root')),
                        svelte: !!(window.svelte || document.querySelector('[data-svelte]')),
                        ember: !!(window.Ember || document.querySelector('.ember-application')),
                        backbone: !!(window.Backbone),
                        jquery: !!(window.jQuery || window.$)
                    };

                    const detected = Object.entries(frameworks)
                        .filter(([name, detected]) => detected)
                        .map(([name]) => name);

                    // バージョン情報を取得
                    const versions = {};
                    if (frameworks.react && window.React) {
                        versions.react = window.React.version;
                    }
                    if (frameworks.vue && window.Vue) {
                        versions.vue = window.Vue.version;
                    }
                    if (frameworks.angular && window.ng) {
                        versions.angular = window.ng.version?.full;
                    }
                    if (frameworks.jquery && window.jQuery) {
                        versions.jquery = window.jQuery.fn.jquery;
                    }

                    return {
                        detected_frameworks: detected,
                        versions: versions,
                        has_spa_indicators: detected.length > 0,
                        bundle_info: {
                            has_webpack: !!(window.webpackJsonp || window.__webpack_require__),
                            has_vite: !!(window.__vite__),
                            has_parcel: !!(window.parcelRequire)
                        }
                    };
                }
            """)

            return framework_detection
        except Exception as e:
            debug_print(f"Error detecting SPA framework: {e}")
            return {'error': str(e)}

    async def collect_initial_spa_data(self, page):
        """初期状態のSPAデータを収集"""
        try:
            initial_data = await page.evaluate("""
                () => {
                    // DOM要素の数を取得
                    const elementCounts = {
                        total_elements: document.querySelectorAll('*').length,
                        components: document.querySelectorAll('[class*="component"], [data-component]').length,
                        dynamic_elements: document.querySelectorAll('[data-bind], [v-], [ng-], [data-react]').length
                    };

                    // ルートコンテナを特定
                    const rootContainers = [
                        document.querySelector('#app'),
                        document.querySelector('#root'),
                        document.querySelector('[data-reactroot]'),
                        document.querySelector('.app'),
                        document.querySelector('app-root')
                    ].filter(el => el !== null);

                    // 初期ルートを取得
                    const currentRoute = {
                        pathname: window.location.pathname,
                        hash: window.location.hash,
                        search: window.location.search,
                        href: window.location.href
                    };

                    // グローバル状態を確認
                    const globalState = {
                        has_redux: !!(window.__REDUX_DEVTOOLS_EXTENSION__ || window.Redux),
                        has_vuex: !!(window.__VUE_DEVTOOLS_GLOBAL_HOOK__),
                        has_mobx: !!(window.__mobxDidRunLazyInitializers),
                        has_context_api: !!(window.React && window.React.createContext)
                    };

                    return {
                        element_counts: elementCounts,
                        root_containers: rootContainers.length,
                        current_route: currentRoute,
                        global_state: globalState,
                        page_title: document.title,
                        meta_tags: Array.from(document.querySelectorAll('meta')).length
                    };
                }
            """)

            return initial_data
        except Exception as e:
            debug_print(f"Error collecting initial SPA data: {e}")
            return {'error': str(e)}

    async def test_spa_routing(self, page):
        """SPAルーティングをテスト"""
        try:
            # ナビゲーションリンクを取得
            nav_links = await page.query_selector_all('a[href^="/"], a[href^="#"]')

            routing_tests = []
            original_url = page.url

            # 最初の3つのリンクをテスト
            for i, link in enumerate(nav_links[:3]):
                try:
                    href = await link.get_attribute('href')
                    if not href or href.startswith('http'):
                        continue

                    debug_print(f"Testing SPA route: {href}")

                    # リンクをクリック
                    await link.click()

                    # ルート変更を待機
                    await page.wait_for_timeout(2000)

                    # 新しいURLを確認
                    new_url = page.url

                    # ページタイトルの変更を確認
                    new_title = await page.title()

                    # コンテンツの変更を確認
                    content_changed = await page.evaluate("""
                        (originalUrl) => {
                            return window.location.href !== originalUrl;
                        }
                    """, original_url)

                    routing_tests.append({
                        'link_index': i,
                        'href': href,
                        'original_url': original_url,
                        'new_url': new_url,
                        'new_title': new_title,
                        'url_changed': new_url != original_url,
                        'content_changed': content_changed,
                        'is_spa_navigation': new_url != original_url and not await page.evaluate("() => window.location.reload")
                    })

                    # 元のページに戻る
                    await page.go_back()
                    await page.wait_for_timeout(1000)

                except Exception as e:
                    routing_tests.append({
                        'link_index': i,
                        'href': href,
                        'error': str(e)
                    })

            return {
                'total_nav_links': len(nav_links),
                'tested_routes': len(routing_tests),
                'routing_tests': routing_tests
            }
        except Exception as e:
            debug_print(f"Error testing SPA routing: {e}")
            return {'error': str(e)}

    async def test_dynamic_content_loading(self, page):
        """動的コンテンツの読み込みをテスト"""
        try:
            # 無限スクロールやLazy Loadingをテスト
            initial_content = await page.evaluate("() => document.body.innerHTML.length")

            # ページを下にスクロール
            await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)

            # 新しいコンテンツが読み込まれたかチェック
            after_scroll_content = await page.evaluate("() => document.body.innerHTML.length")

            # ボタンクリックで動的コンテンツを読み込むテスト
            load_more_buttons = await page.query_selector_all('button:has-text("Load"), button:has-text("More"), button:has-text("Show")')

            dynamic_loading_tests = []
            for i, button in enumerate(load_more_buttons[:2]):
                try:
                    before_click = await page.evaluate("() => document.querySelectorAll('*').length")
                    await button.click()
                    await page.wait_for_timeout(2000)
                    after_click = await page.evaluate("() => document.querySelectorAll('*').length")

                    dynamic_loading_tests.append({
                        'button_index': i,
                        'elements_before': before_click,
                        'elements_after': after_click,
                        'content_loaded': after_click > before_click
                    })
                except Exception as e:
                    dynamic_loading_tests.append({
                        'button_index': i,
                        'error': str(e)
                    })

            return {
                'initial_content_length': initial_content,
                'after_scroll_content_length': after_scroll_content,
                'scroll_loaded_content': after_scroll_content > initial_content,
                'load_more_buttons': len(load_more_buttons),
                'dynamic_loading_tests': dynamic_loading_tests
            }
        except Exception as e:
            debug_print(f"Error testing dynamic content: {e}")
            return {'error': str(e)}

    async def test_state_management(self, page):
        """状態管理をテスト"""
        try:
            state_info = await page.evaluate("""
                () => {
                    const stateManagement = {
                        redux: {
                            available: !!(window.__REDUX_DEVTOOLS_EXTENSION__ || window.Redux),
                            store_exists: !!(window.store || window.__REDUX_STORE__)
                        },
                        vuex: {
                            available: !!(window.__VUE_DEVTOOLS_GLOBAL_HOOK__),
                            store_exists: !!(window.$store)
                        },
                        mobx: {
                            available: !!(window.__mobxDidRunLazyInitializers),
                            observable_exists: !!(window.mobx)
                        },
                        context_api: {
                            available: !!(window.React && window.React.createContext)
                        }
                    };

                    // ローカルストレージとセッションストレージをチェック
                    const storage = {
                        localStorage_keys: Object.keys(localStorage).length,
                        sessionStorage_keys: Object.keys(sessionStorage).length,
                        localStorage_data: Object.keys(localStorage).slice(0, 5),  // 最初の5つのキー
                        sessionStorage_data: Object.keys(sessionStorage).slice(0, 5)
                    };

                    return {
                        state_management: stateManagement,
                        storage: storage
                    };
                }
            """)

            return state_info
        except Exception as e:
            debug_print(f"Error testing state management: {e}")
            return {'error': str(e)}

    async def monitor_api_calls(self, page):
        """APIコールを監視"""
        try:
            api_calls = []

            async def handle_response(response):
                if '/api/' in response.url or response.url.endswith('.json'):
                    try:
                        api_calls.append({
                            'url': response.url,
                            'method': response.request.method,
                            'status': response.status,
                            'content_type': response.headers.get('content-type', ''),
                            'size': len(await response.body()) if response.status < 400 else 0
                        })
                    except Exception:
                        pass

            page.on('response', handle_response)

            # ページ操作を実行してAPIコールを誘発
            await page.evaluate("() => window.scrollTo(0, 100)")
            await page.wait_for_timeout(3000)

            # フォームがあれば操作してみる
            forms = await page.query_selector_all('form')
            if forms:
                try:
                    first_form = forms[0]
                    inputs = await first_form.query_selector_all('input[type="text"], input[type="email"]')
                    if inputs:
                        await inputs[0].fill('test@example.com')
                        await page.wait_for_timeout(1000)
                except Exception:
                    pass

            return {
                'total_api_calls': len(api_calls),
                'api_calls': api_calls,
                'successful_calls': len([call for call in api_calls if call['status'] < 400]),
                'failed_calls': len([call for call in api_calls if call['status'] >= 400])
            }
        except Exception as e:
            debug_print(f"Error monitoring API calls: {e}")
            return {'error': str(e)}

    async def collect_spa_performance(self, page):
        """SPAパフォーマンスメトリクスを収集"""
        try:
            performance_data = await page.evaluate("""
                () => {
                    const perfData = performance.getEntriesByType('navigation')[0];
                    const paintEntries = performance.getEntriesByType('paint');
                    const resourceEntries = performance.getEntriesByType('resource');

                    // SPA特有のメトリクス
                    const spaMetrics = {
                        // 基本的なタイミング
                        time_to_interactive: perfData.domContentLoadedEventEnd - perfData.navigationStart,
                        first_paint: paintEntries.find(entry => entry.name === 'first-paint')?.startTime || 0,
                        first_contentful_paint: paintEntries.find(entry => entry.name === 'first-contentful-paint')?.startTime || 0,

                        // リソース分析
                        total_resources: resourceEntries.length,
                        js_resources: resourceEntries.filter(r => r.name.includes('.js')).length,
                        css_resources: resourceEntries.filter(r => r.name.includes('.css')).length,
                        image_resources: resourceEntries.filter(r => r.initiatorType === 'img').length,

                        // バンドルサイズ推定
                        js_transfer_size: resourceEntries
                            .filter(r => r.name.includes('.js'))
                            .reduce((sum, r) => sum + (r.transferSize || 0), 0),
                        css_transfer_size: resourceEntries
                            .filter(r => r.name.includes('.css'))
                            .reduce((sum, r) => sum + (r.transferSize || 0), 0),

                        // メモリ使用量
                        memory_usage: performance.memory ? {
                            used: performance.memory.usedJSHeapSize,
                            total: performance.memory.totalJSHeapSize,
                            limit: performance.memory.jsHeapSizeLimit
                        } : null,

                        // DOM複雑度
                        dom_elements: document.querySelectorAll('*').length,
                        dom_depth: Math.max(...Array.from(document.querySelectorAll('*')).map(el => {
                            let depth = 0;
                            let parent = el.parentElement;
                            while (parent) {
                                depth++;
                                parent = parent.parentElement;
                            }
                            return depth;
                        }))
                    };

                    return spaMetrics;
                }
            """)

            return performance_data
        except Exception as e:
            debug_print(f"Error collecting SPA performance: {e}")
            return {'error': str(e)}
`
  },
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

            # 関連商品
            related_products = []
            related_items = response.css('#similarities_feature_div .a-carousel-card')[:5]
            for item in related_items:
                related_title = item.css('.a-truncate-cut::text').get()
                related_url = item.css('a::attr(href)').get()
                if related_title and related_url:
                    related_products.append({
                        'title': related_title.strip(),
                        'url': response.urljoin(related_url)
                    })

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
                'related_products': related_products,
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
    id: 'amazon-ranking-spider',
    name: 'Amazon Ranking Spider',
    description: 'Amazonランキング情報を取得するスパイダー（教育用）',
    icon: <Trophy className="w-5 h-5" />,
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

class AmazonRankingSpider(scrapy.Spider):
    name = 'amazon_ranking_spider'
    allowed_domains = ['amazon.co.jp']
    start_urls = [
        'https://www.amazon.co.jp/gp/bestsellers/',  # ベストセラー
        'https://www.amazon.co.jp/gp/new-releases/', # 新着ランキング
        'https://www.amazon.co.jp/gp/movers-and-shakers/', # 急上昇
    ]

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 3,
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
        debug_print(f"Parsing Amazon ranking page: {response.url}")

        # ランキングタイプを判定
        ranking_type = self.determine_ranking_type(response.url)

        # カテゴリリストを取得
        categories = response.css('#zg_browseRoot .zg_browseUp a, .zg_browseRoot a')

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
        if 'bestsellers' in url:
            return 'bestsellers'
        elif 'new-releases' in url:
            return 'new_releases'
        elif 'movers-and-shakers' in url:
            return 'movers_shakers'
        else:
            return 'unknown'

    def parse_ranking_page(self, response, ranking_type=None, category_name=None):
        """ランキングページを解析"""
        if ranking_type is None:
            ranking_type = response.meta.get('ranking_type', 'unknown')
        if category_name is None:
            category_name = response.meta.get('category_name', 'unknown')

        debug_print(f"Parsing ranking: {ranking_type}, category: {category_name}")

        # ランキングアイテムを取得
        ranking_items = response.css('#zg-ordered-list .zg-item-immersion')

        debug_print(f"Found {len(ranking_items)} ranking items")

        for i, item in enumerate(ranking_items):
            try:
                # ランキング順位
                rank = item.css('.zg-badge-text::text').get()
                if rank:
                    rank = re.sub(r'[^0-9]', '', rank)
                    rank = int(rank) if rank.isdigit() else i + 1
                else:
                    rank = i + 1

                # 商品タイトル
                title = item.css('.p13n-sc-truncate::text').get()
                if not title:
                    title = item.css('a[title]::attr(title)').get()

                # 商品URL
                product_url = item.css('a::attr(href)').get()
                if product_url:
                    product_url = response.urljoin(product_url)

                # 価格情報
                price = item.css('.p13n-sc-price::text').get()

                # 評価情報
                rating = item.css('.a-icon-alt::text').get()
                review_count = item.css('.a-size-small a::text').get()

                # 商品画像
                image_url = item.css('img::attr(src)').get()

                # 著者・ブランド情報
                author_brand = item.css('.a-size-small.a-color-base::text').get()

                # ランキング変動情報（急上昇の場合）
                ranking_change = None
                if ranking_type == 'movers_shakers':
                    change_elem = item.css('.zg-percent-change::text').get()
                    if change_elem:
                        ranking_change = change_elem.strip()

                ranking_data = {
                    'rank': rank,
                    'title': title.strip() if title else None,
                    'url': product_url,
                    'price': price.strip() if price else None,
                    'rating': rating,
                    'review_count': review_count,
                    'image_url': image_url,
                    'author_brand': author_brand.strip() if author_brand else None,
                    'ranking_change': ranking_change,
                    'ranking_type': ranking_type,
                    'category_name': category_name,
                    'ranking_url': response.url,
                    'scraped_at': datetime.now().isoformat(),
                    'item_type': 'ranking_item'
                }

                debug_print(f"Rank {rank}: {title}")
                debug_pprint(ranking_data)

                yield ranking_data

            except Exception as e:
                debug_print(f"Error parsing ranking item {i}: {e}")
                continue

        # ページネーション
        next_page = response.css('.a-pagination .a-last a::attr(href)').get()
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
            'scraped_at': datetime.now().isoformat(),
            'item_type': 'category_info'
        }

        yield category_info
`
  },
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
  },
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
  },
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
        'CLOSESPIDER_PAGECOUNT': 30,
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
    id: 'yahoo-news-domestic-spider',
    name: 'Yahoo News Domestic Spider',
    description: 'Yahoo!ニュース国内カテゴリのニュースを取得するスパイダー',
    icon: <Rss className="w-5 h-5" />,
    category: 'news',
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

class YahooNewsDomesticSpider(scrapy.Spider):
    name = 'yahoo_news_domestic_spider'
    allowed_domains = ['news.yahoo.co.jp']
    start_urls = [
        'https://news.yahoo.co.jp/categories/domestic',  # 国内ニュース
    ]

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,  # 必ずrobotstxtを遵守
        'DOWNLOAD_DELAY': 1,     # ニュースサイトには適度な間隔
        'RANDOMIZE_DOWNLOAD_DELAY': 0.3,
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': 2,
        'USER_AGENT': 'ScrapyUI Educational News Bot 1.0 (Research Purpose)',
        'CLOSESPIDER_PAGECOUNT': 30,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        }
    }

    def parse(self, response):
        debug_print(f"Parsing Yahoo News Domestic page: {response.url}")
        debug_print(f"Status code: {response.status}")

        # カテゴリページの場合
        if '/categories/domestic' in response.url:
            yield from self.parse_category_page(response)
        # 記事詳細ページの場合
        elif '/articles/' in response.url:
            yield from self.parse_article_detail(response)
        else:
            debug_print("Unknown page type, extracting basic info")
            yield self.extract_basic_page_info(response)

    def parse_category_page(self, response):
        """国内ニュースカテゴリページを解析"""
        debug_print("Parsing Yahoo News Domestic category page")

        # ニュース記事アイテムを取得
        news_items = response.css('.newsFeed_item, .sc-gKsewC, .sc-iBPRYJ')

        debug_print(f"Found {len(news_items)} news items")

        for i, item in enumerate(news_items[:20]):  # 最初の20個のみ
            try:
                # 記事タイトル
                title = item.css('.newsFeed_item_title a::text').get()
                if not title:
                    title = item.css('a[data-cl-params*="title"]::text').get()
                if not title:
                    title = item.css('.sc-iBPRYJ a::text').get()

                # 記事URL
                article_url = item.css('.newsFeed_item_title a::attr(href)').get()
                if not article_url:
                    article_url = item.css('a[data-cl-params*="title"]::attr(href)').get()
                if not article_url:
                    article_url = item.css('.sc-iBPRYJ a::attr(href)').get()
                if article_url:
                    article_url = response.urljoin(article_url)

                # 記事の概要・リード文
                summary = item.css('.newsFeed_item_summary::text').get()
                if not summary:
                    summary = item.css('.sc-gKsewC p::text').get()

                # 配信元
                source = item.css('.newsFeed_item_media::text').get()
                if not source:
                    source = item.css('.sc-iBPRYJ .sc-fznyAO::text').get()

                # 配信時間
                publish_time = item.css('.newsFeed_item_date::text').get()
                if not publish_time:
                    publish_time = item.css('.sc-iBPRYJ time::text').get()
                if not publish_time:
                    publish_time = item.css('time::attr(datetime)').get()

                # 記事画像
                image_url = item.css('.newsFeed_item_thumbnail img::attr(src)').get()
                if not image_url:
                    image_url = item.css('img::attr(src)').get()

                # カテゴリタグ
                category_tags = item.css('.newsFeed_item_tag::text').getall()

                # コメント数
                comment_count = item.css('.newsFeed_item_comment::text').get()

                news_data = {
                    'item_index': i,
                    'title': title.strip() if title else None,
                    'url': article_url,
                    'summary': summary.strip() if summary else None,
                    'source': source.strip() if source else None,
                    'publish_time': publish_time.strip() if publish_time else None,
                    'image_url': image_url,
                    'category_tags': [tag.strip() for tag in category_tags if tag.strip()],
                    'comment_count': comment_count.strip() if comment_count else None,
                    'category': 'domestic',
                    'category_url': response.url,
                    'scraped_at': datetime.now().isoformat(),
                    'item_type': 'news_list',
                    'platform': 'yahoo_news'
                }

                debug_print(f"News {i+1}: {title}")
                debug_pprint(news_data)

                yield news_data

                # 記事詳細ページもクロール（最初の5個のみ）
                if article_url and i < 5:
                    yield response.follow(
                        article_url,
                        callback=self.parse_article_detail,
                        meta={'list_data': news_data}
                    )

            except Exception as e:
                debug_print(f"Error parsing news item {i}: {e}")
                continue

        # 次のページまたは追加読み込み
        next_page = response.css('.pagination .next::attr(href)').get()
        if next_page:
            debug_print(f"Found next page: {next_page}")
            yield response.follow(next_page, callback=self.parse_category_page)

    def parse_article_detail(self, response):
        """記事詳細ページを解析"""
        debug_print(f"Parsing Yahoo News article detail: {response.url}")

        try:
            # 記事タイトル
            title = response.css('h1::text').get()
            if not title:
                title = response.css('.sc-iBPRYJ h1::text').get()

            # 記事本文
            content_paragraphs = response.css('.sc-gKsewC p::text').getall()
            if not content_paragraphs:
                content_paragraphs = response.css('.article_body p::text').getall()
            content = ' '.join([p.strip() for p in content_paragraphs if p.strip()])

            # 配信元
            source = response.css('.sc-fznyAO::text').get()
            if not source:
                source = response.css('.article_header_source::text').get()

            # 配信時間
            publish_time = response.css('time::attr(datetime)').get()
            if not publish_time:
                publish_time = response.css('.article_header_time::text').get()

            # 記事画像
            main_image = response.css('.article_image img::attr(src)').get()
            if not main_image:
                main_image = response.css('.sc-gKsewC img::attr(src)').get()

            # 関連記事
            related_articles = []
            related_items = response.css('.related_articles .related_item')[:5]
            for item in related_items:
                related_title = item.css('a::text').get()
                related_url = item.css('a::attr(href)').get()
                if related_title and related_url:
                    related_articles.append({
                        'title': related_title.strip(),
                        'url': response.urljoin(related_url)
                    })

            # タグ・キーワード
            tags = response.css('.article_tags .tag::text').getall()

            # コメント数
            comment_count = response.css('.comment_count::text').get()

            # 記事の文字数
            content_length = len(content) if content else 0
            word_count = len(content.split()) if content else 0

            article_detail = {
                'url': response.url,
                'title': title.strip() if title else None,
                'content': content[:1000] if content else None,  # 最初の1000文字
                'content_length': content_length,
                'word_count': word_count,
                'source': source.strip() if source else None,
                'publish_time': publish_time.strip() if publish_time else None,
                'main_image': main_image,
                'related_articles': related_articles,
                'tags': [tag.strip() for tag in tags if tag.strip()],
                'comment_count': comment_count.strip() if comment_count else None,
                'category': 'domestic',
                'scraped_at': datetime.now().isoformat(),
                'item_type': 'article_detail',
                'platform': 'yahoo_news'
            }

            # リストからのメタデータがあれば追加
            list_data = response.meta.get('list_data')
            if list_data:
                article_detail['list_data'] = list_data

            debug_print(f"Article detail: {title}")
            debug_pprint(article_detail)

            yield article_detail

        except Exception as e:
            debug_print(f"Error parsing article detail: {e}")
            yield {
                'url': response.url,
                'error': str(e),
                'item_type': 'error',
                'category': 'domestic',
                'platform': 'yahoo_news',
                'scraped_at': datetime.now().isoformat()
            }

    def extract_basic_page_info(self, response):
        """基本的なページ情報を抽出"""
        return {
            'url': response.url,
            'title': response.css('title::text').get(),
            'status_code': response.status,
            'page_type': 'unknown',
            'category': 'domestic',
            'platform': 'yahoo_news',
            'scraped_at': datetime.now().isoformat(),
            'item_type': 'basic_info'
        }
`
  },
  {
    id: 'yahoo-news-international-spider',
    name: 'Yahoo News International Spider',
    description: 'Yahoo!ニュース国際カテゴリのニュースを取得するスパイダー',
    icon: <Globe className="w-5 h-5" />,
    category: 'news',
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

class YahooNewsInternationalSpider(scrapy.Spider):
    name = 'yahoo_news_international_spider'
    allowed_domains = ['news.yahoo.co.jp']
    start_urls = [
        'https://news.yahoo.co.jp/categories/world',  # 国際ニュース
    ]

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.3,
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': 2,
        'USER_AGENT': 'ScrapyUI Educational News Bot 1.0 (Research Purpose)',
        'CLOSESPIDER_PAGECOUNT': 30,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        }
    }

    def parse(self, response):
        debug_print(f"Parsing Yahoo News International page: {response.url}")
        debug_print(f"Status code: {response.status}")

        # カテゴリページの場合
        if '/categories/world' in response.url:
            yield from self.parse_category_page(response)
        # 記事詳細ページの場合
        elif '/articles/' in response.url:
            yield from self.parse_article_detail(response)
        else:
            debug_print("Unknown page type, extracting basic info")
            yield self.extract_basic_page_info(response)

    def parse_category_page(self, response):
        """国際ニュースカテゴリページを解析"""
        debug_print("Parsing Yahoo News International category page")

        # ニュース記事アイテムを取得
        news_items = response.css('.newsFeed_item, .sc-gKsewC, .sc-iBPRYJ')

        debug_print(f"Found {len(news_items)} international news items")

        for i, item in enumerate(news_items[:20]):  # 最初の20個のみ
            try:
                # 記事タイトル
                title = item.css('.newsFeed_item_title a::text').get()
                if not title:
                    title = item.css('a[data-cl-params*="title"]::text').get()
                if not title:
                    title = item.css('.sc-iBPRYJ a::text').get()

                # 記事URL
                article_url = item.css('.newsFeed_item_title a::attr(href)').get()
                if not article_url:
                    article_url = item.css('a[data-cl-params*="title"]::attr(href)').get()
                if not article_url:
                    article_url = item.css('.sc-iBPRYJ a::attr(href)').get()
                if article_url:
                    article_url = response.urljoin(article_url)

                # 記事の概要・リード文
                summary = item.css('.newsFeed_item_summary::text').get()
                if not summary:
                    summary = item.css('.sc-gKsewC p::text').get()

                # 配信元
                source = item.css('.newsFeed_item_media::text').get()
                if not source:
                    source = item.css('.sc-iBPRYJ .sc-fznyAO::text').get()

                # 配信時間
                publish_time = item.css('.newsFeed_item_date::text').get()
                if not publish_time:
                    publish_time = item.css('.sc-iBPRYJ time::text').get()
                if not publish_time:
                    publish_time = item.css('time::attr(datetime)').get()

                # 記事画像
                image_url = item.css('.newsFeed_item_thumbnail img::attr(src)').get()
                if not image_url:
                    image_url = item.css('img::attr(src)').get()

                # 地域・国タグ（国際ニュース特有）
                region_tags = item.css('.region_tag::text').getall()
                country_tags = item.css('.country_tag::text').getall()

                # 緊急度・重要度
                urgency = item.css('.urgency_tag::text').get()

                news_data = {
                    'item_index': i,
                    'title': title.strip() if title else None,
                    'url': article_url,
                    'summary': summary.strip() if summary else None,
                    'source': source.strip() if source else None,
                    'publish_time': publish_time.strip() if publish_time else None,
                    'image_url': image_url,
                    'region_tags': [tag.strip() for tag in region_tags if tag.strip()],
                    'country_tags': [tag.strip() for tag in country_tags if tag.strip()],
                    'urgency': urgency.strip() if urgency else None,
                    'category': 'international',
                    'category_url': response.url,
                    'scraped_at': datetime.now().isoformat(),
                    'item_type': 'news_list',
                    'platform': 'yahoo_news'
                }

                debug_print(f"International News {i+1}: {title}")
                debug_pprint(news_data)

                yield news_data

                # 記事詳細ページもクロール（最初の5個のみ）
                if article_url and i < 5:
                    yield response.follow(
                        article_url,
                        callback=self.parse_article_detail,
                        meta={'list_data': news_data}
                    )

            except Exception as e:
                debug_print(f"Error parsing international news item {i}: {e}")
                continue

        # 次のページまたは追加読み込み
        next_page = response.css('.pagination .next::attr(href)').get()
        if next_page:
            debug_print(f"Found next page: {next_page}")
            yield response.follow(next_page, callback=self.parse_category_page)

    def parse_article_detail(self, response):
        """国際ニュース記事詳細ページを解析"""
        debug_print(f"Parsing Yahoo News international article detail: {response.url}")

        try:
            # 記事タイトル
            title = response.css('h1::text').get()
            if not title:
                title = response.css('.sc-iBPRYJ h1::text').get()

            # 記事本文
            content_paragraphs = response.css('.sc-gKsewC p::text').getall()
            if not content_paragraphs:
                content_paragraphs = response.css('.article_body p::text').getall()
            content = ' '.join([p.strip() for p in content_paragraphs if p.strip()])

            # 配信元
            source = response.css('.sc-fznyAO::text').get()
            if not source:
                source = response.css('.article_header_source::text').get()

            # 配信時間
            publish_time = response.css('time::attr(datetime)').get()
            if not publish_time:
                publish_time = response.css('.article_header_time::text').get()

            # 記事画像
            main_image = response.css('.article_image img::attr(src)').get()
            if not main_image:
                main_image = response.css('.sc-gKsewC img::attr(src)').get()

            # 関連する国・地域情報
            related_countries = response.css('.related_countries .country::text').getall()
            related_regions = response.css('.related_regions .region::text').getall()

            # 関連記事
            related_articles = []
            related_items = response.css('.related_articles .related_item')[:5]
            for item in related_items:
                related_title = item.css('a::text').get()
                related_url = item.css('a::attr(href)').get()
                if related_title and related_url:
                    related_articles.append({
                        'title': related_title.strip(),
                        'url': response.urljoin(related_url)
                    })

            # 国際ニュース特有のタグ
            international_tags = response.css('.international_tags .tag::text').getall()

            # 記事の分析（国際ニュース特有）
            article_analysis = {
                'mentions_countries': len(related_countries),
                'mentions_regions': len(related_regions),
                'is_breaking_news': bool(response.css('.breaking_news').get()),
                'has_diplomatic_content': 'diplomatic' in content.lower() if content else False,
                'has_economic_content': any(word in content.lower() for word in ['economic', 'trade', 'economy'] if content else []),
                'has_conflict_content': any(word in content.lower() for word in ['war', 'conflict', 'military'] if content else [])
            }

            article_detail = {
                'url': response.url,
                'title': title.strip() if title else None,
                'content': content[:1000] if content else None,  # 最初の1000文字
                'content_length': len(content) if content else 0,
                'source': source.strip() if source else None,
                'publish_time': publish_time.strip() if publish_time else None,
                'main_image': main_image,
                'related_countries': related_countries,
                'related_regions': related_regions,
                'related_articles': related_articles,
                'international_tags': [tag.strip() for tag in international_tags if tag.strip()],
                'article_analysis': article_analysis,
                'category': 'international',
                'scraped_at': datetime.now().isoformat(),
                'item_type': 'article_detail',
                'platform': 'yahoo_news'
            }

            # リストからのメタデータがあれば追加
            list_data = response.meta.get('list_data')
            if list_data:
                article_detail['list_data'] = list_data

            debug_print(f"International article detail: {title}")
            debug_pprint(article_detail)

            yield article_detail

        except Exception as e:
            debug_print(f"Error parsing international article detail: {e}")
            yield {
                'url': response.url,
                'error': str(e),
                'item_type': 'error',
                'category': 'international',
                'platform': 'yahoo_news',
                'scraped_at': datetime.now().isoformat()
            }

    def extract_basic_page_info(self, response):
        """基本的なページ情報を抽出"""
        return {
            'url': response.url,
            'title': response.css('title::text').get(),
            'status_code': response.status,
            'page_type': 'unknown',
            'category': 'international',
            'platform': 'yahoo_news',
            'scraped_at': datetime.now().isoformat(),
            'item_type': 'basic_info'
        }
`
  }
]

export default function TemplateSelector({ onSelectTemplate, onClose }: TemplateSelectorProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  // ESCキーでモーダルを閉じる & ページスクロールを無効化
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    // ページのスクロールを無効化
    document.body.style.overflow = 'hidden'

    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('keydown', handleEscape)
      // ページのスクロールを復元
      document.body.style.overflow = 'unset'
    }
  }, [onClose])

  const categories = [
    { id: 'all', name: 'All Templates' },
    { id: 'basic', name: 'Basic' },
    { id: 'api', name: 'API' },
    { id: 'data', name: 'Data Extraction' },
    { id: 'ecommerce', name: 'E-commerce' },
    { id: 'news', name: 'News' },
    { id: 'social', name: 'Social Media' },
    { id: 'monitoring', name: 'Monitoring' },
    { id: 'security', name: 'Security' },
    { id: 'performance', name: 'Performance' },
    { id: 'testing', name: 'Testing' },
    { id: 'automation', name: 'Automation' },
    { id: 'integration', name: 'Integration' },
    { id: 'mobile', name: 'Mobile' },
    { id: 'media', name: 'Media' },
    { id: 'finance', name: 'Finance' },
    { id: 'travel', name: 'Travel' },
    { id: 'food', name: 'Food' },
    { id: 'real-estate', name: 'Real Estate' },
    { id: 'job', name: 'Job Boards' },
    { id: 'education', name: 'Education' },
    { id: 'health', name: 'Health' },
    { id: 'sports', name: 'Sports' },
    { id: 'gaming', name: 'Gaming' },
    { id: 'weather', name: 'Weather' },
    { id: 'government', name: 'Government' },
    { id: 'legal', name: 'Legal' },
    { id: 'nonprofit', name: 'Non-profit' },
    { id: 'playwright', name: 'Playwright' },
    { id: 'advanced', name: 'Advanced' }
  ]

  const filteredTemplates = selectedCategory === 'all'
    ? templates
    : templates.filter(template => template.category === selectedCategory)

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[80vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Choose a Template
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              ✕
            </button>
          </div>

          {/* カテゴリフィルター */}
          <div className="mt-4 flex flex-wrap gap-2">
            {categories.map(category => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`px-3 py-1 rounded-full text-sm transition-colors ${
                  selectedCategory === category.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                }`}
              >
                {category.name}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6 overflow-y-auto max-h-[60vh]">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredTemplates.map(template => (
              <div
                key={template.id}
                onClick={() => onSelectTemplate(template)}
                className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-500 dark:hover:border-blue-400 cursor-pointer transition-colors group"
              >
                <div className="flex items-start space-x-3">
                  <div className="text-blue-600 dark:text-blue-400 group-hover:text-blue-700 dark:group-hover:text-blue-300">
                    {template.icon}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400">
                      {template.name}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {template.description}
                    </p>
                    <div className="mt-2">
                      <span className="inline-block px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                        {template.category}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
