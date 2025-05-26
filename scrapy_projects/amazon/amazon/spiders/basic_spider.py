import scrapy
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
    allowed_domains = ['quotes.toscrape.com']

    # 軽量で安全な設定
    custom_settings = {
        'DOWNLOAD_HANDLERS': {},  # Playwrightハンドラーを無効化
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'ScrapyUI Educational Bot 1.0'
    }

    start_urls = [
        'https://quotes.toscrape.com/',
        'https://quotes.toscrape.com/page/2/'
    ]

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
                'tags': tags
            }

            debug_print(f"Extracted quote by {author}")
            debug_pprint(data)

            yield data

        # 次のページへのリンクを取得
        next_page = response.css('li.next a::attr(href)').get()
        if next_page:
            debug_print(f"Following next page: {next_page}")
            yield response.follow(next_page, self.parse)
