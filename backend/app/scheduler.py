#!/usr/bin/env python3
"""
カスタムCeleryスケジューラ - データベースからスケジュールを読み込み
"""

import logging
from datetime import datetime, timedelta
from celery.beat import Scheduler, ScheduleEntry
from celery.utils.log import get_logger
from croniter import croniter
from app.database import SessionLocal, Schedule as DBSchedule, Spider as DBSpider, Project as DBProject

logger = get_logger(__name__)

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

                        # スケジュールエントリを作成
                        entry = ScheduleEntry(
                            name=f"schedule_{schedule.id}",
                            task="app.tasks.scrapy_tasks.scheduled_spider_run",
                            schedule=celery_schedule,
                            args=(str(schedule.id),),  # スケジュールIDを渡す
                            kwargs={},
                            options={}
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

                # 重複実行チェック
                if self._is_schedule_running(schedule_id):
                    logger.warning(f"⚠️ スケジュール {entry.name} は既に実行中です。スキップします。")
                    return None

            logger.info(f"📅 スケジュール実行予約: {entry.name}")
            return super().reserve(entry)
        except Exception as e:
            logger.error(f"❌ スケジュール予約エラー: {e}")
            return None

    def _is_schedule_running(self, schedule_id: str) -> bool:
        """指定されたスケジュールが実行中かチェック"""
        try:
            from app.database import Task as DBTask, TaskStatus, SessionLocal as DB
            db = DB()

            running_tasks = db.query(DBTask).filter(
                DBTask.schedule_id == schedule_id,
                DBTask.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING])
            ).count()

            db.close()
            return running_tasks > 0

        except Exception as e:
            logger.error(f"❌ 重複実行チェックエラー: {e}")
            return False

    def apply_async(self, entry, producer=None, advance=True, **kwargs):
        """非同期でタスクを実行"""
        logger.info(f"🚀 スケジュールタスク実行: {entry.name}")
        return super().apply_async(entry, producer=producer, advance=advance, **kwargs)
