#!/usr/bin/env python3
"""
Celeryヘルスチェックスクリプト
Celeryワーカーとビートプロセスの健全性を監視し、問題を検出・修復します。
"""

import subprocess
import time
import sys
import os
from datetime import datetime

class CeleryHealthChecker:
    def __init__(self):
        self.max_workers = 2
        self.max_beats = 1
        
    def log(self, message):
        """ログメッセージを出力"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def get_celery_processes(self, process_type):
        """Celeryプロセスを取得"""
        try:
            if process_type == "worker":
                cmd = ['pgrep', '-f', 'celery.*worker']
            elif process_type == "beat":
                cmd = ['pgrep', '-f', 'celery.*beat']
            else:
                return []
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            pids = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return [pid for pid in pids if pid.isdigit()]
        except Exception as e:
            self.log(f"プロセス取得エラー ({process_type}): {e}")
            return []
    
    def kill_process(self, pid):
        """プロセスを安全に停止"""
        try:
            # まずTERMシグナルで停止を試行
            subprocess.run(['kill', '-TERM', pid], check=False)
            time.sleep(2)
            
            # プロセスがまだ存在するかチェック
            result = subprocess.run(['kill', '-0', pid], capture_output=True)
            if result.returncode == 0:
                # まだ存在する場合はKILLシグナル
                subprocess.run(['kill', '-KILL', pid], check=False)
                self.log(f"プロセス {pid} を強制終了しました")
            else:
                self.log(f"プロセス {pid} を正常に停止しました")
                
        except Exception as e:
            self.log(f"プロセス停止エラー ({pid}): {e}")
    
    def cleanup_duplicate_processes(self):
        """重複プロセスをクリーンアップ"""
        # ワーカープロセスのクリーンアップ
        worker_pids = self.get_celery_processes("worker")
        if len(worker_pids) > self.max_workers:
            self.log(f"⚠️ 重複Celeryワーカーを検出: {len(worker_pids)}個 (最大: {self.max_workers})")
            # 古いプロセスから停止
            for pid in worker_pids[self.max_workers:]:
                self.log(f"重複ワーカープロセス {pid} を停止中...")
                self.kill_process(pid)
        
        # Beatプロセスのクリーンアップ
        beat_pids = self.get_celery_processes("beat")
        if len(beat_pids) > self.max_beats:
            self.log(f"⚠️ 重複Celery Beatを検出: {len(beat_pids)}個 (最大: {self.max_beats})")
            # 古いプロセスから停止
            for pid in beat_pids[self.max_beats:]:
                self.log(f"重複Beatプロセス {pid} を停止中...")
                self.kill_process(pid)
    
    def check_redis_connection(self):
        """Redis接続をチェック"""
        try:
            result = subprocess.run(['redis-cli', 'ping'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'PONG' in result.stdout:
                return True
            else:
                self.log("❌ Redis接続失敗")
                return False
        except Exception as e:
            self.log(f"❌ Redis接続チェックエラー: {e}")
            return False
    
    def check_celery_status(self):
        """Celeryの状態をチェック"""
        try:
            # Celery inspectコマンドでワーカーの状態をチェック
            result = subprocess.run([
                'celery', '-A', 'app.celery_app', 'inspect', 'active'
            ], capture_output=True, text=True, timeout=10, cwd='/home/igtmtakan/workplace/python/scrapyUI/backend')
            
            if result.returncode == 0:
                self.log("✅ Celeryワーカーは応答しています")
                return True
            else:
                self.log(f"❌ Celeryワーカーが応答しません: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            self.log("❌ Celeryワーカーの応答がタイムアウトしました")
            return False
        except Exception as e:
            self.log(f"❌ Celeryステータスチェックエラー: {e}")
            return False
    
    def run_health_check(self):
        """ヘルスチェックを実行"""
        self.log("🔍 Celeryヘルスチェックを開始します...")
        
        # Redis接続チェック
        if not self.check_redis_connection():
            self.log("❌ Redisが利用できません。Redisを起動してください。")
            return False
        
        # 重複プロセスのクリーンアップ
        self.cleanup_duplicate_processes()
        
        # プロセス数の確認
        worker_pids = self.get_celery_processes("worker")
        beat_pids = self.get_celery_processes("beat")
        
        self.log(f"📊 現在のプロセス数:")
        self.log(f"   Celeryワーカー: {len(worker_pids)}個")
        self.log(f"   Celery Beat: {len(beat_pids)}個")
        
        # Celeryの応答性チェック
        celery_responsive = self.check_celery_status()
        
        # 結果の評価
        if len(worker_pids) == 0:
            self.log("❌ Celeryワーカーが起動していません")
            return False
        elif len(beat_pids) == 0:
            self.log("⚠️ Celery Beatが起動していません")
        
        if celery_responsive:
            self.log("✅ Celeryヘルスチェック完了: 正常")
            return True
        else:
            self.log("❌ Celeryヘルスチェック完了: 異常")
            return False

def main():
    """メイン関数"""
    checker = CeleryHealthChecker()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        # クリーンアップのみ実行
        checker.log("🧹 Celeryプロセスクリーンアップを実行します...")
        checker.cleanup_duplicate_processes()
    else:
        # 完全なヘルスチェック
        success = checker.run_health_check()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
