import scrapy
from scrapy import Request
import re


class Omocha9Spider(scrapy.Spider):
    name = "omocha9"
    allowed_domains = ['amazon.co.jp']
    start_urls = [
        'https://www.amazon.co.jp/gp/bestsellers/toys/ref=zg_bs_nav_toys_0'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items_count = 0
        self.requests_count = 0
        self.pages_count = 0

    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'COOKIES_ENABLED': True,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'HTTPCACHE_ENABLED': True,
        'HTTPCACHE_DIR': 'httpcache',
        'HTTPCACHE_EXPIRATION_SECS': 86400,
        'FEED_EXPORT_ENCODING': 'utf-8',
        # 安全のためのデフォルト制限（コマンドラインで上書き可能）
        # 'CLOSESPIDER_PAGECOUNT': 20,  # ページ制限を無効化
        'CLOSESPIDER_TIMEOUT': 3600,  # 60分でタイムアウト
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache',
        }
    }

    def start_requests(self):
        """リクエスト開始"""
        self.logger.info("🚀 Starting omocha9 spider - Unlimited mode (no item limit)")

        # 通常のstart_requestsを実行
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)



    def parse(self, response):
        """おもちゃベストセラーページの解析"""
        self.logger.info(f'Processing page: {response.url}')

        # ページ数とリクエスト数を更新
        self.pages_count += 1
        self.requests_count += 1
        self.logger.info(f'📊 Progress: Pages: {self.pages_count}, Requests: {self.requests_count}, Items: {self.items_count}')

        # Playwrightが使用されているかチェック
        if response.meta.get('playwright'):
            self.logger.info(f'📜 Processing Playwright-rendered page with scroll')
            # スクロール後のページ処理
            yield from self.parse_after_scroll(response)
        else:
            # 通常のHTTPレスポンスの場合、Playwrightでスクロール処理を行う
            self.logger.info(f'🔄 Requesting page with scroll using Playwright...')
            yield Request(
                url=response.url,
                callback=self.parse,
                dont_filter=True,  # 重複フィルターを無効化
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        {'method': 'wait_for_load_state', 'args': ['domcontentloaded']},
                        {'method': 'evaluate', 'args': ['''
                            () => {
                                // 段階的にスクロールして遅延読み込みコンテンツを取得
                                return new Promise((resolve) => {
                                    let totalHeight = 0;
                                    let distance = 100;
                                    let timer = setInterval(() => {
                                        let scrollHeight = document.body.scrollHeight;
                                        window.scrollBy(0, distance);
                                        totalHeight += distance;

                                        if(totalHeight >= scrollHeight){
                                            clearInterval(timer);
                                            // 最下部まで確実にスクロール
                                            window.scrollTo(0, document.body.scrollHeight);
                                            setTimeout(() => {
                                                resolve({
                                                    finalHeight: document.body.scrollHeight,
                                                    scrollCompleted: true
                                                });
                                            }, 1000);
                                        }
                                    }, 100);
                                });
                            }
                        ''']},
                        {'method': 'wait_for_timeout', 'args': [3000]}  # 追加の待機時間
                    ],
                    'page_url': response.url,
                    'page_number': self.pages_count
                }
            )

    def parse_after_scroll(self, response):
        """スクロール後のページ解析"""
        page_number = response.meta.get('page_number', self.pages_count)
        self.logger.info(f'📄 Processing scrolled page {page_number}: {response.url}')

        # スクロール後の商品リンクを取得 (複数のセレクターを試行)
        product_links = []

        # セレクター1: 従来のセレクター
        links1 = response.css('a.a-link-normal.aok-block::attr(href)').getall()
        product_links.extend(links1)

        # セレクター2: ベストセラーページの新しい構造
        links2 = response.css('div[data-component-type="s-search-result"] h3 a::attr(href)').getall()
        product_links.extend(links2)

        # セレクター3: 一般的な商品リンク
        links3 = response.css('a[href*="/dp/"]::attr(href)').getall()
        product_links.extend(links3)

        # セレクター4: ベストセラーランキング用
        links4 = response.css('div.zg-item-immersion a::attr(href)').getall()
        product_links.extend(links4)

        # セレクター5: 新しいAmazonベストセラー構造
        links5 = response.css('div.zg-grid-general-faceout a::attr(href)').getall()
        product_links.extend(links5)

        # セレクター6: ランキングアイテム
        links6 = response.css('span.zg-item a::attr(href)').getall()
        product_links.extend(links6)

        # セレクター7: 商品カード
        links7 = response.css('div[data-asin] h3 a::attr(href)').getall()
        product_links.extend(links7)

        # セレクター8: より広範囲なASIN商品
        links8 = response.css('div[data-asin] a::attr(href)').getall()
        product_links.extend(links8)

        # セレクター9: ベストセラーアイテム
        links9 = response.css('div.zg-item a::attr(href)').getall()
        product_links.extend(links9)

        # セレクター10: 全ての商品リンク（より包括的）
        links10 = response.css('a[href*="amazon.co.jp"][href*="/dp/"]::attr(href)').getall()
        product_links.extend(links10)

        # セレクター11: スクロール後に表示される可能性のある追加商品
        links11 = response.css('div.s-result-item a[href*="/dp/"]::attr(href)').getall()
        product_links.extend(links11)

        # セレクター12: 遅延読み込みされた商品
        links12 = response.css('div[data-component-type] a[href*="/dp/"]::attr(href)').getall()
        product_links.extend(links12)

        # 重複を削除
        product_links = list(set(product_links))

        # 商品ページのリンクのみをフィルタリング
        filtered_links = []
        for link in product_links:
            if link and '/dp/' in link:
                filtered_links.append(link)

        product_links = filtered_links  # 制限を撤廃して全ての商品リンクを処理

        self.logger.info(f'🔍 Found {len(product_links)} unique product links on scrolled page {page_number}')
        self.logger.info(f'📝 Sample links: {product_links[:3]}')

        # セレクター別の結果をログ出力（スクロール後）
        self.logger.debug(f'Scroll Selector results - Links1: {len(links1)}, Links2: {len(links2)}, Links3: {len(links3)}, Links4: {len(links4)}, Links5: {len(links5)}, Links6: {len(links6)}, Links7: {len(links7)}, Links8: {len(links8)}, Links9: {len(links9)}, Links10: {len(links10)}, Links11: {len(links11)}, Links12: {len(links12)}')

        # スクロール効果の確認
        total_before_scroll = len(links1) + len(links2) + len(links3) + len(links4) + len(links5) + len(links6) + len(links7) + len(links8) + len(links9) + len(links10)
        total_after_scroll = len(links11) + len(links12)
        self.logger.info(f'📊 Scroll impact: Before scroll selectors: {total_before_scroll}, After scroll selectors: {total_after_scroll}, Total unique: {len(product_links)}')

        # デバッグ: ページ内容を確認
        if len(product_links) == 0:
            self.logger.warning("No product links found. Debugging page content...")
            # ページタイトルを確認
            page_title = response.css('title::text').get()
            self.logger.debug(f'Page title: {page_title}')

            # 全てのリンクを確認
            all_links = response.css('a::attr(href)').getall()
            dp_links = [link for link in all_links if link and '/dp/' in link]
            self.logger.debug(f'Total links: {len(all_links)}, DP links: {len(dp_links)}')

            # ページの主要な要素を確認
            main_content = response.css('body').get()
            if main_content and len(main_content) < 1000:
                self.logger.warning("Page content seems too small, possible blocking or redirect")

            # デバッグ用にページ内容をファイルに保存
            try:
                with open('debug_page.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                self.logger.info("Page content saved to debug_page.html for inspection")
            except Exception as e:
                self.logger.warning(f"Failed to save debug page: {e}")

            # 可能性のあるセレクターをテスト
            test_selectors = [
                'div.zg-item-immersion',
                'div[data-component-type="s-search-result"]',
                'div.s-result-item',
                'div.a-section.a-spacing-none',
                'span.zg-item'
            ]
            for selector in test_selectors:
                elements = response.css(selector)
                self.logger.debug(f'Selector "{selector}": {len(elements)} elements found')

        # 各商品ページを処理（スクロール後）
        self.logger.info(f'🚀 Processing {len(product_links)} product links from scrolled page {page_number}')
        for i, link in enumerate(product_links, 1):
            if link:
                # 相対URLを絶対URLに変換
                full_url = response.urljoin(link)
                self.logger.debug(f'📦 Queuing product {i}/{len(product_links)}: {full_url}')
                yield Request(
                    url=full_url,
                    callback=self.parse_product,
                    meta={'page_url': response.url, 'product_index': i, 'scrolled': True}
                )

        # ページネーションリンクを取得（再帰的に巡る）
        next_page_links = []

        # セレクター1: 標準的な次ページリンク
        next_page_links.extend(response.css('a[aria-label="次のページに移動"]::attr(href)').getall())

        # セレクター2: 検索結果ページネーション
        next_page_links.extend(response.css('a.s-pagination-next::attr(href)').getall())

        # セレクター3: 一般的なページネーション
        next_page_links.extend(response.css('li.a-last a::attr(href)').getall())

        # セレクター4: ベストセラーページネーション
        next_page_links.extend(response.css('a[aria-label*="次"]::attr(href)').getall())

        # セレクター5: 数字ページネーション
        next_page_links.extend(response.css('a[aria-label*="ページ"]::attr(href)').getall())

        # 重複を削除
        next_page_links = list(set(next_page_links))

        self.logger.info(f'🔗 Found {len(next_page_links)} potential next page links')

        for next_link in next_page_links:
            if next_link:
                next_url = response.urljoin(next_link)
                self.logger.info(f'➡️  Following next page: {next_url}')
                yield Request(
                    url=next_url,
                    callback=self.parse,
                    meta={'page_url': response.url, 'from_scrolled_page': True}
                )

    def parse_product(self, response):
        """商品詳細ページの解析"""
        product_index = response.meta.get('product_index', '?')
        scrolled = response.meta.get('scrolled', False)
        scroll_indicator = '📜' if scrolled else '📄'
        self.logger.info(f'{scroll_indicator} Processing product {product_index}: {response.url}')

        # 商品タイトル (id="title")
        title = response.css('#title span::text').get()
        if not title:
            title = response.css('#title::text').get()
        if title:
            title = title.strip()

        # 評価を取得
        rating = None
        rating_text = response.css('span.a-icon-alt::text').get()
        if rating_text:
            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
            if rating_match:
                rating = rating_match.group(1)

        # 税込価格を取得
        price = None
        price_selectors = [
            '.a-price-whole::text',
            '.a-price .a-offscreen::text',
            '.a-price-current .a-offscreen::text',
            '.a-price-range .a-offscreen::text'
        ]
        for selector in price_selectors:
            price_text = response.css(selector).get()
            if price_text:
                price = price_text.strip()
                break

        # レビュー数を取得
        review_count = None
        review_selectors = [
            '#acrCustomerReviewText::text',
            'span[data-hook="total-review-count"]::text',
            '.a-size-base.a-link-normal::text'
        ]
        for selector in review_selectors:
            review_text = response.css(selector).get()
            if review_text and ('レビュー' in review_text or 'review' in review_text.lower()):
                review_count = review_text.strip()
                break

        # 画像パス (class="a-dynamic-image a-stretch-vertical")
        image_url = response.css('img.a-dynamic-image.a-stretch-vertical::attr(src)').get()
        if not image_url:
            # 代替セレクタ
            image_url = response.css('#landingImage::attr(src)').get()

        # アイテム数を更新
        self.items_count += 1
        self.requests_count += 1

        # データを返す
        item_data = {
            'title': title,
            'rating': rating,
            'price': price,
            'review_count': review_count,
            'image_url': image_url,
            'product_url': response.url,
            'source_page': response.meta.get('page_url', ''),
            'scraped_at': response.headers.get('Date', '').decode('utf-8') if response.headers.get('Date') else ''
        }

        # ログでアイテム情報を出力
        title_display = title[:50] + "..." if title and len(title) > 50 else (title or "No title")
        self.logger.info(f"✅ Item {self.items_count}: {title_display} - Price: {price or 'N/A'} - Rating: {rating or 'N/A'}")

        yield item_data