#!/usr/bin/env python3
"""
Celeryワーカー監視・自動復旧スクリプト
"""

import sys
import os
import time
import signal
import subprocess
import psutil
from pathlib import Path
from datetime import datetime, timedelta

# プロジェクトのルートディレクトリをPythonパスに追加
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

class CeleryMonitor:
    def __init__(self):
        self.backend_dir = backend_dir
        self.worker_process = None
        self.beat_process = None
        self.restart_count = 0
        self.max_restarts = 10
        self.restart_window = timedelta(hours=1)
        self.restart_times = []
        self.running = True
        
    def log(self, message):
        """ログメッセージを出力"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def is_redis_available(self):
        """Redisが利用可能かチェック"""
        try:
            result = subprocess.run(['redis-cli', 'ping'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0 and 'PONG' in result.stdout
        except Exception:
            return False
    
    def start_worker(self):
        """Celeryワーカーを起動"""
        if self.worker_process and self.worker_process.poll() is None:
            self.log("Celeryワーカーは既に実行中です")
            return True
            
        try:
            self.log("Celeryワーカーを起動中...")
            
            # 改善されたワーカー設定
            cmd = [
                sys.executable, "-m", "celery", "-A", "app.celery_app", "worker",
                "--loglevel=info",
                "--concurrency=1",  # 同時実行数を1に削減
                "--queues=scrapy,maintenance,monitoring",
                "--pool=prefork",
                "--optimization=fair",
                "--max-tasks-per-child=50",  # タスク数制限を50に削減
                "--max-memory-per-child=300000",  # 300MB制限（メモリ制限強化）
                "--time-limit=3600",  # 60分タイムアウト
                "--soft-time-limit=3300",  # 55分ソフトタイムアウト
                "--without-gossip",
                "--without-mingle",
                "--without-heartbeat",
                "--prefetch-multiplier=1",
            ]
            
            self.worker_process = subprocess.Popen(
                cmd, 
                cwd=self.backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.log(f"Celeryワーカーを起動しました (PID: {self.worker_process.pid})")
            return True
            
        except Exception as e:
            self.log(f"Celeryワーカー起動エラー: {e}")
            return False
    
    def start_beat(self):
        """Celery Beatを起動"""
        if self.beat_process and self.beat_process.poll() is None:
            self.log("Celery Beatは既に実行中です")
            return True
            
        try:
            self.log("Celery Beatを起動中...")
            
            cmd = [
                sys.executable, "-m", "celery", "-A", "app.celery_app", "beat",
                "--scheduler", "app.scheduler:DatabaseScheduler",
                "--loglevel=info"
            ]
            
            self.beat_process = subprocess.Popen(
                cmd,
                cwd=self.backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.log(f"Celery Beatを起動しました (PID: {self.beat_process.pid})")
            return True
            
        except Exception as e:
            self.log(f"Celery Beat起動エラー: {e}")
            return False
    
    def check_worker_health(self):
        """ワーカーの健全性をチェック"""
        if not self.worker_process:
            return False
            
        # プロセスが終了していないかチェック
        if self.worker_process.poll() is not None:
            self.log(f"Celeryワーカーが終了しました (終了コード: {self.worker_process.returncode})")
            return False
        
        try:
            # プロセスのメモリ使用量をチェック
            process = psutil.Process(self.worker_process.pid)
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > 250:  # 250MB制限（少し緩和）
                self.log(f"Celeryワーカーのメモリ使用量が制限を超えました: {memory_mb:.1f}MB")
                return False
                
            # CPU使用率をチェック
            cpu_percent = process.cpu_percent()
            if cpu_percent > 90:  # 90%制限
                self.log(f"CeleryワーカーのCPU使用率が高すぎます: {cpu_percent:.1f}%")
                
        except psutil.NoSuchProcess:
            self.log("Celeryワーカープロセスが見つかりません")
            return False
        except Exception as e:
            self.log(f"ワーカーヘルスチェックエラー: {e}")

        # 重複プロセスをチェック
        try:
            import subprocess
            result = subprocess.run(['pgrep', '-f', 'celery.*worker'],
                                  capture_output=True, text=True)
            worker_pids = result.stdout.strip().split('\n') if result.stdout.strip() else []

            if len(worker_pids) > 2:  # メインプロセス + 子プロセス
                self.log(f"⚠️ 重複Celeryワーカーを検出: {len(worker_pids)}個のプロセス")
                # 重複プロセスを停止（自分のプロセス以外）
                for pid in worker_pids:
                    try:
                        if int(pid) != self.worker_process.pid:
                            subprocess.run(['kill', '-TERM', pid], check=False)
                            self.log(f"重複ワーカープロセス {pid} を停止しました")
                    except:
                        pass
        except Exception as e:
            self.log(f"重複プロセスチェックエラー: {e}")

        return True
    
    def force_cleanup_workers(self):
        """強制的にすべてのCeleryワーカーをクリーンアップ"""
        try:
            # すべてのCeleryワーカープロセスを検索
            result = subprocess.run(['pgrep', '-f', 'celery.*worker'],
                                  capture_output=True, text=True)
            worker_pids = result.stdout.strip().split('\n') if result.stdout.strip() else []

            for pid in worker_pids:
                try:
                    if pid.strip():
                        subprocess.run(['kill', '-KILL', pid.strip()], check=False)
                        self.log(f"強制終了: ワーカープロセス {pid}")
                except:
                    pass

            # 少し待機
            time.sleep(2)

        except Exception as e:
            self.log(f"強制クリーンアップエラー: {e}")

    def restart_worker(self):
        """ワーカーを再起動"""
        # 再起動回数制限チェック
        now = datetime.now()
        self.restart_times = [t for t in self.restart_times if now - t < self.restart_window]

        if len(self.restart_times) >= self.max_restarts:
            self.log(f"再起動回数が制限に達しました ({self.max_restarts}回/時間)")
            return False

        self.log("Celeryワーカーを再起動中...")

        # 既存プロセスを停止
        if self.worker_process:
            try:
                self.worker_process.terminate()
                self.worker_process.wait(timeout=5)  # タイムアウトを短縮
            except subprocess.TimeoutExpired:
                self.log("通常終了がタイムアウトしました。強制終了します...")
                self.worker_process.kill()
                # 強制クリーンアップを実行
                self.force_cleanup_workers()
            except Exception as e:
                self.log(f"ワーカー停止エラー: {e}")
                # エラー時も強制クリーンアップを実行
                self.force_cleanup_workers()

        # 新しいワーカーを起動
        if self.start_worker():
            self.restart_times.append(now)
            self.restart_count += 1
            self.log(f"Celeryワーカーを再起動しました (再起動回数: {self.restart_count})")
            return True

        return False
    
    def signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        self.log(f"シグナル {signum} を受信しました。監視を停止します...")
        self.running = False
        
        # プロセスを停止
        if self.worker_process:
            try:
                self.worker_process.terminate()
                self.worker_process.wait(timeout=10)
            except:
                self.worker_process.kill()
                
        if self.beat_process:
            try:
                self.beat_process.terminate()
                self.beat_process.wait(timeout=10)
            except:
                self.beat_process.kill()
        
        sys.exit(0)
    
    def run(self):
        """監視ループを実行"""
        # シグナルハンドラーを設定
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.log("Celery監視を開始します...")
        
        # Redisの可用性をチェック
        if not self.is_redis_available():
            self.log("❌ Redisが利用できません。Redisを起動してください。")
            return
        
        # 初期起動
        self.start_worker()
        self.start_beat()
        
        # 監視ループ
        while self.running:
            try:
                # ワーカーの健全性をチェック
                if not self.check_worker_health():
                    if not self.restart_worker():
                        self.log("ワーカーの再起動に失敗しました。監視を停止します。")
                        break
                
                # Beat プロセスをチェック
                if self.beat_process and self.beat_process.poll() is not None:
                    self.log("Celery Beatが終了しました。再起動します...")
                    self.start_beat()

                # Beat重複プロセスをチェック
                try:
                    result = subprocess.run(['pgrep', '-f', 'celery.*beat'],
                                          capture_output=True, text=True)
                    beat_pids = result.stdout.strip().split('\n') if result.stdout.strip() else []

                    if len(beat_pids) > 1:  # 1つのBeatプロセスのみ許可
                        self.log(f"⚠️ 重複Celery Beatを検出: {len(beat_pids)}個のプロセス")
                        # 重複プロセスを停止（自分のプロセス以外）
                        for pid in beat_pids:
                            try:
                                if self.beat_process and int(pid) != self.beat_process.pid:
                                    subprocess.run(['kill', '-TERM', pid], check=False)
                                    self.log(f"重複Beatプロセス {pid} を停止しました")
                            except:
                                pass
                except Exception as e:
                    self.log(f"Beat重複プロセスチェックエラー: {e}")
                
                time.sleep(15)  # 15秒間隔でチェック（より頻繁な監視）
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log(f"監視ループエラー: {e}")
                time.sleep(10)
        
        self.log("Celery監視を終了しました")

if __name__ == "__main__":
    monitor = CeleryMonitor()
    monitor.run()
