#!/usr/bin/env python3
"""
ScrapyUI Server Manager - サーバー安定化管理スクリプト
"""

import os
import sys
import time
import signal
import subprocess
import psutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json
import requests
from datetime import datetime

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/server_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ServerManager:
    """サーバー管理クラス"""

    def __init__(self):
        self.backend_process: Optional[subprocess.Popen] = None
        self.celery_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        self.nodejs_process: Optional[subprocess.Popen] = None

        self.backend_dir = Path(__file__).parent
        self.frontend_dir = self.backend_dir.parent / "frontend"
        self.nodejs_dir = self.backend_dir.parent / "nodejs"

        self.health_check_interval = 30  # 30秒間隔でヘルスチェック
        self.restart_attempts = 3

        # プロセス監視統計
        self.stats = {
            'started_at': datetime.now(),
            'backend_restarts': 0,
            'celery_restarts': 0,
            'frontend_restarts': 0,
            'nodejs_restarts': 0,
            'last_health_check': None,
            'uptime': 0
        }

    def start_backend(self) -> bool:
        """バックエンドサーバーを起動"""
        try:
            logger.info("🚀 Starting backend server...")

            # 既存プロセスを終了
            self.stop_backend()

            # uvicorn設定ファイルを使用して起動
            cmd = [sys.executable, "uvicorn_config.py"]

            self.backend_process = subprocess.Popen(
                cmd,
                cwd=str(self.backend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # 起動確認（最大30秒待機）
            for i in range(30):
                if self.check_backend_health():
                    logger.info(f"✅ Backend server started successfully (PID: {self.backend_process.pid})")
                    return True
                time.sleep(1)

            logger.error("❌ Backend server failed to start within 30 seconds")
            return False

        except Exception as e:
            logger.error(f"❌ Error starting backend server: {str(e)}")
            return False

    def start_celery(self) -> bool:
        """Celeryワーカーを起動"""
        try:
            logger.info("🔄 Starting Celery worker...")

            # 既存プロセスを終了
            self.stop_celery()

            cmd = [
                sys.executable, "-m", "celery", "-A", "app.celery_app", "worker",
                "--loglevel=info", "-Q", "scrapy,maintenance,monitoring",
                "--concurrency=2", "--pool=prefork",
                "--max-tasks-per-child=200", "--max-memory-per-child=500000",
                "--time-limit=3600", "--soft-time-limit=3300"
            ]

            self.celery_process = subprocess.Popen(
                cmd,
                cwd=str(self.backend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # 起動確認（最大15秒待機）
            time.sleep(15)
            if self.celery_process.poll() is None:
                logger.info(f"✅ Celery worker started successfully (PID: {self.celery_process.pid})")
                return True
            else:
                logger.error("❌ Celery worker failed to start")
                return False

        except Exception as e:
            logger.error(f"❌ Error starting Celery worker: {str(e)}")
            return False

    def start_frontend(self) -> bool:
        """フロントエンドサーバーを起動"""
        try:
            if not self.frontend_dir.exists():
                logger.warning("⚠️ Frontend directory not found, skipping...")
                return True

            logger.info("🎨 Starting frontend server...")

            # 既存プロセスを終了
            self.stop_frontend()

            cmd = ["npm", "run", "dev"]

            self.frontend_process = subprocess.Popen(
                cmd,
                cwd=str(self.frontend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # 起動確認（最大30秒待機）
            time.sleep(30)
            if self.frontend_process.poll() is None:
                logger.info(f"✅ Frontend server started successfully (PID: {self.frontend_process.pid})")
                return True
            else:
                logger.error("❌ Frontend server failed to start")
                return False

        except Exception as e:
            logger.error(f"❌ Error starting frontend server: {str(e)}")
            return False

    def start_nodejs(self) -> bool:
        """Node.jsサービスを起動"""
        try:
            if not self.nodejs_dir.exists():
                logger.warning("⚠️ Node.js directory not found, skipping...")
                return True

            logger.info("🟢 Starting Node.js service...")

            # 既存プロセスを終了
            self.stop_nodejs()

            cmd = ["npm", "start"]

            self.nodejs_process = subprocess.Popen(
                cmd,
                cwd=str(self.nodejs_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # 起動確認（最大15秒待機）
            time.sleep(15)
            if self.nodejs_process.poll() is None:
                logger.info(f"✅ Node.js service started successfully (PID: {self.nodejs_process.pid})")
                return True
            else:
                logger.error("❌ Node.js service failed to start")
                return False

        except Exception as e:
            logger.error(f"❌ Error starting Node.js service: {str(e)}")
            return False

    def check_backend_health(self) -> bool:
        """バックエンドサーバーのヘルスチェック"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def check_frontend_health(self) -> bool:
        """フロントエンドサーバーのヘルスチェック"""
        try:
            response = requests.get("http://localhost:4000", timeout=5)
            return response.status_code in [200, 404]  # 404も正常（ルーティング）
        except:
            return False

    def check_nodejs_health(self) -> bool:
        """Node.jsサービスのヘルスチェック"""
        try:
            response = requests.get("http://localhost:3001/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def stop_backend(self):
        """バックエンドサーバーを停止"""
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=10)
            except:
                try:
                    self.backend_process.kill()
                except:
                    pass
            self.backend_process = None

    def stop_celery(self):
        """Celeryワーカーを停止"""
        if self.celery_process:
            try:
                self.celery_process.terminate()
                self.celery_process.wait(timeout=10)
            except:
                try:
                    self.celery_process.kill()
                except:
                    pass
            self.celery_process = None

    def stop_frontend(self):
        """フロントエンドサーバーを停止"""
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=10)
            except:
                try:
                    self.frontend_process.kill()
                except:
                    pass
            self.frontend_process = None

    def stop_nodejs(self):
        """Node.jsサービスを停止"""
        if self.nodejs_process:
            try:
                self.nodejs_process.terminate()
                self.nodejs_process.wait(timeout=10)
            except:
                try:
                    self.nodejs_process.kill()
                except:
                    pass
            self.nodejs_process = None

    def stop_all(self):
        """全サービスを停止"""
        logger.info("🛑 Stopping all services...")
        self.stop_backend()
        self.stop_celery()
        self.stop_frontend()
        self.stop_nodejs()
        logger.info("✅ All services stopped")

    def start_all(self) -> bool:
        """全サービスを起動"""
        logger.info("🚀 Starting all services...")

        success = True

        # バックエンドサーバー
        if not self.start_backend():
            success = False

        # Celeryワーカー
        if not self.start_celery():
            success = False

        # フロントエンドサーバー
        if not self.start_frontend():
            success = False

        # Node.jsサービス
        if not self.start_nodejs():
            success = False

        if success:
            logger.info("✅ All services started successfully")
        else:
            logger.error("❌ Some services failed to start")

        return success

    def monitor_services(self):
        """サービス監視ループ"""
        logger.info("🔍 Starting service monitoring...")

        while True:
            try:
                self.stats['last_health_check'] = datetime.now()
                self.stats['uptime'] = (datetime.now() - self.stats['started_at']).total_seconds()

                # バックエンドヘルスチェック
                if not self.check_backend_health():
                    logger.warning("⚠️ Backend health check failed, attempting restart...")
                    if self.start_backend():
                        self.stats['backend_restarts'] += 1
                        logger.info("✅ Backend restarted successfully")
                    else:
                        logger.error("❌ Backend restart failed")

                # Celeryプロセスチェック
                if self.celery_process and self.celery_process.poll() is not None:
                    logger.warning("⚠️ Celery worker stopped, attempting restart...")
                    if self.start_celery():
                        self.stats['celery_restarts'] += 1
                        logger.info("✅ Celery worker restarted successfully")
                    else:
                        logger.error("❌ Celery worker restart failed")

                # フロントエンドヘルスチェック
                if self.frontend_process and not self.check_frontend_health():
                    logger.warning("⚠️ Frontend health check failed, attempting restart...")
                    if self.start_frontend():
                        self.stats['frontend_restarts'] += 1
                        logger.info("✅ Frontend restarted successfully")
                    else:
                        logger.error("❌ Frontend restart failed")

                # Node.jsヘルスチェック
                if self.nodejs_process and not self.check_nodejs_health():
                    logger.warning("⚠️ Node.js health check failed, attempting restart...")
                    if self.start_nodejs():
                        self.stats['nodejs_restarts'] += 1
                        logger.info("✅ Node.js restarted successfully")
                    else:
                        logger.error("❌ Node.js restart failed")

                # 統計情報をログ出力（5分間隔）
                if int(self.stats['uptime']) % 300 == 0:
                    self.log_stats()

                time.sleep(self.health_check_interval)

            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {str(e)}")
                time.sleep(10)

    def log_stats(self):
        """統計情報をログ出力"""
        uptime_hours = self.stats['uptime'] / 3600
        logger.info(f"📊 Service Statistics:")
        logger.info(f"   Uptime: {uptime_hours:.1f} hours")
        logger.info(f"   Backend restarts: {self.stats['backend_restarts']}")
        logger.info(f"   Celery restarts: {self.stats['celery_restarts']}")
        logger.info(f"   Frontend restarts: {self.stats['frontend_restarts']}")
        logger.info(f"   Node.js restarts: {self.stats['nodejs_restarts']}")

    def signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        logger.info(f"🛑 Received signal {signum}, shutting down...")
        self.stop_all()
        sys.exit(0)


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="ScrapyUI Server Manager")
    parser.add_argument("action", choices=["start", "stop", "restart", "monitor", "status"],
                       help="Action to perform")
    parser.add_argument("--service", choices=["backend", "celery", "frontend", "nodejs", "all"],
                       default="all", help="Service to manage")

    args = parser.parse_args()

    manager = ServerManager()

    # シグナルハンドラーを設定
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)

    if args.action == "start":
        if args.service == "all":
            manager.start_all()
        elif args.service == "backend":
            manager.start_backend()
        elif args.service == "celery":
            manager.start_celery()
        elif args.service == "frontend":
            manager.start_frontend()
        elif args.service == "nodejs":
            manager.start_nodejs()

    elif args.action == "stop":
        if args.service == "all":
            manager.stop_all()
        elif args.service == "backend":
            manager.stop_backend()
        elif args.service == "celery":
            manager.stop_celery()
        elif args.service == "frontend":
            manager.stop_frontend()
        elif args.service == "nodejs":
            manager.stop_nodejs()

    elif args.action == "restart":
        if args.service == "all":
            manager.stop_all()
            time.sleep(2)
            manager.start_all()
        elif args.service == "backend":
            manager.stop_backend()
            time.sleep(2)
            manager.start_backend()
        elif args.service == "celery":
            manager.stop_celery()
            time.sleep(2)
            manager.start_celery()
        elif args.service == "frontend":
            manager.stop_frontend()
            time.sleep(2)
            manager.start_frontend()
        elif args.service == "nodejs":
            manager.stop_nodejs()
            time.sleep(2)
            manager.start_nodejs()

    elif args.action == "monitor":
        manager.start_all()
        manager.monitor_services()

    elif args.action == "status":
        print("🔍 Service Status:")
        print(f"Backend: {'✅ Running' if manager.check_backend_health() else '❌ Stopped'}")
        print(f"Frontend: {'✅ Running' if manager.check_frontend_health() else '❌ Stopped'}")
        print(f"Node.js: {'✅ Running' if manager.check_nodejs_health() else '❌ Stopped'}")


if __name__ == "__main__":
    main()
