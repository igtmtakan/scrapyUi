#!/usr/bin/env python3
"""
自動ファイルクリーンアップスケジューラー
定期的にJSONLファイルをクリーンアップし、システムの性能を維持
"""
import os
import sys
import time
import schedule
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import glob

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoFileCleanupScheduler:
    """自動ファイルクリーンアップスケジューラー"""
    
    def __init__(self):
        self.scrapyui_root = '/home/igtmtakan/workplace/python/scrapyUI'
        self.backend_path = os.path.join(self.scrapyui_root, 'backend')
        self.projects_path = os.path.join(self.scrapyui_root, 'scrapy_projects')
        self.tool_path = os.path.join(self.backend_path, 'jsonl_file_manager.py')
        
        # 設定（極めて積極的なクリーンアップ）
        self.max_file_lines = 500    # 最大行数（極めて小さく）
        self.keep_sessions = 1       # 保持するセッション数（最新のみ）
        self.max_file_age_days = 30  # ファイルの最大保存日数
        self.cleanup_interval_hours = 1  # クリーンアップ間隔（1時間毎）
        
        logger.info(f"🤖 Auto File Cleanup Scheduler initialized")
        logger.info(f"   📁 Projects path: {self.projects_path}")
        logger.info(f"   🔧 Tool path: {self.tool_path}")
        logger.info(f"   📊 Max lines: {self.max_file_lines:,}")
        logger.info(f"   📅 Keep sessions: {self.keep_sessions}")
        logger.info(f"   ⏰ Cleanup interval: {self.cleanup_interval_hours}h")

    def find_jsonl_files(self):
        """すべてのJSONLファイルを検索"""
        jsonl_files = []
        
        try:
            # scrapy_projectsディレクトリ内のすべてのJSONLファイルを検索
            pattern = os.path.join(self.projects_path, "**", "*.jsonl")
            files = glob.glob(pattern, recursive=True)
            
            for file_path in files:
                try:
                    stat = os.stat(file_path)
                    line_count = self._count_file_lines(file_path)
                    
                    jsonl_files.append({
                        'path': file_path,
                        'size': stat.st_size,
                        'lines': line_count,
                        'modified': datetime.fromtimestamp(stat.st_mtime),
                        'age_days': (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
                    })
                except Exception as e:
                    logger.warning(f"⚠️ Error analyzing {file_path}: {e}")
                    
            logger.info(f"📄 Found {len(jsonl_files)} JSONL files")
            return jsonl_files
            
        except Exception as e:
            logger.error(f"❌ Error finding JSONL files: {e}")
            return []

    def _count_file_lines(self, file_path):
        """ファイルの行数を効率的にカウント"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def analyze_files(self):
        """ファイル分析レポートを生成"""
        files = self.find_jsonl_files()
        
        if not files:
            logger.info("📄 No JSONL files found")
            return
        
        total_size = sum(f['size'] for f in files)
        total_lines = sum(f['lines'] for f in files)
        large_files = [f for f in files if f['lines'] > self.max_file_lines]
        old_files = [f for f in files if f['age_days'] > self.max_file_age_days]
        
        logger.info(f"📊 File Analysis Report:")
        logger.info(f"   📄 Total files: {len(files)}")
        logger.info(f"   📏 Total lines: {total_lines:,}")
        logger.info(f"   💾 Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
        logger.info(f"   📈 Large files (>{self.max_file_lines:,} lines): {len(large_files)}")
        logger.info(f"   📅 Old files (>{self.max_file_age_days} days): {len(old_files)}")
        
        if large_files:
            logger.info(f"🔍 Large files details:")
            for f in large_files[:5]:  # 最大5つまで表示
                logger.info(f"   📄 {f['path']}: {f['lines']:,} lines, {f['size']:,} bytes")

    def cleanup_large_files(self):
        """大きなファイルをクリーンアップ"""
        files = self.find_jsonl_files()
        large_files = [f for f in files if f['lines'] > self.max_file_lines]
        
        if not large_files:
            logger.info("✅ No large files to cleanup")
            return
        
        logger.info(f"🧹 Starting cleanup of {len(large_files)} large files")
        
        for file_info in large_files:
            try:
                self._cleanup_file(file_info['path'])
            except Exception as e:
                logger.error(f"❌ Error cleaning up {file_info['path']}: {e}")

    def _cleanup_file(self, file_path):
        """個別ファイルのクリーンアップ"""
        try:
            if not os.path.exists(self.tool_path):
                logger.error(f"❌ Cleanup tool not found: {self.tool_path}")
                return
            
            cmd = [
                sys.executable, self.tool_path, file_path,
                '--clean', '--keep-sessions', str(self.keep_sessions)
            ]
            
            logger.info(f"🔧 Cleaning up: {file_path}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully cleaned up: {file_path}")
                # 結果の詳細をログに記録
                for line in result.stdout.split('\n'):
                    if 'Reduced from' in line or 'items' in line:
                        logger.info(f"   📊 {line.strip()}")
            else:
                logger.error(f"❌ Cleanup failed for {file_path}")
                logger.error(f"   Error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Cleanup timeout for {file_path}")
        except Exception as e:
            logger.error(f"❌ Error cleaning up {file_path}: {e}")

    def remove_old_files(self):
        """古いファイルを削除"""
        files = self.find_jsonl_files()
        old_files = [f for f in files if f['age_days'] > self.max_file_age_days]
        
        if not old_files:
            logger.info("✅ No old files to remove")
            return
        
        logger.info(f"🗑️ Removing {len(old_files)} old files")
        
        for file_info in old_files:
            try:
                # バックアップファイルのみ削除（メインファイルは保持）
                if 'backup_' in file_info['path']:
                    os.remove(file_info['path'])
                    logger.info(f"🗑️ Removed old backup: {file_info['path']}")
                else:
                    logger.info(f"⚠️ Skipping main file: {file_info['path']}")
                    
            except Exception as e:
                logger.error(f"❌ Error removing {file_info['path']}: {e}")

    def run_full_cleanup(self):
        """完全なクリーンアップを実行"""
        logger.info("🚀 Starting full cleanup cycle")
        start_time = time.time()
        
        try:
            # 1. ファイル分析
            self.analyze_files()
            
            # 2. 大きなファイルのクリーンアップ
            self.cleanup_large_files()
            
            # 3. 古いファイルの削除
            self.remove_old_files()
            
            elapsed = time.time() - start_time
            logger.info(f"✅ Full cleanup completed in {elapsed:.1f}s")
            
        except Exception as e:
            logger.error(f"❌ Error in full cleanup: {e}")

    def start_scheduler(self):
        """スケジューラーを開始"""
        logger.info(f"⏰ Starting scheduler with {self.cleanup_interval_hours}h interval")
        
        # 即座に1回実行
        self.run_full_cleanup()
        
        # 定期実行をスケジュール
        schedule.every(self.cleanup_interval_hours).hours.do(self.run_full_cleanup)
        
        # 毎日午前3時に完全クリーンアップ
        schedule.every().day.at("03:00").do(self.run_full_cleanup)
        
        logger.info("🔄 Scheduler started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1分間隔でチェック
        except KeyboardInterrupt:
            logger.info("⏹️ Scheduler stopped by user")

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto File Cleanup Scheduler')
    parser.add_argument('--analyze', action='store_true', help='Analyze files only')
    parser.add_argument('--cleanup', action='store_true', help='Run cleanup once')
    parser.add_argument('--start', action='store_true', help='Start scheduler')
    parser.add_argument('--max-lines', type=int, default=10000, help='Max lines per file')
    parser.add_argument('--keep-sessions', type=int, default=5, help='Sessions to keep')
    
    args = parser.parse_args()
    
    scheduler = AutoFileCleanupScheduler()
    scheduler.max_file_lines = args.max_lines
    scheduler.keep_sessions = args.keep_sessions
    
    if args.analyze:
        scheduler.analyze_files()
    elif args.cleanup:
        scheduler.run_full_cleanup()
    elif args.start:
        scheduler.start_scheduler()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
