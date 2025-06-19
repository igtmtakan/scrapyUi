#!/usr/bin/env python3
import requests
import json

# APIベースURL
BASE_URL = "http://localhost:8000"

def login():
    """ログイン"""
    login_data = {
        'email': 'admin@scrapyui.com',
        'password': 'admin123456'
    }

    print('🔐 ログイン中...')
    response = requests.post(
        f'{BASE_URL}/api/auth/login',
        json=login_data,
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code == 200:
        result = response.json()
        token = result['access_token']
        print('✅ ログイン成功')
        return token
    else:
        print(f'❌ ログイン失敗: {response.status_code}')
        print(response.text)
        return None

def create_project(token):
    """プロジェクト作成または既存プロジェクト取得"""
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    # まず既存プロジェクトを確認
    print('📁 既存プロジェクトを確認中...')
    projects_response = requests.get(f'{BASE_URL}/api/projects/', headers=headers)

    if projects_response.status_code == 200:
        projects = projects_response.json()
        for project in projects:
            if project['name'] == 'admin_omocha20':
                print(f'✅ 既存プロジェクトを使用: {project["id"]}')
                print(f'プロジェクト名: {project["name"]}')
                print(f'プロジェクトパス: {project["path"]}')
                return project

    # 既存プロジェクトがない場合は新規作成
    project_data = {
        'name': 'admin_omocha20',
        'description': 'Amazon software bestsellers scraping project',
        'settings': {}
    }

    print('📁 新規プロジェクト作成中...')
    response = requests.post(
        f'{BASE_URL}/api/projects/',
        json=project_data,
        headers=headers
    )

    if response.status_code == 201:
        project = response.json()
        print(f'✅ プロジェクト作成成功: {project["id"]}')
        print(f'プロジェクト名: {project["name"]}')
        print(f'プロジェクトパス: {project["path"]}')
        return project
    else:
        print(f'❌ プロジェクト作成失敗: {response.status_code}')
        print(response.text)
        return None

def create_spider(token, project_id):
    """omocha20スパイダー作成または既存スパイダー取得"""
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    # まず既存スパイダーを確認
    print('🕷️ 既存スパイダーを確認中...')
    spiders_response = requests.get(f'{BASE_URL}/api/spiders/?project_id={project_id}', headers=headers)

    if spiders_response.status_code == 200:
        spiders = spiders_response.json()
        for spider in spiders:
            if spider['name'] == 'omocha20_jsonl':
                print(f'✅ 既存スパイダーを使用: {spider["id"]}')
                print(f'スパイダー名: {spider["name"]}')
                return spider

    # 既存スパイダーがない場合は新規作成
    print('🕷️ 新規スパイダー作成中...')
    spider_code = '''import scrapy
import re
import urllib.parse

class Omocha20JsonlSpider(scrapy.Spider):
    name = "omocha20_jsonl"
    allowed_domains = ["amazon.co.jp"]
    start_urls = ["https://www.amazon.co.jp/gp/bestsellers/software/ref=zg_bs_nav_software_0"]

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse
            )

    def parse(self, response):
        """ベストセラーページから商品リンクを抽出"""
        # 商品リンクを抽出
        product_links = response.css('a.a-link-normal.aok-block::attr(href)').getall()

        for link in product_links:
            if link and '/dp/' in link:
                full_url = urllib.parse.urljoin(response.url, link)
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_product
                )

        # ページネーションリンクを抽出
        next_page_links = response.css('ul.a-pagination li.a-last a::attr(href)').getall()
        if not next_page_links:
            next_page_links = response.css('a[aria-label="次へ"]::attr(href)').getall()

        for next_link in next_page_links:
            if next_link:
                next_url = urllib.parse.urljoin(response.url, next_link)
                yield scrapy.Request(
                    url=next_url,
                    callback=self.parse
                )

    def parse_product(self, response):
        """商品詳細ページから情報を抽出"""
        # タイトル
        title = response.css('#title span::text').get()
        if not title:
            title = response.css('#productTitle::text').get()

        # 評価
        rating = response.css('span.a-icon-alt::text').re_first(r'5つ星のうち([\\d.]+)')
        if not rating:
            rating = response.css('[data-hook="rating-out-of-text"]::text').re_first(r'([\\d.]+)')

        # 価格
        price = response.css('.a-price-whole::text').get()
        if not price:
            price = response.css('.a-offscreen::text').get()

        # レビュー数
        reviews = response.css('[data-hook="total-review-count"]::text').get()
        if not reviews:
            reviews = response.css('a[href*="#customerReviews"] span::text').get()

        # 画像URL
        image_url = response.css('img.a-dynamic-image.a-stretch-vertical::attr(src)').get()
        if not image_url:
            image_url = response.css('#landingImage::attr(src)').get()

        yield {
            'url': response.url,
            'title': title.strip() if title else None,
            'rating': rating,
            'price': price.strip() if price else None,
            'reviews': reviews.strip() if reviews else None,
            'image_url': image_url
        }
'''

    spider_data = {
        'name': 'omocha20_jsonl',
        'code': spider_code,
        'project_id': project_id,
        'template': 'custom',
        'settings': {}
    }

    print('🕷️ スパイダー作成中...')
    response = requests.post(
        f'{BASE_URL}/api/spiders/',
        json=spider_data,
        headers=headers
    )

    if response.status_code == 201:
        spider = response.json()
        print(f'✅ スパイダー作成成功: {spider["id"]}')
        print(f'スパイダー名: {spider["name"]}')
        return spider
    else:
        print(f'❌ スパイダー作成失敗: {response.status_code}')
        print(response.text)
        return None

def run_spider(token, project_id, spider_id):
    """スパイダー実行（タスク作成）"""
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    run_data = {
        'project_id': project_id,
        'spider_id': spider_id,
        'log_level': 'INFO',
        'settings': {
            'FEED_EXPORT_ENCODING': 'utf-8',
            'FEEDS': {
                'results.jsonl': {
                    'format': 'jsonl',
                    'encoding': 'utf8',
                    'store_empty': False,
                    'item_export_kwargs': {
                        'ensure_ascii': False
                    }
                }
            }
        }
    }

    print('🚀 スパイダー実行中（タスク作成）...')
    response = requests.post(
        f'{BASE_URL}/api/tasks/',
        json=run_data,
        headers=headers
    )

    if response.status_code in [200, 201, 202]:
        result = response.json()
        task_id = result.get("id") or result.get("task_id")
        print(f'✅ スパイダー実行開始: タスクID {task_id}')
        print(f'📊 タスクステータス: {result.get("status", "UNKNOWN")}')
        return result
    else:
        print(f'❌ スパイダー実行失敗: {response.status_code}')
        print(response.text)
        return None

def main():
    # ログイン
    token = login()
    if not token:
        return

    # プロジェクト作成
    project = create_project(token)
    if not project:
        return

    # スパイダー作成
    spider = create_spider(token, project['id'])
    if not spider:
        return

    # スパイダー実行
    result = run_spider(token, project['id'], spider['id'])
    if result:
        task_id = result.get("id") or result.get("task_id")
        print(f'🎉 omocha20スパイダーが正常に作成・実行されました！')
        print(f'タスクID: {task_id}')
        print(f'プロジェクトID: {project["id"]}')
        print(f'スパイダーID: {spider["id"]}')
        print(f'📊 実行ステータス: {result.get("status", "UNKNOWN")}')
        print(f'🌐 WebUI: http://localhost:4000/projects/{project["id"]}/spiders/{spider["id"]}/edit')

if __name__ == "__main__":
    main()
