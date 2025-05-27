import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from croniter import croniter
from sqlalchemy.orm import Session

from ..database import SessionLocal, Schedule as DBSchedule
from ..tasks.scrapy_tasks import run_spider_task
from ..celery_app import celery_app


class SchedulerService:
    """
    スケジュール自動実行サービス
    croniterを使用してスケジュールされたタスクを自動実行
    """
    
    def __init__(self):
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.check_interval = 60  # 1分ごとにチェック
        self.active_schedules: Dict[str, datetime] = {}
        
    def start(self):
        """スケジューラーを開始"""
        if self.running:
            print("⚠️ Scheduler is already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        print("✅ Scheduler service started")
        
    def stop(self):
        """スケジューラーを停止"""
        if not self.running:
            return
            
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        print("🛑 Scheduler service stopped")
        
    def _run_scheduler(self):
        """スケジューラーのメインループ"""
        print("🔄 Scheduler main loop started")
        
        while self.running:
            try:
                self._check_and_execute_schedules()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"❌ Scheduler error: {str(e)}")
                time.sleep(self.check_interval)
                
    def _check_and_execute_schedules(self):
        """スケジュールをチェックして実行"""
        db = SessionLocal()
        
        try:
            # アクティブなスケジュールを取得
            schedules = db.query(DBSchedule).filter(
                DBSchedule.is_active == True
            ).all()
            
            current_time = datetime.now()
            executed_count = 0
            
            for schedule in schedules:
                try:
                    # 次回実行時刻をチェック
                    if self._should_execute_schedule(schedule, current_time):
                        self._execute_schedule(schedule, db)
                        executed_count += 1
                        
                    # 次回実行時刻を更新
                    self._update_next_run_time(schedule, db)
                    
                except Exception as e:
                    print(f"❌ Error processing schedule {schedule.name}: {str(e)}")
                    
            if executed_count > 0:
                print(f"✅ Executed {executed_count} scheduled tasks")
                
        except Exception as e:
            print(f"❌ Error in schedule check: {str(e)}")
        finally:
            db.close()
            
    def _should_execute_schedule(self, schedule: DBSchedule, current_time: datetime) -> bool:
        """スケジュールを実行すべきかチェック"""
        try:
            # next_runが設定されていない場合は計算
            if not schedule.next_run:
                cron = croniter(schedule.cron_expression, current_time)
                schedule.next_run = cron.get_next(datetime)
                return False
                
            # 実行時刻に達しているかチェック
            if current_time >= schedule.next_run:
                # 重複実行を防ぐため、最後の実行から最低1分は空ける
                if schedule.last_run:
                    time_since_last = current_time - schedule.last_run
                    if time_since_last.total_seconds() < 60:
                        return False
                return True
                
            return False
            
        except Exception as e:
            print(f"❌ Error checking schedule {schedule.name}: {str(e)}")
            return False
            
    def _execute_schedule(self, schedule: DBSchedule, db: Session):
        """スケジュールを実行"""
        try:
            print(f"🚀 Executing scheduled task: {schedule.name}")
            
            # Celeryタスクとして実行
            task = run_spider_task.delay(
                schedule.project_id,
                schedule.spider_id,
                schedule.settings or {}
            )
            
            # 実行時刻を更新
            schedule.last_run = datetime.now()
            
            # 次回実行時刻を計算
            cron = croniter(schedule.cron_expression, datetime.now())
            schedule.next_run = cron.get_next(datetime)
            
            db.commit()
            
            print(f"✅ Scheduled task executed: {schedule.name} (Task ID: {task.id})")
            print(f"📅 Next run: {schedule.next_run}")
            
        except Exception as e:
            print(f"❌ Error executing schedule {schedule.name}: {str(e)}")
            db.rollback()
            
    def _update_next_run_time(self, schedule: DBSchedule, db: Session):
        """次回実行時刻を更新"""
        try:
            # next_runが設定されていない場合のみ更新
            if not schedule.next_run:
                cron = croniter(schedule.cron_expression, datetime.now())
                schedule.next_run = cron.get_next(datetime)
                db.commit()
                
        except Exception as e:
            print(f"❌ Error updating next run time for {schedule.name}: {str(e)}")
            
    def get_status(self) -> Dict:
        """スケジューラーの状態を取得"""
        db = SessionLocal()
        
        try:
            schedules = db.query(DBSchedule).filter(
                DBSchedule.is_active == True
            ).all()
            
            return {
                "running": self.running,
                "check_interval": self.check_interval,
                "active_schedules_count": len(schedules),
                "schedules": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "cron_expression": s.cron_expression,
                        "last_run": s.last_run.isoformat() if s.last_run else None,
                        "next_run": s.next_run.isoformat() if s.next_run else None
                    }
                    for s in schedules
                ]
            }
            
        except Exception as e:
            return {
                "running": self.running,
                "error": str(e)
            }
        finally:
            db.close()


# グローバルインスタンス
scheduler_service = SchedulerService()
