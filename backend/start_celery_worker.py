#!/usr/bin/env python3
"""
Celeryワーカーを起動するスクリプト
"""

import sys
import os
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# 環境変数を設定
os.environ.setdefault('PYTHONPATH', str(backend_dir))

if __name__ == "__main__":
    from app.celery_app import celery_app
    
    print("🚀 Starting Celery worker...")
    print(f"📁 Backend directory: {backend_dir}")
    print(f"🔧 Python path: {sys.path}")
    
    # Celeryワーカーを起動
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',
        '--queues=scrapy,maintenance,monitoring'
    ])
