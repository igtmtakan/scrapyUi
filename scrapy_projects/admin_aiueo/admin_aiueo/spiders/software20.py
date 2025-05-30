import scrapy
from scrapy_playwright.page import PageMethod


class Software20Spider(scrapy.Spider):
    name = "software20"
    allowed_domains = ["amazon.co.jp"]
    start_urls = ["https://www.amazon.co.jp/gp/bestsellers/software/ref=zg_bs_nav_software_0"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                        PageMethod("wait_for_timeout", 3000),
                    ],
                },
                callback=self.parse
            )

    def parse(self, response):
        # Extract product links with class="a-link-normal aok-block"
        product_links = response.css("a.a-link-normal.aok-block::attr(href)").getall()

        for link in product_links:
            if link:
                full_url = response.urljoin(link)
                yield scrapy.Request(
                    url=full_url,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_load_state", "domcontentloaded"),
                            PageMethod("wait_for_timeout", 2000),
                        ],
                    },
                    callback=self.parse_product
                )

        # Follow pagination links recursively
        next_page_links = response.css('a[href*="pg="]:contains("次")::attr(href)').getall()
        if not next_page_links:
            next_page_links = response.css('a[href*="pg="]::attr(href)').getall()

        for next_link in next_page_links:
            if next_link:
                next_url = response.urljoin(next_link)
                yield scrapy.Request(
                    url=next_url,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_load_state", "domcontentloaded"),
                            PageMethod("wait_for_timeout", 3000),
                        ],
                    },
                    callback=self.parse
                )

    def parse_product(self, response):
        # Extract product information
        title = response.css("#title::text").get()
        if title:
            title = title.strip()

        # Extract rating
        rating = response.css(".a-icon-alt::text").re_first(r"5つ星のうち([0-9.]+)")

        # Extract price (tax included)
        price = response.css(".a-price .a-offscreen::text").get()
        if not price:
            price = response.css(".a-price-whole::text").get()

        # Extract reviews count
        reviews = response.css('[data-hook="total-review-count"]::text').get()
        if not reviews:
            reviews = response.css(".a-size-base::text").re_first(r"([0-9,]+).*件のカスタマーレビュー")

        # Extract image URL
        image_url = response.css("img.a-dynamic-image.a-stretch-vertical::attr(src)").get()

        yield {
            "title": title,
            "rating": rating,
            "price": price,
            "reviews": reviews,
            "image_url": image_url,
            "product_url": response.url
        }
