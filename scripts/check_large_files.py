#!/usr/bin/env python3
"""
大きなファイルをチェックして、GitHubの制限を超えるファイルを検出するスクリプト
"""
import os
import sys
from pathlib import Path
import subprocess

# GitHubのファイルサイズ制限（100MB）
GITHUB_SIZE_LIMIT = 100 * 1024 * 1024  # 100MB in bytes
WARNING_SIZE_LIMIT = 50 * 1024 * 1024   # 50MB in bytes

def format_size(size_bytes):
    """ファイルサイズを人間が読みやすい形式に変換"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def check_file_sizes(directory="."):
    """指定されたディレクトリ内の大きなファイルをチェック"""
    large_files = []
    warning_files = []
    
    # .gitignoreで除外されるファイルを取得
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            capture_output=True, text=True, cwd=directory
        )
        tracked_files = set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
    except subprocess.CalledProcessError:
        print("⚠️ Git repository not found. Checking all files...")
        tracked_files = None
    
    for root, dirs, files in os.walk(directory):
        # .gitディレクトリをスキップ
        if '.git' in dirs:
            dirs.remove('.git')
        
        # node_modulesディレクトリをスキップ
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
            
        # __pycache__ディレクトリをスキップ
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
        
        for file in files:
            file_path = Path(root) / file
            relative_path = file_path.relative_to(directory)
            
            # Gitで追跡されているファイルのみチェック（tracked_filesがある場合）
            if tracked_files is not None and str(relative_path) not in tracked_files:
                continue
            
            try:
                file_size = file_path.stat().st_size
                
                if file_size > GITHUB_SIZE_LIMIT:
                    large_files.append((relative_path, file_size))
                elif file_size > WARNING_SIZE_LIMIT:
                    warning_files.append((relative_path, file_size))
                    
            except (OSError, IOError):
                continue
    
    return large_files, warning_files

def check_git_staged_files():
    """Gitでステージングされたファイルの大きなファイルをチェック"""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True
        )
        staged_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        large_staged = []
        for file_path in staged_files:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                if file_size > GITHUB_SIZE_LIMIT:
                    large_staged.append((file_path, file_size))
        
        return large_staged
    except subprocess.CalledProcessError:
        return []

def main():
    """メイン処理"""
    print("🔍 大きなファイルをチェック中...")
    print(f"📏 GitHub制限: {format_size(GITHUB_SIZE_LIMIT)}")
    print(f"⚠️ 警告サイズ: {format_size(WARNING_SIZE_LIMIT)}")
    print("-" * 60)
    
    # 現在のディレクトリをチェック
    large_files, warning_files = check_file_sizes()
    
    # ステージングされたファイルをチェック
    staged_large_files = check_git_staged_files()
    
    exit_code = 0
    
    # GitHub制限を超えるファイル
    if large_files or staged_large_files:
        print("❌ GitHub制限を超える大きなファイルが見つかりました:")
        
        for file_path, size in large_files:
            print(f"  🚫 {file_path}: {format_size(size)}")
        
        for file_path, size in staged_large_files:
            print(f"  🚫 [STAGED] {file_path}: {format_size(size)}")
        
        print("\n💡 対処方法:")
        print("  1. ファイルを削除: rm <file_path>")
        print("  2. .gitignoreに追加")
        print("  3. Git LFS を使用: git lfs track '<pattern>'")
        
        exit_code = 1
    
    # 警告サイズのファイル
    if warning_files:
        print("⚠️ 大きなファイル（警告）:")
        for file_path, size in warning_files:
            print(f"  📦 {file_path}: {format_size(size)}")
        print()
    
    if not large_files and not warning_files and not staged_large_files:
        print("✅ 大きなファイルは見つかりませんでした")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
