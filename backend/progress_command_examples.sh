#!/bin/bash

# ScrapyUI Rich Progress Bar コマンドライン実行例
# スパイダーコードを変更せずに進捗バーを有効化する方法

echo "🎨 ScrapyUI Rich Progress Bar コマンドライン実行例"
echo "=" * 60

# ===== 基本的な使用方法 =====

# 1. 進捗バーを有効化して実行
echo "📊 基本的な進捗バー表示"
scrapy crawl myspider \
    -s RICH_PROGRESS_ENABLED=True \
    -s RICH_PROGRESS_SHOW_STATS=True

# 2. シンプルな進捗バーのみ表示
echo "📈 シンプルな進捗バー表示"
scrapy crawl myspider \
    -s RICH_PROGRESS_ENABLED=True \
    -s RICH_PROGRESS_SHOW_STATS=False

# 3. 高頻度更新でリアルタイム表示
echo "⚡ リアルタイム進捗バー表示"
scrapy crawl myspider \
    -s RICH_PROGRESS_ENABLED=True \
    -s RICH_PROGRESS_UPDATE_INTERVAL=0.05

# 4. WebSocket通知を有効化
echo "🌐 WebSocket通知付き進捗バー"
scrapy crawl myspider \
    -s RICH_PROGRESS_ENABLED=True \
    -s RICH_PROGRESS_WEBSOCKET=True

# ===== 拡張機能の動的設定 =====

# 5. 拡張機能を動的に追加
echo "🔧 拡張機能を動的に追加"
scrapy crawl myspider \
    -s EXTENSIONS='{"app.scrapy_extensions.rich_progress_extension.RichProgressExtension": 400}'

# 6. 既存の拡張機能と組み合わせ
echo "🔗 既存拡張機能と組み合わせ"
scrapy crawl myspider \
    -s EXTENSIONS='{
        "scrapy.extensions.corestats.CoreStats": 500,
        "scrapy.extensions.logstats.LogStats": 500,
        "app.scrapy_extensions.rich_progress_extension.RichProgressExtension": 400
    }'

# ===== ScrapyUI特有のコマンド =====

# 7. ScrapyUIのcrawlwithwatchdogコマンドで実行
echo "🐕 ScrapyUI watchdog付き実行"
scrapy crawlwithwatchdog myspider \
    -o results.jsonl \
    --task-id task-123 \
    -s RICH_PROGRESS_ENABLED=True \
    -s RICH_PROGRESS_SHOW_STATS=True

# 8. 大容量データ処理用設定
echo "📦 大容量データ処理用設定"
scrapy crawl myspider \
    -s RICH_PROGRESS_ENABLED=True \
    -s RICH_PROGRESS_SHOW_STATS=True \
    -s CONCURRENT_REQUESTS=2 \
    -s DOWNLOAD_DELAY=1.0 \
    -s AUTOTHROTTLE_ENABLED=True

# ===== 環境変数での設定 =====

# 9. 環境変数で設定
echo "🌍 環境変数での設定"
export SCRAPY_SETTINGS_MODULE=myproject.settings
export RICH_PROGRESS_ENABLED=True
export RICH_PROGRESS_SHOW_STATS=True
scrapy crawl myspider

# ===== デバッグ用設定 =====

# 10. デバッグ情報付きで実行
echo "🐛 デバッグ情報付き実行"
scrapy crawl myspider \
    -s RICH_PROGRESS_ENABLED=True \
    -s RICH_PROGRESS_SHOW_STATS=True \
    -s LOG_LEVEL=DEBUG \
    -L DEBUG

# ===== カスタム設定ファイルの使用 =====

# 11. カスタム設定ファイルを使用
echo "⚙️ カスタム設定ファイル使用"
scrapy crawl myspider \
    --set=SETTINGS_MODULE=myproject.custom_settings

# 12. 設定ファイルを指定して実行
echo "📄 設定ファイル指定実行"
scrapy crawl myspider \
    --custom-settings='{"RICH_PROGRESS_ENABLED": true, "RICH_PROGRESS_SHOW_STATS": true}'

# ===== 実行結果の例 =====
echo "
🎯 実行結果の例:

🕷️ myspider ━━━━━━━━━━━━━━━━━━ 75% 150/200 • 00:02:30

┌─────────────────────────────────────────────────────────┐
│                    🎯 進捗状況                          │
├─────────────────────────────────────────────────────────┤
│ 🕷️ myspider ━━━━━━━━━━━━━━━━━━ 75% 150/200 • 00:02:30    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    📈 詳細統計                          │
├─────────────┬───────────────────────────────────────────┤
│ 項目        │ 値                                       │
├─────────────┼───────────────────────────────────────────┤
│ 📤 リクエスト │ 200                                      │
│ 📥 レスポンス │ 195                                      │
│ 📦 アイテム   │ 150                                      │
│ ❌ エラー     │ 5                                        │
│ ⏱️ 経過時間   │ 150.5秒                                  │
│ 🚀 処理速度   │ 1.0 items/sec                           │
└─────────────┴───────────────────────────────────────────┘

🏁 myspider 完了レポート
┌─────────────────┬─────────────────┐
│ 項目            │ 値              │
├─────────────────┼─────────────────┤
│ 📤 総リクエスト数 │ 200             │
│ 📥 総レスポンス数 │ 195             │
│ 📦 総アイテム数   │ 150             │
│ ❌ エラー数       │ 5               │
│ ⏱️ 総実行時間     │ 150.50秒        │
│ 🏁 終了理由       │ finished        │
│ 🚀 平均処理速度   │ 1.00 items/sec  │
└─────────────────┴─────────────────┘
"

echo "✅ すべてのコマンド例を確認しました！"
