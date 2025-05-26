# 🕷️ Puppeteerテンプレート使用ガイド

## 📋 概要

ScrapyUIでは、Node.js Puppeteerサービスと連携したスクレイピングテンプレートを提供しています。これにより、JavaScript重要なSPAサイトや動的コンテンツのスクレイピングが可能になります。

## 🚀 利用可能なテンプレート

### 1. **Puppeteer SPA Scraper**
- **用途**: 基本的なSPAスクレイピング
- **特徴**: 
  - JavaScript実行環境
  - セレクターベースのデータ抽出
  - スクリーンショット取得
  - カスタムJavaScript実行

### 2. **Scrapy + Puppeteer Spider**
- **用途**: ScrapyとPuppeteerの統合
- **特徴**:
  - Scrapyの機能とPuppeteerの組み合わせ
  - フォールバック機能（Puppeteer失敗時は通常スクレイピング）
  - リンクフォロー機能
  - 自動スクリーンショット保存

### 3. **E-commerce Puppeteer Spider**
- **用途**: ECサイト専用スクレイピング
- **特徴**:
  - 商品情報の構造化抽出
  - 価格データのクリーニング
  - 関連商品の自動発見
  - レビュー・評価データ取得

## 🔧 前提条件

### Node.jsサービスの起動
```bash
# Node.jsサービスが localhost:3001 で動作している必要があります
curl http://localhost:3001/api/health
```

### 必要なPythonパッケージ
```bash
pip install aiohttp asyncio
```

## 📝 使用方法

### 方法1: エディターページから使用

1. ScrapyUI の `/editor` ページにアクセス
2. 「New Spider」ボタンをクリック
3. 「Puppeteer」カテゴリを選択
4. 使用したいテンプレートを選択
5. URLやセレクターを編集
6. 「Run」ボタンで実行

### 方法2: 直接コードをコピー

```python
# 基本的なPuppeteerスクレイピング例
import asyncio
import aiohttp
import json

async def scrape_example():
    async with aiohttp.ClientSession() as session:
        request_data = {
            "url": "https://example.com",
            "extractData": {
                "selectors": {
                    "title": "h1",
                    "content": "p"
                }
            }
        }
        
        async with session.post(
            "http://localhost:3001/api/scraping/spa",
            json=request_data
        ) as response:
            data = await response.json()
            print(json.dumps(data, indent=2))

# 実行
asyncio.run(scrape_example())
```

## ⚙️ 設定オプション

### スクレイピング設定
```python
request_data = {
    "url": "https://example.com",
    "waitFor": ".content-loaded",  # 待機するセレクター
    "timeout": 30000,              # タイムアウト（ミリ秒）
    "viewport": {                  # ビューポート設定
        "width": 1920,
        "height": 1080
    },
    "extractData": {
        "selectors": {             # 抽出するセレクター
            "title": "h1",
            "content": ".content",
            "links": "a[href]"
        },
        "javascript": '''          # カスタムJavaScript
            return {
                pageTitle: document.title,
                loadTime: performance.now()
            };
        '''
    },
    "screenshot": True             # スクリーンショット取得
}
```

### Scrapyスパイダー設定
```python
class MySpider(scrapy.Spider):
    name = 'my_spider'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nodejs_url = "http://localhost:3001"  # Node.jsサービスURL
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,    # 同時リクエスト数
        'DOWNLOAD_DELAY': 2,         # リクエスト間隔
        'ROBOTSTXT_OBEY': False      # robots.txt無視
    }
```

## 🎯 実用例

### ECサイトの商品情報取得
```python
selectors = {
    "name": "h1.product-title",
    "price": ".price",
    "description": ".product-description",
    "images": "img.product-image",
    "availability": ".availability",
    "reviews": ".review-item"
}
```

### ニュースサイトの記事取得
```python
selectors = {
    "headline": "h1",
    "author": ".author",
    "date": ".publish-date",
    "content": ".article-body",
    "tags": ".tag-list a"
}
```

### SNSの投稿取得
```python
selectors = {
    "posts": ".post-item",
    "usernames": ".username",
    "timestamps": ".timestamp",
    "content": ".post-content",
    "likes": ".like-count"
}
```

## 🔍 トラブルシューティング

### よくある問題と解決方法

#### 1. `ModuleNotFoundError: No module named 'scrapy_ui'`
**解決方法**: テンプレートを修正版に更新してください。新しいテンプレートは外部依存関係を使用しません。

#### 2. Node.jsサービスに接続できない
**確認事項**:
- Node.jsサービスが起動しているか
- ポート3001が利用可能か
- ファイアウォール設定

#### 3. スクリーンショットが保存されない
**確認事項**:
- ディスクの空き容量
- ファイル書き込み権限
- base64デコードエラー

#### 4. データが抽出されない
**確認事項**:
- セレクターが正しいか
- ページの読み込み完了を待機しているか
- JavaScriptエラーがないか

## 📊 パフォーマンス最適化

### 推奨設定
```python
# Scrapyスパイダーの場合
custom_settings = {
    'CONCURRENT_REQUESTS': 1,        # Puppeteerは重いので1に制限
    'DOWNLOAD_DELAY': 2,             # 2秒間隔
    'RANDOMIZE_DOWNLOAD_DELAY': 0.5, # ランダム遅延
    'AUTOTHROTTLE_ENABLED': True,    # 自動スロットリング
    'AUTOTHROTTLE_START_DELAY': 1,
    'AUTOTHROTTLE_MAX_DELAY': 10,
    'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0
}
```

### メモリ使用量の監視
```python
# メモリ使用量を監視
import psutil
import os

def check_memory():
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory usage: {memory_mb:.2f} MB")
```

## 🛡️ セキュリティ考慮事項

### 1. レート制限の遵守
- 適切な遅延設定
- robots.txtの確認
- サイトの利用規約確認

### 2. ユーザーエージェントの設定
```python
headers = {
    'User-Agent': 'ScrapyUI-Bot/1.0 (+https://your-domain.com/bot)'
}
```

### 3. プロキシの使用
```python
# プロキシ設定例
request_data = {
    "url": "https://example.com",
    "proxy": "http://proxy-server:port",
    # ... その他の設定
}
```

## 📈 監視とログ

### ログ設定
```python
import logging

# ログレベル設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)
```

### メトリクス収集
```python
# 成功率の追跡
success_count = 0
total_count = 0

def track_success(success):
    global success_count, total_count
    total_count += 1
    if success:
        success_count += 1
    
    success_rate = (success_count / total_count) * 100
    print(f"Success rate: {success_rate:.2f}%")
```

## 🔗 関連リンク

- [ScrapyUI Documentation](/)
- [Node.js Puppeteer Service](/nodejs)
- [Scrapy Documentation](https://docs.scrapy.org/)
- [Puppeteer Documentation](https://pptr.dev/)

---

**注意**: Puppeteerテンプレートを使用する際は、対象サイトの利用規約を必ず確認し、適切なレート制限を設定してください。
