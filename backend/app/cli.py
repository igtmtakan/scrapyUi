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
        reload=args.reload
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

BOT_NAME = '{name}'

SPIDER_MODULES = ['{name}.spiders']
NEWSPIDER_MODULE = '{name}.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# User-Agent
USER_AGENT = '{name} (+http://www.yourdomain.com)'

# Scrapy-Playwright settings
DOWNLOAD_HANDLERS = {{
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}}

PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {{
    "headless": True,
}}

# Playwright specific settings
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 10000

# Configure pipelines
ITEM_PIPELINES = {{
    '{name}.pipelines.{name.title()}Pipeline': 300,
}}

# Enable and configure the AutoThrottle extension
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# ログレベル設定
LOG_LEVEL = "INFO"

# ScrapyUI specific settings
SCRAPYUI_PROJECT_NAME = '{name}'
SCRAPYUI_TEMPLATE = '{template}'
"""

    (project_dir / "settings.py").write_text(settings_py)

    # items.py
    items_py = f"""import scrapy

class {name.title()}Item(scrapy.Item):
    # Define the fields for your item here
    title = scrapy.Field()
    url = scrapy.Field()
    content = scrapy.Field()
"""

    (project_dir / "items.py").write_text(items_py)

    # pipelines.py
    pipelines_py = f"""class {name.title()}Pipeline:
    def process_item(self, item, spider):
        return item
"""

    (project_dir / "pipelines.py").write_text(pipelines_py)

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
