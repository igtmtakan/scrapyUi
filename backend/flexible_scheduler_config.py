#!/usr/bin/env python3
"""
柔軟なスケジューラー設定システム
同時実行の可否を設定可能にする
"""

import logging
from datetime import datetime, timedelta
from croniter import croniter
from app.database import SessionLocal, Schedule as DBSchedule

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlexibleSchedulerConfig:
    """柔軟なスケジューラー設定クラス"""
    
    # 設定オプション
    CONFLICT_RESOLUTION_MODES = {
        'ALLOW_ALL': 'すべての同時実行を許可',
        'PREVENT_SAME_SITE': '同一サイトのみ時間分散',
        'PREVENT_HEAVY_TASKS': '重いタスクのみ時間分散',
        'PREVENT_ALL': 'すべて時間分散（現在の設定）'
    }
    
    def __init__(self, mode='ALLOW_ALL'):
        """
        初期化
        
        Args:
            mode (str): 競合解決モード
        """
        self.mode = mode
        self.db = SessionLocal()
        
    def analyze_schedules_by_mode(self):
        """モードに応じたスケジュール分析"""
        schedules = self.db.query(DBSchedule).filter(DBSchedule.is_active == True).all()
        
        logger.info(f"📋 モード: {self.CONFLICT_RESOLUTION_MODES[self.mode]}")
        logger.info(f"📊 {len(schedules)}個のスケジュールを分析中...")
        
        if self.mode == 'ALLOW_ALL':
            return self._allow_all_conflicts(schedules)
        elif self.mode == 'PREVENT_SAME_SITE':
            return self._prevent_same_site_conflicts(schedules)
        elif self.mode == 'PREVENT_HEAVY_TASKS':
            return self._prevent_heavy_task_conflicts(schedules)
        elif self.mode == 'PREVENT_ALL':
            return self._prevent_all_conflicts(schedules)
    
    def _allow_all_conflicts(self, schedules):
        """すべての同時実行を許可"""
        logger.info("✅ すべての同時実行を許可します")
        
        # 元のCronパターンに戻す
        original_patterns = {
            'Test Schedule - omocha20': '*/5 * * * *',
            '10': '*/10 * * * *',
            '10-2': '*/10 * * * *',
            '40': '*/40 * * * *',
            '1h': '0 * * * *'
        }
        
        for schedule in schedules:
            if schedule.name in original_patterns:
                original_cron = original_patterns[schedule.name]
                if schedule.cron_expression != original_cron:
                    schedule.cron_expression = original_cron
                    logger.info(f"🔄 {schedule.name}: {original_cron} に復元")
        
        self.db.commit()
        return "すべての同時実行を許可しました"
    
    def _prevent_same_site_conflicts(self, schedules):
        """同一サイトのスパイダーのみ時間分散"""
        logger.info("🔍 同一サイトのスパイダーを検出中...")
        
        # サイト別にグループ化（簡易実装）
        site_groups = {}
        for schedule in schedules:
            # スパイダー名からサイトを推定
            site = self._extract_site_from_spider(schedule)
            if site not in site_groups:
                site_groups[site] = []
            site_groups[site].append(schedule)
        
        # 同一サイトのスケジュールのみ調整
        adjusted_count = 0
        for site, site_schedules in site_groups.items():
            if len(site_schedules) > 1:
                logger.info(f"⚠️ {site}: {len(site_schedules)}個のスケジュールが競合")
                adjusted_count += self._adjust_site_schedules(site_schedules)
        
        self.db.commit()
        return f"{adjusted_count}個のスケジュールを調整しました"
    
    def _prevent_heavy_task_conflicts(self, schedules):
        """重いタスクのみ時間分散"""
        logger.info("🔍 重いタスクを検出中...")
        
        # タスクの重さを判定（簡易実装）
        heavy_schedules = []
        light_schedules = []
        
        for schedule in schedules:
            if self._is_heavy_task(schedule):
                heavy_schedules.append(schedule)
            else:
                light_schedules.append(schedule)
        
        logger.info(f"📊 重いタスク: {len(heavy_schedules)}個")
        logger.info(f"📊 軽いタスク: {len(light_schedules)}個")
        
        # 重いタスクのみ時間分散
        adjusted_count = 0
        if len(heavy_schedules) > 1:
            adjusted_count = self._adjust_heavy_schedules(heavy_schedules)
        
        self.db.commit()
        return f"{adjusted_count}個の重いタスクを調整しました"
    
    def _prevent_all_conflicts(self, schedules):
        """すべて時間分散（現在の実装）"""
        logger.info("🔄 すべてのスケジュールを時間分散します")
        # 既存の競合解決システムを使用
        from schedule_conflict_resolver import ScheduleConflictResolver
        resolver = ScheduleConflictResolver()
        resolver.resolve_conflicts()
        resolver.close()
        return "すべての競合を解決しました"
    
    def _extract_site_from_spider(self, schedule):
        """スパイダー名からサイトを抽出"""
        # 簡易実装：スパイダー名から推定
        spider_name = getattr(schedule, 'spider_name', schedule.name.lower())
        
        if 'amazon' in spider_name:
            return 'amazon.co.jp'
        elif 'omocha' in spider_name:
            return 'omocha-sample.com'
        else:
            return 'unknown'
    
    def _is_heavy_task(self, schedule):
        """タスクが重いかどうかを判定"""
        # 簡易実装：間隔が短いほど重いと判定
        cron_parts = schedule.cron_expression.split()
        minute_part = cron_parts[0]
        
        if '/' in minute_part:
            interval = int(minute_part.split('/')[-1])
            return interval <= 10  # 10分以下の間隔は重いタスク
        elif minute_part == '0':
            return False  # 毎時は軽いタスク
        else:
            return True  # その他は重いタスク
    
    def _adjust_site_schedules(self, site_schedules):
        """同一サイトのスケジュールを調整"""
        adjusted_count = 0
        for i, schedule in enumerate(site_schedules[1:], 1):  # 最初以外を調整
            new_cron = self._generate_offset_cron(schedule.cron_expression, i)
            if new_cron and new_cron != schedule.cron_expression:
                schedule.cron_expression = new_cron
                logger.info(f"✅ {schedule.name}: {new_cron}")
                adjusted_count += 1
        return adjusted_count
    
    def _adjust_heavy_schedules(self, heavy_schedules):
        """重いスケジュールを調整"""
        adjusted_count = 0
        for i, schedule in enumerate(heavy_schedules[1:], 1):  # 最初以外を調整
            new_cron = self._generate_offset_cron(schedule.cron_expression, i * 2)
            if new_cron and new_cron != schedule.cron_expression:
                schedule.cron_expression = new_cron
                logger.info(f"✅ {schedule.name}: {new_cron}")
                adjusted_count += 1
        return adjusted_count
    
    def _generate_offset_cron(self, original_cron, offset_minutes):
        """オフセットを適用したCronパターンを生成"""
        parts = original_cron.split()
        minute_part = parts[0]
        
        if '/' in minute_part:
            interval = int(minute_part.split('/')[-1])
            return f"{offset_minutes}-59/{interval} * * * *"
        elif minute_part == '0':
            return f"{offset_minutes} * * * *"
        else:
            return None
    
    def close(self):
        """データベース接続を閉じる"""
        self.db.close()

def main():
    """メイン関数"""
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else 'ALLOW_ALL'
    
    config = FlexibleSchedulerConfig(mode)
    
    try:
        result = config.analyze_schedules_by_mode()
        logger.info(f"✅ 完了: {result}")
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
    finally:
        config.close()

if __name__ == "__main__":
    main()
