#!/usr/bin/env python3
"""
JavaScript重要サイトのPuppeteerスクレイピング
"""

import asyncio
import json
import aiohttp
import base64
import time

class JavaScriptSiteScraper:
    """JavaScript重要サイト専用スクレイパー"""

    def __init__(self, base_url: str = "http://localhost:3001"):
        self.base_url = base_url.rstrip('/')
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def scrape_js_site(self, url: str, wait_selector: str = None, custom_js: str = None):
        """JavaScript重要サイトをスクレイピング"""

        # JavaScript重要サイト用の最適化された設定
        request_data = {
            "url": url,
            "waitFor": wait_selector or "body",
            "timeout": 60000,  # 60秒タイムアウト
            "viewport": {
                "width": 1920,
                "height": 1080
            },
            "extractData": {
                "selectors": {
                    # 汎用的なセレクター
                    "title": "title, h1, h2, .title, .heading",
                    "content": "p, .content, .text, .description, article, .article",
                    "links": "a[href]",
                    "images": "img[src]",
                    "buttons": "button, .btn, .button",
                    "forms": "form, input, textarea",
                    "navigation": "nav, .nav, .menu, .navigation",
                    "cards": ".card, .item, .post, .product",
                    "lists": "ul, ol, .list",
                    "quotes": ".quote, .testimonial, blockquote"
                },
                "javascript": custom_js or '''
                    // JavaScript重要サイト用の包括的データ抽出
                    function extractJavaScriptSiteData() {
                        const data = {
                            // 基本情報
                            pageTitle: document.title,
                            url: window.location.href,
                            loadTime: performance.now(),
                            userAgent: navigator.userAgent,

                            // コンテンツ抽出
                            headings: [],
                            paragraphs: [],
                            links: [],
                            images: [],

                            // インタラクティブ要素
                            buttons: [],
                            forms: [],
                            inputs: [],

                            // 構造化データ
                            navigation: [],
                            cards: [],
                            lists: [],

                            // ページ統計
                            elementCounts: {},
                            hasJavaScript: false,
                            hasAjax: false,
                            hasSPA: false,

                            // 特殊コンテンツ
                            quotes: [],
                            prices: [],
                            dates: []
                        };

                        try {
                            // 見出しを抽出
                            document.querySelectorAll('h1, h2, h3, h4, h5, h6, .title, .heading').forEach(el => {
                                const text = el.textContent?.trim();
                                if (text && text.length > 0 && text.length < 200) {
                                    data.headings.push({
                                        text: text,
                                        tag: el.tagName.toLowerCase(),
                                        level: el.tagName.match(/h([1-6])/i)?.[1] || 'other'
                                    });
                                }
                            });

                            // 段落とコンテンツを抽出
                            document.querySelectorAll('p, .content, .text, .description, article').forEach(el => {
                                const text = el.textContent?.trim();
                                if (text && text.length > 20 && text.length < 500) {
                                    data.paragraphs.push(text);
                                }
                            });

                            // リンクを抽出
                            document.querySelectorAll('a[href]').forEach(el => {
                                const href = el.href;
                                const text = el.textContent?.trim();
                                if (href && text && text.length > 0 && text.length < 100) {
                                    data.links.push({
                                        url: href,
                                        text: text,
                                        isExternal: !href.includes(window.location.hostname)
                                    });
                                }
                            });

                            // 画像を抽出
                            document.querySelectorAll('img[src]').forEach(el => {
                                const src = el.src;
                                const alt = el.alt || '';
                                if (src) {
                                    data.images.push({
                                        src: src,
                                        alt: alt,
                                        width: el.width || 'auto',
                                        height: el.height || 'auto'
                                    });
                                }
                            });

                            // ボタンを抽出
                            document.querySelectorAll('button, .btn, .button, input[type="submit"]').forEach(el => {
                                const text = el.textContent?.trim() || el.value || '';
                                if (text) {
                                    data.buttons.push({
                                        text: text,
                                        type: el.type || 'button',
                                        disabled: el.disabled || false
                                    });
                                }
                            });

                            // フォームを抽出
                            document.querySelectorAll('form').forEach(el => {
                                const action = el.action || '';
                                const method = el.method || 'GET';
                                const inputs = el.querySelectorAll('input, textarea, select').length;
                                data.forms.push({
                                    action: action,
                                    method: method,
                                    inputCount: inputs
                                });
                            });

                            // ナビゲーションを抽出
                            document.querySelectorAll('nav a, .nav a, .menu a, .navigation a').forEach(el => {
                                const text = el.textContent?.trim();
                                const href = el.href;
                                if (text && href) {
                                    data.navigation.push({
                                        text: text,
                                        url: href
                                    });
                                }
                            });

                            // カード/アイテムを抽出
                            document.querySelectorAll('.card, .item, .post, .product').forEach(el => {
                                const title = el.querySelector('h1, h2, h3, h4, .title')?.textContent?.trim();
                                const description = el.querySelector('p, .description, .summary')?.textContent?.trim();
                                if (title || description) {
                                    data.cards.push({
                                        title: title || '',
                                        description: (description || '').substring(0, 200)
                                    });
                                }
                            });

                            // 引用文を抽出
                            document.querySelectorAll('.quote, blockquote, .testimonial').forEach(el => {
                                const text = el.textContent?.trim();
                                if (text && text.length > 10) {
                                    data.quotes.push(text.substring(0, 300));
                                }
                            });

                            // 価格を抽出（正規表現で）
                            const priceRegex = /[¥$€£]\\s*[\\d,]+(?:\\.\\d{2})?|\\d+\\s*円|\\d+\\s*ドル/g;
                            const bodyText = document.body.textContent || '';
                            const priceMatches = bodyText.match(priceRegex);
                            if (priceMatches) {
                                data.prices = [...new Set(priceMatches.slice(0, 10))];
                            }

                            // 日付を抽出（正規表現で）
                            const dateRegex = /\\d{4}[-/]\\d{1,2}[-/]\\d{1,2}|\\d{1,2}[-/]\\d{1,2}[-/]\\d{4}/g;
                            const dateMatches = bodyText.match(dateRegex);
                            if (dateMatches) {
                                data.dates = [...new Set(dateMatches.slice(0, 10))];
                            }

                            // 要素統計
                            data.elementCounts = {
                                divs: document.querySelectorAll('div').length,
                                spans: document.querySelectorAll('span').length,
                                paragraphs: document.querySelectorAll('p').length,
                                links: document.querySelectorAll('a').length,
                                images: document.querySelectorAll('img').length,
                                buttons: document.querySelectorAll('button, .btn').length,
                                forms: document.querySelectorAll('form').length,
                                inputs: document.querySelectorAll('input, textarea, select').length,
                                scripts: document.querySelectorAll('script').length
                            };

                            // JavaScript検出
                            data.hasJavaScript = document.querySelectorAll('script').length > 0;
                            data.hasAjax = window.XMLHttpRequest !== undefined;
                            data.hasSPA = window.history && window.history.pushState !== undefined;

                            // 重複除去
                            data.headings = data.headings.slice(0, 20);
                            data.paragraphs = [...new Set(data.paragraphs)].slice(0, 10);
                            data.links = data.links.slice(0, 20);
                            data.images = data.images.slice(0, 10);
                            data.navigation = data.navigation.slice(0, 15);
                            data.cards = data.cards.slice(0, 10);
                            data.quotes = [...new Set(data.quotes)].slice(0, 5);

                        } catch (error) {
                            data.extractionError = error.message;
                        }

                        return data;
                    }

                    // 5秒待ってからデータを抽出（JavaScript読み込み完了を待機）
                    return new Promise(resolve => {
                        setTimeout(() => {
                            resolve(extractJavaScriptSiteData());
                        }, 5000);
                    });
                '''
            },
            "screenshot": True,
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        print(f"🚀 JavaScript重要サイトスクレイピング開始: {url}")

        async with self.session.post(
            f"{self.base_url}/api/scraping/spa",
            json=request_data
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Request failed: {response.status}")

async def test_javascript_sites():
    """JavaScript重要サイトのテスト"""
    print("🌐 JavaScript重要サイトのPuppeteerスクレイピングテスト")

    # JavaScript重要サイトのリスト
    js_sites = [
        {
            "name": "Quotes to Scrape (JS)",
            "url": "http://quotes.toscrape.com/js/",
            "wait_selector": ".quote",
            "description": "JavaScript動的読み込みの引用サイト"
        },
        {
            "name": "Books to Scrape",
            "url": "http://books.toscrape.com/",
            "wait_selector": ".product_pod",
            "description": "書籍データサイト"
        },
        {
            "name": "HTTPBin HTML",
            "url": "https://httpbin.org/html",
            "wait_selector": "body",
            "description": "HTMLテストサイト"
        },
        {
            "name": "Example Domain",
            "url": "https://example.com",
            "wait_selector": "body",
            "description": "基本テストサイト"
        }
    ]

    async with JavaScriptSiteScraper() as scraper:
        for site in js_sites:
            print(f"\n{'='*60}")
            print(f"📄 テスト対象: {site['name']}")
            print(f"🔗 URL: {site['url']}")
            print(f"📝 説明: {site['description']}")
            print(f"{'='*60}")

            try:
                response = await scraper.scrape_js_site(
                    url=site['url'],
                    wait_selector=site['wait_selector']
                )

                if response.get('success'):
                    data = response.get('data', {})
                    js_data = data.get('javascript', {})

                    print(f"✅ スクレイピング成功!")
                    print(f"📄 ページタイトル: {js_data.get('pageTitle', 'N/A')}")
                    print(f"⏱️ 読み込み時間: {js_data.get('loadTime', 0):.2f}ms")
                    print(f"🔧 JavaScript検出: {'あり' if js_data.get('hasJavaScript') else 'なし'}")
                    print(f"🌐 SPA機能: {'あり' if js_data.get('hasSPA') else 'なし'}")

                    # 見出し
                    headings = js_data.get('headings', [])
                    if headings:
                        print(f"\n📰 見出し ({len(headings)}個):")
                        for i, heading in enumerate(headings[:5]):
                            print(f"   {i+1}. [{heading.get('tag', 'unknown')}] {heading.get('text', '')}")

                    # コンテンツ
                    paragraphs = js_data.get('paragraphs', [])
                    if paragraphs:
                        print(f"\n📝 コンテンツ ({len(paragraphs)}個):")
                        for i, para in enumerate(paragraphs[:3]):
                            print(f"   {i+1}. {para[:100]}...")

                    # リンク
                    links = js_data.get('links', [])
                    if links:
                        print(f"\n🔗 リンク ({len(links)}個):")
                        for i, link in enumerate(links[:5]):
                            external = "🌐" if link.get('isExternal') else "🏠"
                            print(f"   {i+1}. {external} {link.get('text', '')} -> {link.get('url', '')[:50]}...")

                    # カード/アイテム
                    cards = js_data.get('cards', [])
                    if cards:
                        print(f"\n🃏 カード/アイテム ({len(cards)}個):")
                        for i, card in enumerate(cards[:3]):
                            print(f"   {i+1}. {card.get('title', '')} - {card.get('description', '')[:80]}...")

                    # 引用文
                    quotes = js_data.get('quotes', [])
                    if quotes:
                        print(f"\n💬 引用文 ({len(quotes)}個):")
                        for i, quote in enumerate(quotes[:2]):
                            print(f"   {i+1}. \"{quote[:100]}...\"")

                    # 価格
                    prices = js_data.get('prices', [])
                    if prices:
                        print(f"\n💰 価格 ({len(prices)}個): {', '.join(prices)}")

                    # 要素統計
                    counts = js_data.get('elementCounts', {})
                    print(f"\n📊 要素統計:")
                    for element, count in counts.items():
                        print(f"   {element}: {count}")

                    # ファイル名用の安全な名前を生成
                    safe_name = site['name'].replace(' ', '_').replace('(', '').replace(')', '').lower()

                    # スクリーンショット保存
                    if data.get('screenshot'):
                        screenshot_data = base64.b64decode(data['screenshot'])
                        filename = f"js_site_{safe_name}_{int(time.time())}.png"

                        with open(filename, 'wb') as f:
                            f.write(screenshot_data)
                        print(f"\n📸 スクリーンショット保存: {filename}")

                    # 詳細データをJSONで保存
                    json_filename = f"js_site_{safe_name}_data.json"
                    with open(json_filename, 'w', encoding='utf-8') as f:
                        json.dump(js_data, f, indent=2, ensure_ascii=False)
                    print(f"💾 詳細データ保存: {json_filename}")

                else:
                    print(f"❌ スクレイピング失敗: {response.get('error')}")

            except Exception as e:
                print(f"🚨 エラー: {str(e)}")

            # 次のサイトテスト前に少し待機
            print(f"\n⏳ 次のテストまで3秒待機...")
            await asyncio.sleep(3)

# 実行
if __name__ == "__main__":
    asyncio.run(test_javascript_sites())
