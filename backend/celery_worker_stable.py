import sys

def start_celery_worker():
    """Celeryワーカーを起動する"""
    max_retries = 20  # 再起動制限を20回に増加
    retry_interval = 30  # 再起動間隔を30秒に設定
    
    command = [
        sys.executable, "-m", "celery",
        "-A", "app.celery_app", "worker",
        "--loglevel=info",
        "--concurrency=2",
        "--queues=scrapy,monitoring,maintenance",
        "--pool=prefork",
        "--max-memory-per-child=500000",
        "--max-tasks-per-child=100",
        "--time-limit=3600",
        "--soft-time-limit=3300",
        "--without-gossip",
        "--without-mingle",
        "--without-heartbeat",
        "--optimization=fair"
    ]

    # ... existing code ... 