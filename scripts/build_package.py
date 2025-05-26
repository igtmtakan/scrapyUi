#!/usr/bin/env python3
"""
ScrapyUI Package Build Script
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, cwd=None):
    """コマンドを実行"""
    print(f"🔧 Running: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        sys.exit(1)
    
    if result.stdout:
        print(result.stdout)
    
    return result

def clean_build():
    """ビルドディレクトリをクリーンアップ"""
    print("🧹 Cleaning build directories...")
    
    dirs_to_clean = [
        "build",
        "dist", 
        "*.egg-info",
        "backend/build",
        "backend/dist",
        "backend/*.egg-info"
    ]
    
    for pattern in dirs_to_clean:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"   Removed: {path}")
            elif path.is_file():
                path.unlink()
                print(f"   Removed: {path}")

def install_build_tools():
    """ビルドツールをインストール"""
    print("📦 Installing build tools...")
    
    tools = [
        "build",
        "twine",
        "wheel",
        "setuptools"
    ]
    
    for tool in tools:
        run_command(f"pip install --upgrade {tool}")

def build_frontend():
    """フロントエンドをビルド"""
    print("🏗️ Building frontend...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("⚠️ Frontend directory not found, skipping frontend build")
        return
    
    # Install dependencies
    run_command("npm install", cwd=frontend_dir)
    
    # Build production version
    run_command("npm run build", cwd=frontend_dir)
    
    # Copy build files to backend static directory
    build_dir = frontend_dir / "dist"
    static_dir = Path("backend/app/static")
    
    if build_dir.exists():
        if static_dir.exists():
            shutil.rmtree(static_dir)
        shutil.copytree(build_dir, static_dir)
        print(f"   Frontend build copied to {static_dir}")

def build_package():
    """パッケージをビルド"""
    print("📦 Building Python package...")
    
    # Build source distribution and wheel
    run_command("python -m build")
    
    print("✅ Package built successfully!")
    
    # List built files
    dist_dir = Path("dist")
    if dist_dir.exists():
        print("\n📁 Built files:")
        for file in dist_dir.iterdir():
            print(f"   {file.name}")

def check_package():
    """パッケージをチェック"""
    print("🔍 Checking package...")
    
    # Check with twine
    run_command("python -m twine check dist/*")
    
    print("✅ Package check passed!")

def upload_to_testpypi():
    """TestPyPIにアップロード"""
    print("🚀 Uploading to TestPyPI...")
    
    run_command("python -m twine upload --repository testpypi dist/*")
    
    print("✅ Uploaded to TestPyPI!")
    print("🔗 Check: https://test.pypi.org/project/scrapyui/")

def upload_to_pypi():
    """PyPIにアップロード"""
    print("🚀 Uploading to PyPI...")
    
    # Confirm upload
    response = input("Are you sure you want to upload to PyPI? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Upload cancelled")
        return
    
    run_command("python -m twine upload dist/*")
    
    print("✅ Uploaded to PyPI!")
    print("🔗 Check: https://pypi.org/project/scrapyui/")

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ScrapyUI Package Build Script")
    parser.add_argument("--clean", action="store_true", help="Clean build directories")
    parser.add_argument("--frontend", action="store_true", help="Build frontend")
    parser.add_argument("--build", action="store_true", help="Build package")
    parser.add_argument("--check", action="store_true", help="Check package")
    parser.add_argument("--test-upload", action="store_true", help="Upload to TestPyPI")
    parser.add_argument("--upload", action="store_true", help="Upload to PyPI")
    parser.add_argument("--all", action="store_true", help="Run all steps except upload")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    try:
        if args.clean or args.all:
            clean_build()
        
        if args.frontend or args.all:
            build_frontend()
        
        if args.build or args.all:
            install_build_tools()
            build_package()
        
        if args.check or args.all:
            check_package()
        
        if args.test_upload:
            upload_to_testpypi()
        
        if args.upload:
            upload_to_pypi()
        
        print("\n🎉 All tasks completed successfully!")
        
    except KeyboardInterrupt:
        print("\n❌ Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Build failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
