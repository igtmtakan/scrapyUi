#!/usr/bin/env python3
"""
ScrapyUI 統合管理スクリプト
全てのサービスを統合的に管理する
"""

import os
import sys
import time
import subprocess
import argparse
import json
from pathlib import Path
from datetime import datetime

class ScrapyUIManager:
    """ScrapyUI統合管理クラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.nodejs_dir = self.project_root / "nodejs-service"
        
    def install_dependencies(self):
        """依存関係をインストール"""
        print("📦 Installing dependencies...")
        
        # Python依存関係
        print("🐍 Installing Python dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", 
            str(self.backend_dir / "requirements.txt")
        ], cwd=str(self.backend_dir))
        
        # 追加の監視用依存関係
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "psutil", "requests", "watchdog"
        ])
        
        # フロントエンド依存関係
        if self.frontend_dir.exists():
            print("🎨 Installing frontend dependencies...")
            subprocess.run(["npm", "install"], cwd=str(self.frontend_dir))
        
        # Node.js依存関係
        if self.nodejs_dir.exists():
            print("🟢 Installing Node.js dependencies...")
            subprocess.run(["npm", "install"], cwd=str(self.nodejs_dir))
        
        print("✅ Dependencies installed successfully")
    
    def setup_system_service(self):
        """システムサービスとして設定"""
        print("⚙️ Setting up system service...")
        
        service_file = self.backend_dir / "scrapyui.service"
        if service_file.exists():
            # systemdサービスファイルをコピー
            subprocess.run([
                "sudo", "cp", str(service_file), "/etc/systemd/system/"
            ])
            
            # サービスを有効化
            subprocess.run(["sudo", "systemctl", "daemon-reload"])
            subprocess.run(["sudo", "systemctl", "enable", "scrapyui"])
            
            print("✅ System service configured")
        else:
            print("⚠️ Service file not found")
    
    def start_services(self, mode="development"):
        """サービスを起動"""
        print(f"🚀 Starting services in {mode} mode...")
        
        if mode == "production":
            # プロダクションモード：systemdサービスを使用
            subprocess.run(["sudo", "systemctl", "start", "scrapyui"])
            print("✅ Production services started")
        else:
            # 開発モード：直接起動
            if (self.project_root / "start_servers_stable.sh").exists():
                subprocess.run(["./start_servers_stable.sh"], cwd=str(self.project_root))
            else:
                # フォールバック：個別起動
                self._start_development_services()
    
    def _start_development_services(self):
        """開発用サービスを個別起動"""
        print("🔧 Starting development services...")
        
        # バックエンド
        subprocess.Popen([
            sys.executable, "uvicorn_config.py"
        ], cwd=str(self.backend_dir))
        
        # Celery
        subprocess.Popen([
            sys.executable, "-m", "celery", "-A", "app.celery_app", "worker",
            "--loglevel=info", "-Q", "scrapy,maintenance,monitoring",
            "--concurrency=4", "--pool=prefork"
        ], cwd=str(self.backend_dir))
        
        print("✅ Development services started")
    
    def stop_services(self, mode="development"):
        """サービスを停止"""
        print("🛑 Stopping services...")
        
        if mode == "production":
            subprocess.run(["sudo", "systemctl", "stop", "scrapyui"])
        else:
            if (self.project_root / "stop_servers.sh").exists():
                subprocess.run(["./stop_servers.sh"], cwd=str(self.project_root))
            else:
                # フォールバック：プロセス終了
                subprocess.run(["pkill", "-f", "uvicorn.*app.main"], check=False)
                subprocess.run(["pkill", "-f", "celery.*worker"], check=False)
        
        print("✅ Services stopped")
    
    def status(self):
        """サービス状態を確認"""
        print("🔍 Checking service status...")
        
        # サーバー管理スクリプトを使用
        if (self.backend_dir / "server_manager.py").exists():
            subprocess.run([
                sys.executable, "server_manager.py", "status"
            ], cwd=str(self.backend_dir))
        
        # システムサービス状態
        result = subprocess.run(
            ["systemctl", "is-active", "scrapyui"], 
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"System service: ✅ {result.stdout.strip()}")
        else:
            print("System service: ❌ inactive")
    
    def monitor(self):
        """監視モードを開始"""
        print("🔍 Starting monitoring mode...")
        
        # Watchdogを起動
        if (self.backend_dir / "watchdog.py").exists():
            subprocess.run([
                sys.executable, "watchdog.py", "monitor"
            ], cwd=str(self.backend_dir))
        else:
            print("⚠️ Watchdog not found, using basic monitoring...")
            self._basic_monitor()
    
    def _basic_monitor(self):
        """基本的な監視"""
        import requests
        
        while True:
            try:
                # ヘルスチェック
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {datetime.now().strftime('%H:%M:%S')} - Services healthy")
                else:
                    print(f"⚠️ {datetime.now().strftime('%H:%M:%S')} - Health check failed")
                
                time.sleep(30)
                
            except KeyboardInterrupt:
                print("🛑 Monitoring stopped")
                break
            except Exception as e:
                print(f"❌ {datetime.now().strftime('%H:%M:%S')} - Error: {str(e)}")
                time.sleep(10)
    
    def recovery(self):
        """自動復旧を実行"""
        print("🔧 Running auto recovery...")
        
        if (self.backend_dir / "auto_recovery.py").exists():
            result = subprocess.run([
                sys.executable, "auto_recovery.py", "--once"
            ], cwd=str(self.backend_dir), capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Auto recovery completed")
                if result.stdout:
                    try:
                        recovery_data = json.loads(result.stdout)
                        print(f"Issues found: {recovery_data.get('issues_found', 0)}")
                        print(f"Recoveries successful: {recovery_data.get('recoveries_successful', 0)}")
                    except:
                        print(result.stdout)
            else:
                print("❌ Auto recovery failed")
                print(result.stderr)
        else:
            print("⚠️ Auto recovery script not found")
    
    def logs(self, service="all", lines=50):
        """ログを表示"""
        print(f"📝 Showing logs for {service} (last {lines} lines)...")
        
        log_files = {
            "backend": self.backend_dir / "logs" / "scrapyui.log",
            "celery": self.backend_dir / "logs" / "celery.log",
            "watchdog": self.backend_dir / "logs" / "watchdog.log",
            "recovery": self.backend_dir / "logs" / "auto_recovery.log",
            "server_manager": self.backend_dir / "logs" / "server_manager.log"
        }
        
        if service == "all":
            for name, log_file in log_files.items():
                if log_file.exists():
                    print(f"\n=== {name.upper()} ===")
                    subprocess.run(["tail", "-n", str(lines), str(log_file)])
        elif service in log_files:
            log_file = log_files[service]
            if log_file.exists():
                subprocess.run(["tail", "-n", str(lines), str(log_file)])
            else:
                print(f"⚠️ Log file not found: {log_file}")
        else:
            print(f"❌ Unknown service: {service}")
            print(f"Available services: {', '.join(log_files.keys())}, all")
    
    def cleanup(self):
        """クリーンアップを実行"""
        print("🧹 Running cleanup...")
        
        # 古いログファイルを削除
        log_dir = self.backend_dir / "logs"
        if log_dir.exists():
            subprocess.run([
                "find", str(log_dir), "-name", "*.log.*", "-mtime", "+7", "-delete"
            ], check=False)
        
        # 古い結果ファイルを削除
        scrapy_projects = self.project_root / "scrapy_projects"
        if scrapy_projects.exists():
            subprocess.run([
                "find", str(scrapy_projects), "-name", "results_*.json", "-mtime", "+30", "-delete"
            ], check=False)
        
        # 一時ファイルを削除
        subprocess.run([
            "find", "/tmp", "-name", "scrapy*", "-mtime", "+1", "-delete"
        ], check=False)
        
        print("✅ Cleanup completed")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="ScrapyUI Integrated Manager")
    parser.add_argument("action", choices=[
        "install", "setup", "start", "stop", "restart", "status", 
        "monitor", "recovery", "logs", "cleanup"
    ], help="Action to perform")
    
    parser.add_argument("--mode", choices=["development", "production"], 
                       default="development", help="Deployment mode")
    parser.add_argument("--service", default="all", 
                       help="Service name for logs command")
    parser.add_argument("--lines", type=int, default=50, 
                       help="Number of log lines to show")
    
    args = parser.parse_args()
    
    manager = ScrapyUIManager()
    
    if args.action == "install":
        manager.install_dependencies()
    elif args.action == "setup":
        manager.setup_system_service()
    elif args.action == "start":
        manager.start_services(args.mode)
    elif args.action == "stop":
        manager.stop_services(args.mode)
    elif args.action == "restart":
        manager.stop_services(args.mode)
        time.sleep(2)
        manager.start_services(args.mode)
    elif args.action == "status":
        manager.status()
    elif args.action == "monitor":
        manager.monitor()
    elif args.action == "recovery":
        manager.recovery()
    elif args.action == "logs":
        manager.logs(args.service, args.lines)
    elif args.action == "cleanup":
        manager.cleanup()


if __name__ == "__main__":
    main()
