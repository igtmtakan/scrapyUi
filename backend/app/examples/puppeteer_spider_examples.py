"""
Puppeteerスパイダーの使用例
ScrapyUIでPuppeteerを使用したWebスクレイピングの実装例
"""

# 1. 基本的なSPAスクレイピング例
spa_spider_example = {
    "spider_name": "spa_example",
    "spider_type": "spa",
    "start_urls": [
        "https://example-spa.com",
        "https://react-app.example.com"
    ],
    "puppeteer_config": {
        "viewport": {"width": 1920, "height": 1080},
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "timeout": 30000,
        "waitFor": 5000
    },
    "extract_data": {
        "selectors": {
            "title": "h1",
            "description": ".description",
            "price": ".price",
            "images": "img[src]",
            "links": "a[href]"
        },
        "javascript": """
            return {
                pageHeight: document.body.scrollHeight,
                linkCount: document.querySelectorAll('a').length,
                imageCount: document.querySelectorAll('img').length,
                loadTime: performance.now()
            };
        """
    },
    "custom_settings": {
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS": 1,
        "FEEDS": {
            "results/spa_example_%(time)s.jsonl": {
                "format": "jsonlines",
                "encoding": "utf8"
            }
        }
    }
}

# 2. 動的コンテンツスクレイピング例（検索フォーム）
dynamic_search_example = {
    "spider_name": "dynamic_search",
    "spider_type": "dynamic",
    "start_urls": [
        "https://example.com/search"
    ],
    "actions": [
        {
            "type": "type",
            "selector": "input[name='q']",
            "value": "Python スクレイピング"
        },
        {
            "type": "click",
            "selector": "button[type='submit']"
        },
        {
            "type": "wait",
            "delay": 3000
        },
        {
            "type": "scroll"
        }
    ],
    "extract_data": {
        "selectors": {
            "search_results": ".search-result h3",
            "descriptions": ".search-result .description",
            "urls": ".search-result a[href]"
        }
    },
    "custom_settings": {
        "DOWNLOAD_DELAY": 5,
        "CONCURRENT_REQUESTS": 1
    }
}

# 3. ECサイトスクレイピング例
ecommerce_spider_example = {
    "spider_name": "ecommerce_products",
    "spider_type": "spa",
    "start_urls": [
        "https://shop.example.com/products"
    ],
    "puppeteer_config": {
        "viewport": {"width": 1920, "height": 1080},
        "timeout": 45000,
        "waitFor": "div.product-list"
    },
    "extract_data": {
        "selectors": {
            "product_names": ".product-item h3",
            "prices": ".product-item .price",
            "ratings": ".product-item .rating",
            "availability": ".product-item .stock-status",
            "product_links": ".product-item a[href]"
        },
        "javascript": """
            // 無限スクロールを処理
            let lastHeight = document.body.scrollHeight;
            let scrollCount = 0;
            
            while (scrollCount < 5) {
                window.scrollTo(0, document.body.scrollHeight);
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                let newHeight = document.body.scrollHeight;
                if (newHeight === lastHeight) break;
                
                lastHeight = newHeight;
                scrollCount++;
            }
            
            return {
                totalProducts: document.querySelectorAll('.product-item').length,
                scrollCount: scrollCount,
                finalHeight: document.body.scrollHeight
            };
        """
    }
}

# 4. ニュースサイトスクレイピング例
news_spider_example = {
    "spider_name": "news_articles",
    "spider_type": "spa",
    "start_urls": [
        "https://news.example.com"
    ],
    "extract_data": {
        "selectors": {
            "headlines": ".article-headline",
            "summaries": ".article-summary",
            "authors": ".article-author",
            "publish_dates": ".article-date",
            "categories": ".article-category",
            "article_links": ".article-link[href]"
        },
        "javascript": """
            // 記事の詳細情報を取得
            const articles = [];
            const articleElements = document.querySelectorAll('.article-item');
            
            articleElements.forEach((article, index) => {
                const headline = article.querySelector('.article-headline')?.textContent?.trim();
                const summary = article.querySelector('.article-summary')?.textContent?.trim();
                const author = article.querySelector('.article-author')?.textContent?.trim();
                const date = article.querySelector('.article-date')?.textContent?.trim();
                const category = article.querySelector('.article-category')?.textContent?.trim();
                const link = article.querySelector('.article-link')?.href;
                
                if (headline && link) {
                    articles.push({
                        index: index + 1,
                        headline,
                        summary,
                        author,
                        date,
                        category,
                        link
                    });
                }
            });
            
            return {
                articles: articles,
                totalCount: articles.length,
                scrapedAt: new Date().toISOString()
            };
        """
    }
}

# 5. ログイン必要サイトの例
login_required_example = {
    "spider_name": "login_required_site",
    "spider_type": "dynamic",
    "start_urls": [
        "https://secure.example.com/login"
    ],
    "actions": [
        {
            "type": "type",
            "selector": "input[name='username']",
            "value": "your_username"
        },
        {
            "type": "type",
            "selector": "input[name='password']",
            "value": "your_password"
        },
        {
            "type": "click",
            "selector": "button[type='submit']"
        },
        {
            "type": "wait",
            "delay": 5000
        },
        {
            "type": "click",
            "selector": "a[href='/dashboard']"
        },
        {
            "type": "wait",
            "delay": 3000
        }
    ],
    "extract_data": {
        "selectors": {
            "user_info": ".user-profile",
            "dashboard_data": ".dashboard-widget",
            "notifications": ".notification-item"
        }
    }
}

# 6. APIを使用したPuppeteerスパイダー作成の例
def create_puppeteer_spider_example():
    """
    APIを使用してPuppeteerスパイダーを作成する例
    """
    import requests
    import json
    
    # SPAスパイダーの作成
    spa_request = {
        "spider_name": "example_spa_spider",
        "start_urls": ["https://example.com"],
        "spider_type": "spa",
        "extract_data": {
            "selectors": {
                "title": "h1",
                "content": ".content"
            }
        }
    }
    
    # 動的スパイダーの作成
    dynamic_request = {
        "spider_name": "example_dynamic_spider",
        "start_urls": ["https://example.com/search"],
        "spider_type": "dynamic",
        "actions": [
            {"type": "type", "selector": "input[name='q']", "value": "search term"},
            {"type": "click", "selector": "button[type='submit']"},
            {"type": "wait", "delay": 3000}
        ],
        "extract_data": {
            "selectors": {
                "results": ".search-result"
            }
        }
    }
    
    return {
        "spa_request": spa_request,
        "dynamic_request": dynamic_request
    }

# 7. 高度なJavaScript実行例
advanced_javascript_example = {
    "spider_name": "advanced_js_spider",
    "spider_type": "spa",
    "start_urls": ["https://complex-app.example.com"],
    "extract_data": {
        "javascript": """
            // 複雑なデータ抽出ロジック
            async function extractComplexData() {
                // 1. ページが完全に読み込まれるまで待機
                await new Promise(resolve => {
                    if (document.readyState === 'complete') {
                        resolve();
                    } else {
                        window.addEventListener('load', resolve);
                    }
                });
                
                // 2. 動的コンテンツの読み込み待機
                let retries = 0;
                while (retries < 10) {
                    const dynamicContent = document.querySelector('.dynamic-content');
                    if (dynamicContent && dynamicContent.children.length > 0) {
                        break;
                    }
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    retries++;
                }
                
                // 3. データ抽出
                const data = {
                    metadata: {
                        url: window.location.href,
                        title: document.title,
                        timestamp: new Date().toISOString(),
                        userAgent: navigator.userAgent
                    },
                    content: {},
                    performance: {}
                };
                
                // コンテンツデータ
                const contentElements = document.querySelectorAll('.content-item');
                data.content.items = Array.from(contentElements).map((el, index) => ({
                    id: index + 1,
                    title: el.querySelector('h3')?.textContent?.trim(),
                    description: el.querySelector('.description')?.textContent?.trim(),
                    image: el.querySelector('img')?.src,
                    link: el.querySelector('a')?.href
                }));
                
                // パフォーマンスデータ
                if (window.performance) {
                    const navigation = performance.getEntriesByType('navigation')[0];
                    data.performance = {
                        loadTime: navigation.loadEventEnd - navigation.loadEventStart,
                        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime,
                        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime
                    };
                }
                
                return data;
            }
            
            return await extractComplexData();
        """
    }
}

# 使用例のリスト
PUPPETEER_EXAMPLES = {
    "spa_basic": spa_spider_example,
    "dynamic_search": dynamic_search_example,
    "ecommerce": ecommerce_spider_example,
    "news": news_spider_example,
    "login_required": login_required_example,
    "advanced_javascript": advanced_javascript_example
}
