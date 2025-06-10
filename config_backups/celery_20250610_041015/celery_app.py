from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init, worker_shutdown
import os
import signal
import logging

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
    task_time_limit=3600,  # タイムアウトを60分に設定
    task_soft_time_limit=3300,  # ソフトタイムアウトを55分に設定
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,  # タスク数制限を50に設定（安定性とパフォーマンスのバランス）
    worker_max_memory_per_child=300000,  # メモリ制限を300MBに設定（OOM防止）
    # 重複実行防止とタイムアウト設定
    task_acks_late=True,  # タスク完了後にackを送信
    worker_disable_rate_limits=True,  # レート制限を無効化
    task_reject_on_worker_lost=True,  # ワーカー停止時にタスクを拒否
    # ワーカー安定性向上
    worker_pool_restarts=True,  # プールの自動再起動
    worker_autoscaler='celery.worker.autoscale:Autoscaler',
    worker_concurrency=1,  # 同時実行数を1に削減（安定性最優先）
    # 安定性向上設定
    worker_send_task_events=True,  # タスクイベント送信を有効化
    task_send_sent_event=True,  # タスク送信イベントを有効化
    task_ignore_result=False,  # 結果を無視しない
    result_expires=3600,  # 結果の有効期限を1時間に設定
    # エラーハンドリング
    task_annotations={
        '*': {
            'rate_limit': '20/m',  # 1分間に20タスクまで（制限緩和）
            'time_limit': 3600,    # 60分タイムアウト
            'soft_time_limit': 3300,  # 55分ソフトタイムアウト
        }
    },
    # Redis接続設定
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=20,
    broker_transport_options={
        'visibility_timeout': 3600,
        'retry_policy': {
            'timeout': 5.0
        }
    },
    result_backend_transport_options={
        'visibility_timeout': 3600,
        'retry_policy': {
            'timeout': 5.0
        }
    },
    # ワーカーの安定性向上
    worker_hijack_root_logger=False,
    worker_log_color=False,
    worker_redirect_stdouts=True,
    worker_redirect_stdouts_level='INFO',
    # プロセス管理の改善（SIGTERM対策強化）
    worker_proc_alive_timeout=10.0,  # プロセス生存確認タイムアウト
    worker_cancel_long_running_tasks_on_connection_loss=True,  # 接続切断時に長時間タスクをキャンセル
    worker_enable_remote_control=True,  # リモート制御を有効化

    # SIGTERM対策（プロセス安定性向上）
    worker_pool='prefork',  # プロセスプールを明示的に指定
    worker_lost_wait=10.0,  # ワーカー失敗時の待機時間

    # グレースフルシャットダウン設定
    worker_shutdown_timeout=30,  # シャットダウンタイムアウト
    worker_timer_precision=1.0,  # タイマー精度
    # Beat設定
    beat_schedule_filename='celerybeat-schedule',
    beat_sync_every=1,
    beat_max_loop_interval=5,
    max_retries=20,
    retry_interval=30
)

# 定期実行タスクの設定
celery_app.conf.beat_schedule = {
    # 毎日午前2時にクリーンアップタスクを実行
    'cleanup-old-results': {
        'task': 'app.tasks.scrapy_tasks.cleanup_old_results',
        'schedule': crontab(hour=2, minute=0),
    },
    # 5分ごとにシステムヘルスチェック
    'system-health-check': {
        'task': 'app.tasks.scrapy_tasks.system_health_check',
        'schedule': crontab(minute='*/5'),
    },
    # 2分ごとに失敗タスクの自動修復（失敗判定を自動修復に委任）
    'auto-repair-failed-tasks': {
        'task': 'app.tasks.scrapy_tasks.auto_repair_failed_tasks',
        'schedule': crontab(minute='*/2'),
    },
    # 30分ごりにスタックしたタスクをクリーンアップ
    'cleanup-stuck-tasks': {
        'task': 'app.tasks.scrapy_tasks.cleanup_stuck_tasks',
        'schedule': crontab(minute='*/30'),
    },
    # 15分ごとにタスク統計の検証・修正（根本対応）
    'validate-task-statistics': {
        'task': 'app.tasks.scrapy_tasks.validate_task_statistics',
        'schedule': crontab(minute='*/15'),
    },
}

# タスクルーティング（根本対応強化版）
celery_app.conf.task_routes = {
    'app.tasks.scrapy_tasks.run_spider_task': {'queue': 'scrapy'},
    'app.tasks.scrapy_tasks.scheduled_spider_run': {'queue': 'scrapy'},  # スケジュール実行もscrapyキューに配置
    'app.tasks.scrapy_tasks.auto_repair_failed_tasks': {'queue': 'maintenance'},
    'app.tasks.scrapy_tasks.cleanup_old_results': {'queue': 'maintenance'},
    'app.tasks.scrapy_tasks.cleanup_stuck_tasks': {'queue': 'maintenance'},  # スタックタスククリーンアップ
    'app.tasks.scrapy_tasks.validate_task_statistics': {'queue': 'maintenance'},  # 統計検証タスク
    'app.tasks.scrapy_tasks.system_health_check': {'queue': 'monitoring'},
}

# Celeryワーカーのシグナルハンドリング（SIGTERM対策）
@worker_process_init.connect
def worker_process_init_handler(sender=None, **kwargs):
    """ワーカープロセス初期化時のシグナルハンドラー"""
    def graceful_shutdown_handler(signum, frame):
        """グレースフルシャットダウンハンドラー"""
        logging.info(f"🛑 Worker received signal {signum}, initiating graceful shutdown...")
        # 現在実行中のタスクを完了させてからシャットダウン
        import sys
        sys.exit(0)

    # SIGTERMとSIGINTのハンドラーを設定
    signal.signal(signal.SIGTERM, graceful_shutdown_handler)
    signal.signal(signal.SIGINT, graceful_shutdown_handler)
    logging.info("🔧 Worker signal handlers configured for graceful shutdown")

@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """ワーカーシャットダウン時のクリーンアップ"""
    logging.info("🛑 Worker shutdown completed")

if __name__ == '__main__':
    celery_app.start()
