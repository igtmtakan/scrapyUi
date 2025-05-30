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
        self.sync_interval = 60  # 60秒毎にデータベースを同期
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
                            task="app.tasks.scrapy_tasks.run_spider_task",
                            schedule=celery_schedule,
                            args=(str(schedule.project_id), str(schedule.spider_id)),
                            kwargs={"settings": schedule.settings or {}},
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

    def get_schedule(self):
        """現在のスケジュールを取得"""
        # 定期的にデータベースを同期
        if (self.last_sync is None or
            datetime.now() - self.last_sync > timedelta(seconds=self.sync_interval)):
            self.sync_from_database()

        # データベーススケジュールとデフォルトスケジュールを結合
        schedule = dict(self.db_schedules)
        schedule.update(self.app.conf.beat_schedule or {})

        return schedule

    def reserve(self, entry):
        """スケジュールエントリを予約"""
        logger.info(f"📅 スケジュール実行予約: {entry.name}")
        return super().reserve(entry)

    def apply_async(self, entry, publisher=None, **kwargs):
        """非同期でタスクを実行"""
        logger.info(f"🚀 スケジュールタスク実行: {entry.name}")
        return super().apply_async(entry, publisher, **kwargs)
