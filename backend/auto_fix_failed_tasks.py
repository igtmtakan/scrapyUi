#!/usr/bin/env python3
"""
自動失敗タスク修正サービス

定期的に失敗タスクをチェックし、結果ファイルがある場合は自動的に修正します。
"""

import os
import sys
import time
import schedule
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fix_failed_tasks import fix_failed_tasks

def auto_fix_service():
    """自動修正サービス"""
    print(f"\n🔄 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting auto-fix service...")
    
    try:
        fix_failed_tasks()
        print(f"✅ Auto-fix completed successfully")
    except Exception as e:
        print(f"❌ Auto-fix failed: {e}")

def run_scheduler():
    """スケジューラーを実行"""
    print("🚀 Starting auto-fix scheduler...")
    print("📅 Schedule: Every 5 minutes")
    print("🔧 Function: Check and fix failed tasks with results")
    print("⏹️  Press Ctrl+C to stop")
    
    # 5分ごとに実行
    schedule.every(5).minutes.do(auto_fix_service)
    
    # 初回実行
    auto_fix_service()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # 30秒ごとにチェック
    except KeyboardInterrupt:
        print("\n⏹️  Auto-fix scheduler stopped")

if __name__ == "__main__":
    run_scheduler()
