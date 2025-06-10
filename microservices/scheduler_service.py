#!/usr/bin/env python3
"""
独立したスケジューラーマイクロサービス
真のマイクロサービス化とデーモン化対応
"""

import os
import sys
import signal
import daemon
import lockfile
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.scheduler_service import SchedulerService
from backend.app.database import SessionLocal
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/scrapyui/scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SchedulerMicroservice:
    """独立したスケジューラーマイクロサービス"""
    
    def __init__(self):
        self.scheduler = None
        self.running = False
        
    def start(self):
        """スケジューラーサービスを開始"""
        try:
            logger.info("🚀 Starting Scheduler Microservice...")
            
            # データベース接続テスト
            db = SessionLocal()
            db.close()
            logger.info("✅ Database connection verified")
            
            # スケジューラーサービス初期化
            self.scheduler = SchedulerService()
            self.running = True
            
            # スケジューラー開始
            self.scheduler.start()
            logger.info("✅ Scheduler Microservice started successfully")
            
            # メインループ
            while self.running:
                import time
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Error starting scheduler microservice: {str(e)}")
            raise
            
    def stop(self):
        """スケジューラーサービスを停止"""
        try:
            logger.info("🛑 Stopping Scheduler Microservice...")
            self.running = False
            
            if self.scheduler:
                self.scheduler.stop()
                
            logger.info("✅ Scheduler Microservice stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Error stopping scheduler microservice: {str(e)}")

# グローバルインスタンス
scheduler_microservice = SchedulerMicroservice()

def signal_handler(signum, frame):
    """シグナルハンドラー"""
    logger.info(f"📡 Received signal {signum}")
    scheduler_microservice.stop()
    sys.exit(0)

def run_as_daemon():
    """デーモンとして実行"""
    
    # PIDファイルのパス
    pid_file = '/var/run/scrapyui/scheduler.pid'
    
    # デーモンコンテキスト
    context = daemon.DaemonContext(
        pidfile=lockfile.FileLock(pid_file),
        signal_map={
            signal.SIGTERM: signal_handler,
            signal.SIGINT: signal_handler,
            signal.SIGHUP: signal_handler,
        },
        working_directory='/home/igtmtakan/workplace/python/scrapyUI',
        umask=0o002,
    )
    
    with context:
        scheduler_microservice.start()

def run_foreground():
    """フォアグラウンドで実行"""
    
    # シグナルハンドラー設定
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        scheduler_microservice.start()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ScrapyUI Scheduler Microservice')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--stop', action='store_true', help='Stop daemon')
    
    args = parser.parse_args()
    
    if args.stop:
        # デーモン停止
        pid_file = '/var/run/scrapyui/scheduler.pid'
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            logger.info(f"✅ Stopped scheduler daemon (PID: {pid})")
        except FileNotFoundError:
            logger.error("❌ PID file not found. Daemon may not be running.")
        except ProcessLookupError:
            logger.error("❌ Process not found. Daemon may have already stopped.")
    elif args.daemon:
        # デーモンとして実行
        run_as_daemon()
    else:
        # フォアグラウンドで実行
        run_foreground()
