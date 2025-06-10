#!/usr/bin/env python3
"""
カスタムCeleryスケジューラ - データベースからスケジュールを読み込み
"""

import logging
from datetime import datetime, timedelta
from celery.beat import Scheduler, ScheduleEntry
from celery.utils.log import get_logger
from croniter import croniter
from app.database import SessionLocal, Schedule as DBSchedule, Spider as DBSpider, Project as DBProject, Task as DBTask, TaskStatus

logger = get_logger(__name__)

class CustomScheduleEntry(ScheduleEntry):
    """カスタムスケジュールエントリ"""

    def default_now(self):
        """現在時刻を返す"""
        return datetime.now()

class DatabaseScheduler(Scheduler):
    """データベースからスケジュールを読み込むカスタムスケジューラ"""

    def __init__(self, *args, **kwargs):
        self.db_schedules = {}
        self.last_sync = None
        self.sync_interval = 10  # 10秒毎にデータベースを同期
        super().__init__(*args, **kwargs)

    def setup_schedule(self):
        """スケジュールの初期設定"""
        logger.info("🔧 DatabaseScheduler: スケジュールを初期化中...")
        self.sync_from_database()

    def sync_from_database(self):
        """データベースからスケジュールを同期"""
        try:
            db = SessionLocal()

            # アクティブなスケジュールを取得
            schedules = db.query(DBSchedule).filter(
                DBSchedule.is_active == True
            ).all()

            logger.info(f"📋 データベースから {len(schedules)} 個のアクティブなスケジュールを読み込み")

            # 既存のスケジュールをクリア
            self.db_schedules.clear()

            for schedule in schedules:
                try:
                    # スパイダー情報を取得
                    spider = db.query(DBSpider).filter(DBSpider.id == schedule.spider_id).first()
                    project = db.query(DBProject).filter(DBProject.id == schedule.project_id).first()

                    if not spider or not project:
                        logger.warning(f"⚠️ スケジュール {schedule.name}: スパイダーまたはプロジェクトが見つかりません")
                        continue

                    # Cronスケジュールを作成
                    from celery.schedules import crontab

                    # Cron式を解析 (例: "*/10 * * * *" -> 10分毎)
                    cron_parts = schedule.cron_expression.split()
                    if len(cron_parts) == 5:
                        minute, hour, day, month, day_of_week = cron_parts

                        # Celeryのcrontabに変換
                        celery_schedule = crontab(
                            minute=minute,
                            hour=hour,
                            day_of_month=day,
                            month_of_year=month,
                            day_of_week=day_of_week
                        )

                        # カスタムスケジュールエントリを作成
                        entry = CustomScheduleEntry(
                            name=f"schedule_{schedule.id}",
                            task="app.tasks.scrapy_tasks.scheduled_spider_run",
                            schedule=celery_schedule,
                            args=(str(schedule.id),),  # スケジュールIDを渡す
                            kwargs={},
                            options={
                                'queue': 'scrapy',  # 明示的にキューを指定
                                'routing_key': 'scrapy',  # ルーティングキーを指定
                                'expires': 3600,  # 1時間で期限切れ
                                'retry': True,  # リトライを有効化
                                'retry_policy': {
                                    'max_retries': 3,
                                    'interval_start': 0,
                                    'interval_step': 0.2,
                                    'interval_max': 0.5,
                                }
                            }
                        )

                        self.db_schedules[f"schedule_{schedule.id}"] = entry

                        logger.info(f"✅ スケジュール追加: {schedule.name} ({schedule.cron_expression}) - {project.name}/{spider.name}")

                    else:
                        logger.warning(f"⚠️ 無効なCron式: {schedule.cron_expression}")

                except Exception as e:
                    logger.error(f"❌ スケジュール {schedule.name} の処理エラー: {e}")

            self.last_sync = datetime.now()
            logger.info(f"🔄 スケジュール同期完了: {len(self.db_schedules)} 個のスケジュールが登録されました")

        except Exception as e:
            logger.error(f"❌ データベース同期エラー: {e}")
        finally:
            db.close()

    @property
    def schedule(self):
        """現在のスケジュールを取得（プロパティ）"""
        return self.get_schedule()

    def get_schedule(self):
        """現在のスケジュールを取得"""
        # 定期的にデータベースを同期
        if (self.last_sync is None or
            datetime.now() - self.last_sync > timedelta(seconds=self.sync_interval)):
            self.sync_from_database()

        # データベーススケジュールのみを返す（デフォルトスケジュールは除外）
        return dict(self.db_schedules)

    def reserve(self, entry):
        """スケジュールエントリを予約（重複実行チェック付き）"""
        try:
            # スケジュールIDを抽出
            if entry.name.startswith("schedule_"):
                schedule_id = entry.name.replace("schedule_", "")

                # 重複実行チェック（より緩和された条件）
                if self._is_schedule_running(schedule_id):
                    logger.warning(f"⚠️ スケジュール {entry.name} は既に実行中です。スキップします。")
                    return None

                # スケジュールの最終実行時刻を更新
                self._update_schedule_last_run(schedule_id)

                # タスクを実行
                logger.info(f"📅 スケジュール実行予約: {entry.name}")
                return self.apply_async(entry)

            return None
        except Exception as e:
            logger.error(f"❌ スケジュール予約エラー: {e}")
            return None

    def _is_schedule_running(self, schedule_id: str) -> bool:
        """指定されたスケジュールが実行中かチェック（より緩和された条件）"""
        try:
            db = SessionLocal()

            # 直近5分以内に開始された実行中のタスクをチェック
            five_minutes_ago = datetime.now() - timedelta(minutes=5)
            running_tasks = db.query(DBTask).filter(
                DBTask.schedule_id == schedule_id,
                DBTask.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING]),
                DBTask.started_at >= five_minutes_ago
            ).count()

            db.close()
            return running_tasks > 0

        except Exception as e:
            logger.error(f"❌ 重複実行チェックエラー: {e}")
            return False

    def _update_schedule_last_run(self, schedule_id: str):
        """スケジュールの最終実行時刻を更新"""
        try:
            db = SessionLocal()
            schedule = db.query(DBSchedule).filter(DBSchedule.id == schedule_id).first()
            if schedule:
                schedule.last_run = datetime.now()
                schedule.next_run = self._calculate_next_run(schedule.cron_expression)
                db.commit()
                logger.info(f"⏰ スケジュール {schedule.name} の最終実行時刻を更新")
        except Exception as e:
            logger.error(f"❌ 最終実行時刻更新エラー: {e}")
        finally:
            db.close()

    def _calculate_next_run(self, cron_expression: str) -> datetime:
        """次の実行時刻を計算"""
        try:
            base = datetime.now()
            cron = croniter(cron_expression, base)
            return cron.get_next(datetime)
        except Exception as e:
            logger.error(f"❌ 次回実行時刻計算エラー: {e}")
            return datetime.now() + timedelta(minutes=5)

    def apply_async(self, entry, producer=None, advance=True, **kwargs):
        """非同期でタスクを実行"""
        try:
            logger.info(f"🚀 スケジュールタスク実行: {entry.name}")
            # タスクを直接実行
            return self.app.send_task(
                entry.task,
                args=entry.args,
                kwargs=entry.kwargs,
                **entry.options
            )
        except Exception as e:
            logger.error(f"❌ タスク実行エラー: {e}")
            return None
