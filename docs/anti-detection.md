# Anti-Detection Features

ScrapyUIには、Webスクレイピング時の検出を回避するための高度な機能が組み込まれています。

## 🛡️ 概要

現代のWebサイトは、ボットやスクレイピングツールを検出するための様々な手法を使用しています。ScrapyUIは以下の機能でこれらの検出を回避します：

- **User-Agent ローテーション**: 毎回異なるブラウザとして認識
- **プロキシサポート**: IPアドレスの変更でアクセス元を分散
- **HTTPキャッシュ**: 開発効率の向上
- **日本語対応**: 日本語コンテンツの適切な取得

## 🔄 User-Agent ローテーション

### 自動設定

新規プロジェクトでは、以下の設定が自動的に適用されます：

```python
# User-Agent ミドルウェア設定
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
    'scrapy_fake_useragent.middleware.RetryUserAgentMiddleware': 401,
}

# User-Agent プロバイダー設定
FAKEUSERAGENT_PROVIDERS = [
    'scrapy_fake_useragent.providers.FakeUserAgentProvider',  # メイン
    'scrapy_fake_useragent.providers.FakerProvider',         # フォールバック
    'scrapy_fake_useragent.providers.FixedUserAgentProvider', # フォールバック
]
```

### 動作原理

1. **リクエスト毎に変更**: 各HTTPリクエストで異なるUser-Agentを使用
2. **実在ブラウザ**: Chrome、Firefox、Safari、Edgeなどの実際のブラウザ情報
3. **最新バージョン**: 定期的に更新される最新のブラウザバージョン
4. **フォールバック**: メインプロバイダーが失敗した場合の代替手段

### 対応ブラウザ

- **Chrome**: Windows、Mac、Linux、Android
- **Firefox**: Windows、Mac、Linux、Android
- **Safari**: Mac、iOS
- **Edge**: Windows
- **その他**: Opera、Samsung Internet等

## 🌐 プロキシサポート

### 基本設定

プロキシを使用する場合は、settings.pyで以下の設定を有効化：

```python
# プロキシ設定（必要に応じてコメントアウト）
PROXY_LIST = '/path/to/proxy_list.txt'
PROXY_MODE = 0  # 0: random, 1: round-robin, 2: only once

# プロキシミドルウェア（自動設定済み）
DOWNLOADER_MIDDLEWARES = {
    'scrapy_proxies.RandomProxy': 350,
}
```

### プロキシリストファイル

```
# proxy_list.txt
http://proxy1.example.com:8080
http://username:password@proxy2.example.com:8080
https://proxy3.example.com:8080
socks5://proxy4.example.com:1080
```

### プロキシモード

- **0 (random)**: ランダムにプロキシを選択
- **1 (round-robin)**: 順番にプロキシを使用
- **2 (only once)**: 各プロキシを一度だけ使用

## ⚡ HTTPキャッシュ

### 開発効率の向上

```python
# HTTPキャッシュ設定（自動設定済み）
HTTPCACHE_ENABLED = True
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_EXPIRATION_SECS = 86400  # 1日
```

### 効果

- **初回実行**: 通常通りページをダウンロード
- **2回目以降**: キャッシュから高速読み込み
- **開発時**: コード修正時の待機時間を大幅短縮
- **自動期限切れ**: 1日経過後は自動的に再ダウンロード

## 🌍 日本語対応

### 自動設定

```python
# 日本語コンテンツ優先設定
DEFAULT_REQUEST_HEADERS = {
    'Accept-Language': 'ja',
}

# UTF-8エンコーディング
FEED_EXPORT_ENCODING = 'utf-8'
```

### 効果

- **日本語優先**: 多言語サイトで日本語版を自動取得
- **文字化け防止**: 出力ファイルで日本語が正しく表示
- **エンコーディング**: 全ての出力形式でUTF-8を使用

## 🎯 使用例

### 基本的なスパイダー

```python
import scrapy

class MySpider(scrapy.Spider):
    name = 'example'
    start_urls = ['https://example.com']
    
    def parse(self, response):
        # User-Agentとプロキシは自動的にローテーション
        yield {
            'url': response.url,
            'title': response.css('title::text').get(),
            'user_agent': response.request.headers.get('User-Agent'),
        }
```

### カスタム設定

特定のスパイダーでのみ設定を変更：

```python
class MySpider(scrapy.Spider):
    name = 'example'
    
    custom_settings = {
        'PROXY_MODE': 1,  # round-robin
        'HTTPCACHE_EXPIRATION_SECS': 3600,  # 1時間
    }
```

## 📊 効果測定

### 成功率の向上

- **User-Agent**: ボット検出率を大幅に削減
- **プロキシ**: IPブロックを回避
- **組み合わせ**: 最大限の検出回避効果

### 開発効率

- **キャッシュ**: 開発時間を60-80%短縮
- **自動設定**: 手動設定の手間を削減
- **エラー削減**: 設定ミスによるエラーを防止

## ⚠️ 注意事項

### 法的・倫理的考慮

- **利用規約**: 対象サイトの利用規約を必ず確認
- **robots.txt**: robots.txtの内容を尊重
- **レート制限**: 適切な間隔でリクエストを送信
- **法的制限**: 各国の法律を遵守

### 技術的注意

- **プロキシ品質**: 高品質なプロキシサービスを使用
- **動的コンテンツ**: JavaScriptで生成されるコンテンツに注意
- **本番環境**: 本番環境ではキャッシュを無効化することを検討

## 🔧 トラブルシューティング

### User-Agentが変更されない

1. ミドルウェアの優先順位を確認
2. fake-useragentライブラリの更新
3. ログでUser-Agentの変更を確認

### プロキシが動作しない

1. プロキシリストファイルのパスを確認
2. プロキシの認証情報を確認
3. プロキシサーバーの稼働状況を確認

### キャッシュが効かない

1. HTTPCACHE_ENABLEDの設定を確認
2. キャッシュディレクトリの権限を確認
3. キャッシュの有効期限を確認

## 📚 関連ドキュメント

- [Proxy Setup Guide](proxy-setup.md)
- [Scrapy Documentation](https://docs.scrapy.org/)
- [scrapy-fake-useragent](https://github.com/alecxe/scrapy-fake-useragent)
- [scrapy-proxies](https://github.com/aivarsk/scrapy-proxies)
