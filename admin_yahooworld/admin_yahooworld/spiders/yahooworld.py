import scrapy
from urllib.parse import urljoin
import re
from datetime import datetime

class YahooworldSpider(scrapy.Spider):
    name = 'yahooworld'
    allowed_domains = ['news.yahoo.co.jp']
    start_urls = [
        'https://news.yahoo.co.jp/categories/world'
    ]

    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.3,
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': 2,
        'USER_AGENT': 'ScrapyUI Educational News Bot 1.0 (Research Purpose)',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        },
        'FEEDS': {
            'yahoo_world_news.jsonl': {
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

    def parse(self, response):
        """Yahoo国際ニュースページを解析"""
        self.logger.info(f"Parsing Yahoo World News page: {response.url}")

        # ニュース記事のセレクター
        news_selectors = [
            '.newsFeed_item',
            '.sc-gKsewC',
            '.sc-iBPRYJ',
            'article',
            '.topicsListItem',
        ]

        news_items = []
        for selector in news_selectors:
            items = response.css(selector)
            if items:
                self.logger.info(f"Found {len(items)} news items with selector: {selector}")
                news_items = items
                break

        if not news_items:
            self.logger.warning("No news items found with any selector")
            return

        for i, item in enumerate(news_items[:20]):  # 最大20件
            try:
                # タイトル
                title_selectors = [
                    'a::text',
                    '.newsFeed_item_title::text',
                    '.sc-fznyAO::text',
                    'h3::text',
                    'h2::text',
                ]
                
                title = None
                for title_sel in title_selectors:
                    title = item.css(title_sel).get()
                    if title:
                        title = title.strip()
                        break

                # リンク
                link_selectors = [
                    'a::attr(href)',
                    '.newsFeed_item_link::attr(href)',
                ]
                
                link = None
                for link_sel in link_selectors:
                    link = item.css(link_sel).get()
                    if link:
                        break

                if link:
                    link = urljoin(response.url, link)

                # 時間
                time_selectors = [
                    'time::text',
                    '.newsFeed_item_date::text',
                    '.sc-fznWqX::text',
                ]
                
                published_time = None
                for time_sel in time_selectors:
                    published_time = item.css(time_sel).get()
                    if published_time:
                        published_time = published_time.strip()
                        break

                # 概要
                summary_selectors = [
                    '.newsFeed_item_summary::text',
                    '.sc-fzpjYC::text',
                    'p::text',
                ]
                
                summary = None
                for summary_sel in summary_selectors:
                    summary = item.css(summary_sel).get()
                    if summary:
                        summary = summary.strip()
                        break

                if title:
                    news_data = {
                        'title': title,
                        'link': link,
                        'published_time': published_time,
                        'summary': summary,
                        'source': 'Yahoo News World',
                        'category': 'international',
                        'scraped_at': datetime.now().isoformat(),
                        'crawl_start_datetime': self.crawl_start_datetime,
                        'position': i + 1,
                        'source_url': response.url,
                    }

                    self.logger.info(f"News {i+1}: {title}")
                    yield news_data
                    self.items_scraped += 1

                    # 詳細ページも取得（オプション）
                    if link and 'yahoo.co.jp' in link:
                        yield scrapy.Request(
                            link,
                            callback=self.parse_article,
                            meta={'news_data': news_data},
                            dont_filter=True
                        )

            except Exception as e:
                self.logger.error(f"Error parsing news item {i}: {e}")

    def parse_article(self, response):
        """ニュース記事詳細を解析"""
        news_data = response.meta.get('news_data', {})
        
        try:
            # 記事本文
            content_selectors = [
                '.sc-dRFtgE p::text',
                '.article_body p::text',
                '.ynDetailText p::text',
                'p::text',
            ]
            
            content_parts = []
            for content_sel in content_selectors:
                parts = response.css(content_sel).getall()
                if parts:
                    content_parts = [p.strip() for p in parts if p.strip()]
                    break

            content = ' '.join(content_parts) if content_parts else None

            # 記事画像
            image_selectors = [
                '.article_image img::attr(src)',
                '.ynDetailPhoto img::attr(src)',
                'img::attr(src)',
            ]
            
            image_url = None
            for img_sel in image_selectors:
                image_url = response.css(img_sel).get()
                if image_url:
                    break

            # 詳細データ
            detailed_data = {
                **news_data,
                'content': content,
                'image_url': image_url,
                'detail_scraped_at': datetime.now().isoformat(),
                'item_type': 'detailed_article'
            }

            self.logger.info(f"Detailed article: {news_data.get('title', 'Unknown')}")
            yield detailed_data

        except Exception as e:
            self.logger.error(f"Error parsing article detail: {e}")
            error_data = {
                **news_data,
                'error': str(e),
                'item_type': 'article_error',
                'error_scraped_at': datetime.now().isoformat()
            }
            yield error_data

    def closed(self, reason):
        """スパイダー終了時の処理"""
        self.logger.info(f"Yahoo World News spider closed. Reason: {reason}")
        self.logger.info(f"Total items scraped: {self.items_scraped}")
