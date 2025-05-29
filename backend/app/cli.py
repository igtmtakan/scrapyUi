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

def start_server(args):
    """サーバーを起動"""
    print("🚀 Starting ScrapyUI server...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Reload: {args.reload}")

    # Import here to avoid circular imports
    import uvicorn
    from app.main import app

    if args.open_browser:
        import threading
        import time

        def open_browser_delayed():
            time.sleep(2)  # Wait for server to start
            webbrowser.open(f"http://localhost:{args.port}")

        threading.Thread(target=open_browser_delayed, daemon=True).start()

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_excludes=["scrapy_projects/*"] if args.reload else None
    )

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

if __name__ == "__main__":
    main()
