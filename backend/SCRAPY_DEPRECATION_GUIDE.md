# Scrapy非推奨関数対応ガイド

## 🎯 概要

Scrapy 2.13.0以降で非推奨となった関数・メソッドへの対応状況と移行ガイドです。

## ❌ **非推奨となった関数・メソッド**

### 1. **Spider.start_requests() → Spider.start()**

#### **変更内容：**
- **非推奨：** `def start_requests(self):`
- **推奨：** `async def start(self):`

#### **ScrapyUIでの対応：**
```python
# 新しい方法（推奨）
async def start(self):
    for url in self.start_urls:
        yield scrapy.Request(url, callback=self.parse)

# 後方互換性（非推奨だが動作する）
def start_requests(self):
    for url in self.start_urls:
        yield scrapy.Request(url, callback=self.parse)
```

#### **影響範囲：**
- ✅ `backend/app/templates/spider_templates.py` - 対応済み
- ⚠️ 既存のスパイダーファイル - 手動更新が必要

### 2. **SpiderMiddleware.process_start_requests() → process_start()**

#### **変更内容：**
- **非推奨：** `def process_start_requests(self, start_requests, spider):`
- **推奨：** `async def process_start(self, start):`

#### **ScrapyUIでの対応：**
```python
# 新しい方法（推奨）
async def process_start(self, start):
    async for item_or_request in start:
        yield item_or_request

# 後方互換性（非推奨だが動作する）
def process_start_requests(self, start_requests, spider):
    for r in start_requests:
        yield r
```

#### **影響範囲：**
- ⚠️ 既存のmiddlewareファイル - 手動更新が必要

### 3. **その他の非推奨関数**

#### **scrapy.utils.url関数群**
```python
# 非推奨
from scrapy.utils.url import canonicalize_url

# 推奨
from w3lib.url import canonicalize_url
```

#### **scrapy.utils.versions**
```python
# 非推奨
from scrapy.utils.versions import scrapy_components_versions

# 推奨
from scrapy.utils.versions import get_versions
```

## 🔧 **移行手順**

### 1. **新しいスパイダー作成時**

ScrapyUIで新しいスパイダーを作成する場合、自動的に新しい形式が適用されます：

```python
class MySpider(scrapy.Spider):
    name = 'my_spider'
    
    # 新しい方法（自動生成）
    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)
    
    # 後方互換性も含まれる
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)
```

### 2. **既存スパイダーの更新**

既存のスパイダーを手動で更新する場合：

```python
# 既存のコード
def start_requests(self):
    for url in self.start_urls:
        yield scrapy.Request(url, callback=self.parse)

# 新しいコードを追加（既存コードは残す）
async def start(self):
    for url in self.start_urls:
        yield scrapy.Request(url, callback=self.parse)
```

### 3. **Middlewareの更新**

既存のmiddlewareを更新する場合：

```python
# 既存のコード
def process_start_requests(self, start_requests, spider):
    for r in start_requests:
        yield r

# 新しいコードを追加
async def process_start(self, start):
    async for item_or_request in start:
        yield item_or_request
```

## 📋 **チェックリスト**

### ✅ **対応済み**
- [x] スパイダーテンプレートの更新
- [x] 新しい`start()`メソッドの追加
- [x] 後方互換性の維持

### ⚠️ **今後の対応が必要**
- [ ] 既存プロジェクトのスパイダー更新
- [ ] 既存middlewareの更新
- [ ] w3lib関数への移行
- [ ] ユーザー向けマイグレーションツール

## 🚨 **重要な注意事項**

### 1. **後方互換性**
- 現在のScrapyUIは新旧両方の形式をサポート
- 既存のスパイダーは引き続き動作
- 段階的な移行が可能

### 2. **パフォーマンス**
- 新しい`start()`メソッドはasync対応
- より効率的なリソース使用
- 大規模スクレイピングでの改善

### 3. **将来の削除予定**
- Scrapy 3.0で古い形式が削除予定
- 早めの移行を推奨

## 🔄 **自動移行ツール（計画中）**

将来的に以下の機能を追加予定：

```bash
# 既存プロジェクトの自動更新
scrapyui migrate --project my_project

# 非推奨関数の検出
scrapyui check-deprecated --project my_project

# 一括更新
scrapyui update-all-projects
```

## 📚 **参考資料**

- [Scrapy 2.13.0 Release Notes](https://docs.scrapy.org/en/latest/news.html#scrapy-2-13-0-2025-05-08)
- [Scrapy Spider Documentation](https://docs.scrapy.org/en/latest/topics/spiders.html)
- [Scrapy Middleware Documentation](https://docs.scrapy.org/en/latest/topics/spider-middleware.html)

---

**このガイドにより、ScrapyUIは最新のScrapyバージョンに対応し、将来的な互換性を確保します。** 🚀
