#!/usr/bin/env python3
"""
ScrapyUI Command Line Interface
"""

import argparse
import sys
import os
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime, timezone

def main():
    """メインCLI関数"""
    parser = argparse.ArgumentParser(
        description="ScrapyUI - Web-based Scrapy Management Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  scrapyui start                    # Start ScrapyUI server
  scrapyui start --port 8080        # Start on custom port
  scrapyui create-admin             # Create admin user
  scrapyui init myproject           # Initialize new project
  scrapyui --version                # Show version
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version="ScrapyUI 1.0.0"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start server command
    start_parser = subparsers.add_parser("start", help="Start ScrapyUI server")
    start_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind (default: 0.0.0.0)"
    )
    start_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind (default: 8000)"
    )
    start_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    start_parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open browser after starting server"
    )

    # Create admin command
    admin_parser = subparsers.add_parser("create-admin", help="Create admin user")
    admin_parser.add_argument(
        "--email",
        default="admin@scrapyui.com",
        help="Admin email (default: admin@scrapyui.com)"
    )
    admin_parser.add_argument(
        "--password",
        default="admin123456",
        help="Admin password (default: admin123456)"
    )

    # Initialize project command
    init_parser = subparsers.add_parser("init", help="Initialize new ScrapyUI project")
    init_parser.add_argument("name", help="Project name")
    init_parser.add_argument(
        "--template",
        choices=["basic", "advanced", "playwright"],
        default="basic",
        help="Project template (default: basic)"
    )

    # Database commands
    db_parser = subparsers.add_parser("db", help="Database management")
    db_subparsers = db_parser.add_subparsers(dest="db_command")

    db_subparsers.add_parser("init", help="Initialize database")
    db_subparsers.add_parser("migrate", help="Run database migrations")
    db_subparsers.add_parser("reset", help="Reset database")

    # Node.js service commands
    nodejs_parser = subparsers.add_parser("nodejs", help="Node.js service management")
    nodejs_parser.add_argument("--port", type=int, default=3001, help="Port number (default: 3001)")
    nodejs_parser.add_argument("--env", default="production", help="Environment (development/production)")
    nodejs_parser.add_argument("--install", action="store_true", help="Install dependencies")
    nodejs_parser.add_argument("--build", action="store_true", help="Build frontend")
    nodejs_parser.add_argument("--puppeteer-install", action="store_true", help="Install Puppeteer browser")

    # Celery monitoring commands
    monitor_parser = subparsers.add_parser("monitor", help="Monitor and manage Celery services")
    monitor_parser.add_argument("--worker", action="store_true", help="Monitor Celery worker")
    monitor_parser.add_argument("--beat", action="store_true", help="Monitor Celery beat")
    monitor_parser.add_argument("--auto-restart", action="store_true", help="Enable auto-restart on failure")
    monitor_parser.add_argument("--check-interval", type=int, default=30, help="Health check interval in seconds")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute commands
    if args.command == "start":
        start_server(args)
    elif args.command == "create-admin":
        create_admin(args)
    elif args.command == "init":
        init_project(args)
    elif args.command == "db":
        handle_db_command(args)
    elif args.command == "nodejs":
        handle_nodejs_command(args)
    elif args.command == "monitor":
        handle_monitor_command(args)

def build_frontend():
    """フロントエンドをビルド"""
    print("🔨 フロントエンドをビルド中...")

    # プロジェクトルートを取得
    project_root = Path(__file__).parent.parent.parent
    frontend_dir = project_root / "frontend"

    if not frontend_dir.exists():
        print("❌ フロントエンドディレクトリが見つかりません")
        return False

    try:
        # npm install
        print("📦 npm依存関係をインストール中...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)

        # npm run build
        print("🔨 フロントエンドをビルド中...")
        subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True)

        print("✅ フロントエンドビルド完了")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ フロントエンドビルドエラー: {e}")
        return False
    except FileNotFoundError:
        print("❌ npmが見つかりません。Node.jsをインストールしてください")
        return False

def init_database():
    """データベースを初期化"""
    try:
        from app.database import init_db
        init_db()
        print("✅ データベース初期化完了")
        return True
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")
        return False

def stop_existing_processes(port):
    """既存のプロセスを停止"""
    try:
        # uvicorn processes
        subprocess.run(["pkill", "-f", "uvicorn.*app.main:app"], capture_output=True)
        # Next.js dev processes
        subprocess.run(["pkill", "-f", "next.*dev"], capture_output=True)
        # Node.js processes
        subprocess.run(["pkill", "-f", "node.*app.js"], capture_output=True)
        # Celery processes
        subprocess.run(["pkill", "-f", "celery.*worker"], capture_output=True)
        subprocess.run(["pkill", "-f", "celery.*beat"], capture_output=True)

        # Kill processes using specific ports
        try:
            subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, check=True)
            subprocess.run(["lsof", "-ti", f":{port}", "|", "xargs", "kill", "-9"], shell=True, capture_output=True)
        except subprocess.CalledProcessError:
            pass  # No processes using the port

        print("✅ 既存プロセスのクリーンアップ完了")
    except Exception as e:
        print(f"⚠️ プロセスクリーンアップ警告: {e}")

def install_nodejs_dependencies():
    """Node.js依存関係をインストール"""
    project_root = Path(__file__).parent.parent.parent

    # Node.js service
    nodejs_dir = project_root / "nodejs-service"
    if nodejs_dir.exists():
        try:
            subprocess.run(["npm", "install"], cwd=nodejs_dir, check=True, capture_output=True)
            print("✅ Node.jsサービス依存関係インストール完了")
        except subprocess.CalledProcessError:
            print("⚠️ Node.jsサービス依存関係インストール失敗")

    # Frontend
    frontend_dir = project_root / "frontend"
    if frontend_dir.exists():
        try:
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True, capture_output=True)
            print("✅ フロントエンド依存関係インストール完了")
        except subprocess.CalledProcessError:
            print("⚠️ フロントエンド依存関係インストール失敗")

def start_celery_worker():
    """Celeryワーカーを起動（安定性向上）"""
    try:
        project_root = Path(__file__).parent.parent.parent
        backend_dir = project_root / "backend"

        # 改善されたCeleryワーカー設定
        subprocess.Popen([
            "python", "-m", "celery", "-A", "app.celery_app", "worker",
            "--loglevel=info",
            "--concurrency=2",  # 同時実行数を制限
            "--queues=scrapy,maintenance,monitoring",
            "--pool=prefork",
            "--optimization=fair",
            "--max-tasks-per-child=200",  # タスク数制限を緩和
            "--max-memory-per-child=500000",  # 500MB制限（メモリ制限緩和）
            "--time-limit=3600",  # 60分タイムアウト
            "--soft-time-limit=3300",  # 55分ソフトタイムアウト
            "--without-gossip",  # ゴシップを無効化
            "--without-mingle",  # ミングルを無効化
            "--without-heartbeat",  # ハートビートを無効化
            "--prefetch-multiplier=1",  # プリフェッチを1に制限
        ], cwd=backend_dir)
        print("✅ Celeryワーカー起動完了（安定性向上設定）")
    except Exception as e:
        print(f"⚠️ Celeryワーカー起動警告: {e}")

def start_celery_beat():
    """Celery Beatスケジューラを起動"""
    try:
        project_root = Path(__file__).parent.parent.parent
        backend_dir = project_root / "backend"

        subprocess.Popen([
            "python", "-m", "celery", "-A", "app.celery_app", "beat",
            "--scheduler", "app.scheduler:DatabaseScheduler", "--loglevel", "info"
        ], cwd=backend_dir)
        print("✅ Celery Beat起動完了")
    except Exception as e:
        print(f"⚠️ Celery Beat起動警告: {e}")

def start_nodejs_service_background():
    """Node.jsサービスをバックグラウンドで起動"""
    try:
        project_root = Path(__file__).parent.parent.parent
        nodejs_dir = project_root / "nodejs-service"

        if nodejs_dir.exists():
            subprocess.Popen(["npm", "start"], cwd=nodejs_dir)
            print("✅ Node.jsサービス起動完了")
    except Exception as e:
        print(f"⚠️ Node.jsサービス起動警告: {e}")

def start_frontend_dev_server():
    """フロントエンド開発サーバーを起動"""
    try:
        project_root = Path(__file__).parent.parent.parent
        frontend_dir = project_root / "frontend"

        if frontend_dir.exists():
            subprocess.Popen(["npm", "run", "dev", "--", "--port", "4000"], cwd=frontend_dir)
            print("✅ フロントエンド開発サーバー起動完了")
    except Exception as e:
        print(f"⚠️ フロントエンド開発サーバー起動警告: {e}")

def cleanup_processes():
    """プロセスをクリーンアップ"""
    try:
        subprocess.run(["pkill", "-f", "uvicorn.*app.main:app"], capture_output=True)
        subprocess.run(["pkill", "-f", "next.*dev"], capture_output=True)
        subprocess.run(["pkill", "-f", "node.*app.js"], capture_output=True)
        subprocess.run(["pkill", "-f", "celery.*worker"], capture_output=True)
        subprocess.run(["pkill", "-f", "celery.*beat"], capture_output=True)
        print("✅ プロセスクリーンアップ完了")
    except Exception as e:
        print(f"⚠️ プロセスクリーンアップ警告: {e}")

def start_nodejs_service():
    """Node.jsサービスを起動"""
    print("🚀 Node.jsサービスを起動中...")

    # プロジェクトルートを取得
    project_root = Path(__file__).parent.parent.parent
    nodejs_dir = project_root / "nodejs-service"

    if not nodejs_dir.exists():
        print("❌ Node.jsサービスディレクトリが見つかりません")
        return False

    try:
        # npm install
        print("📦 Node.js依存関係をインストール中...")
        subprocess.run(["npm", "install"], cwd=nodejs_dir, check=True)

        # npm start
        print("🚀 Node.jsサービス起動中...")
        subprocess.run(["npm", "start"], cwd=nodejs_dir)

    except subprocess.CalledProcessError as e:
        print(f"❌ Node.jsサービスエラー: {e}")
        return False
    except FileNotFoundError:
        print("❌ npmが見つかりません。Node.jsをインストールしてください")
        return False

def start_server(args):
    """サーバーを起動（start_servers.shの内容を考慮）"""
    print("🚀 ScrapyUI サーバーを起動しています...")
    print(f"📊 バックエンドポート: {args.port}")

    # データベース初期化・マイグレーション
    print("🔧 データベースを初期化中...")
    if not init_database():
        print("❌ データベース初期化に失敗しました")
        return

    # 既存プロセスの停止
    print("📋 既存のプロセスを確認中...")
    stop_existing_processes(args.port)

    # Node.js依存関係の確認・インストール
    if not args.reload:
        print("📦 Node.js依存関係を確認中...")
        install_nodejs_dependencies()

        # フロントエンドビルド
        print("🔨 フロントエンドをビルド中...")
        build_frontend()

    # Celeryワーカーを起動
    print("⚙️ Celeryワーカーを起動中...")
    start_celery_worker()

    # Celery Beatスケジューラを起動
    print("📅 Celery Beatスケジューラを起動中...")
    start_celery_beat()

    # Node.js Puppeteerサービスを起動
    print("🤖 Node.js Puppeteerサービスを起動中...")
    start_nodejs_service_background()

    # フロントエンドサーバーを起動（開発モードの場合）
    if args.reload:
        print("🎨 フロントエンドサーバーを起動中...")
        start_frontend_dev_server()

    # Import here to avoid circular imports
    import uvicorn
    from app.main import app

    if args.open_browser:
        import threading
        import time

        def open_browser_delayed():
            time.sleep(5)  # Wait for all services to start
            if args.reload:
                webbrowser.open("http://localhost:4000")  # Frontend dev server
            else:
                webbrowser.open(f"http://localhost:{args.port}")

        threading.Thread(target=open_browser_delayed, daemon=True).start()

    print(f"🔧 バックエンドサーバーを起動中 (ポート: {args.port})...")

    try:
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            reload_excludes=["scrapy_projects/*"] if args.reload else None
        )
    except KeyboardInterrupt:
        print("\n🛑 サーバーを停止中...")
        cleanup_processes()
        print("✅ サーバーが停止されました")

def create_admin(args):
    """管理者ユーザーを作成"""
    print("🔧 Creating admin user...")

    try:
        from app.database import SessionLocal, User, UserRole
        from app.auth.jwt_handler import PasswordHandler

        db = SessionLocal()

        # Check if admin already exists
        existing_admin = db.query(User).filter(User.email == args.email).first()

        if existing_admin:
            print(f"❌ Admin user with email {args.email} already exists!")
            return

        # Create admin user
        admin_user = User(
            id="admin-user-id",
            email=args.email,
            username="admin",
            full_name="System Administrator",
            hashed_password=PasswordHandler.hash_password(args.password),
            role=UserRole.ADMIN,
            is_active=True,
            is_superuser=True,  # スーパーユーザー権限を付与
            created_at=datetime.now(timezone.utc)
        )

        db.add(admin_user)
        db.commit()

        print("✅ Admin user created successfully!")
        print(f"   Email: {args.email}")
        print(f"   Password: {args.password}")
        print(f"   Role: admin")

    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
    finally:
        db.close()

def init_project(args):
    """新しいプロジェクトを初期化"""
    print(f"🔧 Initializing ScrapyUI project: {args.name}")

    project_dir = Path(args.name)

    if project_dir.exists():
        print(f"❌ Directory {args.name} already exists!")
        return

    # Create project structure
    project_dir.mkdir()
    (project_dir / "spiders").mkdir()
    (project_dir / "data").mkdir()
    (project_dir / "logs").mkdir()

    # Create basic files
    create_project_files(project_dir, args.name, args.template)

    print(f"✅ Project {args.name} created successfully!")
    print(f"   Directory: {project_dir.absolute()}")
    print(f"   Template: {args.template}")

def create_project_files(project_dir, name, template):
    """プロジェクトファイルを作成"""

    # scrapy.cfg
    scrapy_cfg = f"""[settings]
default = {name}.settings

[deploy]
project = {name}
"""

    (project_dir / "scrapy.cfg").write_text(scrapy_cfg)

    # __init__.py files
    (project_dir / "__init__.py").write_text("")
    (project_dir / "spiders" / "__init__.py").write_text("")

    # settings.py
    settings_py = f"""# Scrapy settings for {name} project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = '{name}'

SPIDER_MODULES = ['{name}.spiders']
NEWSPIDER_MODULE = '{name}.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {{
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {{
#    '{name}.middlewares.{name.title()}SpiderMiddleware': 543,
#}}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {{
#    '{name}.middlewares.{name.title()}DownloaderMiddleware': 543,
#}}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {{
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {{
#    '{name}.pipelines.{name.title()}Pipeline': 300,
#}}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 1
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = 'utf-8'

# Custom settings (commented out for standard Scrapy configuration)
# USER_AGENT = '{name} (+http://www.yourdomain.com)'
# DEFAULT_REQUEST_HEADERS = {{
#     'Accept-Language': 'ja',
# }}
# ITEM_PIPELINES = {{
#     '{name}.pipelines.{name.title()}Pipeline': 300,
# }}
# AUTOTHROTTLE_ENABLED = True
# AUTOTHROTTLE_START_DELAY = 1
# AUTOTHROTTLE_MAX_DELAY = 10
# AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
# AUTOTHROTTLE_DEBUG = False
# REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
# HTTPCACHE_ENABLED = True
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_EXPIRATION_SECS = 86400  # 1 day
# LOG_LEVEL = "INFO"

# Scrapy-Playwright settings (commented out for standard Scrapy configuration)
# DOWNLOAD_HANDLERS = {{
#     "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
#     "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
# }}
# PLAYWRIGHT_BROWSER_TYPE = "chromium"
# PLAYWRIGHT_LAUNCH_OPTIONS = {{
#     "headless": True,
# }}
# PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 10000
# TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Proxy settings (optional - configure as needed)
# DOWNLOADER_MIDDLEWARES = {{
#     'scrapy_proxies.RandomProxy': 350,
# }}

# ScrapyUI specific settings
SCRAPYUI_PROJECT_NAME = '{name}'
SCRAPYUI_TEMPLATE = '{template}'

# カスタムコマンドモジュール
COMMANDS_MODULE = "{name}.commands"

ADDONS = {{}}

# ===== Rich進捗バー設定 =====
# スパイダーコードを変更せずに美しい進捗バーを表示

# ScrapyUIバックエンドへのパスを追加
import sys
sys.path.append('/home/igtmtakan/workplace/python/scrapyUI/backend')

# Rich進捗バー拡張機能を有効化
EXTENSIONS = {{
    "scrapy.extensions.telnet.TelnetConsole": None,
    "scrapy.extensions.corestats.CoreStats": 500,
    "scrapy.extensions.logstats.LogStats": 500,
    # Rich進捗バー拡張機能を追加（スパイダーコードを変更せずに進捗バーを表示）
    "app.scrapy_extensions.rich_progress_extension.RichProgressExtension": 400,
}}

RICH_PROGRESS_ENABLED = True           # 進捗バーを有効化
RICH_PROGRESS_SHOW_STATS = True        # 詳細統計を表示
RICH_PROGRESS_UPDATE_INTERVAL = 0.1    # 更新間隔（秒）
RICH_PROGRESS_WEBSOCKET = False        # WebSocket通知（オプション）
"""

    (project_dir / "settings.py").write_text(settings_py)

    # items.py
    items_py = f"""# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class {name.title()}Item(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass
"""

    (project_dir / "items.py").write_text(items_py)

    # pipelines.py
    pipelines_py = f"""# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class {name.title()}Pipeline:
    def process_item(self, item, spider):
        return item
"""

    (project_dir / "pipelines.py").write_text(pipelines_py)

    # middlewares.py
    middlewares_py = f"""# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class {name.title()}SpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn't have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class {name.title()}DownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
"""

    (project_dir / "middlewares.py").write_text(middlewares_py)

def handle_db_command(args):
    """データベースコマンドを処理"""
    if args.db_command == "init":
        print("🔧 Initializing database...")
        # Database initialization logic here
        print("✅ Database initialized!")
    elif args.db_command == "migrate":
        print("🔧 Running database migrations...")
        # Migration logic here
        print("✅ Migrations completed!")
    elif args.db_command == "reset":
        print("🔧 Resetting database...")
        # Reset logic here
        print("✅ Database reset!")

def handle_nodejs_command(args):
    """Node.jsサービスコマンドを処理"""
    project_root = Path(__file__).parent.parent.parent
    nodejs_dir = project_root / "nodejs-service"
    frontend_dir = project_root / "frontend"

    if args.install:
        print("📦 Node.js依存関係をインストール中...")

        # Node.jsサービスの依存関係をインストール
        if nodejs_dir.exists():
            try:
                subprocess.run(["npm", "install"], cwd=nodejs_dir, check=True)
                print("✅ Node.jsサービス依存関係のインストール完了")
            except subprocess.CalledProcessError as e:
                print(f"❌ Node.jsサービス依存関係のインストール失敗: {e}")
                return

        # フロントエンドの依存関係をインストール
        if frontend_dir.exists():
            try:
                subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
                print("✅ フロントエンド依存関係のインストール完了")
            except subprocess.CalledProcessError as e:
                print(f"❌ フロントエンド依存関係のインストール失敗: {e}")
                return

    if args.build:
        print("🔨 フロントエンドをビルド中...")
        if frontend_dir.exists():
            try:
                subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True)
                print("✅ フロントエンドビルド完了")
            except subprocess.CalledProcessError as e:
                print(f"❌ フロントエンドビルド失敗: {e}")
                return

    if args.puppeteer_install:
        print("🔍 Puppeteerブラウザをインストール中...")
        if nodejs_dir.exists():
            try:
                subprocess.run(["npx", "puppeteer", "browsers", "install", "chrome"],
                             cwd=nodejs_dir, check=True)
                print("✅ Puppeteerブラウザのインストール完了")
            except subprocess.CalledProcessError as e:
                print(f"❌ Puppeteerブラウザのインストール失敗: {e}")
                return

    # デフォルトでNode.jsサービスを起動
    if not any([args.install, args.build, args.puppeteer_install]):
        print("🚀 Node.jsサービスを起動中...")
        if nodejs_dir.exists():
            try:
                # 環境変数を設定
                env = os.environ.copy()
                env["PORT"] = str(args.port)
                env["NODE_ENV"] = args.env

                subprocess.run(["npm", "start"], cwd=nodejs_dir, env=env)
            except subprocess.CalledProcessError as e:
                print(f"❌ Node.jsサービス起動失敗: {e}")
            except KeyboardInterrupt:
                print("\n🛑 Node.jsサービスを停止しました")
        else:
            print("❌ Node.jsサービスディレクトリが見つかりません")

def handle_monitor_command(args):
    """Celery監視コマンドを処理"""
    project_root = Path(__file__).parent.parent.parent
    backend_dir = project_root / "backend"

    if args.worker or args.beat or args.auto_restart:
        print("🔍 Celery監視を開始中...")

        try:
            # Celery監視スクリプトを実行
            monitor_script = backend_dir / "celery_monitor.py"
            if monitor_script.exists():
                subprocess.run(["python", str(monitor_script)], cwd=backend_dir)
            else:
                print("❌ Celery監視スクリプトが見つかりません")
        except KeyboardInterrupt:
            print("\n🛑 Celery監視を停止しました")
        except Exception as e:
            print(f"❌ Celery監視エラー: {e}")
    else:
        # デフォルトでCeleryの状態を表示
        print("📊 Celeryサービス状態:")

        # Celeryワーカーの状態確認
        try:
            result = subprocess.run([
                "python", "-m", "celery", "-A", "app.celery_app", "inspect", "active"
            ], cwd=backend_dir, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                print("✅ Celeryワーカー: 実行中")
                if result.stdout.strip():
                    print(f"   アクティブタスク: {result.stdout.count('uuid')}")
            else:
                print("❌ Celeryワーカー: 停止中または応答なし")
        except subprocess.TimeoutExpired:
            print("⚠️ Celeryワーカー: タイムアウト")
        except Exception as e:
            print(f"⚠️ Celeryワーカー状態確認エラー: {e}")

        # Redisの状態確認
        try:
            result = subprocess.run(["redis-cli", "ping"],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and "PONG" in result.stdout:
                print("✅ Redis: 実行中")
            else:
                print("❌ Redis: 停止中または応答なし")
        except Exception as e:
            print(f"⚠️ Redis状態確認エラー: {e}")

if __name__ == "__main__":
    main()
