#!/usr/bin/env python3
"""
スケジュール競合解決システム
複数のスケジュールが同時実行されることを防ぐため、Cronパターンを自動調整
"""

import logging
from datetime import datetime, timedelta
from croniter import croniter
from app.database import SessionLocal, Schedule as DBSchedule

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScheduleConflictResolver:
    """スケジュール競合解決クラス"""
    
    def __init__(self):
        self.db = SessionLocal()
        
    def analyze_conflicts(self):
        """競合を分析"""
        schedules = self.db.query(DBSchedule).filter(DBSchedule.is_active == True).all()
        
        logger.info(f"📋 {len(schedules)}個のアクティブなスケジュールを分析中...")
        
        # 各スケジュールの実行時刻を計算
        execution_times = {}
        now = datetime.now()
        
        for schedule in schedules:
            try:
                cron = croniter(schedule.cron_expression, now)
                next_runs = []
                
                # 次の24時間分の実行時刻を計算
                for i in range(100):  # 十分な数を計算
                    next_run = cron.get_next(datetime)
                    if next_run > now + timedelta(hours=24):
                        break
                    next_runs.append(next_run.strftime('%H:%M'))
                
                execution_times[schedule.id] = {
                    'name': schedule.name,
                    'cron': schedule.cron_expression,
                    'times': next_runs
                }
                
            except Exception as e:
                logger.error(f"❌ スケジュール {schedule.name} の分析エラー: {e}")
        
        # 競合を検出
        conflicts = self._detect_conflicts(execution_times)
        return conflicts, execution_times
    
    def _detect_conflicts(self, execution_times):
        """競合を検出"""
        time_conflicts = {}
        
        for schedule_id, data in execution_times.items():
            for time_str in data['times']:
                if time_str not in time_conflicts:
                    time_conflicts[time_str] = []
                time_conflicts[time_str].append({
                    'id': schedule_id,
                    'name': data['name']
                })
        
        # 競合がある時刻のみを抽出
        conflicts = {}
        for time_str, schedules_list in time_conflicts.items():
            if len(schedules_list) > 1:
                conflicts[time_str] = schedules_list
        
        return conflicts
    
    def resolve_conflicts(self):
        """競合を自動解決"""
        conflicts, execution_times = self.analyze_conflicts()
        
        if not conflicts:
            logger.info("✅ 競合は検出されませんでした")
            return
        
        logger.info(f"🚨 {len(conflicts)}個の時刻で競合が検出されました")
        
        # 競合解決戦略
        resolved_count = 0
        
        for time_str, conflicting_schedules in conflicts.items():
            logger.info(f"⚠️ {time_str}: {len(conflicting_schedules)}個のスケジュールが競合")
            
            # 最初のスケジュール以外を調整
            for i, schedule_info in enumerate(conflicting_schedules[1:], 1):
                schedule_id = schedule_info['id']
                schedule_name = schedule_info['name']
                
                new_cron = self._generate_non_conflicting_cron(
                    schedule_id, execution_times, conflicts, offset_minutes=i
                )
                
                if new_cron:
                    self._update_schedule_cron(schedule_id, new_cron)
                    logger.info(f"✅ {schedule_name}: Cronを調整 → {new_cron}")
                    resolved_count += 1
        
        logger.info(f"🎉 {resolved_count}個のスケジュールの競合を解決しました")
    
    def _generate_non_conflicting_cron(self, schedule_id, execution_times, conflicts, offset_minutes=1):
        """競合しないCronパターンを生成"""
        original_data = execution_times[schedule_id]
        original_cron = original_data['cron']
        
        # 基本的な調整パターン
        adjustments = [
            f"{offset_minutes}-59/{self._extract_interval(original_cron)} * * * *",  # 分をオフセット
            f"*/{self._extract_interval(original_cron)} * * * *",  # 元のパターン維持
        ]
        
        # 各調整パターンをテスト
        for new_cron in adjustments:
            if self._test_cron_conflicts(new_cron, execution_times, schedule_id):
                return new_cron
        
        # フォールバック: 分を大きくオフセット
        interval = self._extract_interval(original_cron)
        for offset in range(2, min(interval, 10)):
            new_cron = f"{offset}-59/{interval} * * * *"
            if self._test_cron_conflicts(new_cron, execution_times, schedule_id):
                return new_cron
        
        return None
    
    def _extract_interval(self, cron_expression):
        """Cronパターンから間隔を抽出"""
        parts = cron_expression.split()
        minute_part = parts[0]
        
        if '/' in minute_part:
            return int(minute_part.split('/')[-1])
        elif minute_part == '0':
            return 60  # 毎時
        else:
            return 10  # デフォルト
    
    def _test_cron_conflicts(self, new_cron, execution_times, exclude_schedule_id):
        """新しいCronパターンが競合しないかテスト"""
        try:
            now = datetime.now()
            cron = croniter(new_cron, now)
            
            # 次の24時間分をテスト
            test_times = []
            for i in range(100):
                next_run = cron.get_next(datetime)
                if next_run > now + timedelta(hours=24):
                    break
                test_times.append(next_run.strftime('%H:%M'))
            
            # 他のスケジュールと競合チェック
            for schedule_id, data in execution_times.items():
                if schedule_id == exclude_schedule_id:
                    continue
                
                for test_time in test_times:
                    if test_time in data['times']:
                        return False  # 競合あり
            
            return True  # 競合なし
            
        except Exception:
            return False
    
    def _update_schedule_cron(self, schedule_id, new_cron):
        """スケジュールのCronパターンを更新"""
        try:
            schedule = self.db.query(DBSchedule).filter(DBSchedule.id == schedule_id).first()
            if schedule:
                schedule.cron_expression = new_cron
                self.db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ スケジュール更新エラー: {e}")
            self.db.rollback()
        return False
    
    def close(self):
        """データベース接続を閉じる"""
        self.db.close()

def main():
    """メイン関数"""
    resolver = ScheduleConflictResolver()
    
    try:
        logger.info("🔍 スケジュール競合解決を開始...")
        resolver.resolve_conflicts()
        logger.info("✅ スケジュール競合解決完了")
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
    finally:
        resolver.close()

if __name__ == "__main__":
    main()
