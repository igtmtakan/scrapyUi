# 🔍 watchdog監視機能 使用ガイド

## 📋 概要

ScrapyUIでは、**2つの方法**でwatchdog監視付きスパイダー実行が利用できます：

1. **ScrapyUI API** - WebUIまたはAPI経由での実行
2. **scrapy crawlwithwatchdog** - コマンドライン実行

どちらも**JSONLファイルの変更をリアルタイムで監視し、新しいアイテムを即座にデータベースにインサート**します。

## 🚀 方法1: ScrapyUI API

### WebUI経由での実行

1. ブラウザで `http://localhost:4000` にアクセス
2. プロジェクト → スパイダー → **実行ボタン**をクリック
3. 内部的にwatchdog監視付きAPIが呼ばれます

### API直接呼び出し

```bash
# ログイン
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@scrapyui.com", "password": "admin123456"}'

# watchdog監視付きでスパイダーを実行
curl -X POST "http://localhost:8000/api/spiders/{spider_id}/run-with-watchdog?project_id={project_id}" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "settings": {
      "LOG_LEVEL": "INFO",
      "ROBOTSTXT_OBEY": false,
      "DOWNLOAD_DELAY": 1
    }
  }'
```

### レスポンス例

```json
{
  "task_id": "12345678-1234-1234-1234-123456789abc",
  "celery_task_id": "12345678-1234-1234-1234-123456789abc",
  "status": "started_with_watchdog",
  "monitoring": "jsonl_file_watchdog",
  "spider_name": "example_spider",
  "project_name": "example_project",
  "message": "Spider example_spider started with watchdog monitoring"
}
```

## 🔧 方法2: scrapy crawlwithwatchdog コマンド

### 前提条件

```bash
# watchdogライブラリをインストール
pip install watchdog
```

### 基本的な使用方法

```bash
# プロジェクトディレクトリに移動
cd scrapy_projects/your_project

# watchdog監視付きでスパイダーを実行
scrapy crawlwithwatchdog spider_name -o results.jsonl --task-id=test_123
```

### オプション

```bash
scrapy crawlwithwatchdog spider_name [オプション]

オプション:
  -o, --output FILE         JSONLファイルの出力先（必須）
  --task-id TASK_ID        タスクID（省略時は自動生成）
  --db-path DB_PATH        データベースパス（デフォルト: backend/database/scrapy_ui.db）
  -h, --help               ヘルプを表示
```

### 使用例

```bash
# 基本的な実行
scrapy crawlwithwatchdog my_spider -o results.jsonl

# タスクIDを指定
scrapy crawlwithwatchdog my_spider -o results.jsonl --task-id=custom_task_123

# データベースパスを指定
scrapy crawlwithwatchdog my_spider -o results.jsonl --db-path=/path/to/custom.db

# Scrapyの標準オプションも使用可能
scrapy crawlwithwatchdog my_spider -o results.jsonl -s LOG_LEVEL=DEBUG -s DOWNLOAD_DELAY=2
```

## 📊 動作の仕組み

### 1. 実行開始

```bash
🚀 Starting spider with watchdog monitoring
   Spider: example_spider
   Task ID: cmd_example_spider_1703123456
   Output: results.jsonl
   DB Path: backend/database/scrapy_ui.db
   Watchdog Available: Yes
```

### 2. 監視開始

```bash
🔍 watchdog監視開始: /path/to/results.jsonl
🕷️ Starting Scrapy crawler...
```

### 3. リアルタイム処理

```bash
📝 新しい行を検出: 5件
✅ DBインサート成功: item_id_1
✅ DBインサート成功: item_id_2
✅ DBインサート成功: item_id_3
✅ DBインサート成功: item_id_4
✅ DBインサート成功: item_id_5
📊 総処理済みアイテム数: 5
```

### 4. 完了

```bash
🛑 監視停止: 処理済み行数 25

📊 Final Statistics:
   Total items processed: 25
   Output file: results.jsonl
   Database: backend/database/scrapy_ui.db
✅ crawlwithwatchdog completed
```

## 🔍 利用可能なコマンドの確認

```bash
# プロジェクトで利用可能なコマンドを確認
curl -X GET "http://localhost:8000/api/spiders/commands/available?project_id={project_id}" \
  -H "Authorization: Bearer {token}"
```

### レスポンス例

```json
{
  "standard_commands": [
    {
      "name": "crawl",
      "description": "Run a spider",
      "usage": "scrapy crawl <spider_name>",
      "watchdog_support": false
    }
  ],
  "custom_commands": [
    {
      "name": "crawlwithwatchdog",
      "description": "Run a spider with watchdog monitoring for real-time DB insertion",
      "usage": "scrapy crawlwithwatchdog <spider_name> -o results.jsonl --task-id=<task_id>",
      "watchdog_support": true,
      "file_path": "/path/to/project/commands/crawlwithwatchdog.py",
      "requirements": []
    }
  ],
  "watchdog_available": true
}
```

## 🛠️ トラブルシューティング

### watchdogライブラリが見つからない

```bash
❌ watchdogライブラリが利用できません。ポーリング監視を使用します。
🔄 ポーリング監視開始: /path/to/results.jsonl
```

**解決方法:**
```bash
pip install watchdog
```

### 出力ファイルが指定されていない

```bash
❌ Usage error: Output file (-o) is required for watchdog monitoring
```

**解決方法:**
```bash
scrapy crawlwithwatchdog spider_name -o results.jsonl
```

### データベース接続エラー

```bash
❌ DBインサートエラー: no such table: scraped_items
```

**解決方法:**
1. データベースパスを確認
2. ScrapyUIのデータベースが正しく初期化されているか確認

### プロジェクトにコマンドが見つからない

```bash
❌ crawlwithwatchdogコマンドが見つかりません
```

**解決方法:**
1. 新しいプロジェクトを作成（自動的にコマンドが追加されます）
2. 既存プロジェクトの場合は、手動でコマンドファイルを追加

## 📈 パフォーマンス比較

| 方法 | リアルタイム性 | 設定の簡単さ | 監視効率 | 推奨用途 |
|------|---------------|-------------|----------|----------|
| **ScrapyUI API** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | WebUI、自動化 |
| **crawlwithwatchdog** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | コマンドライン、開発 |

## 🎯 推奨される使用方法

### 開発・テスト時
```bash
# コマンドラインで直接実行
scrapy crawlwithwatchdog my_spider -o test_results.jsonl --task-id=dev_test
```

### 本番・自動化時
```bash
# ScrapyUI API経由で実行
curl -X POST "http://localhost:8000/api/spiders/{spider_id}/run-with-watchdog?project_id={project_id}"
```

### WebUI使用時
- ブラウザでScrapyUI WebUIにアクセス
- プロジェクト → スパイダー → 実行ボタン

## 🔧 カスタマイズ

### データベーステーブル構造

```sql
CREATE TABLE scraped_items (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    project_id TEXT,
    spider_name TEXT,
    data TEXT,  -- JSON形式のアイテムデータ
    scraped_at TEXT,
    created_at TEXT
);
```

### 監視間隔の調整

コマンドファイル内の `time.sleep(1)` を変更することで、ポーリング監視の間隔を調整できます。

## 📚 関連ドキュメント

- [ScrapyUI API ドキュメント](http://localhost:8000/docs)
- [Scrapy公式ドキュメント](https://docs.scrapy.org/)
- [watchdogライブラリ](https://python-watchdog.readthedocs.io/)
