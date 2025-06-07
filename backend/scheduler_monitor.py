#!/usr/bin/env python3
"""
統一スケジューラー監視・自動復旧システム
根本対応後の継続的な安定性を確保
"""

import time
import psutil
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SchedulerMonitor:
    """統一スケジューラー監視システム"""
    
    def __init__(self):
        self.check_interval = 60  # 1分間隔でチェック
        self.restart_threshold = 3  # 3回連続失敗で再起動
        self.failure_count = 0
        self.last_check_time = datetime.now()
        
    def check_scheduler_health(self):
        """スケジューラーの健全性をチェック"""
        try:
            # プロセス存在チェック
            scheduler_running = self._is_scheduler_running()
            
            # データベース接続チェック
            db_connection = self._check_database_connection()
            
            # スケジュール実行チェック
            schedule_execution = self._check_schedule_execution()
            
            health_status = {
                'scheduler_running': scheduler_running,
                'db_connection': db_connection,
                'schedule_execution': schedule_execution,
                'overall_health': scheduler_running and db_connection and schedule_execution
            }
            
            logger.info(f"🔍 スケジューラー健全性チェック: {health_status}")
            return health_status
            
        except Exception as e:
            logger.error(f"❌ 健全性チェックエラー: {str(e)}")
            return {'overall_health': False, 'error': str(e)}
    
    def _is_scheduler_running(self):
        """スケジューラープロセスが動作中かチェック"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'scheduler_service' in cmdline:
                    logger.info(f"✅ スケジューラープロセス発見: PID {proc.info['pid']}")
                    return True
            
            logger.warning("⚠️ スケジューラープロセスが見つかりません")
            return False
            
        except Exception as e:
            logger.error(f"❌ プロセスチェックエラー: {str(e)}")
            return False
    
    def _check_database_connection(self):
        """データベース接続をチェック"""
        try:
            # ScrapyUIのデータベース接続をテスト
            sys.path.append(str(Path(__file__).parent))
            from app.database import SessionLocal, Schedule as DBSchedule
            
            db = SessionLocal()
            try:
                # 簡単なクエリでテスト
                count = db.query(DBSchedule).count()
                logger.info(f"✅ データベース接続正常: {count}個のスケジュール")
                return True
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ データベース接続エラー: {str(e)}")
            return False
    
    def _check_schedule_execution(self):
        """スケジュールが正常に実行されているかチェック"""
        try:
            sys.path.append(str(Path(__file__).parent))
            from app.database import SessionLocal, Schedule as DBSchedule
            
            db = SessionLocal()
            try:
                # 最近10分以内に実行されたスケジュールをチェック
                recent_time = datetime.now() - timedelta(minutes=10)
                recent_schedules = db.query(DBSchedule).filter(
                    DBSchedule.is_active == True,
                    DBSchedule.last_run >= recent_time
                ).count()
                
                if recent_schedules > 0:
                    logger.info(f"✅ 最近の実行: {recent_schedules}個のスケジュール")
                    return True
                else:
                    logger.warning("⚠️ 最近10分間にスケジュール実行がありません")
                    return False
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ スケジュール実行チェックエラー: {str(e)}")
            return False
    
    def restart_scheduler(self):
        """スケジューラーを再起動"""
        try:
            logger.info("🔄 スケジューラーを再起動中...")
            
            # 既存のスケジューラープロセスを停止
            subprocess.run(['pkill', '-f', 'scheduler_service'], check=False)
            time.sleep(3)
            
            # 新しいスケジューラーを起動
            scheduler_script = Path(__file__).parent / 'start_unified_scheduler.py'
            if scheduler_script.exists():
                subprocess.Popen([
                    sys.executable, str(scheduler_script)
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info("✅ スケジューラーを再起動しました")
                return True
            else:
                logger.error("❌ スケジューラー起動スクリプトが見つかりません")
                return False
                
        except Exception as e:
            logger.error(f"❌ スケジューラー再起動エラー: {str(e)}")
            return False
    
    def run_monitoring(self):
        """監視ループを実行"""
        logger.info("🚀 統一スケジューラー監視を開始します")
        
        while True:
            try:
                health = self.check_scheduler_health()
                
                if health['overall_health']:
                    self.failure_count = 0
                    logger.info("✅ スケジューラーは正常に動作中")
                else:
                    self.failure_count += 1
                    logger.warning(f"⚠️ スケジューラー異常検出 (連続失敗: {self.failure_count}/{self.restart_threshold})")
                    
                    if self.failure_count >= self.restart_threshold:
                        logger.error("❌ 連続失敗回数が閾値に達しました。再起動を実行します")
                        if self.restart_scheduler():
                            self.failure_count = 0
                            logger.info("✅ スケジューラー再起動完了")
                        else:
                            logger.error("❌ スケジューラー再起動に失敗しました")
                
                # 次のチェックまで待機
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 監視を停止します")
                break
            except Exception as e:
                logger.error(f"❌ 監視ループエラー: {str(e)}")
                time.sleep(self.check_interval)

if __name__ == "__main__":
    monitor = SchedulerMonitor()
    monitor.run_monitoring()
