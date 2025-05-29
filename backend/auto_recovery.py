#!/usr/bin/env python3
"""
ScrapyUI Auto Recovery - 自動復旧システム
システム異常を検知し、自動的に復旧処理を実行
"""

import os
import sys
import time
import subprocess
import psutil
import logging
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_recovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoRecovery:
    """自動復旧システム"""
    
    def __init__(self):
        self.backend_dir = Path(__file__).parent
        self.project_root = self.backend_dir.parent
        
        # 復旧シナリオ
        self.recovery_scenarios = {
            'backend_down': {
                'description': 'バックエンドサーバー停止',
                'check': self.check_backend_down,
                'recovery': self.recover_backend,
                'priority': 1
            },
            'celery_down': {
                'description': 'Celeryワーカー停止',
                'check': self.check_celery_down,
                'recovery': self.recover_celery,
                'priority': 2
            },
            'database_locked': {
                'description': 'データベースロック',
                'check': self.check_database_locked,
                'recovery': self.recover_database,
                'priority': 3
            },
            'disk_full': {
                'description': 'ディスク容量不足',
                'check': self.check_disk_full,
                'recovery': self.recover_disk_space,
                'priority': 4
            },
            'memory_leak': {
                'description': 'メモリリーク',
                'check': self.check_memory_leak,
                'recovery': self.recover_memory,
                'priority': 5
            },
            'zombie_processes': {
                'description': 'ゾンビプロセス',
                'check': self.check_zombie_processes,
                'recovery': self.recover_zombies,
                'priority': 6
            }
        }
        
        self.recovery_stats = {
            'total_recoveries': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'last_recovery': None,
            'recovery_history': []
        }
    
    def check_backend_down(self) -> bool:
        """バックエンドサーバー停止チェック"""
        try:
            response = requests.get('http://localhost:8000/health', timeout=5)
            return response.status_code != 200
        except:
            return True
    
    def check_celery_down(self) -> bool:
        """Celeryワーカー停止チェック"""
        try:
            # Celeryプロセスの存在確認
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'celery' in proc.info['name'] or any('celery' in arg for arg in proc.info['cmdline'] or []):
                    return False
            return True
        except:
            return True
    
    def check_database_locked(self) -> bool:
        """データベースロックチェック"""
        try:
            db_path = self.backend_dir / 'database' / 'scrapy_ui.db'
            if not db_path.exists():
                return False
            
            conn = sqlite3.connect(str(db_path), timeout=1)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            return False
        except sqlite3.OperationalError:
            return True
        except:
            return False
    
    def check_disk_full(self) -> bool:
        """ディスク容量不足チェック"""
        try:
            usage = psutil.disk_usage('/')
            free_percent = (usage.free / usage.total) * 100
            return free_percent < 5  # 5%未満で警告
        except:
            return False
    
    def check_memory_leak(self) -> bool:
        """メモリリークチェック"""
        try:
            memory = psutil.virtual_memory()
            return memory.percent > 90  # 90%以上で警告
        except:
            return False
    
    def check_zombie_processes(self) -> bool:
        """ゾンビプロセスチェック"""
        try:
            zombie_count = 0
            for proc in psutil.process_iter(['pid', 'status']):
                if proc.info['status'] == psutil.STATUS_ZOMBIE:
                    zombie_count += 1
            return zombie_count > 5  # 5個以上で警告
        except:
            return False
    
    def recover_backend(self) -> bool:
        """バックエンドサーバー復旧"""
        try:
            logger.info("🔧 Recovering backend server...")
            
            # 既存プロセスを停止
            subprocess.run(['pkill', '-f', 'uvicorn.*app.main'], check=False)
            time.sleep(2)
            
            # 新しいプロセスを起動
            subprocess.Popen(
                ['python', 'uvicorn_config.py'],
                cwd=str(self.backend_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # 起動確認
            for i in range(30):
                if not self.check_backend_down():
                    logger.info("✅ Backend server recovered")
                    return True
                time.sleep(1)
            
            logger.error("❌ Failed to recover backend server")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error recovering backend: {str(e)}")
            return False
    
    def recover_celery(self) -> bool:
        """Celeryワーカー復旧"""
        try:
            logger.info("🔧 Recovering Celery worker...")
            
            # 既存プロセスを停止
            subprocess.run(['pkill', '-f', 'celery.*worker'], check=False)
            time.sleep(2)
            
            # 新しいプロセスを起動
            subprocess.Popen([
                'python', '-m', 'celery', '-A', 'app.celery_app', 'worker',
                '--loglevel=info', '-Q', 'scrapy,maintenance,monitoring',
                '--concurrency=4', '--pool=prefork'
            ], cwd=str(self.backend_dir),
               stdout=subprocess.DEVNULL,
               stderr=subprocess.DEVNULL)
            
            # 起動確認
            time.sleep(5)
            if not self.check_celery_down():
                logger.info("✅ Celery worker recovered")
                return True
            else:
                logger.error("❌ Failed to recover Celery worker")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error recovering Celery: {str(e)}")
            return False
    
    def recover_database(self) -> bool:
        """データベース復旧"""
        try:
            logger.info("🔧 Recovering database...")
            
            # データベースファイルのバックアップ
            db_path = self.backend_dir / 'database' / 'scrapy_ui.db'
            backup_path = self.backend_dir / 'database' / f'scrapy_ui_backup_{int(time.time())}.db'
            
            if db_path.exists():
                subprocess.run(['cp', str(db_path), str(backup_path)], check=False)
            
            # データベース接続を強制終了
            subprocess.run(['pkill', '-f', 'python.*app.main'], check=False)
            time.sleep(2)
            
            # データベースファイルの整合性チェック
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                conn.close()
                
                if result[0] != 'ok':
                    logger.warning("⚠️ Database integrity issues detected")
                    
            except Exception as e:
                logger.error(f"Database integrity check failed: {str(e)}")
            
            logger.info("✅ Database recovery completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error recovering database: {str(e)}")
            return False
    
    def recover_disk_space(self) -> bool:
        """ディスク容量復旧"""
        try:
            logger.info("🔧 Recovering disk space...")
            
            # ログファイルのクリーンアップ
            log_dir = self.backend_dir / 'logs'
            if log_dir.exists():
                for log_file in log_dir.glob('*.log.*'):
                    if log_file.stat().st_mtime < time.time() - 86400 * 7:  # 7日以上古い
                        log_file.unlink()
            
            # 一時ファイルのクリーンアップ
            temp_dirs = ['/tmp', '/var/tmp']
            for temp_dir in temp_dirs:
                subprocess.run(['find', temp_dir, '-name', 'scrapy*', '-mtime', '+1', '-delete'], 
                             check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 結果ファイルのクリーンアップ（30日以上古い）
            scrapy_projects = self.project_root / 'scrapy_projects'
            if scrapy_projects.exists():
                subprocess.run(['find', str(scrapy_projects), '-name', 'results_*.json', '-mtime', '+30', '-delete'],
                             check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            logger.info("✅ Disk space recovery completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error recovering disk space: {str(e)}")
            return False
    
    def recover_memory(self) -> bool:
        """メモリ復旧"""
        try:
            logger.info("🔧 Recovering memory...")
            
            # メモリ使用量の多いプロセスを特定
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cmdline']):
                if proc.info['memory_percent'] > 5:  # 5%以上のメモリ使用
                    processes.append(proc.info)
            
            # ScrapyUIプロセスを再起動
            subprocess.run(['pkill', '-f', 'python.*app.main'], check=False)
            subprocess.run(['pkill', '-f', 'celery.*worker'], check=False)
            time.sleep(3)
            
            # システムキャッシュをクリア
            subprocess.run(['sync'], check=False)
            subprocess.run(['echo', '3', '>', '/proc/sys/vm/drop_caches'], 
                         shell=True, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            logger.info("✅ Memory recovery completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error recovering memory: {str(e)}")
            return False
    
    def recover_zombies(self) -> bool:
        """ゾンビプロセス復旧"""
        try:
            logger.info("🔧 Recovering zombie processes...")
            
            # ゾンビプロセスの親プロセスを特定して再起動
            zombie_parents = set()
            for proc in psutil.process_iter(['pid', 'ppid', 'status']):
                if proc.info['status'] == psutil.STATUS_ZOMBIE:
                    zombie_parents.add(proc.info['ppid'])
            
            # 親プロセスに SIGCHLD を送信
            for ppid in zombie_parents:
                try:
                    os.kill(ppid, signal.SIGCHLD)
                except:
                    pass
            
            time.sleep(2)
            
            # まだゾンビが残っている場合は強制終了
            remaining_zombies = 0
            for proc in psutil.process_iter(['pid', 'status']):
                if proc.info['status'] == psutil.STATUS_ZOMBIE:
                    remaining_zombies += 1
                    try:
                        os.kill(proc.info['pid'], signal.SIGKILL)
                    except:
                        pass
            
            logger.info(f"✅ Zombie process recovery completed (cleaned {len(zombie_parents)} parents)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error recovering zombies: {str(e)}")
            return False
    
    def run_recovery(self) -> Dict:
        """復旧処理を実行"""
        logger.info("🔍 Starting auto recovery check...")
        
        recovery_results = {
            'timestamp': datetime.now().isoformat(),
            'scenarios_checked': 0,
            'issues_found': 0,
            'recoveries_attempted': 0,
            'recoveries_successful': 0,
            'details': []
        }
        
        # 優先度順にチェック
        scenarios = sorted(self.recovery_scenarios.items(), key=lambda x: x[1]['priority'])
        
        for name, scenario in scenarios:
            recovery_results['scenarios_checked'] += 1
            
            try:
                if scenario['check']():
                    recovery_results['issues_found'] += 1
                    logger.warning(f"⚠️ Issue detected: {scenario['description']}")
                    
                    recovery_results['recoveries_attempted'] += 1
                    self.recovery_stats['total_recoveries'] += 1
                    
                    if scenario['recovery']():
                        recovery_results['recoveries_successful'] += 1
                        self.recovery_stats['successful_recoveries'] += 1
                        recovery_results['details'].append({
                            'scenario': name,
                            'description': scenario['description'],
                            'status': 'success'
                        })
                    else:
                        self.recovery_stats['failed_recoveries'] += 1
                        recovery_results['details'].append({
                            'scenario': name,
                            'description': scenario['description'],
                            'status': 'failed'
                        })
                        
            except Exception as e:
                logger.error(f"❌ Error checking {name}: {str(e)}")
                recovery_results['details'].append({
                    'scenario': name,
                    'description': scenario['description'],
                    'status': 'error',
                    'error': str(e)
                })
        
        self.recovery_stats['last_recovery'] = datetime.now()
        self.recovery_stats['recovery_history'].append(recovery_results)
        
        # 履歴は最新100件のみ保持
        if len(self.recovery_stats['recovery_history']) > 100:
            self.recovery_stats['recovery_history'] = self.recovery_stats['recovery_history'][-100:]
        
        logger.info(f"✅ Recovery check completed: {recovery_results['recoveries_successful']}/{recovery_results['recoveries_attempted']} successful")
        
        return recovery_results


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ScrapyUI Auto Recovery")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    
    args = parser.parse_args()
    
    recovery = AutoRecovery()
    
    if args.once:
        result = recovery.run_recovery()
        print(json.dumps(result, indent=2))
    else:
        logger.info(f"🔄 Starting auto recovery daemon (interval: {args.interval}s)")
        
        while True:
            try:
                recovery.run_recovery()
                time.sleep(args.interval)
            except KeyboardInterrupt:
                logger.info("🛑 Auto recovery stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in recovery loop: {str(e)}")
                time.sleep(30)


if __name__ == "__main__":
    main()
