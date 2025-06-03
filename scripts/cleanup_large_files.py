#!/usr/bin/env python3
"""
不要な大きなファイルを自動的にクリーンアップするスクリプト
"""
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import glob

def format_size(size_bytes):
    """ファイルサイズを人間が読みやすい形式に変換"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def cleanup_database_backups():
    """データベースバックアップファイルをクリーンアップ"""
    patterns = [
        "backend/database/*.db.backup*",
        "backend/database/*.db.bak*",
        "backend/database/*.sqlite.backup*",
        "backend/database/*.sqlite.bak*",
        "**/*.db.backup*",
        "**/*.db.bak*",
    ]
    
    cleaned_files = []
    total_size = 0
    
    for pattern in patterns:
        for file_path in glob.glob(pattern, recursive=True):
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                try:
                    os.remove(file_path)
                    cleaned_files.append((file_path, file_size))
                    total_size += file_size
                    print(f"🗑️ 削除: {file_path} ({format_size(file_size)})")
                except OSError as e:
                    print(f"❌ 削除失敗: {file_path} - {e}")
    
    return cleaned_files, total_size

def cleanup_old_logs():
    """古いログファイルをクリーンアップ（7日以上前）"""
    log_patterns = [
        "logs/*.log",
        "scrapy_projects/*/logs/*.log",
        "**/*.log",
    ]
    
    cutoff_date = datetime.now() - timedelta(days=7)
    cleaned_files = []
    total_size = 0
    
    for pattern in log_patterns:
        for file_path in glob.glob(pattern, recursive=True):
            if os.path.exists(file_path):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_mtime < cutoff_date:
                    file_size = os.path.getsize(file_path)
                    try:
                        os.remove(file_path)
                        cleaned_files.append((file_path, file_size))
                        total_size += file_size
                        print(f"🗑️ 古いログ削除: {file_path} ({format_size(file_size)})")
                    except OSError as e:
                        print(f"❌ 削除失敗: {file_path} - {e}")
    
    return cleaned_files, total_size

def cleanup_temp_files():
    """一時ファイルをクリーンアップ"""
    temp_patterns = [
        "*.tmp",
        "*.temp",
        "**/*.tmp",
        "**/*.temp",
        "**/__pycache__",
        "**/.pytest_cache",
        "**/node_modules/.cache",
    ]
    
    cleaned_files = []
    total_size = 0
    
    for pattern in temp_patterns:
        for path in glob.glob(pattern, recursive=True):
            if os.path.exists(path):
                try:
                    if os.path.isfile(path):
                        file_size = os.path.getsize(path)
                        os.remove(path)
                        cleaned_files.append((path, file_size))
                        total_size += file_size
                        print(f"🗑️ 一時ファイル削除: {path} ({format_size(file_size)})")
                    elif os.path.isdir(path) and any(name in path for name in ['__pycache__', '.pytest_cache', '.cache']):
                        dir_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                                     for dirpath, dirnames, filenames in os.walk(path)
                                     for filename in filenames)
                        shutil.rmtree(path)
                        cleaned_files.append((path, dir_size))
                        total_size += dir_size
                        print(f"🗑️ キャッシュディレクトリ削除: {path} ({format_size(dir_size)})")
                except OSError as e:
                    print(f"❌ 削除失敗: {path} - {e}")
    
    return cleaned_files, total_size

def cleanup_large_result_files():
    """大きな結果ファイルをクリーンアップ（1週間以上前、50MB以上）"""
    result_patterns = [
        "scrapy_projects/*/*.jsonl",
        "scrapy_projects/*/*.json",
        "scrapy_projects/*/*.csv",
        "scrapy_projects/*/ranking_results.*",
        "scrapy_projects/*/stats_task_*.json",
    ]
    
    cutoff_date = datetime.now() - timedelta(days=7)
    size_limit = 50 * 1024 * 1024  # 50MB
    cleaned_files = []
    total_size = 0
    
    for pattern in result_patterns:
        for file_path in glob.glob(pattern, recursive=True):
            if os.path.exists(file_path):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                file_size = os.path.getsize(file_path)
                
                if file_mtime < cutoff_date and file_size > size_limit:
                    try:
                        os.remove(file_path)
                        cleaned_files.append((file_path, file_size))
                        total_size += file_size
                        print(f"🗑️ 大きな結果ファイル削除: {file_path} ({format_size(file_size)})")
                    except OSError as e:
                        print(f"❌ 削除失敗: {file_path} - {e}")
    
    return cleaned_files, total_size

def main():
    """メイン処理"""
    print("🧹 自動クリーンアップを開始...")
    print(f"📅 実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    total_cleaned = 0
    total_size_cleaned = 0
    
    # データベースバックアップファイルのクリーンアップ
    print("🗄️ データベースバックアップファイルをクリーンアップ中...")
    db_files, db_size = cleanup_database_backups()
    total_cleaned += len(db_files)
    total_size_cleaned += db_size
    
    # 古いログファイルのクリーンアップ
    print("\n📝 古いログファイルをクリーンアップ中...")
    log_files, log_size = cleanup_old_logs()
    total_cleaned += len(log_files)
    total_size_cleaned += log_size
    
    # 一時ファイルのクリーンアップ
    print("\n🗂️ 一時ファイルをクリーンアップ中...")
    temp_files, temp_size = cleanup_temp_files()
    total_cleaned += len(temp_files)
    total_size_cleaned += temp_size
    
    # 大きな結果ファイルのクリーンアップ
    print("\n📊 大きな結果ファイルをクリーンアップ中...")
    result_files, result_size = cleanup_large_result_files()
    total_cleaned += len(result_files)
    total_size_cleaned += result_size
    
    print("\n" + "=" * 60)
    print(f"✅ クリーンアップ完了!")
    print(f"📁 削除ファイル数: {total_cleaned}")
    print(f"💾 解放容量: {format_size(total_size_cleaned)}")
    
    if total_cleaned == 0:
        print("🎉 クリーンアップするファイルはありませんでした")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
