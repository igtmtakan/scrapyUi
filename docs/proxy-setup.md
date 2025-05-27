# Proxy Setup Guide for ScrapyUI

## Overview

ScrapyUIでは、`scrapy-proxies-tool`を使用してプロキシローテーション機能を提供しています。これにより、IPアドレスを変更してスクレイピング時のブロックを回避できます。

## Proxy設定の有効化

### 1. settings.pyでの設定

新規プロジェクトでは自動的に以下の設定が含まれます：

```python
# Proxy settings (optional - configure as needed)
# PROXY_LIST = '/path/to/proxy/list.txt'
# PROXY_MODE = 0  # 0: random, 1: round-robin, 2: only once
```

### 2. プロキシリストファイルの作成

プロキシを使用する場合は、プロキシリストファイルを作成します：

#### ファイル形式

```
# proxy_list.txt
http://proxy1.example.com:8080
http://proxy2.example.com:8080
http://username:password@proxy3.example.com:8080
https://proxy4.example.com:8080
socks5://proxy5.example.com:1080
```

#### 設定の有効化

settings.pyで以下のコメントを外して設定：

```python
PROXY_LIST = '/path/to/your/proxy_list.txt'
PROXY_MODE = 0  # 0: random, 1: round-robin, 2: only once
```

## Proxy Mode説明

- **0 (random)**: ランダムにプロキシを選択
- **1 (round-robin)**: 順番にプロキシを使用
- **2 (only once)**: 各プロキシを一度だけ使用

## User Agent設定

### 自動設定

新規プロジェクトでは以下が自動設定されます：

```python
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
    'scrapy_fake_useragent.middleware.RetryUserAgentMiddleware': 401,
    'scrapy_proxies.RandomProxy': 350,
}

FAKEUSERAGENT_PROVIDERS = [
    'scrapy_fake_useragent.providers.FakeUserAgentProvider',
    'scrapy_fake_useragent.providers.FakerProvider',
    'scrapy_fake_useragent.providers.FixedUserAgentProvider',
]
```

## 使用例

### 基本的な使用方法

```python
import scrapy

class MySpider(scrapy.Spider):
    name = 'example'
    start_urls = ['https://example.com']

    def parse(self, response):
        # User Agentとプロキシは自動的にローテーション
        yield {
            'url': response.url,
            'user_agent': response.request.headers.get('User-Agent'),
            'data': response.css('title::text').get()
        }
```

### カスタム設定

特定のスパイダーでのみプロキシを使用する場合：

```python
class MySpider(scrapy.Spider):
    name = 'example'

    custom_settings = {
        'PROXY_LIST': '/path/to/specific/proxy_list.txt',
        'PROXY_MODE': 1,  # round-robin
    }
```

## 注意事項

1. **プロキシの品質**: 高品質なプロキシを使用してください
2. **レート制限**: プロキシでもレート制限を守ってください
3. **法的遵守**: 利用規約とrobots.txtを確認してください
4. **コスト**: 有料プロキシサービスの利用を推奨

## トラブルシューティング

### プロキシが動作しない場合

1. プロキシリストファイルのパスを確認
2. プロキシの認証情報を確認
3. プロキシサーバーの稼働状況を確認
4. ログでエラーメッセージを確認

### User Agentが変更されない場合

1. ミドルウェアの優先順位を確認
2. fake-useragentライブラリの更新を確認
3. ログでUser Agentの変更を確認

## 推奨プロキシサービス

- ProxyMesh
- Bright Data (旧Luminati)
- Smartproxy
- Oxylabs

## セキュリティ

- プロキシの認証情報は環境変数で管理
- プロキシリストファイルは適切な権限設定
- 本番環境では信頼できるプロキシのみ使用
