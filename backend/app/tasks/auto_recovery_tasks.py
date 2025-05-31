"""
自動修復タスク

Celeryを使用して定期的にタスクの自動修復を実行
"""

import logging
from datetime import datetime

from ..celery_app import celery_app
from ..services.task_auto_recovery import task_auto_recovery_service

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def run_auto_recovery_task(self, hours_back: int = 24):
    """
    自動修復タスクを実行
    
    Args:
        hours_back: 過去何時間のタスクをチェックするか
    """
    try:
        logger.info(f"🔧 Starting scheduled auto recovery task (hours_back={hours_back})")
        
        # 非同期関数を同期的に実行
        import asyncio
        
        async def run_recovery():
            return await task_auto_recovery_service.run_auto_recovery(hours_back)
        
        # イベントループを作成して実行
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        recovery_results = loop.run_until_complete(run_recovery())
        
        # 結果をログに記録
        checked_tasks = recovery_results.get('checked_tasks', 0)
        recovered_tasks = recovery_results.get('recovered_tasks', 0)
        
        logger.info(f"✅ Scheduled auto recovery completed: {recovered_tasks}/{checked_tasks} tasks recovered")
        
        # 修復されたタスクの詳細をログに記録
        if recovery_results.get('recovery_details'):
            for detail in recovery_results['recovery_details']:
                logger.info(f"   Recovered task {detail['task_id']}: {detail['items_count']} items")
        
        return {
            'status': 'success',
            'checked_tasks': checked_tasks,
            'recovered_tasks': recovered_tasks,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Scheduled auto recovery failed: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@celery_app.task(bind=True)
def health_check_and_recovery_task(self):
    """
    ヘルスチェックと自動修復を組み合わせたタスク
    
    より頻繁に実行して、問題のあるタスクを早期発見・修復
    """
    try:
        logger.info("🏥 Starting health check and recovery task")
        
        # 過去2時間のタスクをチェック（より頻繁なチェック）
        import asyncio
        
        async def run_health_check():
            return await task_auto_recovery_service.run_auto_recovery(hours_back=2)
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        recovery_results = loop.run_until_complete(run_health_check())
        
        checked_tasks = recovery_results.get('checked_tasks', 0)
        recovered_tasks = recovery_results.get('recovered_tasks', 0)
        
        if recovered_tasks > 0:
            logger.warning(f"⚠️ Health check found and recovered {recovered_tasks} failed tasks")
        else:
            logger.info(f"✅ Health check completed: {checked_tasks} tasks checked, all healthy")
        
        return {
            'status': 'success',
            'type': 'health_check',
            'checked_tasks': checked_tasks,
            'recovered_tasks': recovered_tasks,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Health check and recovery failed: {str(e)}")
        return {
            'status': 'error',
            'type': 'health_check',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# Celeryビートスケジュール設定用の関数
def get_auto_recovery_schedule():
    """
    自動修復タスクのスケジュール設定を返す
    
    Returns:
        dict: Celeryビートスケジュール設定
    """
    return {
        # 毎日午前3時に24時間分の自動修復を実行
        'daily-auto-recovery': {
            'task': 'app.tasks.auto_recovery_tasks.run_auto_recovery_task',
            'schedule': 60 * 60 * 24,  # 24時間ごと
            'args': (24,),  # 過去24時間をチェック
            'options': {
                'expires': 60 * 60,  # 1時間でタイムアウト
            }
        },
        
        # 30分ごとにヘルスチェックと軽微な修復を実行
        'health-check-recovery': {
            'task': 'app.tasks.auto_recovery_tasks.health_check_and_recovery_task',
            'schedule': 60 * 30,  # 30分ごと
            'options': {
                'expires': 60 * 10,  # 10分でタイムアウト
            }
        }
    }
