import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from croniter import croniter
from sqlalchemy.orm import Session

from ..database import SessionLocal, Schedule as DBSchedule
from ..tasks.scrapy_tasks import scheduled_spider_run
from ..celery_app import celery_app


class SchedulerService:
    """
    スケジュール自動実行サービス
    croniterを使用してスケジュールされたタスクを自動実行
    """

    def __init__(self):
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.check_interval = 10  # 10秒ごとにチェック（デバッグ用）
        self.active_schedules: Dict[str, datetime] = {}
        self.last_check_time = None

    def start(self):
        """スケジューラーを開始"""
        if self.running:
            print("⚠️ Scheduler is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()

        # 統計検証スケジュールを追加（根本対応）
        self._setup_statistics_validation()

        print("✅ Scheduler service started with statistics validation")

    def _setup_statistics_validation(self):
        """統計検証スケジュールのセットアップ（根本対応）"""
        try:
            # 統計検証を30分毎に実行するスケジュールを追加
            self.statistics_validation_interval = 30 * 60  # 30分（秒）
            self.last_validation_time = None
            print("🔧 Statistics validation schedule setup completed (every 30 minutes)")
        except Exception as e:
            print(f"❌ Error setting up statistics validation: {str(e)}")

    def _check_and_execute_statistics_validation(self):
        """統計検証の実行チェック（根本対応）"""
        try:
            if not hasattr(self, 'statistics_validation_interval'):
                return

            import pytz
            jst = pytz.timezone('Asia/Tokyo')
            current_time = datetime.now(jst).replace(tzinfo=None)

            # 初回実行または30分経過した場合
            should_validate = False
            if self.last_validation_time is None:
                should_validate = True
                print("🔍 First-time statistics validation")
            else:
                time_since_last = (current_time - self.last_validation_time).total_seconds()
                if time_since_last >= self.statistics_validation_interval:
                    should_validate = True
                    print(f"🔍 Statistics validation due: {time_since_last:.0f}s since last validation")

            if should_validate:
                self._validate_task_statistics()
                self.last_validation_time = current_time

        except Exception as e:
            print(f"❌ Error in statistics validation check: {str(e)}")

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
                # デバッグ用：ループの開始を記録
                import pytz
                jst = pytz.timezone('Asia/Tokyo')
                loop_start = datetime.now(jst).replace(tzinfo=None)
                print(f"🔄 Scheduler loop iteration at {loop_start.strftime('%H:%M:%S.%f')[:-3]}")

                self._check_and_execute_schedules()

                # 統計検証の実行チェック（根本対応）
                self._check_and_execute_statistics_validation()

                # デバッグ用：スリープ前の時刻を記録
                sleep_start = datetime.now(jst).replace(tzinfo=None)
                print(f"😴 Scheduler sleeping for {self.check_interval}s at {sleep_start.strftime('%H:%M:%S.%f')[:-3]}")

                time.sleep(self.check_interval)
            except Exception as e:
                print(f"❌ Scheduler error: {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(self.check_interval)

    def _check_and_execute_schedules(self):
        """スケジュールをチェックして実行"""
        db = SessionLocal()

        try:
            # アクティブなスケジュールを取得
            schedules = db.query(DBSchedule).filter(
                DBSchedule.is_active == True
            ).all()

            # 日本時間（Asia/Tokyo）で統一
            import pytz
            jst = pytz.timezone('Asia/Tokyo')
            current_time = datetime.now(jst).replace(tzinfo=None)
            self.last_check_time = current_time
            executed_count = 0
            checked_count = 0

            # 常に基本情報を出力
            print(f"🔍 Scheduler check at {current_time.strftime('%H:%M:%S')} (JST) - Found {len(schedules)} active schedules")

            for schedule in schedules:
                try:
                    checked_count += 1

                    # 各スケジュールの詳細情報を出力
                    print(f"  📋 {schedule.name}:")
                    print(f"    - Cron: {schedule.cron_expression}")
                    print(f"    - Current: {current_time.strftime('%H:%M:%S')}")
                    print(f"    - Next run: {schedule.next_run.strftime('%H:%M:%S') if schedule.next_run else 'None'}")
                    print(f"    - Last run: {schedule.last_run.strftime('%H:%M:%S') if schedule.last_run else 'None'}")

                    # デバッグ情報を出力
                    should_execute = self._should_execute_schedule(schedule, current_time)
                    print(f"    - Should execute: {should_execute}")

                    # 次回実行時刻をチェック
                    if should_execute:
                        print(f"🚀 Executing scheduled task: {schedule.name}")
                        self._execute_schedule(schedule, db)
                        executed_count += 1

                    # 次回実行時刻を更新
                    self._update_next_run_time(schedule, db)

                    # 変更をコミット
                    db.commit()

                except Exception as e:
                    print(f"❌ Error processing schedule {schedule.name}: {str(e)}")
                    import traceback
                    traceback.print_exc()

            # 実行結果のサマリー
            if executed_count > 0:
                print(f"✅ Executed {executed_count} scheduled tasks")
            elif checked_count > 0 and current_time.minute % 10 == 0:  # 10分ごとに状況報告
                print(f"📊 Checked {checked_count} schedules, none executed at {current_time.strftime('%H:%M:%S')}")

        except Exception as e:
            print(f"❌ Error in schedule check: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()

    def _should_execute_schedule(self, schedule: DBSchedule, current_time: datetime) -> bool:
        """スケジュールを実行すべきかチェック"""
        try:
            # 現在時刻を分単位で丸める（秒・マイクロ秒を0にする）
            current_time_rounded = current_time.replace(second=0, microsecond=0)

            # next_runが設定されていない場合は計算
            if not schedule.next_run:
                # 最後の実行時刻がある場合はそれを基準にする
                base_time = schedule.last_run if schedule.last_run else current_time_rounded
                cron = croniter(schedule.cron_expression, base_time)
                schedule.next_run = cron.get_next(datetime)
                print(f"🔧 Initialized next_run for {schedule.name}: {schedule.next_run.strftime('%H:%M:%S')}")
                return False

            # 詳細な時刻比較情報を出力
            print(f"🔍 Time comparison for {schedule.name}:")
            print(f"  Current: {current_time_rounded} ({current_time_rounded.strftime('%Y-%m-%d %H:%M:%S')})")
            print(f"  Next run: {schedule.next_run} ({schedule.next_run.strftime('%Y-%m-%d %H:%M:%S')})")
            print(f"  Current >= Next: {current_time_rounded >= schedule.next_run}")

            # 実行判定：現在時刻が次回実行時刻以降の場合
            should_execute = current_time_rounded >= schedule.next_run

            if should_execute:
                # 重複実行を防ぐため、最後の実行から最低1分は空ける
                if schedule.last_run:
                    time_since_last = current_time - schedule.last_run
                    if time_since_last.total_seconds() < 60:
                        print(f"⏳ Skipping {schedule.name}: Last run was {time_since_last.total_seconds():.0f}s ago (< 60s)")
                        should_execute = False

                # 実行中タスクチェック（重複実行防止）
                if should_execute:
                    running_tasks = self._check_running_tasks(schedule)
                    if running_tasks:
                        print(f"⏳ Skipping {schedule.name}: {len(running_tasks)} running task(s) found")
                        for task in running_tasks:
                            elapsed = (current_time - task.started_at).total_seconds() if task.started_at else 0
                            print(f"   - Task {task.id[:8]}... running for {elapsed:.0f}s")
                        should_execute = False

                if should_execute:
                    print(f"✅ Should execute {schedule.name}: Current={current_time_rounded.strftime('%H:%M:%S')}, Next={schedule.next_run.strftime('%H:%M:%S')}")

                    # 実行が決定したら、次回実行時刻を事前に計算
                    print(f"🔄 Pre-calculating next_run for {schedule.name}")
                    # 現在の次回実行時刻を基準にして次の実行時刻を計算
                    cron = croniter(schedule.cron_expression, schedule.next_run)
                    new_next_run = cron.get_next(datetime)
                    print(f"🔧 Next execution will be: {new_next_run.strftime('%Y-%m-%d %H:%M:%S')}")

                    return True

            # 次回実行時刻が過去の場合は再計算（実行はしない）
            elif current_time_rounded > schedule.next_run:
                print(f"🔄 Recalculating next_run for {schedule.name}: current={current_time_rounded.strftime('%Y-%m-%d %H:%M:%S')}, old_next={schedule.next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                # 現在時刻を基準に次回実行時刻を再計算
                cron = croniter(schedule.cron_expression, current_time_rounded)
                schedule.next_run = cron.get_next(datetime)
                print(f"🔧 New next_run for {schedule.name}: {schedule.next_run.strftime('%Y-%m-%d %H:%M:%S')}")

            return False

        except Exception as e:
            print(f"❌ Error checking schedule {schedule.name}: {str(e)}")
            return False

    def _execute_schedule(self, schedule: DBSchedule, db: Session):
        """スケジュールを実行"""
        try:
            print(f"🚀 Executing scheduled task: {schedule.name}")

            # Celeryタスクとして実行（手動実行APIと同じ方式）
            task = scheduled_spider_run.delay(schedule.id)

            # 実行時刻を更新（日本時間で統一）
            import pytz
            jst = pytz.timezone('Asia/Tokyo')
            current_jst = datetime.now(jst).replace(tzinfo=None, second=0, microsecond=0)
            schedule.last_run = current_jst

            # 次回実行時刻を計算（現在の次回実行時刻を基準にする）
            if schedule.next_run:
                # 既存の次回実行時刻から次の実行時刻を計算
                cron = croniter(schedule.cron_expression, schedule.next_run)
                schedule.next_run = cron.get_next(datetime)
            else:
                # 次回実行時刻が設定されていない場合は現在時刻から計算
                cron = croniter(schedule.cron_expression, current_jst)
                schedule.next_run = cron.get_next(datetime)

            db.commit()

            print(f"✅ Scheduled task executed: {schedule.name} (Task ID: {task.id})")
            print(f"📅 Next run: {schedule.next_run}")

        except Exception as e:
            print(f"❌ Error executing schedule {schedule.name}: {str(e)}")
            db.rollback()

    def _check_running_tasks(self, schedule: DBSchedule) -> List:
        """指定されたスケジュールの実行中タスクをチェック"""
        try:
            from ..database import Task as DBTask, TaskStatus

            db = SessionLocal()
            try:
                # 同じプロジェクト・スパイダーの実行中タスクを検索
                running_tasks = db.query(DBTask).filter(
                    DBTask.project_id == schedule.project_id,
                    DBTask.spider_id == schedule.spider_id,
                    DBTask.status.in_([TaskStatus.RUNNING, TaskStatus.PENDING])
                ).all()

                # 長時間実行タスクのタイムアウトチェック（30分以上）
                current_time = datetime.now()
                timeout_threshold = current_time - timedelta(minutes=30)

                valid_running_tasks = []
                for task in running_tasks:
                    if task.started_at and task.started_at < timeout_threshold:
                        print(f"⚠️ Task {task.id[:8]}... timed out (running for {(current_time - task.started_at).total_seconds()/60:.1f} minutes), marking as completed")
                        # タイムアウトしたタスクを完了状態に変更
                        task.status = TaskStatus.FINISHED
                        task.finished_at = current_time
                        db.commit()
                    else:
                        valid_running_tasks.append(task)

                return valid_running_tasks

            finally:
                db.close()

        except Exception as e:
            print(f"❌ Error checking running tasks for {schedule.name}: {str(e)}")
            return []

    def _update_next_run_time(self, schedule: DBSchedule, db: Session):
        """次回実行時刻を更新"""
        try:
            # next_runが設定されていない場合のみ更新
            if not schedule.next_run:
                import pytz
                jst = pytz.timezone('Asia/Tokyo')
                current_jst = datetime.now(jst).replace(tzinfo=None)
                cron = croniter(schedule.cron_expression, current_jst)
                schedule.next_run = cron.get_next(datetime)
                db.commit()

        except Exception as e:
            print(f"❌ Error updating next run time for {schedule.name}: {str(e)}")

    def _validate_task_statistics(self):
        """定期的なタスク統計検証（根本対応）"""
        try:
            from .task_statistics_validator import validate_recent_tasks

            print("🔍 Starting periodic task statistics validation...")
            result = validate_recent_tasks(hours_back=2)  # 過去2時間のタスクを検証

            if "error" in result:
                print(f"❌ Task validation error: {result['error']}")
                return

            summary = result.get("summary", {})
            fixed_count = len(result.get("fixed_tasks", []))

            if fixed_count > 0:
                print(f"✅ Task validation completed: {fixed_count} tasks fixed")
                print(f"   Items fixed: {summary.get('items_fixed', 0)}")
                print(f"   Requests fixed: {summary.get('requests_fixed', 0)}")
                print(f"   Status fixed: {summary.get('status_fixed', 0)}")
            else:
                print(f"✅ Task validation completed: All {result.get('total_checked', 0)} tasks are accurate")

        except Exception as e:
            print(f"❌ Error in periodic task validation: {str(e)}")
            import traceback
            traceback.print_exc()

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
                "active_schedules": len(schedules),
                "last_check": self.last_check_time.isoformat() if self.last_check_time else None,
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
