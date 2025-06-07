"""
プロセスクリーンアップサービス

重複プロセスとゾンビプロセスの自動クリーンアップを提供します。
"""

import os
import signal
import subprocess
import psutil
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ProcessCleanupService:
    """プロセスクリーンアップサービス"""
    
    def __init__(self):
        self.cleanup_patterns = [
            "celery.*worker",
            "celery.*beat", 
            "celery.*flower",
            "uvicorn.*app.main:app",
            "next.*dev",
            "node.*app.js"
        ]
        
        self.ports_to_check = [8000, 4000, 3001, 5556]
        
    def cleanup_zombie_processes(self) -> Dict[str, int]:
        """ゾンビプロセスをクリーンアップ"""
        logger.info("🧹 Checking for zombie processes...")
        
        zombies_found = 0
        zombies_cleaned = 0
        
        try:
            for proc in psutil.process_iter(['pid', 'ppid', 'status', 'name']):
                try:
                    if proc.info['status'] == psutil.STATUS_ZOMBIE:
                        zombies_found += 1
                        parent_pid = proc.info['ppid']
                        
                        logger.info(f"Found zombie process PID {proc.info['pid']}, parent PID {parent_pid}")
                        
                        # 親プロセスにSIGCHLDを送信
                        if parent_pid and parent_pid != 1:
                            try:
                                os.kill(parent_pid, signal.SIGCHLD)
                                zombies_cleaned += 1
                                logger.info(f"Sent SIGCHLD to parent process {parent_pid}")
                            except (OSError, ProcessLookupError):
                                logger.warning(f"Could not send SIGCHLD to parent process {parent_pid}")
                                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            logger.error(f"Error during zombie cleanup: {e}")
            
        logger.info(f"✅ Zombie cleanup completed: {zombies_found} found, {zombies_cleaned} cleaned")
        return {"found": zombies_found, "cleaned": zombies_cleaned}
    
    def cleanup_duplicate_processes(self) -> Dict[str, int]:
        """重複プロセスをクリーンアップ"""
        logger.info("🧹 Checking for duplicate processes...")
        
        cleanup_stats = {}
        
        for pattern in self.cleanup_patterns:
            try:
                # プロセスを検索
                result = subprocess.run(
                    ["pgrep", "-f", pattern],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    pids = [int(pid.strip()) for pid in result.stdout.strip().split('\n') if pid.strip()]
                    
                    # 期待される数を超えている場合はクリーンアップ
                    expected_count = self._get_expected_process_count(pattern)
                    if len(pids) > expected_count:
                        excess_count = len(pids) - expected_count
                        logger.warning(f"Found {len(pids)} {pattern} processes (expected: {expected_count})")
                        
                        # 古いプロセスから終了
                        pids_to_kill = pids[:-expected_count] if expected_count > 0 else pids
                        killed_count = self._safe_kill_processes(pids_to_kill, pattern)
                        
                        cleanup_stats[pattern] = {
                            "found": len(pids),
                            "killed": killed_count,
                            "expected": expected_count
                        }
                    else:
                        cleanup_stats[pattern] = {
                            "found": len(pids),
                            "killed": 0,
                            "expected": expected_count
                        }
                        
            except Exception as e:
                logger.error(f"Error checking pattern {pattern}: {e}")
                
        logger.info("✅ Duplicate process cleanup completed")
        return cleanup_stats
    
    def cleanup_port_conflicts(self) -> Dict[int, bool]:
        """ポート競合を解決"""
        logger.info("🧹 Checking for port conflicts...")
        
        cleanup_stats = {}
        
        for port in self.ports_to_check:
            try:
                # ポートを使用しているプロセスを検索
                connections = psutil.net_connections(kind='inet')
                port_users = [
                    conn for conn in connections 
                    if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN
                ]
                
                if port_users:
                    for conn in port_users:
                        try:
                            proc = psutil.Process(conn.pid)
                            proc_name = proc.name()
                            
                            # ScrapyUI関連プロセスかチェック
                            if self._is_scrapyui_process(proc_name, proc.cmdline()):
                                logger.info(f"Stopping ScrapyUI process on port {port}: {proc_name} (PID: {conn.pid})")
                                proc.terminate()
                                
                                # 3秒待って強制終了
                                try:
                                    proc.wait(timeout=3)
                                except psutil.TimeoutExpired:
                                    proc.kill()
                                    
                                cleanup_stats[port] = True
                            else:
                                logger.info(f"Skipping non-ScrapyUI process on port {port}: {proc_name}")
                                cleanup_stats[port] = False
                                
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            cleanup_stats[port] = False
                else:
                    cleanup_stats[port] = True  # ポートは空いている
                    
            except Exception as e:
                logger.error(f"Error checking port {port}: {e}")
                cleanup_stats[port] = False
                
        logger.info("✅ Port conflict cleanup completed")
        return cleanup_stats
    
    def cleanup_old_files(self) -> Dict[str, int]:
        """古いファイルをクリーンアップ"""
        logger.info("🧹 Cleaning up old files...")
        
        cleanup_stats = {
            "log_files": 0,
            "result_files": 0,
            "temp_files": 0,
            "pid_files": 0
        }
        
        try:
            current_time = datetime.now()
            
            # 7日以上古いログファイル
            for root, dirs, files in os.walk("."):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        age = current_time - file_time
                        
                        if file.endswith('.log') and age > timedelta(days=7):
                            os.remove(file_path)
                            cleanup_stats["log_files"] += 1
                        elif file.startswith('results_') and file.endswith('.jsonl') and age > timedelta(days=1):
                            os.remove(file_path)
                            cleanup_stats["result_files"] += 1
                        elif file.endswith('.pid'):
                            os.remove(file_path)
                            cleanup_stats["pid_files"] += 1
                            
                    except (OSError, ValueError):
                        continue
                        
        except Exception as e:
            logger.error(f"Error during file cleanup: {e}")
            
        logger.info(f"✅ File cleanup completed: {cleanup_stats}")
        return cleanup_stats
    
    def _get_expected_process_count(self, pattern: str) -> int:
        """パターンに応じた期待プロセス数を返す"""
        if "worker" in pattern:
            return 1  # Celeryワーカーは1つ
        elif "beat" in pattern:
            return 1  # Celery Beatは1つ
        elif "flower" in pattern:
            return 1  # Flowerは1つ
        elif "uvicorn" in pattern:
            return 1  # バックエンドは1つ
        elif "next" in pattern:
            return 1  # フロントエンドは1つ
        elif "node" in pattern:
            return 1  # Node.jsサービスは1つ
        else:
            return 0  # その他は0
    
    def _safe_kill_processes(self, pids: List[int], pattern: str) -> int:
        """プロセスを安全に終了"""
        killed_count = 0
        
        for pid in pids:
            try:
                proc = psutil.Process(pid)
                logger.info(f"Terminating {pattern} process PID {pid}")
                
                # まずTERMシグナル
                proc.terminate()
                
                # 3秒待機
                try:
                    proc.wait(timeout=3)
                    killed_count += 1
                except psutil.TimeoutExpired:
                    # 強制終了
                    logger.warning(f"Force killing {pattern} process PID {pid}")
                    proc.kill()
                    killed_count += 1
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            except Exception as e:
                logger.error(f"Error killing process {pid}: {e}")
                
        return killed_count
    
    def _is_scrapyui_process(self, proc_name: str, cmdline: List[str]) -> bool:
        """ScrapyUI関連プロセスかどうかを判定"""
        scrapyui_indicators = [
            "python", "node", "uvicorn", "celery", "flower", "next"
        ]
        
        cmdline_str = " ".join(cmdline).lower()
        scrapyui_keywords = [
            "scrapyui", "app.main", "app.celery_app", "scrapy", "flower"
        ]
        
        return (
            any(indicator in proc_name.lower() for indicator in scrapyui_indicators) and
            any(keyword in cmdline_str for keyword in scrapyui_keywords)
        )
    
    def full_cleanup(self) -> Dict[str, any]:
        """完全なクリーンアップを実行"""
        logger.info("🧹 Starting full process cleanup...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "zombies": self.cleanup_zombie_processes(),
            "duplicates": self.cleanup_duplicate_processes(),
            "ports": self.cleanup_port_conflicts(),
            "files": self.cleanup_old_files()
        }
        
        logger.info("✅ Full process cleanup completed")
        return results

# グローバルインスタンス
process_cleanup_service = ProcessCleanupService()
