import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from croniter import croniter
from sqlalchemy.orm import Session

from ..database import SessionLocal, Schedule as DBSchedule
# Celery廃止済み - マイクロサービス対応
# from ..tasks.scrapy_tasks import scheduled_spider_run
# Celery廃止済み - マイクロサービス対応
# from ..celery_app import celery_app


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
        self.executed_schedules: Dict[str, datetime] = {}  # 実行済みスケジュールの追跡

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

        # 追加の定期実行タスクを設定
        self._setup_maintenance_tasks()

        # スケジュールの次回実行時刻を修正（根本対応）
        self._fix_schedule_next_run_times()

        print("✅ Scheduler service started with statistics validation and maintenance tasks")

    def _setup_statistics_validation(self):
        """統計検証スケジュールのセットアップ（根本対応）"""
        try:
            # 統計検証を30分毎に実行するスケジュールを追加
            self.statistics_validation_interval = 30 * 60  # 30分（秒）
            self.last_validation_time = None
            print("🔧 Statistics validation schedule setup completed (every 30 minutes)")
        except Exception as e:
            print(f"❌ Error setting up statistics validation: {str(e)}")

    def _setup_maintenance_tasks(self):
        """メンテナンスタスクのセットアップ（今後の対応）"""
        try:
            # 自動修復タスクを1時間毎に実行
            self.auto_repair_interval = 60 * 60  # 1時間（秒）
            self.last_auto_repair_time = None

            # クリーンアップタスクを6時間毎に実行
            self.cleanup_interval = 6 * 60 * 60  # 6時間（秒）
            self.last_cleanup_time = None

            print("🔧 Maintenance tasks setup completed (auto-repair: 1h, cleanup: 6h)")
        except Exception as e:
            print(f"❌ Error setting up maintenance tasks: {str(e)}")

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

    def _check_and_execute_maintenance_tasks(self):
        """メンテナンスタスクの実行チェック（今後の対応）"""
        try:
            if not hasattr(self, 'auto_repair_interval'):
                return

            import pytz
            jst = pytz.timezone('Asia/Tokyo')
            current_time = datetime.now(jst).replace(tzinfo=None)

            # 自動修復タスクのチェック
            should_auto_repair = False
            if self.last_auto_repair_time is None:
                should_auto_repair = True
                print("🔧 First-time auto-repair task")
            else:
                time_since_last = (current_time - self.last_auto_repair_time).total_seconds()
                if time_since_last >= self.auto_repair_interval:
                    should_auto_repair = True
                    print(f"🔧 Auto-repair task due: {time_since_last:.0f}s since last repair")

            if should_auto_repair:
                self._execute_auto_repair()
                self.last_auto_repair_time = current_time

            # クリーンアップタスクのチェック
            should_cleanup = False
            if self.last_cleanup_time is None:
                should_cleanup = True
                print("🧹 First-time cleanup task")
            else:
                time_since_last = (current_time - self.last_cleanup_time).total_seconds()
                if time_since_last >= self.cleanup_interval:
                    should_cleanup = True
                    print(f"🧹 Cleanup task due: {time_since_last:.0f}s since last cleanup")

            if should_cleanup:
                self._execute_cleanup()
                self.last_cleanup_time = current_time

        except Exception as e:
            print(f"❌ Error in maintenance tasks check: {str(e)}")

    def _fix_schedule_next_run_times(self):
        """スケジュールの次回実行時刻を修正（根本対応版）"""
        try:
            db = SessionLocal()
            try:
                # 全てのアクティブなスケジュールを取得
                schedules = db.query(DBSchedule).filter(
                    DBSchedule.is_active == True
                ).all()

                import pytz
                jst = pytz.timezone('Asia/Tokyo')
                current_time = datetime.now(jst).replace(tzinfo=None, second=0, microsecond=0)

                fixed_count = 0
                for schedule in schedules:
                    try:
                        # 現在のnext_runが正しいかチェック
                        if schedule.next_run:
                            time_diff = (current_time - schedule.next_run).total_seconds()

                            # 次回実行時刻が30分以上過去の場合は修正
                            if time_diff > 1800:
                                old_next_run = schedule.next_run.strftime('%H:%M:%S')
                                schedule.next_run = self._calculate_next_run_from_current(schedule.cron_expression, current_time)
                                new_next_run = schedule.next_run.strftime('%H:%M:%S')

                                print(f"🔧 Fixed next_run for {schedule.name}: {old_next_run} → {new_next_run}")
                                fixed_count += 1
                        else:
                            # next_runが設定されていない場合は設定
                            schedule.next_run = self._calculate_next_run_from_current(schedule.cron_expression, current_time)
                            print(f"🔧 Set next_run for {schedule.name}: {schedule.next_run.strftime('%H:%M:%S')}")
                            fixed_count += 1

                    except Exception as e:
                        print(f"❌ Error fixing schedule {schedule.name}: {str(e)}")

                if fixed_count > 0:
                    db.commit()
                    print(f"✅ Fixed {fixed_count} schedule next_run times")
                else:
                    print(f"✅ All schedule next_run times are correct")

            finally:
                db.close()

        except Exception as e:
            print(f"❌ Error fixing schedule next_run times: {str(e)}")

    def _cleanup_executed_schedules(self):
        """実行済みスケジュールのクリーンアップ（1時間以上古いものを削除）"""
        try:
            import pytz
            jst = pytz.timezone('Asia/Tokyo')
            current_time = datetime.now(jst).replace(tzinfo=None)
            cutoff_time = current_time - timedelta(hours=1)

            # 1時間以上古い実行済みスケジュールを削除
            keys_to_remove = []
            for key, execution_time in self.executed_schedules.items():
                if execution_time < cutoff_time:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.executed_schedules[key]

            if keys_to_remove:
                print(f"🧹 Cleaned up {len(keys_to_remove)} old executed schedule records")

        except Exception as e:
            print(f"❌ Error in executed schedules cleanup: {str(e)}")

    def _execute_auto_repair(self):
        """自動修復タスクを実行（マイクロサービス化対応）"""
        try:
            from ..services.task_auto_repair import task_auto_repair
            print("🔧 Executing auto-repair task...")

            # Celeryの代わりに直接サービスを呼び出し
            result = task_auto_repair.repair_failed_tasks(hours_back=24)

            if "error" in result:
                print(f"❌ Auto-repair failed: {result['error']}")
            else:
                repaired_count = result.get('repaired_count', 0)
                total_failed = result.get('total_failed_tasks', 0)
                print(f"✅ Auto-repair completed: {repaired_count}/{total_failed} tasks repaired")

        except Exception as e:
            print(f"❌ Error executing auto-repair task: {str(e)}")

    def _execute_cleanup(self):
        """クリーンアップタスクを実行（マイクロサービス化対応）"""
        try:
            print("🧹 Executing cleanup tasks...")

            # スタックしたタスクのクリーンアップ（直接実装）
            stuck_count = self._cleanup_stuck_tasks()
            print(f"✅ Stuck tasks cleanup completed: {stuck_count} tasks cleaned")

            # 古い結果のクリーンアップ（直接実装）
            cleanup_count = self._cleanup_old_results()
            print(f"✅ Old results cleanup completed: {cleanup_count} tasks cleaned")

        except Exception as e:
            print(f"❌ Error executing cleanup tasks: {str(e)}")

    def _cleanup_stuck_tasks(self) -> int:
        """スタックしたタスクをクリーンアップ（直接実装）"""
        try:
            from ..database import SessionLocal, Task as DBTask, TaskStatus
            from datetime import datetime, timedelta

            db = SessionLocal()
            try:
                # 1時間以上RUNNING状態のタスクを強制終了
                cutoff_time = datetime.now() - timedelta(hours=1)

                stuck_tasks = db.query(DBTask).filter(
                    DBTask.status == TaskStatus.RUNNING,
                    DBTask.started_at < cutoff_time
                ).all()

                cleaned_count = 0
                for task in stuck_tasks:
                    print(f"🧹 Cleaning stuck task: {task.id}")
                    task.status = TaskStatus.FAILED
                    task.finished_at = datetime.now()
                    task.error_count = 1
                    cleaned_count += 1

                db.commit()
                return cleaned_count

            finally:
                db.close()

        except Exception as e:
            print(f"❌ Error in stuck tasks cleanup: {str(e)}")
            return 0

    def _cleanup_old_results(self, days_old: int = 30) -> int:
        """古い結果とログを削除するクリーンアップ（直接実装）"""
        try:
            from ..database import SessionLocal, Task as DBTask, TaskStatus
            from datetime import datetime, timedelta

            db = SessionLocal()
            try:
                cutoff_date = datetime.now() - timedelta(days=days_old)

                # 古いタスクを取得
                old_tasks = db.query(DBTask).filter(
                    DBTask.created_at < cutoff_date,
                    DBTask.status.in_([TaskStatus.FINISHED, TaskStatus.FAILED, TaskStatus.CANCELLED])
                ).all()

                deleted_count = 0
                for task in old_tasks:
                    # 関連する結果とログも削除される（CASCADE設定により）
                    db.delete(task)
                    deleted_count += 1

                db.commit()
                return deleted_count

            finally:
                db.close()

        except Exception as e:
            print(f"❌ Error in old results cleanup: {str(e)}")
            return 0

    def stop(self):
        """スケジューラーを停止"""
        if not self.running:
            return

        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        print("🛑 Scheduler service stopped")

    def _check_database_health(self):
        """データベース接続の健全性をチェック（根本対応）"""
        try:
            db = SessionLocal()
            try:
                # 簡単なクエリでデータベース接続をテスト
                from sqlalchemy import text
                db.execute(text("SELECT 1"))
                db.close()
            except Exception as db_error:
                print(f"⚠️ Database health check failed: {db_error}")
                db.close()
                # データベース接続プールをリセット
                from ..database import engine
                engine.dispose()
                print("🔄 Database connection pool reset")
        except Exception as e:
            print(f"❌ Database health check error: {e}")

    def _restart_scheduler(self):
        """スケジューラーを再起動（根本対応）"""
        try:
            print("🔄 Restarting scheduler due to critical errors...")

            # 現在のスレッドを停止
            self.running = False
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=10)

            # 少し待機
            import time
            time.sleep(5)

            # 新しいスレッドで再起動
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()

            print("✅ Scheduler restarted successfully")

        except Exception as e:
            print(f"❌ Failed to restart scheduler: {e}")

    def _run_scheduler(self):
        """スケジューラーのメインループ（根本対応版）"""
        print("🔄 Scheduler main loop started with enhanced error handling")

        consecutive_errors = 0
        max_consecutive_errors = 5
        error_backoff_multiplier = 1

        while self.running:
            try:
                # デバッグ用：ループの開始を記録
                import pytz
                jst = pytz.timezone('Asia/Tokyo')
                loop_start = datetime.now(jst).replace(tzinfo=None)
                print(f"🔄 Scheduler loop iteration at {loop_start.strftime('%H:%M:%S.%f')[:-3]}")

                # データベース接続の健全性チェック
                self._check_database_health()

                self._check_and_execute_schedules()

                # 統計検証の実行チェック（根本対応）
                self._check_and_execute_statistics_validation()

                # メンテナンスタスクの実行チェック（今後の対応）
                self._check_and_execute_maintenance_tasks()

                # 実行済みスケジュールのクリーンアップ（1時間以上古いものを削除）
                self._cleanup_executed_schedules()

                # 正常実行時はエラーカウンターをリセット
                consecutive_errors = 0
                error_backoff_multiplier = 1

                # デバッグ用：スリープ前の時刻を記録
                sleep_start = datetime.now(jst).replace(tzinfo=None)
                print(f"😴 Scheduler sleeping for {self.check_interval}s at {sleep_start.strftime('%H:%M:%S.%f')[:-3]}")

                time.sleep(self.check_interval)

            except Exception as e:
                consecutive_errors += 1
                print(f"❌ Scheduler error ({consecutive_errors}/{max_consecutive_errors}): {str(e)}")
                import traceback
                traceback.print_exc()

                # 連続エラーが多い場合は指数バックオフ
                if consecutive_errors >= max_consecutive_errors:
                    error_backoff_multiplier = min(error_backoff_multiplier * 2, 8)
                    print(f"⚠️ Too many consecutive errors, applying backoff multiplier: {error_backoff_multiplier}")

                # エラー時のスリープ時間を調整
                error_sleep_time = self.check_interval * error_backoff_multiplier
                print(f"😴 Error recovery sleep for {error_sleep_time}s")
                time.sleep(error_sleep_time)

                # 致命的エラーの場合はスケジューラーを再起動
                if consecutive_errors >= max_consecutive_errors * 2:
                    print("🚨 Critical error threshold reached, attempting scheduler restart...")
                    self._restart_scheduler()
                    break

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

                    # missed execution（実行漏れ）をチェックして即座に実行 - 一時的に無効化
                    # missed_executions = self._check_and_execute_missed_executions(schedule, current_time, db)
                    # if missed_executions > 0:
                    #     print(f"⚠️ Detected and executed {missed_executions} missed executions for {schedule.name}")
                    #     executed_count += missed_executions
                    print(f"    ⚠️ Missed execution check disabled to prevent spam")

                    # デバッグ情報を出力
                    should_execute = self._should_execute_schedule(schedule, current_time, db)
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

    def _should_execute_schedule(self, schedule: DBSchedule, current_time: datetime, db=None) -> bool:
        """スケジュールを実行すべきかチェック（根本対応版）"""
        try:
            # 現在時刻を分単位で丸める（秒・マイクロ秒を0にする）
            current_time_rounded = current_time.replace(second=0, microsecond=0)

            # next_runが設定されていない場合は計算
            if not schedule.next_run:
                # 初回実行の場合、現在時刻から次回実行時刻を計算
                schedule.next_run = self._calculate_next_run_from_current(schedule.cron_expression, current_time_rounded)
                print(f"🔧 Initialized next_run for {schedule.name}: {schedule.next_run.strftime('%H:%M:%S')}")
                # 初回は実行しない（次回から実行）
                return False

            # 詳細な時刻比較情報を出力
            print(f"🔍 Time comparison for {schedule.name}:")
            print(f"  Current: {current_time_rounded} ({current_time_rounded.strftime('%Y-%m-%d %H:%M:%S')})")
            print(f"  Next run: {schedule.next_run} ({schedule.next_run.strftime('%Y-%m-%d %H:%M:%S')})")

            # 実行判定：現在時刻が次回実行時刻と一致または過ぎている場合に実行
            time_diff = (current_time_rounded - schedule.next_run).total_seconds()

            # 実行条件：現在時刻が次回実行時刻以降で、30分以内の遅延
            is_execution_time = time_diff >= 0 and time_diff <= 1800  # 30分の許容範囲

            print(f"  Time difference: {time_diff} seconds")
            print(f"  Is execution time: {is_execution_time}")

            # デバッグ：Croniterで正しい次回実行時刻を確認
            from croniter import croniter
            cron_debug = croniter(schedule.cron_expression, current_time_rounded)
            correct_next = cron_debug.get_next(datetime)
            print(f"  🔧 Correct next run should be: {correct_next.strftime('%Y-%m-%d %H:%M:%S')}")

            # 5分毎スケジュールの特別処理（根本対応版）
            if schedule.cron_expression == "*/5 * * * *":
                current_minute = current_time_rounded.minute

                # 現在時刻が5分毎の実行時刻かチェック
                if current_minute % 5 == 0:
                    print(f"  🔥 5-minute schedule execution time detected: {current_time_rounded.strftime('%H:%M:%S')}")

                    # 重複実行防止チェック（根本対応版）
                    execution_key = f"{schedule.id}_{current_time_rounded.strftime('%Y%m%d%H%M')}"

                    # 実際のタスク完了を確認（緊急修正：RUNNINGタスクも含める）
                    from ..database import Task as DBTask, TaskStatus
                    recent_task = db.query(DBTask).filter(
                        DBTask.schedule_id == schedule.id,
                        DBTask.started_at >= current_time_rounded.replace(second=0, microsecond=0),
                        DBTask.started_at < current_time_rounded.replace(second=0, microsecond=0) + timedelta(minutes=1),
                        DBTask.status.in_([TaskStatus.RUNNING, TaskStatus.FINISHED, TaskStatus.FAILED])  # RUNNINGを追加
                    ).first()

                    if not recent_task:
                        # メモリキャッシュもチェック（二重防止）
                        if execution_key not in self.executed_schedules:
                            is_execution_time = True
                            time_diff = 0
                            print(f"  ✅ 5-minute schedule ready for execution (no recent task found)")
                            # 実行をマーク
                            self.executed_schedules[execution_key] = current_time_rounded
                            print(f"  🔒 Marked execution: {execution_key}")
                        else:
                            print(f"  ⚠️ 5-minute schedule already marked for execution: {execution_key}")
                            # 緊急修正：実行済みマークをクリアして再実行を許可
                            print(f"  🔧 EMERGENCY FIX: Clearing execution mark to allow re-execution")
                            del self.executed_schedules[execution_key]
                            self.executed_schedules[execution_key] = current_time_rounded
                            print(f"  🔒 Re-marked execution: {execution_key}")
                            is_execution_time = True
                    else:
                        print(f"  ⚠️ 5-minute schedule already executed: Task {recent_task.id[:8]}... at {recent_task.started_at} (status: {recent_task.status})")
                        is_execution_time = False
                else:
                    # 次回実行時刻を正確に計算
                    next_minute = ((current_minute // 5) + 1) * 5
                    if next_minute >= 60:
                        next_minute = 0
                        correct_next = current_time_rounded.replace(minute=next_minute, second=0, microsecond=0) + timedelta(hours=1)
                    else:
                        correct_next = current_time_rounded.replace(minute=next_minute, second=0, microsecond=0)
                    print(f"  🔧 5-minute schedule next run: {correct_next.strftime('%Y-%m-%d %H:%M:%S')}")

                    # next_runを更新（実行失敗時でも正確な次回時刻を設定）
                    if abs((schedule.next_run - correct_next).total_seconds()) > 60:
                        schedule.next_run = correct_next
                        print(f"  🔧 Updated next_run to: {correct_next.strftime('%H:%M:%S')}")

            # next_runが間違っている場合は修正
            if abs((schedule.next_run - correct_next).total_seconds()) > 60:
                print(f"  ❌ next_run is incorrect! Fixing: {schedule.next_run.strftime('%H:%M:%S')} → {correct_next.strftime('%H:%M:%S')}")
                schedule.next_run = correct_next
                # 修正後に再判定
                time_diff = (current_time_rounded - schedule.next_run).total_seconds()
                is_execution_time = time_diff >= 0 and time_diff <= 1800
                print(f"  🔧 After fix - Time difference: {time_diff} seconds, Is execution time: {is_execution_time}")

            if is_execution_time:
                # 重複実行防止チェック
                execution_key = f"{schedule.id}_{schedule.next_run.strftime('%Y%m%d%H%M')}"
                if execution_key in self.executed_schedules:
                    print(f"  ⚠️ Already executed: {execution_key}")
                    # 次回実行時刻を更新して重複を防ぐ
                    schedule.next_run = self._calculate_next_run_from_current(schedule.cron_expression, current_time_rounded)
                    print(f"  🔧 Updated next_run to: {schedule.next_run.strftime('%H:%M:%S')}")
                    return False

                # 実行済みとしてマーク
                self.executed_schedules[execution_key] = current_time_rounded
                print(f"  ✅ Marked for execution: {execution_key}")
                return True

            # 次回実行時刻が過去すぎる場合（30分以上前）は再計算
            elif time_diff > 1800:
                print(f"🔄 Next run too old ({time_diff/60:.1f} min ago), recalculating for {schedule.name}")
                schedule.next_run = self._calculate_next_run_from_current(schedule.cron_expression, current_time_rounded)
                print(f"🔧 New next_run: {schedule.next_run.strftime('%Y-%m-%d %H:%M:%S')}")

            return False

        except Exception as e:
            print(f"❌ Error checking schedule {schedule.name}: {str(e)}")
            return False

    def _execute_schedule(self, schedule: DBSchedule, db: Session):
        """スケジュールを実行"""
        try:
            print(f"🚀 Executing scheduled task: {schedule.name}")

            # マイクロサービス経由で実行（Celery廃止済み）
            # ポート8002のSpider Managerサービスが利用できない場合は直接レガシー実行
            print(f"🔄 Microservices not available (port 8002), using legacy execution...")
            task_id = self._execute_schedule_legacy(schedule, db)
            if task_id:
                print(f"✅ Legacy execution successful: Task {task_id[:8]}...")

                # レガシー実行成功時のみlast_runとnext_runを更新（タスク作成確認後）
                import pytz
                jst = pytz.timezone('Asia/Tokyo')
                current_jst = datetime.now(jst).replace(tzinfo=None, second=0, microsecond=0)

                # データベースでタスクの存在と完了状態を確認（根本対応）
                from ..database import Task as DBTask, TaskStatus
                task_exists = db.query(DBTask).filter(DBTask.id == task_id).first()

                if task_exists and task_exists.status in [TaskStatus.FINISHED, TaskStatus.FAILED]:
                    # タスクが実際に完了している場合のみlast_runを更新
                    schedule.last_run = current_jst
                    schedule.next_run = self._calculate_next_run_from_current(schedule.cron_expression, current_jst)
                    print(f"✅ Updated schedule times after legacy execution: last_run={current_jst.strftime('%H:%M:%S')}, next_run={schedule.next_run.strftime('%H:%M:%S')}")
                    print(f"✅ Task status: {task_exists.status}, Items: {task_exists.items_count}, Requests: {task_exists.requests_count}")

                    # 実行成功時のみ重複防止に記録（タスク作成確認後）
                    if task_exists and task_exists.status in [TaskStatus.FINISHED, TaskStatus.FAILED]:
                        execution_key = f"{schedule.id}_{current_jst.strftime('%Y%m%d%H%M')}"
                        self.executed_schedules[execution_key] = current_jst
                        print(f"✅ Execution recorded for duplicate prevention: {execution_key}")
                    else:
                        print(f"⚠️ Task not completed, execution NOT recorded for duplicate prevention")

                    db.commit()
                    print(f"✅ Scheduled task executed: {schedule.name} (Task ID: {task_id})")
                    print(f"📅 Next run: {schedule.next_run}")
                    return  # 成功時は早期リターン
                elif task_exists:
                    print(f"❌ Task {task_id[:8]}... exists but status is {task_exists.status} (not completed)")
                else:
                    print(f"❌ Task {task_id[:8]}... not found in database")

            else:
                print(f"❌ Legacy execution failed for {schedule.name}")

            print(f"❌ Schedule execution failed for {schedule.name} - times NOT updated")
            db.rollback()
            return

        except Exception as e:
            print(f"❌ Error executing schedule {schedule.name}: {str(e)}")
            db.rollback()

    def _execute_schedule_legacy(self, schedule: DBSchedule, db):
        """レガシー実行モード（緊急修正版）"""
        # 新しいデータベースセッションを作成
        from ..database import get_db, Project, Spider, Task as DBTask, TaskStatus
        import uuid
        import subprocess
        import os
        import sys

        # 独立したデータベースセッションを使用
        db_session = next(get_db())

        try:
            print(f"🚨 EMERGENCY FIX: Legacy execution for {schedule.name}")

            # プロジェクトとスパイダー情報を取得（新しいセッション）
            project = db_session.query(Project).filter(Project.id == schedule.project_id).first()
            spider = db_session.query(Spider).filter(Spider.id == schedule.spider_id).first()

            if not project or not spider:
                print(f"❌ Project or spider not found for schedule {schedule.name}")
                return None

            print(f"🔧 Legacy execution for {schedule.name}: {project.name}/{spider.name}")

            # タスクをデータベースに作成（根本修正版）
            # タスクIDを統一フォーマットで生成
            import time
            timestamp = int(time.time())
            task_id = f"task_{timestamp}"

            # プロジェクトディレクトリの確認
            project_dir = f"/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects/{project.name}"
            if not os.path.exists(project_dir):
                print(f"❌ Project directory not found: {project_dir}")
                return None

            # resultsディレクトリの作成
            results_dir = os.path.join(project_dir, "results")
            os.makedirs(results_dir, exist_ok=True)
            print(f"✅ Results directory ensured: {results_dir}")

            # システム管理者ユーザーIDを取得
            from ..database import User
            system_user = db_session.query(User).filter(User.email == 'admin@scrapyui.com').first()
            system_user_id = system_user.id if system_user else None

            if not system_user_id:
                print(f"❌ CRITICAL: System admin user not found")
                return None

            new_task = DBTask(
                id=task_id,
                project_id=schedule.project_id,
                spider_id=schedule.spider_id,
                schedule_id=schedule.id,
                status=TaskStatus.RUNNING,
                settings=schedule.settings or {},
                created_at=datetime.now(),
                started_at=datetime.now(),
                user_id=system_user_id  # システム管理者として実行
            )

            print(f"🚨 EMERGENCY: Creating task with new database session")

            # 緊急修正: 独立したデータベースセッションでタスク作成
            print(f"🚨 EMERGENCY: Adding task to NEW database session...")
            db_session.add(new_task)

            print(f"🚨 EMERGENCY: Committing task to database...")
            db_session.commit()
            print(f"✅ EMERGENCY: Task committed to database: {new_task.id[:8]}...")

            # データベース接続の確認
            print(f"🔧 Verifying database connection...")
            try:
                from sqlalchemy import text
                db_session.execute(text("SELECT 1"))
                print(f"✅ Database connection verified")
            except Exception as db_error:
                print(f"❌ Database connection failed: {db_error}")
                # 接続エラーでもScrapy実行を続行
                print(f"🔧 Continuing with Scrapy execution despite database error")

            # タスクの存在確認（独立したセッション）
            print(f"🔧 Verifying task exists in database...")
            try:
                task_check = db_session.query(DBTask).filter(DBTask.id == new_task.id).first()
                if task_check:
                    print(f"✅ Task verified in database: {task_check.id[:8]}... status={task_check.status}")
                else:
                    print(f"❌ CRITICAL: Task NOT found in database after commit!")
                    db_session.rollback()
                    return None
            except Exception as verify_error:
                print(f"⚠️ Task verification failed: {verify_error}")
                print(f"🔧 Continuing with Scrapy execution")

            # Scrapyコマンドを構築（lightprogress統合版）
            print(f"🚀 Starting Scrapy execution for task {new_task.id[:8]}...")
            try:
                python_path = sys.executable
                cmd = [
                    python_path, "-m", "scrapy", "crawlwithwatchdog",
                    spider.name,
                    "-s", f"TASK_ID={new_task.id}",
                    "-s", f"SCHEDULE_ID={schedule.id}",
                    "-s", "FEED_EXPORT_ENCODING=utf-8",
                    "-s", "ROBOTSTXT_OBEY=False",
                    "-s", "LIGHTWEIGHT_PROGRESS_WEBSOCKET=True",
                    "--task-id", new_task.id,  # lightprogress統合のため追加
                    "-o", f"results/{new_task.id}.jsonl"
                ]

                # 環境変数にタスクIDを設定（lightprogress統合）
                import os
                os.environ['SCRAPYUI_TASK_ID'] = new_task.id
                print(f"🔧 Set SCRAPYUI_TASK_ID environment variable for scheduler: {new_task.id}")

                # 環境変数でタスクIDを確実に渡す
                env = os.environ.copy()
                env['SCRAPY_TASK_ID'] = new_task.id
                env['SCRAPY_SCHEDULE_ID'] = str(schedule.id)
                env['SCRAPY_PROJECT_PATH'] = project_dir

                print(f"🚀 Executing command: {' '.join(cmd)}")
                print(f"📁 Working directory: {project_dir}")

                # プロジェクトディレクトリの存在確認
                if not os.path.exists(project_dir):
                    print(f"❌ Project directory not found: {project_dir}")
                    raise Exception(f"Project directory not found: {project_dir}")

                # 同期でScrapyを実行（根本修正版）
                print(f"🔧 Starting subprocess.run with env vars...")
                print(f"🔧 SCRAPY_TASK_ID: {env.get('SCRAPY_TASK_ID')}")
                result = subprocess.run(
                    cmd,
                    cwd=project_dir,
                    env=env,  # 環境変数を渡す
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分タイムアウト
                )

                print(f"✅ Scrapy command completed with return code: {result.returncode}")
                print(f"📊 Command execution successful")

                if result.stdout:
                    print(f"📝 Scrapy stdout: {result.stdout[-500:]}")  # 最後の500文字
                if result.stderr:
                    print(f"⚠️ Scrapy stderr: {result.stderr[-500:]}")  # 最後の500文字

                # lightprogressシステムでタスクステータスを更新
                print(f"🔧 Updating task status with lightprogress system...")
                try:
                    from ..services.scrapy_watchdog_monitor import ScrapyWatchdogMonitor
                    from pathlib import Path

                    # lightprogress監視インスタンスを作成
                    lightprogress_monitor = ScrapyWatchdogMonitor(
                        task_id=new_task.id,
                        project_path=project_dir,
                        spider_name=spider.name
                    )

                    # JSONLファイルパスを設定
                    result_file = os.path.join(results_dir, f"{new_task.id}.jsonl")
                    lightprogress_monitor.jsonl_file_path = Path(result_file)

                    # 結果ファイル→DB保存（richprogressと同じ方法）
                    print(f"📁 Storing results to database...")
                    lightprogress_monitor._store_results_to_db_like_richprogress()

                    # タスクステータスを更新（lightprogressロジック）
                    print(f"🔧 Updating task status...")
                    lightprogress_monitor._update_task_status_on_completion(
                        success=(result.returncode == 0),
                        process_success=(result.returncode == 0),
                        data_success=True,  # データ取得成功と仮定
                        result={'return_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
                    )

                    print(f"✅ lightprogress integration completed for scheduler task")

                except Exception as e:
                    print(f"❌ lightprogress integration error: {e}")
                    import traceback
                    print(f"❌ Error details: {traceback.format_exc()}")

                # 実行結果に基づいてタスクステータスを更新（レガシー処理）
                if result.returncode == 0:
                    new_task.status = TaskStatus.FINISHED
                    new_task.finished_at = datetime.now()

                    # 結果ファイルの確認
                    result_file = os.path.join(results_dir, f"{new_task.id}.jsonl")
                    if os.path.exists(result_file):
                        # ファイルサイズと行数を確認
                        file_size = os.path.getsize(result_file)
                        with open(result_file, 'r', encoding='utf-8') as f:
                            line_count = sum(1 for _ in f)

                        new_task.items_count = line_count
                        new_task.requests_count = 1  # 最低1リクエスト
                        print(f"✅ Result file created: {result_file} ({file_size} bytes, {line_count} items)")
                    else:
                        print(f"⚠️ Result file not found: {result_file}")
                        new_task.items_count = 0
                        new_task.requests_count = 1
                else:
                    new_task.status = TaskStatus.FAILED
                    new_task.finished_at = datetime.now()
                    new_task.error_message = f"Scrapy exit code: {result.returncode}\nStderr: {result.stderr}"
                    print(f"❌ Scrapy execution failed with code {result.returncode}")

                print(f"🔧 Updating task status in database...")
                try:
                    db_session.commit()
                    print(f"✅ Database transaction committed successfully")
                except Exception as commit_error:
                    print(f"⚠️ Database commit failed: {commit_error}")
                    print(f"🔧 Task execution was successful, but database update failed")

                # 最終確認
                print(f"🔧 Final verification of task in database...")
                try:
                    final_check = db_session.query(DBTask).filter(DBTask.id == new_task.id).first()
                    if final_check:
                        print(f"✅ Final verification successful: Task {final_check.id[:8]}... status={final_check.status}")
                    else:
                        print(f"❌ Final verification failed: Task not found after commit!")
                except Exception as verify_error:
                    print(f"⚠️ Final verification failed: {verify_error}")

                print(f"✅ Task {new_task.id[:8]}... completed with status: {new_task.status}")
                return new_task.id

            except subprocess.TimeoutExpired:
                print(f"❌ Scrapy execution timed out after 5 minutes")
                new_task.status = TaskStatus.FAILED
                new_task.finished_at = datetime.now()
                new_task.error_message = "Execution timeout (5 minutes)"
                db_session.commit()
                return None

            except Exception as exec_error:
                print(f"❌ Failed to execute legacy Scrapy command: {exec_error}")
                new_task.status = TaskStatus.FAILED
                new_task.finished_at = datetime.now()
                new_task.error_message = str(exec_error)
                db_session.commit()
                return None

        except Exception as e:
            print(f"❌ CRITICAL ERROR in legacy execution for {schedule.name}: {str(e)}")
            print(f"❌ Exception type: {type(e).__name__}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            db_session.rollback()
            return None
        finally:
            # セッションを確実にクローズ
            db_session.close()

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

    def _calculate_next_run(self, cron_expression: str, base_time: datetime) -> datetime:
        """統一された次回実行時刻計算メソッド（根本対応）"""
        try:
            # 基準時刻を分単位で正規化
            normalized_base = base_time.replace(second=0, microsecond=0)

            # Croniterを使用して次回実行時刻を計算
            cron = croniter(cron_expression, normalized_base)
            next_run = cron.get_next(datetime)

            # 分単位で正規化
            next_run_normalized = next_run.replace(second=0, microsecond=0)

            print(f"🔧 Next run calculated: {normalized_base.strftime('%H:%M:%S')} → {next_run_normalized.strftime('%H:%M:%S')}")
            return next_run_normalized

        except Exception as e:
            print(f"❌ Error calculating next run: {str(e)}")
            # フォールバック: 5分後
            fallback = base_time + timedelta(minutes=5)
            return fallback.replace(second=0, microsecond=0)

    def _calculate_next_run_from_current(self, cron_expression: str, current_time: datetime) -> datetime:
        """現在時刻から次回実行時刻を計算（根本対応版）"""
        try:
            # 現在時刻を分単位で正規化
            normalized_current = current_time.replace(second=0, microsecond=0)

            # Croniterを使用して現在時刻から次回実行時刻を計算
            cron = croniter(cron_expression, normalized_current)
            next_run = cron.get_next(datetime)

            # 分単位で正規化
            next_run_normalized = next_run.replace(second=0, microsecond=0)

            print(f"🔧 Next run from current: {normalized_current.strftime('%H:%M:%S')} → {next_run_normalized.strftime('%H:%M:%S')}")
            return next_run_normalized

        except Exception as e:
            print(f"❌ Error calculating next run from current: {str(e)}")
            # フォールバック: 5分後
            fallback = current_time + timedelta(minutes=5)
            return fallback.replace(second=0, microsecond=0)

    def _check_missed_executions(self, schedule: DBSchedule, current_time: datetime) -> int:
        """実行漏れ（missed executions）をチェック（根本対応版）"""
        try:
            if not schedule.last_run or not schedule.next_run:
                return 0

            # 現在時刻を分単位で正規化
            current_time_rounded = current_time.replace(second=0, microsecond=0)

            # 最後の実行時刻から現在時刻までの間に実行されるべきだった回数を計算
            from croniter import croniter

            # 最後の実行時刻から開始
            cron = croniter(schedule.cron_expression, schedule.last_run)
            missed_count = 0

            # 最大10回まで（無限ループ防止）
            for _ in range(10):
                next_expected = cron.get_next(datetime)
                if next_expected > current_time_rounded:
                    break

                # この時刻に実行されるべきだったが実行されていない
                execution_key = f"{schedule.id}_{next_expected.strftime('%Y%m%d%H%M')}"
                if execution_key not in self.executed_schedules:
                    missed_count += 1
                    print(f"  📅 Missed execution at: {next_expected.strftime('%H:%M:%S')}")

                    # 実行漏れを記録（今後の重複防止のため）
                    self.executed_schedules[execution_key] = current_time_rounded

            if missed_count > 0:
                print(f"⚠️ Total missed executions for {schedule.name}: {missed_count}")
                # 次回実行時刻を現在時刻から再計算
                schedule.next_run = self._calculate_next_run_from_current(schedule.cron_expression, current_time_rounded)
                print(f"🔧 Updated next_run due to missed executions: {schedule.next_run.strftime('%H:%M:%S')}")

            return missed_count

        except Exception as e:
            print(f"❌ Error checking missed executions for {schedule.name}: {str(e)}")
            return 0

    def _check_and_execute_missed_executions(self, schedule: DBSchedule, current_time: datetime, db) -> int:
        """実行漏れ（missed executions）をチェックして即座に実行（完全根本対応版）"""
        try:
            if not schedule.last_run or not schedule.next_run:
                return 0

            # 現在時刻を分単位で正規化
            current_time_rounded = current_time.replace(second=0, microsecond=0)

            # 最後の実行時刻から現在時刻までの間に実行されるべきだった回数を計算
            from croniter import croniter

            # 最後の実行時刻から開始
            cron = croniter(schedule.cron_expression, schedule.last_run)
            executed_count = 0

            # 最大5回まで（無限ループ防止、過度な補完実行を防ぐ）
            for _ in range(5):
                next_expected = cron.get_next(datetime)
                if next_expected > current_time_rounded:
                    break

                # この時刻に実行されるべきだったが実行されていない
                execution_key = f"{schedule.id}_{next_expected.strftime('%Y%m%d%H%M')}"
                if execution_key not in self.executed_schedules:
                    print(f"  🔥 Executing missed execution at: {next_expected.strftime('%H:%M:%S')}")

                    # 実行漏れを即座に実行（完全修正版）
                    try:
                        # マイクロサービス経由で実行を試行
                        from ..services.microservice_client import MicroserviceClient
                        from ..database import Project, Spider
                        microservice_client = MicroserviceClient()

                        project = db.query(Project).filter(Project.id == schedule.project_id).first()
                        spider = db.query(Spider).filter(Spider.id == schedule.spider_id).first()

                        if project and spider:
                            try:
                                result = microservice_client.execute_watchdog_task(
                                    project_name=project.name,
                                    spider_name=spider.name,
                                    settings=schedule.settings or {},
                                    schedule_id=str(schedule.id)
                                )

                                if "error" not in result:
                                    print(f"  ✅ Missed execution completed via microservice: {result.get('task_id', 'unknown')}")
                                    executed_count += 1
                                else:
                                    # マイクロサービス失敗時はレガシー実行
                                    task_id = self._execute_schedule_legacy(schedule, db)
                                    if task_id:
                                        print(f"  ✅ Missed execution completed via legacy: {task_id[:8]}...")
                                        executed_count += 1

                            except Exception as micro_error:
                                print(f"  ⚠️ Microservice failed for missed execution: {micro_error}")
                                # レガシー実行にフォールバック
                                task_id = self._execute_schedule_legacy(schedule, db)
                                if task_id:
                                    print(f"  ✅ Missed execution completed via legacy fallback: {task_id[:8]}...")
                                    executed_count += 1

                    except Exception as exec_error:
                        print(f"  ❌ Failed to execute missed execution: {exec_error}")

                    # 実行済みとしてマーク
                    self.executed_schedules[execution_key] = current_time_rounded

                    # 短い間隔で実行を避けるため少し待機
                    import time
                    time.sleep(2)

            if executed_count > 0:
                print(f"🎯 Executed {executed_count} missed executions for {schedule.name}")
                # 次回実行時刻を現在時刻から再計算
                schedule.next_run = self._calculate_next_run_from_current(schedule.cron_expression, current_time_rounded)
                print(f"🔧 Updated next_run after missed executions: {schedule.next_run.strftime('%H:%M:%S')}")

            return executed_count

        except Exception as e:
            print(f"❌ Error executing missed executions for {schedule.name}: {str(e)}")
            return 0

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
