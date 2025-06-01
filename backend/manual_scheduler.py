#!/usr/bin/env python3
"""
手動スケジューラー - データベースのスケジュールを定期的にチェックして実行
"""

import time
import logging
from datetime import datetime, timedelta
from croniter import croniter
from app.database import SessionLocal, Schedule as DBSchedule, Task as DBTask, TaskStatus
from app.tasks.scrapy_tasks import scheduled_spider_run

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ManualScheduler:
    """手動スケジューラー"""
    
    def __init__(self, check_interval=60):
        """
        初期化
        
        Args:
            check_interval (int): チェック間隔（秒）
        """
        self.check_interval = check_interval
        self.running = False
        
    def start(self):
        """スケジューラーを開始"""
        self.running = True
        logger.info("🚀 手動スケジューラーを開始しました")
        
        try:
            while self.running:
                self.check_and_execute_schedules()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("🛑 手動スケジューラーを停止しました")
        except Exception as e:
            logger.error(f"❌ スケジューラーエラー: {e}")
        finally:
            self.running = False
    
    def stop(self):
        """スケジューラーを停止"""
        self.running = False
        logger.info("🛑 手動スケジューラーの停止を要求しました")
    
    def check_and_execute_schedules(self):
        """スケジュールをチェックして実行"""
        db = SessionLocal()
        
        try:
            # アクティブなスケジュールを取得
            schedules = db.query(DBSchedule).filter(
                DBSchedule.is_active == True
            ).all()
            
            logger.info(f"📋 {len(schedules)}個のアクティブなスケジュールをチェック中...")
            
            for schedule in schedules:
                if self.should_execute_schedule(schedule):
                    self.execute_schedule(schedule, db)
                    
        except Exception as e:
            logger.error(f"❌ スケジュールチェックエラー: {e}")
        finally:
            db.close()
    
    def should_execute_schedule(self, schedule):
        """スケジュールを実行すべきかチェック"""
        try:
            now = datetime.now()
            
            # 次回実行時刻をチェック
            if schedule.next_run and schedule.next_run <= now:
                logger.info(f"⏰ スケジュール「{schedule.name}」の実行時刻です")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"❌ スケジュール実行判定エラー: {e}")
            return False
    
    def execute_schedule(self, schedule, db):
        """スケジュールを実行"""
        try:
            # 重複実行チェック
            running_tasks = db.query(DBTask).filter(
                DBTask.schedule_id == schedule.id,
                DBTask.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING])
            ).count()
            
            if running_tasks > 0:
                logger.warning(f"⚠️ スケジュール「{schedule.name}」は既に実行中です ({running_tasks}個のタスク)")
                return
            
            logger.info(f"🚀 スケジュール「{schedule.name}」を実行します")
            
            # Celeryタスクとして実行
            task = scheduled_spider_run.delay(schedule.id)
            logger.info(f"✅ タスクを送信しました: {task.id}")
            
            # 次回実行時刻を更新
            self.update_next_run(schedule, db)
            
        except Exception as e:
            logger.error(f"❌ スケジュール実行エラー: {e}")
    
    def update_next_run(self, schedule, db):
        """次回実行時刻を更新"""
        try:
            now = datetime.now()
            cron = croniter(schedule.cron_expression, now)
            next_run = cron.get_next(datetime)
            
            schedule.last_run = now
            schedule.next_run = next_run
            
            db.commit()
            
            logger.info(f"📅 スケジュール「{schedule.name}」の次回実行: {next_run}")
            
        except Exception as e:
            logger.error(f"❌ 次回実行時刻更新エラー: {e}")
            db.rollback()

def main():
    """メイン関数"""
    scheduler = ManualScheduler(check_interval=30)  # 30秒ごとにチェック
    scheduler.start()

if __name__ == "__main__":
    main()
