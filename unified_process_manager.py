#!/usr/bin/env python3
"""
ScrapyUI 統合プロセス管理システム
全サービスの起動・停止・監視を統一管理
"""

import os
import sys
import time
import signal
import subprocess
import threading
import logging
import json
import psutil
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('unified_process_manager.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ServiceConfig:
    """サービス設定"""
    name: str
    command: List[str]
    cwd: str
    port: Optional[int] = None
    health_url: Optional[str] = None
    dependencies: List[str] = None
    restart_policy: str = "always"  # always, on-failure, never
    max_restarts: int = 5
    restart_window: int = 300  # 5分
    startup_timeout: int = 30
    shutdown_timeout: int = 10
    environment: Dict[str, str] = None

class UnifiedProcessManager:
    """統合プロセス管理システム"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.absolute()
        self.services: Dict[str, ServiceConfig] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.service_stats: Dict[str, Dict] = {}
        self.monitoring = False
        self.monitor_thread = None
        
        # PIDファイルディレクトリ
        self.pid_dir = self.base_dir / "pids"
        self.pid_dir.mkdir(exist_ok=True)
        
        # ログディレクトリ
        self.log_dir = self.base_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        self._setup_services()
        self._setup_signal_handlers()
    
    def _setup_services(self):
        """サービス設定の初期化"""
        
        # バックエンドサーバー
        self.services["backend"] = ServiceConfig(
            name="backend",
            command=["python3", "-m", "uvicorn", "backend.app.main:app", 
                    "--host", "0.0.0.0", "--port", "8000"],
            cwd=str(self.base_dir),
            port=8000,
            health_url="http://localhost:8000/health",
            dependencies=[],
            environment={"PYTHONPATH": str(self.base_dir)}
        )
        
        # Spider Manager
        self.services["spider-manager"] = ServiceConfig(
            name="spider-manager",
            command=["python3", "simple_main.py"],
            cwd=str(self.base_dir / "microservices" / "spider-manager"),
            port=8002,
            health_url="http://localhost:8002/health",
            dependencies=["backend"],
            startup_timeout=15
        )
        
        # Test Service
        self.services["test-service"] = ServiceConfig(
            name="test-service",
            command=["python3", "simple_server.py"],
            cwd=str(self.base_dir / "microservices" / "test-service"),
            port=8005,
            health_url="http://localhost:8005/health",
            dependencies=["backend"],
            startup_timeout=15
        )
        
        # フロントエンド（オプション）
        if (self.base_dir / "frontend").exists():
            self.services["frontend"] = ServiceConfig(
                name="frontend",
                command=["npm", "run", "dev"],
                cwd=str(self.base_dir / "frontend"),
                port=4000,
                dependencies=["backend"],
                startup_timeout=30
            )
        
        # Node.js Puppeteer Service（オプション）
        if (self.base_dir / "nodejs-puppeteer").exists():
            self.services["nodejs-puppeteer"] = ServiceConfig(
                name="nodejs-puppeteer",
                command=["npm", "start"],
                cwd=str(self.base_dir / "nodejs-puppeteer"),
                port=3001,
                dependencies=["backend"],
                startup_timeout=20
            )
    
    def _setup_signal_handlers(self):
        """シグナルハンドラーの設定"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        logger.info(f"🛑 Received signal {signum}, shutting down...")
        self.stop_all()
        sys.exit(0)
    
    def _get_pid_file(self, service_name: str) -> Path:
        """PIDファイルパスを取得"""
        return self.pid_dir / f"{service_name}.pid"
    
    def _save_pid(self, service_name: str, pid: int):
        """PIDをファイルに保存"""
        pid_file = self._get_pid_file(service_name)
        with open(pid_file, 'w') as f:
            f.write(str(pid))
    
    def _load_pid(self, service_name: str) -> Optional[int]:
        """PIDファイルから読み込み"""
        pid_file = self._get_pid_file(service_name)
        if pid_file.exists():
            try:
                with open(pid_file, 'r') as f:
                    return int(f.read().strip())
            except (ValueError, IOError):
                pass
        return None
    
    def _remove_pid(self, service_name: str):
        """PIDファイルを削除"""
        pid_file = self._get_pid_file(service_name)
        if pid_file.exists():
            pid_file.unlink()
    
    def _is_process_running(self, pid: int) -> bool:
        """プロセスが実行中かチェック"""
        try:
            return psutil.pid_exists(pid)
        except:
            return False
    
    def _kill_process_tree(self, pid: int, timeout: int = 10):
        """プロセスツリーを終了"""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # 子プロセスを先に終了
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            
            # 親プロセスを終了
            parent.terminate()
            
            # 終了を待機
            gone, alive = psutil.wait_procs(children + [parent], timeout=timeout)
            
            # まだ生きているプロセスを強制終了
            for proc in alive:
                try:
                    proc.kill()
                except psutil.NoSuchProcess:
                    pass
                    
        except psutil.NoSuchProcess:
            pass
        except Exception as e:
            logger.error(f"❌ Error killing process tree {pid}: {e}")
    
    def _check_health(self, service_name: str) -> bool:
        """サービスのヘルスチェック"""
        config = self.services.get(service_name)
        if not config or not config.health_url:
            # ヘルスチェックURLがない場合はプロセスの存在確認
            return service_name in self.processes and self.processes[service_name].poll() is None
        
        try:
            response = requests.get(config.health_url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _wait_for_dependencies(self, service_name: str) -> bool:
        """依存関係の起動を待機"""
        config = self.services[service_name]
        if not config.dependencies:
            return True
        
        logger.info(f"⏳ Waiting for dependencies of {service_name}: {config.dependencies}")
        
        for dep in config.dependencies:
            timeout = 60  # 60秒タイムアウト
            while timeout > 0:
                if self._check_health(dep):
                    logger.info(f"✅ Dependency {dep} is ready")
                    break
                time.sleep(2)
                timeout -= 2
            else:
                logger.error(f"❌ Dependency {dep} failed to start within timeout")
                return False
        
        return True

    def start_service(self, service_name: str) -> bool:
        """サービスを起動"""
        if service_name not in self.services:
            logger.error(f"❌ Unknown service: {service_name}")
            return False

        config = self.services[service_name]

        # 既存プロセスをチェック
        if service_name in self.processes:
            if self.processes[service_name].poll() is None:
                logger.info(f"✅ Service {service_name} is already running")
                return True
            else:
                # プロセスが終了している場合は削除
                del self.processes[service_name]

        # 依存関係の確認
        if not self._wait_for_dependencies(service_name):
            return False

        logger.info(f"🚀 Starting service: {service_name}")

        try:
            # 環境変数の設定
            env = os.environ.copy()
            if config.environment:
                env.update(config.environment)

            # ログファイルの設定
            log_file = self.log_dir / f"{service_name}.log"

            # プロセス起動
            with open(log_file, 'a') as log:
                process = subprocess.Popen(
                    config.command,
                    cwd=config.cwd,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setsid  # 新しいプロセスグループを作成
                )

            self.processes[service_name] = process
            self._save_pid(service_name, process.pid)

            # 起動確認
            timeout = config.startup_timeout
            while timeout > 0:
                if config.health_url:
                    if self._check_health(service_name):
                        logger.info(f"✅ Service {service_name} started successfully (PID: {process.pid})")
                        self._init_service_stats(service_name)
                        return True
                else:
                    if process.poll() is None:
                        logger.info(f"✅ Service {service_name} started successfully (PID: {process.pid})")
                        self._init_service_stats(service_name)
                        return True

                time.sleep(1)
                timeout -= 1

            logger.error(f"❌ Service {service_name} failed to start within {config.startup_timeout} seconds")
            self.stop_service(service_name)
            return False

        except Exception as e:
            logger.error(f"❌ Error starting service {service_name}: {e}")
            return False

    def stop_service(self, service_name: str) -> bool:
        """サービスを停止"""
        if service_name not in self.services:
            logger.error(f"❌ Unknown service: {service_name}")
            return False

        config = self.services[service_name]
        logger.info(f"🛑 Stopping service: {service_name}")

        # プロセス管理からの停止
        if service_name in self.processes:
            process = self.processes[service_name]
            try:
                self._kill_process_tree(process.pid, config.shutdown_timeout)
                del self.processes[service_name]
            except Exception as e:
                logger.error(f"❌ Error stopping service {service_name}: {e}")

        # PIDファイルからの停止
        pid = self._load_pid(service_name)
        if pid and self._is_process_running(pid):
            try:
                self._kill_process_tree(pid, config.shutdown_timeout)
            except Exception as e:
                logger.error(f"❌ Error stopping PID {pid}: {e}")

        self._remove_pid(service_name)
        logger.info(f"✅ Service {service_name} stopped")
        return True

    def restart_service(self, service_name: str) -> bool:
        """サービスを再起動"""
        logger.info(f"🔄 Restarting service: {service_name}")
        self.stop_service(service_name)
        time.sleep(2)  # 少し待機
        return self.start_service(service_name)

    def _init_service_stats(self, service_name: str):
        """サービス統計の初期化"""
        self.service_stats[service_name] = {
            'started_at': datetime.now(),
            'restart_count': 0,
            'last_restart': None,
            'health_checks': 0,
            'health_failures': 0
        }

    def start_all(self, services: List[str] = None) -> bool:
        """全サービスまたは指定されたサービスを起動"""
        if services is None:
            services = list(self.services.keys())

        logger.info(f"🚀 Starting services: {services}")

        # 依存関係順にソート
        sorted_services = self._sort_by_dependencies(services)

        success = True
        for service_name in sorted_services:
            if not self.start_service(service_name):
                success = False
                logger.error(f"❌ Failed to start {service_name}")

        if success:
            logger.info("✅ All services started successfully")
            self.start_monitoring()
        else:
            logger.error("❌ Some services failed to start")

        return success

    def stop_all(self):
        """全サービスを停止"""
        logger.info("🛑 Stopping all services...")

        # 監視を停止
        self.stop_monitoring()

        # 依存関係の逆順で停止
        services = list(self.services.keys())
        sorted_services = self._sort_by_dependencies(services)

        for service_name in reversed(sorted_services):
            self.stop_service(service_name)

        logger.info("✅ All services stopped")

    def _sort_by_dependencies(self, services: List[str]) -> List[str]:
        """依存関係順にサービスをソート"""
        sorted_services = []
        remaining = services.copy()

        while remaining:
            # 依存関係のないサービスを探す
            for service in remaining[:]:
                config = self.services[service]
                if not config.dependencies or all(dep in sorted_services for dep in config.dependencies):
                    sorted_services.append(service)
                    remaining.remove(service)
                    break
            else:
                # 循環依存関係がある場合は残りをそのまま追加
                sorted_services.extend(remaining)
                break

        return sorted_services

    def start_monitoring(self):
        """監視を開始"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("🔍 Service monitoring started")

    def stop_monitoring(self):
        """監視を停止"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("🛑 Service monitoring stopped")

    def _monitor_loop(self):
        """監視ループ"""
        while self.monitoring:
            try:
                for service_name in self.services:
                    if service_name in self.processes:
                        self._check_service_health(service_name)

                time.sleep(30)  # 30秒間隔でチェック

            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(60)

    def _check_service_health(self, service_name: str):
        """サービスのヘルスチェックと自動復旧"""
        if service_name not in self.service_stats:
            return

        stats = self.service_stats[service_name]
        stats['health_checks'] += 1

        if not self._check_health(service_name):
            stats['health_failures'] += 1
            logger.warning(f"⚠️ Health check failed for {service_name}")

            # 再起動ポリシーに基づく処理
            config = self.services[service_name]
            if config.restart_policy == "always":
                self._auto_restart_service(service_name)
            elif config.restart_policy == "on-failure":
                if service_name in self.processes and self.processes[service_name].poll() is not None:
                    self._auto_restart_service(service_name)

    def _auto_restart_service(self, service_name: str):
        """サービスの自動再起動"""
        config = self.services[service_name]
        stats = self.service_stats[service_name]

        # 再起動制限チェック
        now = datetime.now()
        if stats['last_restart']:
            time_since_restart = (now - stats['last_restart']).total_seconds()
            if time_since_restart < config.restart_window:
                if stats['restart_count'] >= config.max_restarts:
                    logger.error(f"❌ Service {service_name} exceeded max restarts ({config.max_restarts})")
                    return
            else:
                # 再起動ウィンドウをリセット
                stats['restart_count'] = 0

        logger.info(f"🔄 Auto-restarting service: {service_name}")
        if self.restart_service(service_name):
            stats['restart_count'] += 1
            stats['last_restart'] = now
            logger.info(f"✅ Service {service_name} auto-restarted successfully")
        else:
            logger.error(f"❌ Failed to auto-restart service {service_name}")

    def get_status(self) -> Dict[str, Any]:
        """全サービスの状態を取得"""
        status = {}
        for service_name in self.services:
            is_running = service_name in self.processes and self.processes[service_name].poll() is None
            is_healthy = self._check_health(service_name) if is_running else False

            status[service_name] = {
                'running': is_running,
                'healthy': is_healthy,
                'pid': self.processes[service_name].pid if is_running else None,
                'stats': self.service_stats.get(service_name, {})
            }

        return status

    def print_status(self):
        """状態を表示"""
        status = self.get_status()

        print("\n" + "="*60)
        print("🔍 ScrapyUI Services Status")
        print("="*60)

        for service_name, info in status.items():
            status_icon = "✅" if info['healthy'] else ("🟡" if info['running'] else "❌")
            pid_info = f"(PID: {info['pid']})" if info['pid'] else ""

            print(f"{status_icon} {service_name:<20} {pid_info}")

            if info['stats']:
                stats = info['stats']
                if 'started_at' in stats:
                    uptime = datetime.now() - stats['started_at']
                    print(f"   ⏱️  Uptime: {uptime}")
                if 'restart_count' in stats and stats['restart_count'] > 0:
                    print(f"   🔄 Restarts: {stats['restart_count']}")

        print("="*60)


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description='ScrapyUI Unified Process Manager')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'monitor'],
                       help='Action to perform')
    parser.add_argument('--services', nargs='*', help='Specific services to manage')
    parser.add_argument('--no-monitor', action='store_true', help='Start without monitoring')

    args = parser.parse_args()

    manager = UnifiedProcessManager()

    try:
        if args.action == 'start':
            success = manager.start_all(args.services)
            if success and not args.no_monitor:
                logger.info("🔍 Press Ctrl+C to stop all services")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
            sys.exit(0 if success else 1)

        elif args.action == 'stop':
            manager.stop_all()

        elif args.action == 'restart':
            if args.services:
                for service in args.services:
                    manager.restart_service(service)
            else:
                manager.stop_all()
                time.sleep(2)
                manager.start_all()

        elif args.action == 'status':
            manager.print_status()

        elif args.action == 'monitor':
            manager.start_monitoring()
            logger.info("🔍 Monitoring started. Press Ctrl+C to stop")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                manager.stop_monitoring()

    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
        manager.stop_all()
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
