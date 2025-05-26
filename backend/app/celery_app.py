from celery import Celery
from celery.schedules import crontab
import os

# Celeryアプリケーションの作成
celery_app = Celery(
    "scrapy_ui",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["app.tasks.scrapy_tasks"]
)

# Celery設定
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tokyo",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分でタイムアウト
    task_soft_time_limit=25 * 60,  # 25分でソフトタイムアウト
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 定期実行タスクの設定
celery_app.conf.beat_schedule = {
    # 例: 毎日午前2時にクリーンアップタスクを実行
    'cleanup-old-results': {
        'task': 'app.tasks.scrapy_tasks.cleanup_old_results',
        'schedule': crontab(hour=2, minute=0),
    },
    # 例: 5分ごとにシステムヘルスチェック
    'system-health-check': {
        'task': 'app.tasks.scrapy_tasks.system_health_check',
        'schedule': crontab(minute='*/5'),
    },
}

# タスクルーティング
celery_app.conf.task_routes = {
    'app.tasks.scrapy_tasks.run_spider_task': {'queue': 'scrapy'},
    'app.tasks.scrapy_tasks.cleanup_old_results': {'queue': 'maintenance'},
    'app.tasks.scrapy_tasks.system_health_check': {'queue': 'monitoring'},
}

if __name__ == '__main__':
    celery_app.start()
