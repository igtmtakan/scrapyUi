#!/usr/bin/env python3
"""
手動でwatchdog監視を開始してからscrapy crawlを実行する例
"""
import asyncio
import subprocess
import sys
from pathlib import Path

# watchdog監視クラスをインポート
sys.path.append('backend/app/services')
from scrapy_watchdog_monitor import ScrapyWatchdogMonitor

async def manual_watchdog_scrapy():
    """手動でwatchdog監視付きscrapy crawlを実行"""
    
    print("🎯 手動watchdog監視 + scrapy crawl実行例")
    
    # 設定
    task_id = "manual_test_123"
    project_path = "scrapy_projects/test_project"  # 実際のプロジェクトパスに変更
    spider_name = "test_spider"  # 実際のスパイダー名に変更
    
    # WebSocketコールバック例
    async def websocket_callback(data):
        print(f"📡 リアルタイム通知: {data}")
    
    # watchdog監視クラスを作成
    monitor = ScrapyWatchdogMonitor(
        task_id=task_id,
        project_path=project_path,
        spider_name=spider_name,
        websocket_callback=websocket_callback
    )
    
    # watchdog監視付きで実行
    result = await monitor.execute_spider_with_monitoring({
        'LOG_LEVEL': 'INFO',
        'ROBOTSTXT_OBEY': False
    })
    
    print(f"🎉 実行結果: {result}")

if __name__ == "__main__":
    asyncio.run(manual_watchdog_scrapy())
