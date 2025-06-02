# ScrapyUI Rich Progress Bar 設定例
# スパイダーコードを一切変更せずに進捗バーを追加する方法

# ===== 基本設定 =====
BOT_NAME = 'myproject'
SPIDER_MODULES = ['myproject.spiders']
NEWSPIDER_MODULE = 'myproject.spiders'

# ===== Rich進捗バー設定 =====
# 拡張機能を有効化
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
    'scrapy.extensions.corestats.CoreStats': 500,
    'scrapy.extensions.memusage.MemoryUsage': 500,
    'scrapy.extensions.logstats.LogStats': 500,
    # Rich進捗バー拡張機能を追加
    'app.scrapy_extensions.rich_progress_extension.RichProgressExtension': 400,
}

# Rich進捗バーの詳細設定
RICH_PROGRESS_ENABLED = True           # 進捗バーを有効化
RICH_PROGRESS_SHOW_STATS = True        # 詳細統計を表示
RICH_PROGRESS_UPDATE_INTERVAL = 0.1    # 更新間隔（秒）
RICH_PROGRESS_WEBSOCKET = False        # WebSocket通知（オプション）

# ===== その他のScrapy設定 =====
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# ===== ログ設定 =====
LOG_LEVEL = 'INFO'

# ===== フィード設定 =====
FEEDS = {
    'results.jsonl': {
        'format': 'jsonlines',
        'encoding': 'utf8',
        'store_empty': False,
    }
}

# ===== User Agent =====
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# ===== 進捗バーのカスタマイズ例 =====

# 1. シンプルな進捗バーのみ表示
# RICH_PROGRESS_SHOW_STATS = False

# 2. 高頻度更新（リアルタイム）
# RICH_PROGRESS_UPDATE_INTERVAL = 0.05

# 3. WebSocket通知を有効化（ScrapyUIと連携）
# RICH_PROGRESS_WEBSOCKET = True

# 4. 進捗バーを無効化
# RICH_PROGRESS_ENABLED = False

# ===== 使用方法 =====
"""
この設定ファイルを使用すると、既存のスパイダーコードを一切変更せずに
美しい進捗バーが自動的に表示されます。

実行例:
scrapy crawl myspider

表示例:
🕷️ myspider ━━━━━━━━━━━━━━━━━━ 75% 150/200 • 00:02:30

📊 スクレイピング統計
┌─────────────┬──────────┐
│ 項目        │ 値       │
├─────────────┼──────────┤
│ 📤 リクエスト │ 200      │
│ 📥 レスポンス │ 195      │
│ 📦 アイテム   │ 150      │
│ ❌ エラー     │ 5        │
│ ⏱️ 経過時間   │ 150.5秒  │
│ 🚀 処理速度   │ 1.0 items/sec │
└─────────────┴──────────┘
"""
