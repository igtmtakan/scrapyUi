import scrapy
from scrapy_playwright.page import PageMethod


class LplplpSpider(scrapy.Spider):
    name = 'lplplp'
    
    start_urls = [
        'http://www.yahoo.co.jp'
    ]

    # Scrapy-Playwright設定
    custom_settings = {
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
            "args": ["--no-sandbox", "--disable-setuid-sandbox"],
        },
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "body"),
                        PageMethod("wait_for_timeout", 1000),
                    ],
                },
                callback=self.parse
            )

    def parse(self, response):
        # Extract data from the page
        yield {
            'url': response.url,
            'title': response.css('title::text').get(),
            # Add more fields as needed
        }

        # Follow links to next pages
        for link in response.css('a::attr(href)').getall():
            yield response.follow(link, self.parse)
