import React from 'react'
import { Rss, Globe, TrendingUp, Gamepad2, Activity } from 'lucide-react'
import { Template } from '../types'

export const yahooNewsTemplates: Template[] = [
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
  },
  {
    id: 'yahoo-news-economy-spider',
    name: 'Yahoo News Economy Spider',
    description: 'Yahoo!ニュース経済カテゴリのニュースを取得するスパイダー',
    icon: <TrendingUp className="w-5 h-5" />,
    category: 'news',
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

class YahooNewsEconomySpider(scrapy.Spider):
    name = 'yahoo_news_economy_spider'
    allowed_domains = ['news.yahoo.co.jp']
    start_urls = [
        'https://news.yahoo.co.jp/categories/business',  # 経済ニュース
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
        debug_print(f"Parsing Yahoo News Economy page: {response.url}")

        # 経済ニュース特有の要素を解析
        news_items = response.css('.newsFeed_item, .sc-gKsewC, .sc-iBPRYJ')

        for i, item in enumerate(news_items[:20]):
            try:
                title = item.css('.newsFeed_item_title a::text').get()
                article_url = item.css('.newsFeed_item_title a::attr(href)').get()
                summary = item.css('.newsFeed_item_summary::text').get()
                source = item.css('.newsFeed_item_media::text').get()
                publish_time = item.css('.newsFeed_item_date::text').get()

                # 経済ニュース特有の要素
                stock_info = item.css('.stock_info::text').get()
                market_data = item.css('.market_data::text').get()
                company_name = item.css('.company_name::text').get()

                # 経済指標の抽出
                economic_indicators = self.extract_economic_indicators(title, summary)

                news_data = {
                    'item_index': i,
                    'title': title.strip() if title else None,
                    'url': response.urljoin(article_url) if article_url else None,
                    'summary': summary.strip() if summary else None,
                    'source': source.strip() if source else None,
                    'publish_time': publish_time.strip() if publish_time else None,
                    'stock_info': stock_info.strip() if stock_info else None,
                    'market_data': market_data.strip() if market_data else None,
                    'company_name': company_name.strip() if company_name else None,
                    'economic_indicators': economic_indicators,
                    'category': 'economy',
                    'category_url': response.url,
                    'scraped_at': datetime.now().isoformat(),
                    'item_type': 'news_list',
                    'platform': 'yahoo_news'
                }

                debug_print(f"Economy News {i+1}: {title}")
                debug_pprint(news_data)

                yield news_data

            except Exception as e:
                debug_print(f"Error parsing economy news item {i}: {e}")
                continue

    def extract_economic_indicators(self, title, summary):
        """経済指標を抽出"""
        indicators = {}
        text = f"{title or ''} {summary or ''}"

        # 株価関連
        stock_match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?)円', text)
        if stock_match:
            indicators['stock_price'] = stock_match.group(1)

        # パーセンテージ
        percent_match = re.search(r'(\d+(?:\.\d+)?)%', text)
        if percent_match:
            indicators['percentage'] = percent_match.group(1)

        # 企業名
        company_patterns = ['株式会社', '(株)', 'ホールディングス', 'HD']
        for pattern in company_patterns:
            if pattern in text:
                indicators['has_company_info'] = True
                break

        return indicators
`
  },
  {
    id: 'yahoo-news-sports-spider',
    name: 'Yahoo News Sports Spider',
    description: 'Yahoo!ニューススポーツカテゴリのニュースを取得するスパイダー',
    icon: <Activity className="w-5 h-5" />,
    category: 'news',
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

class YahooNewsSportsSpider(scrapy.Spider):
    name = 'yahoo_news_sports_spider'
    allowed_domains = ['news.yahoo.co.jp']
    start_urls = [
        'https://news.yahoo.co.jp/categories/sports',  # スポーツニュース
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
        debug_print(f"Parsing Yahoo News Sports page: {response.url}")

        # スポーツニュース特有の要素を解析
        news_items = response.css('.newsFeed_item, .sc-gKsewC, .sc-iBPRYJ')

        for i, item in enumerate(news_items[:20]):
            try:
                title = item.css('.newsFeed_item_title a::text').get()
                article_url = item.css('.newsFeed_item_title a::attr(href)').get()
                summary = item.css('.newsFeed_item_summary::text').get()
                source = item.css('.newsFeed_item_media::text').get()
                publish_time = item.css('.newsFeed_item_date::text').get()

                # スポーツ特有の要素
                sport_type = item.css('.sport_type::text').get()
                team_names = item.css('.team_name::text').getall()
                score_info = item.css('.score::text').get()

                # スポーツ情報の抽出
                sports_data = self.extract_sports_info(title, summary)

                news_data = {
                    'item_index': i,
                    'title': title.strip() if title else None,
                    'url': response.urljoin(article_url) if article_url else None,
                    'summary': summary.strip() if summary else None,
                    'source': source.strip() if source else None,
                    'publish_time': publish_time.strip() if publish_time else None,
                    'sport_type': sport_type.strip() if sport_type else None,
                    'team_names': [team.strip() for team in team_names if team.strip()],
                    'score_info': score_info.strip() if score_info else None,
                    'sports_data': sports_data,
                    'category': 'sports',
                    'category_url': response.url,
                    'scraped_at': datetime.now().isoformat(),
                    'item_type': 'news_list',
                    'platform': 'yahoo_news'
                }

                debug_print(f"Sports News {i+1}: {title}")
                debug_pprint(news_data)

                yield news_data

            except Exception as e:
                debug_print(f"Error parsing sports news item {i}: {e}")
                continue

    def extract_sports_info(self, title, summary):
        """スポーツ情報を抽出"""
        sports_info = {}
        text = f"{title or ''} {summary or ''}"

        # スコア情報
        score_match = re.search(r'(\d+)-(\d+)', text)
        if score_match:
            sports_info['score'] = f"{score_match.group(1)}-{score_match.group(2)}"

        # 順位情報
        rank_match = re.search(r'(\d+)位', text)
        if rank_match:
            sports_info['rank'] = rank_match.group(1)

        # スポーツ種目の判定
        sports_keywords = {
            'baseball': ['野球', 'プロ野球', 'MLB', 'WBC'],
            'soccer': ['サッカー', 'Jリーグ', 'ワールドカップ'],
            'basketball': ['バスケ', 'NBA', 'Bリーグ'],
            'tennis': ['テニス', 'ウィンブルドン', '全豪オープン'],
            'golf': ['ゴルフ', 'マスターズ', 'PGA'],
            'olympics': ['オリンピック', '五輪']
        }

        for sport, keywords in sports_keywords.items():
            if any(keyword in text for keyword in keywords):
                sports_info['sport_category'] = sport
                break

        return sports_info
`
  },
  {
    id: 'yahoo-news-entertainment-spider',
    name: 'Yahoo News Entertainment Spider',
    description: 'Yahoo!ニュースエンタメカテゴリのニュースを取得するスパイダー',
    icon: <Gamepad2 className="w-5 h-5" />,
    category: 'news',
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

class YahooNewsEntertainmentSpider(scrapy.Spider):
    name = 'yahoo_news_entertainment_spider'
    allowed_domains = ['news.yahoo.co.jp']
    start_urls = [
        'https://news.yahoo.co.jp/categories/entertainment',  # エンタメニュース
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
        debug_print(f"Parsing Yahoo News Entertainment page: {response.url}")

        # エンタメニュース特有の要素を解析
        news_items = response.css('.newsFeed_item, .sc-gKsewC, .sc-iBPRYJ')

        for i, item in enumerate(news_items[:20]):
            try:
                title = item.css('.newsFeed_item_title a::text').get()
                article_url = item.css('.newsFeed_item_title a::attr(href)').get()
                summary = item.css('.newsFeed_item_summary::text').get()
                source = item.css('.newsFeed_item_media::text').get()
                publish_time = item.css('.newsFeed_item_date::text').get()

                # エンタメ特有の要素
                celebrity_names = item.css('.celebrity_name::text').getall()
                genre_tags = item.css('.genre_tag::text').getall()

                # エンタメ情報の抽出
                entertainment_data = self.extract_entertainment_info(title, summary)

                news_data = {
                    'item_index': i,
                    'title': title.strip() if title else None,
                    'url': response.urljoin(article_url) if article_url else None,
                    'summary': summary.strip() if summary else None,
                    'source': source.strip() if source else None,
                    'publish_time': publish_time.strip() if publish_time else None,
                    'celebrity_names': [name.strip() for name in celebrity_names if name.strip()],
                    'genre_tags': [tag.strip() for tag in genre_tags if tag.strip()],
                    'entertainment_data': entertainment_data,
                    'category': 'entertainment',
                    'category_url': response.url,
                    'scraped_at': datetime.now().isoformat(),
                    'item_type': 'news_list',
                    'platform': 'yahoo_news'
                }

                debug_print(f"Entertainment News {i+1}: {title}")
                debug_pprint(news_data)

                yield news_data

            except Exception as e:
                debug_print(f"Error parsing entertainment news item {i}: {e}")
                continue

    def extract_entertainment_info(self, title, summary):
        """エンタメ情報を抽出"""
        entertainment_info = {}
        text = f"{title or ''} {summary or ''}"

        # エンタメジャンルの判定
        entertainment_keywords = {
            'music': ['音楽', 'アルバム', 'シングル', 'ライブ', 'コンサート'],
            'movie': ['映画', '劇場版', '公開', '上映'],
            'tv': ['テレビ', 'ドラマ', '番組', '放送'],
            'anime': ['アニメ', 'アニメーション', '声優'],
            'game': ['ゲーム', 'ゲーム機', 'プレイステーション', 'Nintendo'],
            'celebrity': ['芸能人', 'タレント', '俳優', '女優', 'アイドル']
        }

        for genre, keywords in entertainment_keywords.items():
            if any(keyword in text for keyword in keywords):
                entertainment_info['entertainment_genre'] = genre
                break

        # 年齢情報の抽出
        age_match = re.search(r'(\d+)歳', text)
        if age_match:
            entertainment_info['age_mentioned'] = age_match.group(1)

        # 日付情報の抽出
        date_match = re.search(r'(\d+)月(\d+)日', text)
        if date_match:
            entertainment_info['event_date'] = f"{date_match.group(1)}月{date_match.group(2)}日"

        return entertainment_info
`
  }
]
