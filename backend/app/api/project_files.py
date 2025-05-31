from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from pathlib import Path
import uuid
import os
from datetime import datetime, timezone

from ..database import get_db, Project, ProjectFile as DBProjectFile
from ..models.schemas import ProjectFileCreate, ProjectFileResponse, ProjectFileUpdate

router = APIRouter()

# Scrapyプロジェクトの標準ファイル
SCRAPY_FILES = [
    'scrapy.cfg',
    'settings.py',
    'items.py',
    'pipelines.py',
    'middlewares.py',
    '__init__.py',
    'spiders/__init__.py'
]

def get_project_files_dir(project_id: str) -> Path:
    """プロジェクトファイルのディレクトリパスを取得"""
    return Path(f"projects/{project_id}/files")

def ensure_project_files_dir(project_id: str) -> Path:
    """プロジェクトファイルディレクトリを作成"""
    files_dir = get_project_files_dir(project_id)
    files_dir.mkdir(parents=True, exist_ok=True)
    return files_dir

def get_default_file_content(filename: str, project_name: str = "myproject") -> str:
    """デフォルトファイル内容を取得"""
    if filename == 'scrapy.cfg':
        return f"""# Automatically created by: scrapy startproject
#
# For more information about the [deploy] section see:
# https://scrapyd.readthedocs.io/en/latest/deploy.html

[settings]
default = {project_name}.settings

[deploy]
#url = http://localhost:6800/
project = {project_name}
"""
    elif filename == 'settings.py':
        return f"""# Scrapy settings for {project_name} project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = '{project_name}'

SPIDER_MODULES = ['{project_name}.spiders']
NEWSPIDER_MODULE = '{project_name}.spiders'

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
#    '{project_name}.middlewares.{project_name.capitalize()}SpiderMiddleware': 543,
#}}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {{
#    '{project_name}.middlewares.{project_name.capitalize()}DownloaderMiddleware': 543,
#}}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {{
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {{
#    '{project_name}.pipelines.{project_name.capitalize()}Pipeline': 300,
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
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
FEED_EXPORT_ENCODING = 'utf-8'



"""
    elif filename == 'items.py':
        return f"""# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class {project_name.capitalize()}Item(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


"""
    elif filename == 'middlewares.py':
        return f"""# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class {project_name.capitalize()}SpiderMiddleware:
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


class {project_name.capitalize()}DownloaderMiddleware:
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
    elif filename == 'pipelines.py':
        return f"""# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class {project_name.capitalize()}Pipeline:
    def process_item(self, item, spider):
        return item



"""
    elif filename == '__init__.py':
        return ""
    elif filename == 'spiders/__init__.py':
        return """# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
"""
    else:
        return ""

def _initialize_project_files_from_filesystem(db: Session, project: Project) -> List[DBProjectFile]:
    """ファイルシステムからプロジェクトファイルをデータベースに初期化"""
    try:
        from pathlib import Path

        db_files = []

        # 実際のプロジェクトディレクトリから読み取り
        scrapy_projects_dir = Path("scrapy_projects")
        actual_project_dir = scrapy_projects_dir / project.path

        # プロジェクト構造のパスパターンを試す
        possible_project_dirs = [
            actual_project_dir / project.path,  # 標準構造: scrapy_projects/project_path/project_path/
            actual_project_dir,                 # 簡略構造: scrapy_projects/project_path/
        ]

        project_package_dir = None
        for dir_path in possible_project_dirs:
            if dir_path.exists():
                project_package_dir = dir_path
                break

        if not project_package_dir:
            # ファイルシステムにプロジェクトが見つからない場合はデフォルト内容を使用
            print(f"⚠️ Project directory not found in filesystem, using default content: {project.path}")
            files_dir = get_project_files_dir(project.id)

            for filename in SCRAPY_FILES:
                file_path = files_dir / filename
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
                else:
                    content = get_default_file_content(filename, project.name)

                # ファイル名とパスを正しく設定
                file_name = filename.split('/')[-1]  # ファイル名のみ
                file_path = filename  # フルパス

                # データベースに保存
                db_file = DBProjectFile(
                    id=str(uuid.uuid4()),
                    name=file_name,
                    path=file_path,
                    content=content,
                    file_type="python" if filename.endswith('.py') else "config",
                    project_id=project.id,
                    user_id=project.user_id
                )
                db.add(db_file)
                db_files.append(db_file)
        else:
            # ファイルシステムから実際のファイル内容を読み取り
            print(f"✅ Reading project files from filesystem: {project_package_dir}")

            # 実際のファイルマッピング
            file_mappings = [
                ("scrapy.cfg", actual_project_dir / "scrapy.cfg"),
                ("settings.py", project_package_dir / "settings.py"),
                ("items.py", project_package_dir / "items.py"),
                ("pipelines.py", project_package_dir / "pipelines.py"),
                ("middlewares.py", project_package_dir / "middlewares.py"),
                ("__init__.py", project_package_dir / "__init__.py"),
                ("spiders/__init__.py", project_package_dir / "spiders" / "__init__.py"),
            ]

            for db_filename, actual_file_path in file_mappings:
                if actual_file_path.exists():
                    try:
                        content = actual_file_path.read_text(encoding='utf-8')
                        print(f"  📄 Read from filesystem: {db_filename} ({len(content)} chars)")
                    except Exception as read_error:
                        print(f"  ❌ Failed to read {actual_file_path}: {read_error}")
                        content = get_default_file_content(db_filename, project.name)
                else:
                    print(f"  📝 Using default content: {db_filename}")
                    content = get_default_file_content(db_filename, project.name)

                # ファイル名とパスを正しく設定
                file_name = db_filename.split('/')[-1]  # ファイル名のみ
                file_path = db_filename  # フルパス

                # データベースに保存
                db_file = DBProjectFile(
                    id=str(uuid.uuid4()),
                    name=file_name,
                    path=file_path,
                    content=content,
                    file_type="python" if db_filename.endswith('.py') else "config",
                    project_id=project.id,
                    user_id=project.user_id
                )
                db.add(db_file)
                db_files.append(db_file)

        db.commit()
        print(f"✅ Initialized {len(db_files)} project files in database")
        return db_files

    except Exception as e:
        db.rollback()
        print(f"❌ Failed to initialize project files: {str(e)}")
        raise Exception(f"Failed to initialize project files: {str(e)}")

@router.get("/projects/{project_id}/files/sync-from-filesystem")
async def sync_project_file_from_filesystem(
    project_id: str,
    file_path: str = Query(..., description="File path to sync from filesystem"),
    db: Session = Depends(get_db)
):
    """実際のファイルシステムからプロジェクトファイルの内容を取得"""
    try:
        # プロジェクトの存在確認
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # ファイル名の検証（セキュリティチェック）
        if '..' in file_path or file_path.startswith('/'):
            raise HTTPException(status_code=400, detail="Invalid file path")

        # 実際のファイルシステムから読み取り
        from pathlib import Path
        import os

        # プロジェクトルートディレクトリからの相対パス
        current_dir = Path(__file__).parent.parent.parent.parent  # backend/app/api -> backend/app -> backend -> root
        scrapy_projects_dir = current_dir / "scrapy_projects"
        actual_project_dir = scrapy_projects_dir / project.path

        print(f"🔍 Looking for project in: {actual_project_dir}")
        print(f"🔍 Project path: {project.path}")
        print(f"🔍 Scrapy projects dir: {scrapy_projects_dir}")
        print(f"🔍 Current working directory: {os.getcwd()}")

        # プロジェクト構造のパスパターンを試す
        possible_project_dirs = [
            actual_project_dir / project.path,  # 標準構造: scrapy_projects/project_path/project_path/
            actual_project_dir,                 # 簡略構造: scrapy_projects/project_path/
        ]

        project_package_dir = None
        for dir_path in possible_project_dirs:
            if dir_path.exists():
                project_package_dir = dir_path
                break

        if not project_package_dir:
            raise HTTPException(status_code=404, detail="Project directory not found in filesystem")

        # ファイルマッピング
        file_mappings = {
            "scrapy.cfg": actual_project_dir / "scrapy.cfg",
            "settings.py": project_package_dir / "settings.py",
            "items.py": project_package_dir / "items.py",
            "pipelines.py": project_package_dir / "pipelines.py",
            "middlewares.py": project_package_dir / "middlewares.py",
            "__init__.py": project_package_dir / "__init__.py",
            "spiders/__init__.py": project_package_dir / "spiders" / "__init__.py",
        }

        # プロジェクトパス付きファイルパスも対応
        for key in list(file_mappings.keys()):
            file_mappings[f"{project.path}/{key}"] = file_mappings[key]

        # ファイルパスに対応する実際のファイルパスを取得
        actual_file_path = file_mappings.get(file_path)

        if not actual_file_path:
            raise HTTPException(status_code=404, detail=f"File mapping not found for: {file_path}")

        if not actual_file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found in filesystem: {actual_file_path}")

        # ファイル内容を読み取り
        try:
            content = actual_file_path.read_text(encoding='utf-8')
            print(f"✅ Read from filesystem: {file_path} -> {actual_file_path} ({len(content)} chars)")

            return {
                "file_path": file_path,
                "actual_path": str(actual_file_path),
                "content": content,
                "size": len(content.encode('utf-8'))
            }
        except Exception as read_error:
            raise HTTPException(status_code=500, detail=f"Failed to read file: {str(read_error)}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file from filesystem: {str(e)}")

@router.get("/projects/{project_id}/files/", response_model=List[ProjectFileResponse])
async def get_project_files(project_id: str, db: Session = Depends(get_db)):
    """プロジェクトファイル一覧を取得（データベースから）"""
    try:
        # プロジェクトの存在確認
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # データベースからプロジェクトファイルを取得
        db_files = db.query(DBProjectFile).filter(
            DBProjectFile.project_id == project_id
        ).all()

        # データベースにファイルがない場合、ファイルシステムから初期化
        if not db_files:
            db_files = _initialize_project_files_from_filesystem(db, project)

        # レスポンス形式に変換
        files = []
        for db_file in db_files:
            # content が bytes の場合は文字列に変換
            content = db_file.content
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            elif content is None:
                content = ""

            files.append(ProjectFileResponse(
                id=db_file.id,
                name=db_file.name,
                path=db_file.path,
                content=content,
                file_type=db_file.file_type,
                project_id=db_file.project_id,
                created_at=db_file.created_at,
                updated_at=db_file.updated_at,
                size=len(content.encode('utf-8'))
            ))

        print(f"📁 Returning {len(files)} project files for project {project_id}:")
        for file in files:
            print(f"  - {file.name} ({file.path}) - {len(file.content)} chars")

            # admin_mytest/settings.pyの詳細ログ
            if file.path == "admin_mytest/settings.py":
                print(f"    🔍 DETAILED API RESPONSE for {file.path}:")
                print(f"    📝 Content type: {type(file.content)}")
                print(f"    📝 Content is None: {file.content is None}")
                print(f"    📝 Content is empty: {file.content == ''}")
                print(f"    📝 Content starts with header: {file.content.startswith('# Scrapy settings for') if file.content else False}")
                print(f"    📝 Content preview: {repr(file.content[:100]) if file.content else 'None'}")

        return files

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to get project files: {str(e)}")

@router.get("/projects/{project_id}/files/{file_path:path}", response_model=ProjectFileResponse)
async def get_project_file(project_id: str, file_path: str, db: Session = Depends(get_db)):
    """特定のプロジェクトファイルを取得（データベースから）"""
    try:
        # プロジェクトの存在確認
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # ファイル名の検証（セキュリティチェック）
        if '..' in file_path or file_path.startswith('/'):
            raise HTTPException(status_code=400, detail="Invalid file path")

        # データベースからファイルを取得（nameまたはpathで検索）
        db_file = db.query(DBProjectFile).filter(
            DBProjectFile.project_id == project_id,
            (DBProjectFile.name == file_path) | (DBProjectFile.path == file_path)
        ).first()

        if not db_file:
            # データベースにない場合、デフォルト内容で作成
            content = get_default_file_content(file_path, project.name)
            db_file = DBProjectFile(
                id=str(uuid.uuid4()),
                name=file_path,
                path=file_path,
                content=content,
                file_type="python" if file_path.endswith('.py') else "config",
                project_id=project_id,
                user_id=project.user_id
            )
            db.add(db_file)
            db.commit()

        # content が bytes の場合は文字列に変換
        content = db_file.content
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        elif content is None:
            content = ""

        # admin_mytest/settings.pyの詳細ログ
        if file_path == "admin_mytest/settings.py":
            print(f"🔍 INDIVIDUAL FILE API RESPONSE for {file_path}:")
            print(f"📝 Content type: {type(content)}")
            print(f"📝 Content length: {len(content)} characters")
            print(f"📝 Content is None: {content is None}")
            print(f"📝 Content is empty: {content == ''}")
            print(f"📝 Content starts with header: {content.startswith('# Scrapy settings for') if content else False}")
            print(f"📝 Content preview: {repr(content[:100]) if content else 'None'}")

        return ProjectFileResponse(
            id=db_file.id,
            name=db_file.name,
            path=db_file.path,
            content=content,
            file_type=db_file.file_type,
            project_id=db_file.project_id,
            created_at=db_file.created_at,
            updated_at=db_file.updated_at,
            size=len(content.encode('utf-8'))
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to get project file: {str(e)}")

@router.post("/projects/{project_id}/files")
async def create_project_file(
    project_id: str,
    file_create: ProjectFileCreate,
    db: Session = Depends(get_db)
):
    """新しいプロジェクトファイルを作成"""
    # プロジェクトの存在確認
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    files_dir = ensure_project_files_dir(project_id)
    file_full_path = files_dir / file_create.path

    if file_full_path.exists():
        raise HTTPException(status_code=400, detail="File already exists")

    try:
        file_full_path.write_text(file_create.content, encoding='utf-8')
        return {"message": "File created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create file: {str(e)}")

@router.put("/projects/{project_id}/files/{file_path:path}")
async def save_project_file(
    project_id: str,
    file_path: str,
    file_content: dict,
    db: Session = Depends(get_db)
):
    """プロジェクトファイルを保存（DB優先 + ファイルシステム同期 + 完全トランザクション）"""
    print(f"🔄 Starting file save transaction: {file_path}")

    # トランザクション開始
    try:
        # プロジェクトの存在確認
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        content = file_content.get("content", "")
        if content is None:
            raise HTTPException(status_code=400, detail="Content is required")

        print(f"📝 Content length: {len(content)} characters")
        print(f"📝 Content preview (first 200 chars): {repr(content[:200])}")
        print(f"📝 Content starts with header: {content.startswith('# Scrapy settings for')}")

        # Step 1: データベースでプロジェクトファイルを検索（pathフィールドで検索）
        db_file = db.query(DBProjectFile).filter(
            DBProjectFile.project_id == project_id,
            DBProjectFile.path == file_path
        ).first()

        # Step 2: データベース操作（まずDBに保存）
        if db_file:
            print(f"📄 Updating existing file in database: {file_path}")
            # 既存ファイルを更新
            old_content = db_file.content
            db_file.content = content
            db_file.updated_at = datetime.now(timezone.utc)
        else:
            print(f"📄 Creating new file in database: {file_path}")
            # 新しいファイルを作成
            db_file = DBProjectFile(
                id=str(uuid.uuid4()),
                name=file_path.split('/')[-1],  # ファイル名のみ
                path=file_path,  # フルパス
                content=content,
                file_type="python" if file_path.endswith('.py') else "config",
                project_id=project_id,
                user_id=project.user_id
            )
            db.add(db_file)
            old_content = None

        # Step 3: データベースに保存（コミット前）
        db.flush()  # データベースに書き込むがコミットはしない
        print(f"✅ Database operation prepared successfully")

        # Step 4: ファイルシステムに保存（トランザクション内）
        try:
            from ..services.scrapy_service import ScrapyPlaywrightService
            scrapy_service = ScrapyPlaywrightService()

            print(f"💾 Saving to filesystem: {project.path}/{file_path}")
            success = scrapy_service.save_project_file(project.path, file_path, content)

            if not success:
                raise Exception("Filesystem save returned False")

            print(f"✅ Filesystem save successful")

        except Exception as fs_error:
            print(f"❌ Filesystem save failed: {fs_error}")
            # ファイルシステム保存に失敗した場合はロールバック
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save to filesystem: {str(fs_error)}"
            )

        # Step 5: 両方成功した場合のみコミット
        db.commit()
        print(f"🎉 Transaction completed successfully: {file_path}")

        return {
            "message": "File saved successfully to both database and filesystem",
            "file_path": file_path,
            "content_length": len(content),
            "database_updated": True,
            "filesystem_updated": True
        }

    except HTTPException:
        db.rollback()
        print(f"❌ HTTP Exception occurred, transaction rolled back")
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Unexpected error occurred, transaction rolled back: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save project file: {str(e)}"
        )



@router.delete("/projects/{project_id}/files/{file_path:path}")
async def delete_project_file(project_id: str, file_path: str, db: Session = Depends(get_db)):
    """プロジェクトファイルを削除"""
    # プロジェクトの存在確認
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # ファイル名の検証
    if file_path not in SCRAPY_FILES:
        raise HTTPException(status_code=400, detail="Invalid file path")

    files_dir = get_project_files_dir(project_id)
    file_full_path = files_dir / file_path

    if not file_full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        file_full_path.unlink()
        return {"message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
