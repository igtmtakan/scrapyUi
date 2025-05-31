#!/bin/bash
"""
scrapy crawlコマンドをwatchdog監視付きで実行するシェルスクリプト
使用例: ./scrapy_with_watchdog.sh spider_name
"""

# 設定
SPIDER_NAME=$1
TASK_ID=${2:-"shell_$(date +%s)"}
PROJECT_PATH=$(pwd)
OUTPUT_FILE="results_${TASK_ID}.jsonl"
DB_PATH="backend/database/scrapy_ui.db"

if [ -z "$SPIDER_NAME" ]; then
    echo "❌ Usage: $0 <spider_name> [task_id]"
    exit 1
fi

echo "🎯 Starting Scrapy with watchdog monitoring"
echo "   Spider: $SPIDER_NAME"
echo "   Task ID: $TASK_ID"
echo "   Output: $OUTPUT_FILE"
echo "   Project: $PROJECT_PATH"

# Python watchdog監視スクリプトを作成
cat > /tmp/watchdog_monitor_${TASK_ID}.py << EOF
#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append('${PROJECT_PATH}/backend/app/services')

from scrapy_watchdog_monitor import ScrapyWatchdogMonitor

async def main():
    monitor = ScrapyWatchdogMonitor(
        task_id='${TASK_ID}',
        project_path='${PROJECT_PATH}',
        spider_name='${SPIDER_NAME}',
        db_path='${DB_PATH}'
    )
    
    await monitor._start_jsonl_monitoring('${OUTPUT_FILE}')

if __name__ == "__main__":
    asyncio.run(main())
EOF

# watchdog監視をバックグラウンドで開始
echo "🔍 Starting watchdog monitoring..."
python /tmp/watchdog_monitor_${TASK_ID}.py &
WATCHDOG_PID=$!

# 少し待ってからScrapyを開始
sleep 2

echo "🚀 Starting Scrapy crawler..."
scrapy crawl $SPIDER_NAME -o $OUTPUT_FILE -s FEED_FORMAT=jsonlines -s LOG_LEVEL=INFO

# Scrapyが完了したらwatchdog監視を停止
echo "🛑 Stopping watchdog monitoring..."
kill $WATCHDOG_PID 2>/dev/null

# 一時ファイルを削除
rm -f /tmp/watchdog_monitor_${TASK_ID}.py

echo "✅ Scrapy with watchdog monitoring completed"
echo "   Results saved to: $OUTPUT_FILE"
echo "   Database updated with real-time inserts"
