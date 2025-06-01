#!/usr/bin/env python3
"""
Celeryワーカーを起動するスクリプト
"""

import sys
import os
import signal
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# 環境変数を設定
os.environ.setdefault('PYTHONPATH', str(backend_dir))

def signal_handler(signum, _frame):
    """シグナルハンドラー"""
    print(f"\n🛑 Received signal {signum}. Shutting down Celery worker...")
    sys.exit(0)

if __name__ == "__main__":
    # シグナルハンドラーを設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        from app.celery_app import celery_app

        print("🚀 Starting Celery worker...")
        print(f"📁 Backend directory: {backend_dir}")
        print(f"🔧 Python path: {sys.path}")
        print("⚙️ Worker configuration:")
        print("   - Log level: INFO")
        print("   - Concurrency: 2")
        print("   - Queues: scrapy, maintenance, monitoring")
        print("🔄 Press Ctrl+C to stop the worker")

        # Celeryワーカーを起動（安定性向上設定）
        celery_app.worker_main([
            'worker',
            '--loglevel=info',
            '--concurrency=2',
            '--queues=scrapy,maintenance,monitoring',
            '--pool=prefork',
            '--optimization=fair',
            '--max-tasks-per-child=200',  # タスク数制限を緩和
            '--max-memory-per-child=500000',  # 500MB制限（メモリ制限緩和）
            '--time-limit=3600',  # 60分タイムアウト
            '--soft-time-limit=3300',  # 55分ソフトタイムアウト
            '--without-gossip',  # ゴシップを無効化（パフォーマンス向上）
            '--without-mingle',  # ミングルを無効化（起動高速化）
            '--without-heartbeat',  # ハートビートを無効化（ネットワーク負荷軽減）
            '--prefetch-multiplier=1',  # プリフェッチを1に制限
        ])

    except KeyboardInterrupt:
        print("\n🛑 Celery worker stopped by user")
    except Exception as e:
        print(f"❌ Error starting Celery worker: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
