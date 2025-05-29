#!/usr/bin/env python3
"""
ScrapyUI Watchdog - プロセス監視デーモン
サーバーの異常終了を監視し、自動復旧を行う
"""

import os
import sys
import time
import signal
import subprocess
import psutil
import logging
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import queue

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/watchdog.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProcessWatchdog:
    """プロセス監視クラス"""
    
    def __init__(self):
        self.backend_dir = Path(__file__).parent
        self.project_root = self.backend_dir.parent
        
        # 監視対象プロセス
        self.processes = {
            'backend': {
                'cmd': ['python', 'uvicorn_config.py'],
                'cwd': str(self.backend_dir),
                'port': 8000,
                'health_url': 'http://localhost:8000/health',
                'process': None,
                'restart_count': 0,
                'last_restart': None,
                'max_restarts': 5,
                'restart_window': 300  # 5分間
            },
            'celery': {
                'cmd': ['python', '-m', 'celery', '-A', 'app.celery_app', 'worker', 
                       '--loglevel=info', '-Q', 'scrapy,maintenance,monitoring', 
                       '--concurrency=4', '--pool=prefork'],
                'cwd': str(self.backend_dir),
                'port': None,
                'health_url': None,
                'process': None,
                'restart_count': 0,
                'last_restart': None,
                'max_restarts': 5,
                'restart_window': 300
            }
        }
        
        self.monitoring = True
        self.check_interval = 10  # 10秒間隔
        self.stats = {
            'started_at': datetime.now(),
            'total_restarts': 0,
            'last_check': None,
            'alerts_sent': 0
        }
        
        # アラートキュー
        self.alert_queue = queue.Queue()
        
    def start_process(self, name: str) -> bool:
        """プロセスを起動"""
        try:
            config = self.processes[name]
            
            # 既存プロセスを停止
            self.stop_process(name)
            
            logger.info(f"🚀 Starting {name} process...")
            
            # プロセス起動
            process = subprocess.Popen(
                config['cmd'],
                cwd=config['cwd'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            config['process'] = process
            
            # 起動確認
            if name == 'backend':
                # バックエンドの場合はヘルスチェック
                for i in range(30):
                    if self.check_health(name):
                        logger.info(f"✅ {name} started successfully (PID: {process.pid})")
                        return True
                    time.sleep(1)
                logger.error(f"❌ {name} failed to start within 30 seconds")
                return False
            else:
                # Celeryの場合は5秒待機
                time.sleep(5)
                if process.poll() is None:
                    logger.info(f"✅ {name} started successfully (PID: {process.pid})")
                    return True
                else:
                    logger.error(f"❌ {name} failed to start")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error starting {name}: {str(e)}")
            return False
    
    def stop_process(self, name: str):
        """プロセスを停止"""
        config = self.processes[name]
        if config['process']:
            try:
                config['process'].terminate()
                config['process'].wait(timeout=10)
            except:
                try:
                    config['process'].kill()
                except:
                    pass
            config['process'] = None
    
    def check_health(self, name: str) -> bool:
        """プロセスのヘルスチェック"""
        config = self.processes[name]
        
        # プロセス存在チェック
        if not config['process'] or config['process'].poll() is not None:
            return False
        
        # HTTPヘルスチェック（バックエンドのみ）
        if config['health_url']:
            try:
                response = requests.get(config['health_url'], timeout=5)
                return response.status_code == 200
            except:
                return False
        
        return True
    
    def should_restart(self, name: str) -> bool:
        """再起動すべきかチェック"""
        config = self.processes[name]
        
        # 最大再起動回数チェック
        if config['last_restart']:
            window_start = datetime.now() - timedelta(seconds=config['restart_window'])
            if config['last_restart'] > window_start:
                if config['restart_count'] >= config['max_restarts']:
                    logger.error(f"❌ {name} exceeded max restarts ({config['max_restarts']}) in {config['restart_window']}s")
                    self.send_alert(f"{name} exceeded max restarts")
                    return False
            else:
                # ウィンドウ外なのでカウントリセット
                config['restart_count'] = 0
        
        return True
    
    def restart_process(self, name: str) -> bool:
        """プロセスを再起動"""
        if not self.should_restart(name):
            return False
        
        config = self.processes[name]
        config['restart_count'] += 1
        config['last_restart'] = datetime.now()
        self.stats['total_restarts'] += 1
        
        logger.warning(f"🔄 Restarting {name} (attempt {config['restart_count']})")
        
        if self.start_process(name):
            logger.info(f"✅ {name} restarted successfully")
            return True
        else:
            logger.error(f"❌ Failed to restart {name}")
            self.send_alert(f"Failed to restart {name}")
            return False
    
    def send_alert(self, message: str):
        """アラートを送信"""
        try:
            self.alert_queue.put({
                'timestamp': datetime.now().isoformat(),
                'message': message,
                'stats': self.stats.copy()
            })
            self.stats['alerts_sent'] += 1
            logger.warning(f"🚨 ALERT: {message}")
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
    
    def monitor_loop(self):
        """監視ループ"""
        logger.info("🔍 Starting process monitoring...")
        
        while self.monitoring:
            try:
                self.stats['last_check'] = datetime.now()
                
                for name, config in self.processes.items():
                    if not self.check_health(name):
                        logger.warning(f"⚠️ {name} health check failed")
                        self.restart_process(name)
                
                # 統計情報を定期的にログ出力
                uptime = (datetime.now() - self.stats['started_at']).total_seconds()
                if int(uptime) % 300 == 0:  # 5分間隔
                    self.log_stats()
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {str(e)}")
                time.sleep(30)  # エラー時は30秒待機
    
    def log_stats(self):
        """統計情報をログ出力"""
        uptime = (datetime.now() - self.stats['started_at']).total_seconds()
        logger.info(f"📊 Watchdog Statistics:")
        logger.info(f"   Uptime: {uptime/3600:.1f} hours")
        logger.info(f"   Total restarts: {self.stats['total_restarts']}")
        logger.info(f"   Alerts sent: {self.stats['alerts_sent']}")
        
        for name, config in self.processes.items():
            status = "✅ Running" if self.check_health(name) else "❌ Stopped"
            logger.info(f"   {name}: {status} (restarts: {config['restart_count']})")
    
    def start_all(self):
        """全プロセスを起動"""
        logger.info("🚀 Starting all processes...")
        
        success = True
        for name in self.processes.keys():
            if not self.start_process(name):
                success = False
        
        if success:
            logger.info("✅ All processes started successfully")
        else:
            logger.error("❌ Some processes failed to start")
        
        return success
    
    def stop_all(self):
        """全プロセスを停止"""
        logger.info("🛑 Stopping all processes...")
        
        for name in self.processes.keys():
            self.stop_process(name)
        
        logger.info("✅ All processes stopped")
    
    def signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        logger.info(f"🛑 Received signal {signum}, shutting down...")
        self.monitoring = False
        self.stop_all()
        sys.exit(0)


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ScrapyUI Process Watchdog")
    parser.add_argument("action", choices=["start", "stop", "monitor", "status"], 
                       help="Action to perform")
    
    args = parser.parse_args()
    
    watchdog = ProcessWatchdog()
    
    # シグナルハンドラーを設定
    signal.signal(signal.SIGINT, watchdog.signal_handler)
    signal.signal(signal.SIGTERM, watchdog.signal_handler)
    
    if args.action == "start":
        watchdog.start_all()
    elif args.action == "stop":
        watchdog.stop_all()
    elif args.action == "monitor":
        watchdog.start_all()
        watchdog.monitor_loop()
    elif args.action == "status":
        print("🔍 Process Status:")
        for name, config in watchdog.processes.items():
            status = "✅ Running" if watchdog.check_health(name) else "❌ Stopped"
            print(f"{name}: {status}")


if __name__ == "__main__":
    main()
