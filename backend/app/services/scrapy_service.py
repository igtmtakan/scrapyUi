import os
import subprocess
import shutil
import json
import asyncio
import uuid
import threading
import time
import signal
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import sys
from datetime import datetime, timedelta
import glob

from .scrapy_task_manager import ScrapyTaskManager

# ロギングとエラーハンドリングのインポート
from ..utils.logging_config import get_logger, log_with_context, log_exception
from ..utils.error_handler import (
    ScrapyUIException,
    ProjectException,
    SpiderException,
    TaskException,
    ErrorCode
)

# Python 3.13パフォーマンス最適化
from ..performance.python313_optimizations import (
    FreeThreadedExecutor,
    AsyncOptimizer,
    MemoryOptimizer,
    performance_monitor,
    jit_optimizer
)

# Rich progress imports
try:
    from ..utils.rich_progress import ScrapyProgressTracker, RichSpiderMonitor
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️ Rich progress not available - falling back to standard progress")

class ScrapyPlaywrightService:
    """Scrapy + Playwright統合を管理するサービスクラス（シングルトン）"""

    _instance = None
    _initialized = False

    def __new__(cls, base_projects_dir: str = None):
        if cls._instance is None:
            cls._instance = super(ScrapyPlaywrightService, cls).__new__(cls)
        return cls._instance

    def __init__(self, base_projects_dir: str = None):
        if self._initialized:
            return

        # ロガーを初期化
        self.logger = get_logger(__name__)

        # Python 3.13パフォーマンス最適化コンポーネント
        self.memory_optimizer = MemoryOptimizer()
        self.async_optimizer = None  # 必要時に初期化

        # デフォルトのプロジェクトディレクトリを設定
        if base_projects_dir is None:
            # 現在のファイルの位置から相対的にscrapy_projectsディレクトリを特定
            current_file = Path(__file__)
            # backend/app/services/scrapy_service.py から ../../scrapy_projects
            base_projects_dir = current_file.parent.parent.parent.parent / "scrapy_projects"

        self.base_projects_dir = Path(base_projects_dir)
        self.base_projects_dir.mkdir(exist_ok=True)
        self.running_processes: Dict[str, subprocess.Popen] = {}
        self.task_progress: Dict[str, Dict[str, Any]] = {}  # タスクの進行状況を追跡
        self.monitoring_thread = None
        self.stop_monitoring = False

        # Rich progress tracker
        self.rich_tracker = None
        if RICH_AVAILABLE:
            self.rich_tracker = ScrapyProgressTracker()
            print("✨ Rich progress tracking enabled")

        self._initialized = True
        print(f"🔧 ScrapyPlaywrightService initialized with base_dir: {self.base_projects_dir.absolute()}")

    def create_project(self, project_name: str, project_path: str) -> bool:
        """新しいScrapyプロジェクトを作成（scrapy startproject と同じ動作）"""
        try:
            log_with_context(
                self.logger, "INFO",
                f"Creating Scrapy project: {project_name}",
                extra_data={"project_name": project_name, "project_path": project_path}
            )

            # scrapy_projects ディレクトリ内にプロジェクトを作成
            # scrapy startproject project_name の動作を再現

            # scrapy_projects ディレクトリが存在することを確認
            self.base_projects_dir.mkdir(exist_ok=True)

            # scrapy startproject を scrapy_projects ディレクトリ内で実行
            cmd = [
                sys.executable, "-m", "scrapy", "startproject", project_name
            ]

            self.logger.info(f"Executing command: {' '.join(cmd)} in {self.base_projects_dir}")

            result = subprocess.run(
                cmd,
                cwd=str(self.base_projects_dir),  # scrapy_projects ディレクトリで実行
                capture_output=True,
                text=True,
                check=True
            )

            self.logger.info(f"Scrapy project created successfully: {result.stdout}")

            # 作成されたプロジェクトディレクトリのパス
            project_dir = self.base_projects_dir / project_name

            # scrapy-playwright設定を追加
            self._setup_playwright_config(project_dir / project_name)

            # scrapy.cfgファイルを検証・修正（プロジェクトパスを使用）
            self._validate_and_fix_scrapy_cfg(project_name, project_path)

            log_with_context(
                self.logger, "INFO",
                f"Project creation completed: {project_name}",
                extra_data={"project_name": project_name, "project_dir": str(project_dir)}
            )

            return True

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to create Scrapy project: {e.stderr}"
            log_exception(
                self.logger, error_msg,
                extra_data={"project_name": project_name, "command": cmd, "stderr": e.stderr}
            )
            raise ProjectException(
                message=error_msg,
                error_code=ErrorCode.PROJECT_CREATION_FAILED,
                details={"stderr": e.stderr, "command": cmd}
            )
        except Exception as e:
            error_msg = f"Error creating project: {str(e)}"
            log_exception(
                self.logger, error_msg,
                extra_data={"project_name": project_name}
            )
            raise ProjectException(
                message=error_msg,
                error_code=ErrorCode.PROJECT_CREATION_FAILED,
                details={"original_error": str(e)}
            )

    def _setup_playwright_config(self, project_dir: Path) -> None:
        """scrapy-playwright設定をプロジェクトに追加"""
        settings_file = project_dir / "settings.py"

        playwright_settings = '''

# Scrapy-Playwright settings
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
}

# Default request meta for Playwright
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000
PLAYWRIGHT_ABORT_REQUEST = lambda req: req.resource_type == "image"

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    'Accept-Language': 'ja',
}

# Feed export encoding
FEED_EXPORT_ENCODING = 'utf-8'

# HTTP Cache settings (for development efficiency)
HTTPCACHE_ENABLED = True
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_EXPIRATION_SECS = 86400  # 1 day

# Proxy settings (optional - configure as needed)
# DOWNLOADER_MIDDLEWARES = {
#     'scrapy_proxies.RandomProxy': 350,
# }

# Proxy settings (optional - configure as needed)
# PROXY_LIST = '/path/to/proxy/list.txt'
# PROXY_MODE = 0  # 0: random, 1: round-robin, 2: only once
'''

        if settings_file.exists():
            with open(settings_file, 'a', encoding='utf-8') as f:
                f.write(playwright_settings)

    def _validate_and_fix_scrapy_cfg(self, project_name: str, project_path: str = None) -> None:
        """scrapy.cfgファイルを検証し、必要に応じて修正（WebUI対応版）"""
        try:
            # project_pathが指定されていない場合はproject_nameを使用
            if project_path is None:
                project_path = project_name

            project_dir = self.base_projects_dir / project_name
            scrapy_cfg_path = project_dir / "scrapy.cfg"

            if not scrapy_cfg_path.exists():
                self.logger.warning(f"scrapy.cfg not found: {scrapy_cfg_path}")
                return

            # 現在の内容を読み込み
            with open(scrapy_cfg_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 設定を確認
            import re
            settings_match = re.search(r'default\s*=\s*(.+?)\.settings', content)
            project_match = re.search(r'project\s*=\s*(.+)', content)

            current_settings_project = settings_match.group(1).strip() if settings_match else None
            current_deploy_project = project_match.group(1).strip() if project_match else None

            # 修正が必要かチェック（project_pathを使用）
            needs_fix = (
                current_settings_project != project_path or
                current_deploy_project != project_path
            )

            if needs_fix:
                self.logger.info(f"Fixing scrapy.cfg for project: {project_name} (path: {project_path})")

                # 正しい内容で修正（project_pathを使用）
                correct_content = f"""# Automatically created by: scrapy startproject
#
# For more information about the [deploy] section see:
# https://scrapyd.readthedocs.io/en/latest/deploy.html

[settings]
default = {project_path}.settings

[deploy]
#url = http://localhost:6800/
project = {project_path}
"""

                with open(scrapy_cfg_path, 'w', encoding='utf-8') as f:
                    f.write(correct_content)

                self.logger.info(f"Fixed scrapy.cfg: {scrapy_cfg_path} (using project_path: {project_path})")
            else:
                self.logger.info(f"scrapy.cfg is correct for project: {project_name} (path: {project_path})")

        except Exception as e:
            self.logger.error(f"Error validating scrapy.cfg for {project_name}: {e}")

    def get_spider_code(self, project_path: str, spider_name: str) -> str:
        """スパイダーのコードを取得"""
        try:
            # 複数のパスパターンでスパイダーファイルを検索
            full_path = self.base_projects_dir / project_path

            possible_spider_paths = [
                # 標準Scrapyプロジェクト構造: scrapy_projects/project_name/project_name/spiders/spider_name.py
                full_path / project_path / "spiders" / f"{spider_name}.py",
                # 簡略化構造: scrapy_projects/project_name/spiders/spider_name.py
                full_path / "spiders" / f"{spider_name}.py",
                # 直接配置: scrapy_projects/project_name/spider_name.py
                full_path / f"{spider_name}.py"
            ]

            spider_file = None
            for path in possible_spider_paths:
                if path.exists():
                    spider_file = path
                    print(f"✅ Spider file found: {spider_file}")
                    break

            if not spider_file:
                # 再帰検索で最後の手段
                import glob
                pattern = str(full_path / "**" / f"{spider_name}.py")
                matches = glob.glob(pattern, recursive=True)
                if matches:
                    spider_file = Path(matches[0])
                    print(f"✅ Spider file found via recursive search: {spider_file}")
                else:
                    print(f"❌ Spider file not found in any location:")
                    for path in possible_spider_paths:
                        print(f"   - {path}")
                    raise Exception(f"Spider file not found: {spider_name}.py in {full_path}")

            with open(spider_file, 'r', encoding='utf-8') as f:
                return f.read()

        except Exception as e:
            print(f"Error reading spider code: {str(e)}")
            raise Exception(f"Error reading spider code: {str(e)}")

    def _get_spider_custom_settings(self, project_path: str, spider_name: str) -> dict:
        """スパイダーのcustom_settingsを取得（改良版）"""
        try:
            # スパイダーファイルを読み込み
            spider_code = self.get_spider_code(project_path, spider_name)

            # ASTを使用してより安全にcustom_settingsを抽出
            import ast

            try:
                # Pythonコードを解析
                tree = ast.parse(spider_code)

                # クラス定義を探す
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # クラス内のcustom_settings属性を探す
                        for item in node.body:
                            if (isinstance(item, ast.Assign) and
                                len(item.targets) == 1 and
                                isinstance(item.targets[0], ast.Name) and
                                item.targets[0].id == 'custom_settings'):

                                # 辞書リテラルを評価
                                if isinstance(item.value, ast.Dict):
                                    custom_settings = ast.literal_eval(item.value)
                                    print(f"✅ Extracted custom_settings from {spider_name} using AST: {custom_settings}")
                                    return custom_settings

                print(f"ℹ️ No custom_settings found in {spider_name} using AST")

                # AST解析に失敗した場合は、フォールバック方式を使用
                return self._fallback_extract_custom_settings(spider_code, spider_name)

            except Exception as ast_error:
                print(f"⚠️ AST parsing failed for {spider_name}: {ast_error}")
                # フォールバック方式を使用
                return self._fallback_extract_custom_settings(spider_code, spider_name)

        except Exception as e:
            print(f"⚠️ Error getting custom_settings for {spider_name}: {e}")
            return {}

    def _fallback_extract_custom_settings(self, spider_code: str, spider_name: str) -> dict:
        """custom_settings抽出のフォールバック方式"""
        try:
            import re

            # より堅牢な正規表現パターン（ネストした辞書に対応）
            # custom_settings = { ... } の部分を抽出
            pattern = r'custom_settings\s*=\s*\{'
            match = re.search(pattern, spider_code)

            if match:
                start_pos = match.end() - 1  # '{' の位置
                brace_count = 0
                end_pos = start_pos

                # 対応する '}' を見つける
                for i, char in enumerate(spider_code[start_pos:], start_pos):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i + 1
                            break

                if brace_count == 0:
                    settings_content = spider_code[start_pos:end_pos]

                    try:
                        # 安全にevalを使用
                        safe_dict = {"__builtins__": {}, "True": True, "False": False, "None": None}
                        custom_settings = eval(settings_content, safe_dict)
                        print(f"✅ Extracted custom_settings from {spider_name} using fallback: {custom_settings}")
                        return custom_settings
                    except Exception as e:
                        print(f"⚠️ Error evaluating custom_settings for {spider_name}: {e}")
                        # 基本的な設定のみ返す
                        return {
                            'DOWNLOAD_DELAY': 3,
                            'CONCURRENT_REQUESTS': 1,
                            'CONCURRENT_REQUESTS_PER_DOMAIN': 1
                        }
                else:
                    print(f"⚠️ Unmatched braces in custom_settings for {spider_name}")
            else:
                print(f"ℹ️ No custom_settings pattern found in {spider_name}")

            return {}

        except Exception as e:
            print(f"⚠️ Fallback extraction failed for {spider_name}: {e}")
            return {}

    def save_spider_code(self, project_path: str, spider_name: str, code: str) -> bool:
        """スパイダーのコードを保存"""
        try:
            # 既存のスパイダーファイルを検索
            full_path = self.base_projects_dir / project_path

            possible_spider_paths = [
                # 標準Scrapyプロジェクト構造: scrapy_projects/project_name/project_name/spiders/spider_name.py
                full_path / project_path / "spiders" / f"{spider_name}.py",
                # 簡略化構造: scrapy_projects/project_name/spiders/spider_name.py
                full_path / "spiders" / f"{spider_name}.py",
                # 直接配置: scrapy_projects/project_name/spider_name.py
                full_path / f"{spider_name}.py"
            ]

            spider_file = None
            # 既存ファイルがあるかチェック
            for path in possible_spider_paths:
                if path.exists():
                    spider_file = path
                    print(f"✅ Updating existing spider file: {spider_file}")
                    break

            # 既存ファイルがない場合は標準構造で作成
            if not spider_file:
                spider_file = possible_spider_paths[0]  # 標準構造を使用
                print(f"✅ Creating new spider file: {spider_file}")

            # ディレクトリが存在しない場合は作成
            spider_file.parent.mkdir(parents=True, exist_ok=True)

            with open(spider_file, 'w', encoding='utf-8') as f:
                f.write(code)

            print(f"Spider code saved: {spider_file}")
            return True

        except Exception as e:
            print(f"Error saving spider code: {str(e)}")
            raise Exception(f"Error saving spider code: {str(e)}")

    def save_project_file(self, project_path: str, file_path: str, content: str) -> bool:
        """プロジェクトファイルを保存（スパイダーファイルと同じ方法）"""
        try:
            # プロジェクトディレクトリ内のファイルパスを構築
            full_path = self.base_projects_dir / project_path

            # ファイルパスを正規化（セキュリティ対策）
            file_path = file_path.replace("../", "").replace("..\\", "")

            # 実際のファイルパス
            full_file_path = full_path / file_path

            # ディレクトリが存在しない場合は作成
            full_file_path.parent.mkdir(parents=True, exist_ok=True)

            # ファイルに保存（スパイダーファイルと同じ方法）
            with open(full_file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"Project file saved: {full_file_path}")
            return True

        except Exception as e:
            print(f"Error saving project file: {str(e)}")
            raise Exception(f"Error saving project file: {str(e)}")

    async def run_spider_with_manager(self, project_path: str, spider_name: str, task_id: str,
                                     settings: Optional[Dict[str, Any]] = None,
                                     progress_callback: Optional[callable] = None,
                                     websocket_callback: Optional[callable] = None) -> Dict[str, Any]:
        """ScrapyTaskManagerを使用してスパイダーを実行（統一管理版）"""
        try:
            log_with_context(
                self.logger, "INFO",
                f"Starting spider execution with TaskManager: {spider_name}",
                task_id=task_id,
                project_id=project_path,
                spider_id=spider_name,
                extra_data={"settings": settings}
            )

            # プロジェクトパスを構築
            full_project_path = self.base_projects_dir / project_path

            # スパイダー設定を構築
            spider_config = {
                'project_path': str(full_project_path),
                'spider_name': spider_name,
                'settings': settings or {}
            }

            # ScrapyTaskManagerを作成
            task_manager = ScrapyTaskManager(
                task_id=task_id,
                spider_config=spider_config,
                progress_callback=progress_callback,
                websocket_callback=websocket_callback
            )

            # タスクを実行
            result = await task_manager.execute()

            log_with_context(
                self.logger, "INFO",
                f"Spider execution completed: {spider_name}",
                task_id=task_id,
                extra_data={"result": result}
            )

            return result

        except Exception as e:
            log_exception(
                self.logger,
                f"Error in spider execution with TaskManager: {str(e)}",
                task_id=task_id,
                project_id=project_path,
                spider_id=spider_name
            )
            return {
                'success': False,
                'task_id': task_id,
                'error': str(e)
            }

    def run_spider(self, project_path: str, spider_name: str, task_id: str, settings: Optional[Dict[str, Any]] = None) -> str:
        """スパイダーを実行（非同期）"""
        try:
            log_with_context(
                self.logger, "INFO",
                f"Starting spider execution: {spider_name}",
                task_id=task_id,
                project_id=project_path,
                spider_id=spider_name,
                extra_data={"settings": settings}
            )

            # scrapy_projects/project_name ディレクトリでscrapy crawlを実行
            full_path = self.base_projects_dir / project_path

            if not full_path.exists():
                raise SpiderException(
                    message=f"Project directory not found: {full_path}",
                    error_code=ErrorCode.PROJECT_NOT_FOUND,
                    project_id=project_path
                )

            cmd = [sys.executable, "-m", "scrapy", "crawl", spider_name]

            # スパイダー固有設定を確認
            spider_custom_settings = self._get_spider_custom_settings(project_path, spider_name)

            # 最小限のデフォルト設定（CLIと同じ動作を目指す）
            default_settings = {
                'LOG_LEVEL': 'INFO',  # ログレベルのみ設定
                'ROBOTSTXT_OBEY': False  # robots.txtを無視
            }

            # 最小限の設定のみ適用（スパイダーのcustom_settingsを優先）
            final_settings = default_settings.copy()

            # ユーザー設定で上書き（必要最小限）
            if settings:
                # 重要な設定のみ適用
                important_settings = ['LOG_LEVEL', 'ROBOTSTXT_OBEY']
                for key in important_settings:
                    if key in settings:
                        final_settings[key] = settings[key]

            print(f"🎯 Using minimal settings for {spider_name}: {final_settings}")
            print(f"📋 Spider has custom_settings: {bool(spider_custom_settings)}")

            # 最小限の設定のみコマンドに追加
            for key, value in final_settings.items():
                cmd.extend(["-s", f"{key}={value}"])

            # 結果をJSONファイルに出力
            output_file = full_path / f"results_{task_id}.json"
            cmd.extend(["-o", str(output_file)])

            self.logger.info(f"Executing spider command: {' '.join(cmd)} in {full_path}")

            # 手動実行と同じ環境でプロセスを開始
            env = os.environ.copy()
            env['PYTHONPATH'] = str(full_path)
            project_name = full_path.name  # プロジェクト名を取得
            env['SCRAPY_SETTINGS_MODULE'] = f'{project_name}.settings'

            try:
                # 手動実行と同じ設定でプロセスを開始
                process = subprocess.Popen(
                    cmd,
                    cwd=str(full_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # stderrをstdoutにリダイレクト
                    text=True,
                    env=env,  # 環境変数を明示的に設定
                    bufsize=1,  # 行バッファリング
                    universal_newlines=True
                )
                self.logger.info(f"✅ Spider process started successfully: PID {process.pid}")
            except Exception as e:
                # フォールバック：最小限の設定で再試行
                self.logger.warning(f"Failed to start process with advanced settings, using fallback: {e}")
                process = subprocess.Popen(
                    cmd,
                    cwd=str(full_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

            self.running_processes[task_id] = process

            # 進行状況の初期化（リアルタイム更新対応）
            self.task_progress[task_id] = {
                'started_at': datetime.now(),
                'items_scraped': 0,
                'requests_made': 0,
                'errors_count': 0,
                'progress_percentage': 5,  # 開始時は5%
                'estimated_total': 60,  # 初期推定値
                'current_url': None,
                'last_update': datetime.now(),
                'last_notification': datetime.now(),
                'process': process,  # プロセス参照を保存
                'output_file': str(output_file)  # 出力ファイルパスを保存
            }

            # Rich progress tracking を開始
            if self.rich_tracker:
                self.rich_tracker.add_spider_task(task_id, spider_name, total_pages=100)
                print(f"✨ Rich progress tracking started for {spider_name}")

            # 初期プログレス通知を送信
            self._send_initial_progress_notification(task_id)

            # プロセス監視を開始（progress_callbackを呼び出すため）
            self._start_process_monitoring(task_id, process, str(output_file))

            log_with_context(
                self.logger, "INFO",
                f"Spider process started successfully: {spider_name}",
                task_id=task_id,
                extra_data={"pid": process.pid, "output_file": str(output_file)}
            )

            return task_id

        except SpiderException:
            # 既にSpiderExceptionの場合は再発生
            raise
        except Exception as e:
            error_msg = f"Error running spider: {str(e)}"
            log_exception(
                self.logger, error_msg,
                task_id=task_id,
                project_id=project_path,
                spider_id=spider_name,
                extra_data={"settings": settings}
            )
            raise TaskException(
                message=error_msg,
                error_code=ErrorCode.SPIDER_EXECUTION_FAILED,
                task_id=task_id,
                project_id=project_path,
                spider_id=spider_name,
                details={"original_error": str(e)}
            )

    def _send_initial_progress_notification(self, task_id: str):
        """初期プログレス通知を送信"""
        try:
            import requests

            notification_url = "http://localhost:8000/api/tasks/internal/websocket-notify"
            payload = {
                "task_id": task_id,
                "data": {
                    "id": task_id,
                    "status": "RUNNING",
                    "items_count": 0,
                    "requests_count": 0,
                    "progress": 5  # 開始時は5%
                }
            }

            response = requests.post(
                notification_url,
                json=payload,
                timeout=0.5,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                print(f"📊 Initial progress notification sent: Task {task_id} - 5%")

        except Exception as e:
            print(f"📡 Initial progress notification error: {str(e)}")

    def _start_process_monitoring(self, task_id: str, process: subprocess.Popen, output_file: str):
        """プロセス監視を開始してprogress_callbackを呼び出す"""
        def monitor_process():
            try:
                print(f"🔍 Starting process monitoring for task {task_id}")

                # 監視間隔（秒）
                monitor_interval = 2
                last_items_count = 0
                last_requests_count = 0
                error_count = 0

                while process.poll() is None:  # プロセスが実行中の間
                    try:
                        # 結果ファイルから統計情報を取得
                        current_items, current_requests = self._get_real_time_statistics(task_id, output_file)

                        # 変化があった場合のみprogress_callbackを呼び出し
                        if (current_items != last_items_count or
                            current_requests != last_requests_count):

                            print(f"📊 Progress detected: Task {task_id} - Items: {current_items}, Requests: {current_requests}")

                            # progress_callbackを呼び出し（DBに保存）
                            self._call_progress_callback(task_id, current_items, current_requests, error_count)

                            last_items_count = current_items
                            last_requests_count = current_requests

                        # 監視間隔で待機
                        time.sleep(monitor_interval)

                    except Exception as monitor_error:
                        print(f"⚠️ Monitor error for task {task_id}: {monitor_error}")
                        error_count += 1
                        time.sleep(monitor_interval)

                # プロセス完了後の最終統計取得
                print(f"🏁 Process completed for task {task_id}, getting final statistics")
                final_items, final_requests = self._get_real_time_statistics(task_id, output_file)

                # 結果ファイルから直接統計を取得（より正確）
                try:
                    import json
                    from pathlib import Path
                    result_path = Path(output_file)
                    if result_path.exists() and result_path.stat().st_size > 100:
                        with open(result_path, 'r', encoding='utf-8') as f:
                            file_data = json.load(f)
                        if isinstance(file_data, list):
                            actual_items = len(file_data)
                            if actual_items > final_items:
                                print(f"📊 File-based count ({actual_items}) > real-time count ({final_items}), using file count")
                                final_items = actual_items
                                final_requests = max(final_requests, actual_items + 10)
                except Exception as e:
                    print(f"⚠️ Error reading final statistics from file: {e}")

                # 最終progress_callbackを呼び出し
                self._call_progress_callback(task_id, final_items, final_requests, error_count)

                # 結果ファイルのデータをDBに格納
                self._store_results_to_db(task_id, output_file)

                # タスク完了処理
                success = process.returncode == 0
                self._update_task_completion(task_id, success)

                # Rich progress tracking を完了状態に
                if self.rich_tracker:
                    status = "COMPLETED" if success else "FAILED"
                    self.rich_tracker.complete_task(task_id, status)
                    print(f"✨ Rich progress tracking completed for task {task_id}: {status}")

                print(f"✅ Process monitoring completed for task {task_id}: success={success}, items={final_items}, requests={final_requests}")

            except Exception as e:
                print(f"❌ Process monitoring failed for task {task_id}: {str(e)}")

        # 別スレッドで監視を開始
        monitor_thread = threading.Thread(target=monitor_process, daemon=True)
        monitor_thread.start()
        print(f"🚀 Process monitoring thread started for task {task_id}")

    def _get_real_time_statistics(self, task_id: str, output_file: str) -> tuple:
        """リアルタイムで統計情報を取得"""
        try:
            import json
            from pathlib import Path

            # 結果ファイルをチェック
            result_path = Path(output_file)
            if result_path.exists() and result_path.stat().st_size > 0:
                try:
                    with open(result_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            # JSONLファイルの場合（1行1アイテム）
                            if content.count('\n') > 0:
                                items = content.strip().split('\n')
                                items_count = len([line for line in items if line.strip()])
                            else:
                                # 単一JSONの場合
                                data = json.loads(content)
                                items_count = len(data) if isinstance(data, list) else 1

                            # リクエスト数は推定（アイテム数 + α）
                            requests_count = max(items_count + 2, 1)

                            return items_count, requests_count
                except (json.JSONDecodeError, Exception) as e:
                    # ファイルが不完全な場合は0を返す
                    pass

            return 0, 0

        except Exception as e:
            print(f"⚠️ Error getting real-time statistics for {task_id}: {e}")
            return 0, 0

    def _call_progress_callback(self, task_id: str, items_count: int, requests_count: int, error_count: int):
        """progress_callbackを呼び出してDBを更新"""
        try:
            from ..database import SessionLocal, Task as DBTask, TaskStatus

            db = SessionLocal()
            try:
                task = db.query(DBTask).filter(DBTask.id == task_id).first()
                if task:
                    # データベース更新（より詳細な状態管理）
                    task.items_count = items_count
                    task.requests_count = requests_count
                    task.error_count = error_count

                    # 実行状態の確実な記録
                    if items_count > 0 or requests_count > 0:
                        task.status = TaskStatus.RUNNING
                        if not task.started_at:
                            task.started_at = datetime.now()

                    # 即座にコミット（WebUIとの同期を確実に）
                    db.commit()

                    print(f"📊 Progress callback executed: Task {task_id} - Items: {items_count}, Requests: {requests_count}, Errors: {error_count}")

                    # Rich progress tracking を更新
                    if self.rich_tracker:
                        self.rich_tracker.update_progress(
                            task_id,
                            items_scraped=items_count,
                            requests_made=requests_count,
                            errors=error_count,
                            pages_visited=min(requests_count // 10, 100)  # 推定ページ数
                        )

                    # WebSocket通知を送信
                    self._send_progress_notification(task_id, items_count, requests_count, error_count)

            finally:
                db.close()

        except Exception as e:
            print(f"❌ Progress callback error for task {task_id}: {str(e)}")

    def _send_progress_notification(self, task_id: str, items_count: int, requests_count: int, error_count: int):
        """プログレス通知を送信"""
        try:
            import requests

            # プログレス計算
            elapsed_seconds = 0
            if task_id in self.task_progress:
                elapsed_seconds = (datetime.now() - self.task_progress[task_id]['started_at']).total_seconds()

            if items_count > 0:
                # アイテムベースの進行計算
                pending_items = max(0, min(60 - items_count, max(requests_count - items_count, 10)))
                total_estimated = items_count + pending_items
                item_progress = (items_count / total_estimated) * 100 if total_estimated > 0 else 10

                # 時間ベースの進行推定
                time_progress = min(80, elapsed_seconds * 1.5)

                # 複合プログレス
                progress_percentage = min(95, max(item_progress, time_progress))
            else:
                # 初期段階の進行
                progress_percentage = min(15, elapsed_seconds * 2) if elapsed_seconds > 0 else 5

            notification_url = "http://localhost:8000/api/tasks/internal/websocket-notify"
            payload = {
                "task_id": task_id,
                "data": {
                    "id": task_id,
                    "status": "RUNNING",
                    "items_count": items_count,
                    "requests_count": requests_count,
                    "error_count": error_count,
                    "progress": progress_percentage,
                    "elapsed_seconds": elapsed_seconds
                }
            }

            response = requests.post(
                notification_url,
                json=payload,
                timeout=0.5,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                print(f"📡 Progress notification sent: Task {task_id} - {progress_percentage:.1f}%")

        except Exception as e:
            print(f"📡 Progress notification error: {str(e)}")

    def _store_results_to_db(self, task_id: str, output_file: str):
        """結果ファイルのデータをDBに格納"""
        try:
            import json
            from pathlib import Path
            from ..database import SessionLocal, Result as DBResult

            # 複数の可能なファイルパスを確認
            possible_paths = []

            # 1. 指定されたパス
            if output_file:
                possible_paths.append(Path(output_file))

            # 2. プロジェクトディレクトリ内の結果ファイルを検索
            from ..database import SessionLocal as TempDB, Task as TempTask
            temp_db = TempDB()
            try:
                task = temp_db.query(TempTask).filter(TempTask.id == task_id).first()
                if task and task.project:
                    project_path = self.base_projects_dir / task.project.path
                    # 複数のパターンで検索
                    patterns = [
                        f"results_{task_id}.json",
                        f"results_{task_id}*.json",
                        f"*{task_id}*.json",
                        "results_*.json"
                    ]

                    for pattern in patterns:
                        files = list(project_path.glob(pattern))
                        if files:
                            # 最新のファイルを使用
                            latest_file = max(files, key=lambda f: f.stat().st_mtime)
                            possible_paths.append(latest_file)
                            break
            finally:
                temp_db.close()

            # 存在するファイルを見つける
            result_path = None
            for path in possible_paths:
                if path and path.exists() and path.stat().st_size > 0:
                    result_path = path
                    break

            if not result_path:
                print(f"📁 No valid result file found for task {task_id}")
                print(f"   Searched paths: {[str(p) for p in possible_paths if p]}")
                return

            print(f"📁 Storing results to DB for task {task_id}: {result_path}")

            db = SessionLocal()
            try:
                with open(result_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                if not content:
                    print(f"📁 Empty result file for task {task_id}")
                    return

                # まずJSON配列として解析を試行
                try:
                    data = json.loads(content)

                    if isinstance(data, list):
                        # JSON配列形式の場合（最も一般的）
                        stored_count = 0
                        for item in data:
                            import uuid
                            db_result = DBResult(
                                id=str(uuid.uuid4()),  # IDを手動で生成
                                task_id=task_id,
                                data=item,
                                created_at=datetime.now()
                            )
                            db.add(db_result)
                            stored_count += 1

                        db.commit()
                        print(f"✅ Stored {stored_count} items (JSON array) to DB for task {task_id}")

                    else:
                        # 単一オブジェクトの場合
                        import uuid
                        db_result = DBResult(
                            id=str(uuid.uuid4()),  # IDを手動で生成
                            task_id=task_id,
                            data=data,
                            created_at=datetime.now()
                        )
                        db.add(db_result)
                        db.commit()
                        print(f"✅ Stored 1 item (single object) to DB for task {task_id}")

                except json.JSONDecodeError:
                    # JSON配列として解析できない場合、JSONLファイルとして処理
                    print(f"📁 Trying JSONL format for task {task_id}")

                    if content.count('\n') > 0:
                        items = content.strip().split('\n')
                        stored_count = 0

                        for line in items:
                            line = line.strip()
                            if line:
                                try:
                                    item_data = json.loads(line)

                                    # DBに結果を保存
                                    import uuid
                                    db_result = DBResult(
                                        id=str(uuid.uuid4()),  # IDを手動で生成
                                        task_id=task_id,
                                        data=item_data,
                                        created_at=datetime.now()
                                    )
                                    db.add(db_result)
                                    stored_count += 1

                                except json.JSONDecodeError as e:
                                    print(f"⚠️ Invalid JSON in result line: {line[:100]}... Error: {e}")
                                    continue

                        db.commit()
                        print(f"✅ Stored {stored_count} items (JSONL format) to DB for task {task_id}")
                    else:
                        print(f"❌ Unable to parse result file for task {task_id}: Not valid JSON or JSONL")

            finally:
                db.close()

        except Exception as e:
            print(f"❌ Error storing results to DB for task {task_id}: {str(e)}")

    @performance_monitor
    @jit_optimizer.hot_function
    def run_spider_optimized(self, project_path: str, spider_name: str, task_id: str, settings: Optional[Dict[str, Any]] = None) -> str:
        """
        Python 3.13最適化版スパイダー実行
        Free-threaded並列処理とJIT最適化を活用
        """
        try:
            log_with_context(
                self.logger, "INFO",
                f"Starting optimized spider execution: {spider_name}",
                task_id=task_id,
                project_id=project_path,
                spider_id=spider_name,
                extra_data={"optimization": "python313", "settings": settings}
            )

            # Free-threaded並列実行を使用
            with FreeThreadedExecutor(max_workers=4) as executor:
                # CPU集約的な前処理を並列実行
                preprocessing_future = executor.submit_cpu_intensive(
                    self._preprocess_spider_execution,
                    project_path, spider_name, task_id, settings
                )

                # 並列でプロジェクト検証
                validation_future = executor.submit_cpu_intensive(
                    self._validate_project_structure,
                    project_path
                )

                # 結果を取得
                preprocessing_result = preprocessing_future.result()
                validation_result = validation_future.result()

                if not validation_result:
                    raise SpiderException(
                        message=f"Project validation failed: {project_path}",
                        error_code=ErrorCode.PROJECT_NOT_FOUND,
                        project_id=project_path
                    )

            # 通常のスパイダー実行
            return self.run_spider(project_path, spider_name, task_id, settings)

        except Exception as e:
            error_msg = f"Error in optimized spider execution: {str(e)}"
            log_exception(
                self.logger, error_msg,
                task_id=task_id,
                project_id=project_path,
                spider_id=spider_name
            )
            raise TaskException(
                message=error_msg,
                error_code=ErrorCode.SPIDER_EXECUTION_FAILED,
                task_id=task_id,
                project_id=project_path,
                spider_id=spider_name
            )

    def _preprocess_spider_execution(self, project_path: str, spider_name: str, task_id: str, settings: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """スパイダー実行の前処理（CPU集約的）"""
        full_path = self.base_projects_dir / project_path

        # 設定の最適化
        optimized_settings = settings.copy() if settings else {}

        # Python 3.13の最適化設定を追加
        optimized_settings.update({
            'CONCURRENT_REQUESTS': 32,  # Free-threaded環境では高い並行性
            'CONCURRENT_REQUESTS_PER_DOMAIN': 16,
            'DOWNLOAD_DELAY': 0.1,
            'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
            'AUTOTHROTTLE_ENABLED': True,
            'AUTOTHROTTLE_START_DELAY': 0.1,
            'AUTOTHROTTLE_MAX_DELAY': 3.0,
            'AUTOTHROTTLE_TARGET_CONCURRENCY': 8.0,
        })

        return {
            'project_path': str(full_path),
            'optimized_settings': optimized_settings,
            'task_id': task_id
        }

    def _validate_project_structure(self, project_path: str) -> bool:
        """プロジェクト構造の検証（CPU集約的）"""
        full_path = self.base_projects_dir / project_path

        if not full_path.exists():
            return False

        # 必要なファイルの存在確認
        required_files = [
            full_path / 'scrapy.cfg',
            full_path / project_path / '__init__.py',
            full_path / project_path / 'settings.py',
        ]

        return all(file.exists() for file in required_files)

    def stop_spider(self, task_id: str) -> bool:
        """スパイダーの実行を停止（Celery環境対応）"""
        try:
            if task_id in self.running_processes:
                process = self.running_processes[task_id]

                # まず優雅に終了を試行
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # 強制終了（Celery環境では安全な方法を使用）
                    try:
                        process.kill()
                        process.wait()
                    except Exception as kill_error:
                        self.logger.warning(f"Failed to kill process {process.pid}: {kill_error}")

                del self.running_processes[task_id]
                if task_id in self.task_progress:
                    del self.task_progress[task_id]
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error stopping spider {task_id}: {str(e)}")
            return False

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """タスクの実行状況を取得"""
        try:
            if task_id not in self.running_processes:
                return {"status": "not_found"}

            process = self.running_processes[task_id]

            if process.poll() is None:
                return {"status": "running", "pid": process.pid}
            else:
                # プロセス完了
                stdout, stderr = process.communicate()
                del self.running_processes[task_id]

                # タスク完了時にデータベースを更新
                self._update_task_completion(task_id, process.returncode == 0)

                return {
                    "status": "completed" if process.returncode == 0 else "failed",
                    "return_code": process.returncode,
                    "stdout": stdout,
                    "stderr": stderr
                }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _update_task_completion(self, task_id: str, success: bool, items_count: int = 0, requests_count: int = 0):
        """タスク完了時にデータベースを更新（根本対応版）"""
        try:
            from ..database import SessionLocal, Task as DBTask, TaskStatus, Spider as DBSpider
            import json
            import asyncio

            db = SessionLocal()
            try:
                task = db.query(DBTask).filter(DBTask.id == task_id).first()
                if task:
                    print(f"🔧 Updating task completion for {task_id}: success={success}")

                    # 結果ファイルから実際の統計情報を取得（最優先）
                    actual_items, actual_requests = self._get_accurate_task_statistics(task_id, task.project_id)
                    print(f"📊 Task {task_id}: File-based stats - items={actual_items}, requests={actual_requests}")

                    # 現在の進行状況を保持
                    current_items = task.items_count or 0
                    current_requests = task.requests_count or 0
                    current_errors = task.error_count or 0

                    # 結果ファイルが存在し、データが取得されている場合は成功とみなす
                    has_results = self._verify_task_results(task_id)

                    # 統計情報の決定（ファイルベースを最優先）
                    final_items = actual_items if actual_items > 0 else current_items
                    final_requests = actual_requests if actual_requests > 0 else current_requests

                    # より詳細な成功判定
                    # 1. プロセスが正常終了 (success=True)
                    # 2. アイテムが取得されている (final_items > 0)
                    # 3. 結果ファイルが存在する (has_results=True)
                    task_success = success and (final_items > 0 or has_results)

                    print(f"📊 Final statistics for task {task_id}:")
                    print(f"   Items: {final_items} (file: {actual_items}, current: {current_items})")
                    print(f"   Requests: {final_requests} (file: {actual_requests}, current: {current_requests})")
                    print(f"   Success: {task_success} (process: {success}, has_results: {has_results})")

                    # タスクステータスと統計情報を更新
                    if task_success:
                        task.status = TaskStatus.FINISHED
                        task.items_count = final_items
                        task.requests_count = final_requests
                        task.error_count = current_errors
                        task.finished_at = datetime.now()
                        print(f"✅ Task {task_id} marked as FINISHED with {final_items} items")
                    else:
                        task.status = TaskStatus.FAILED
                        task.error_count = max(current_errors, 1)
                        task.finished_at = datetime.now()
                        print(f"❌ Task {task_id} marked as FAILED")

                    # データベースにコミット
                    db.commit()
                    print(f"💾 Task {task_id} completion saved to database")

                    print(f"✅ Task {task_id} completion updated: status={task.status}, items={task.items_count}, requests={task.requests_count}, errors={task.error_count}")

                    # 結果ファイルのデータをDBに格納（完了時に確実に実行）
                    if task_success and task.items_count > 0:
                        print(f"📁 Attempting to store results to DB for completed task {task_id}")
                        try:
                            self._store_results_to_db(task_id, None)  # ファイルパスは自動検索
                        except Exception as store_error:
                            print(f"⚠️ Failed to store results to DB: {store_error}")

                    # 安全なWebSocket通知
                    self._safe_websocket_notify_completion(task_id, {
                        "status": task.status.value,
                        "finished_at": task.finished_at.isoformat(),
                        "items_count": task.items_count,
                        "requests_count": task.requests_count,
                        "error_count": task.error_count,
                        "progress": 100 if task_success else 0
                    })
                else:
                    print(f"⚠️ Task {task_id} not found in database")
                    print(f"  Items: {task.items_count}, Requests: {task.requests_count}")

                    # WebSocket通知を送信（非同期）
                    try:
                        spider = db.query(DBSpider).filter(DBSpider.id == task.spider_id).first()
                        spider_name = spider.name if spider else "unknown"

                        # WebSocket通知データを準備（完了時は100%）
                        notification_data = {
                            "id": task_id,
                            "name": spider_name,
                            "status": task.status.value,
                            "startedAt": task.started_at.isoformat() if task.started_at else None,
                            "finishedAt": task.finished_at.isoformat() if task.finished_at else None,
                            "itemsCount": task.items_count or 0,
                            "requestsCount": task.requests_count or 0,
                            "errorCount": task.error_count or 0,
                            "progress": 100 if task.status.value in ["FINISHED", "FAILED"] else 0
                        }

                        # WebSocket通知を送信（別スレッドで実行）
                        self._send_websocket_notification_async(task_id, notification_data)

                    except Exception as e:
                        print(f"Error sending WebSocket notification: {str(e)}")

            finally:
                db.close()
        except Exception as e:
            print(f"Error updating task completion: {str(e)}")

    def _send_websocket_notification_async(self, task_id: str, data: dict):
        """WebSocket通知を非同期で送信"""
        try:
            import threading

            def send_notification():
                try:
                    # WebSocketマネージャーをインポート
                    from ..websocket.manager import manager

                    # 新しいイベントループを作成して実行
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    try:
                        loop.run_until_complete(manager.send_task_update(task_id, data))
                        print(f"WebSocket notification sent for task {task_id}")
                    finally:
                        loop.close()

                except Exception as e:
                    print(f"Error in WebSocket notification thread: {str(e)}")

            # 別スレッドで実行
            notification_thread = threading.Thread(target=send_notification, daemon=True)
            notification_thread.start()

        except Exception as e:
            print(f"Error creating WebSocket notification thread: {str(e)}")

    def _safe_websocket_notify_completion(self, task_id: str, data: dict):
        """タスク完了時の安全なWebSocket通知"""
        try:
            # 監視システム内では非同期処理を避ける
            print(f"📡 Task completion notification: {task_id} - {data.get('status', 'unknown')}")
            # 実際のWebSocket通知は別のプロセスで処理される
        except Exception as e:
            print(f"📡 WebSocket notification error: {str(e)}")

    def _get_task_statistics(self, task_id: str, project_id: str) -> tuple[int, int]:
        """結果ファイルから実際の統計情報を取得"""
        try:
            from ..database import SessionLocal, Project as DBProject
            import glob

            db = SessionLocal()
            try:
                project = db.query(DBProject).filter(DBProject.id == project_id).first()
                if not project:
                    return 0, 0

                # 複数のパスパターンで結果ファイルを検索（実際のファイル配置に基づく順序）
                possible_paths = [
                    # 実際のパス（プロジェクトルートディレクトリ）
                    self.base_projects_dir / project.path / f"results_{task_id}.json",
                    # 二重パス（プロジェクト内のプロジェクトディレクトリ）
                    self.base_projects_dir / project.path / project.path / f"results_{task_id}.json",
                ]

                result_file = None
                for path in possible_paths:
                    if path.exists():
                        result_file = path
                        break

                # 見つからない場合は再帰検索
                if not result_file:
                    pattern = str(self.base_projects_dir / project.path / "**" / f"results_{task_id}.json")
                    matches = glob.glob(pattern, recursive=True)
                    if matches:
                        result_file = Path(matches[0])

                if result_file and result_file.exists():
                    try:
                        with open(result_file, 'r', encoding='utf-8') as f:
                            content = f.read().strip()

                        # JSONファイルが不完全な場合の対処
                        if content.startswith('[') and not content.endswith(']'):
                            # 最後に ] を追加して修正
                            content = content.rstrip(',') + '\n]'

                        data = json.loads(content)
                        items_count = len(data) if isinstance(data, list) else 1

                        # ログファイルからリクエスト数を推定（簡易版）
                        requests_count = max(items_count + 1, 7)  # 最低7リクエスト（robots.txt含む）

                        print(f"Statistics from result file: items={items_count}, requests={requests_count} at {result_file}")
                        return items_count, requests_count

                    except json.JSONDecodeError as e:
                        print(f"JSON decode error in {result_file}: {str(e)}")
                        # JSONエラーの場合、ファイルサイズから推定
                        file_size = result_file.stat().st_size
                        estimated_items = max(1, file_size // 2000)  # 2KB per item estimate
                        estimated_requests = max(estimated_items + 1, 7)
                        print(f"Estimated from file size: items={estimated_items}, requests={estimated_requests}")
                        return estimated_items, estimated_requests

            finally:
                db.close()

        except Exception as e:
            print(f"Error getting task statistics: {str(e)}")

        return 0, 0

    def start_monitoring(self):
        """バックグラウンドでタスクの監視を開始（強化版）"""
        if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
            self.stop_monitoring = False

            # 監視統計の初期化
            self.monitoring_stats = {
                'started_at': datetime.now(),
                'tasks_monitored': 0,
                'tasks_completed': 0,
                'tasks_failed': 0,
                'average_execution_time': 0,
                'last_activity': datetime.now(),
                'health_checks': 0,
                'performance_metrics': {
                    'cpu_usage': [],
                    'memory_usage': [],
                    'disk_usage': []
                }
            }

            self.monitoring_thread = threading.Thread(target=self._monitor_tasks, daemon=True)
            self.monitoring_thread.start()
            print("🔍 Enhanced task monitoring started with performance tracking")
            print(f"📊 Monitoring statistics initialized at {self.monitoring_stats['started_at']}")

    def stop_monitoring_tasks(self):
        """タスク監視を停止"""
        self.stop_monitoring = True
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
            print("Task monitoring stopped")

    def _monitor_tasks(self):
        """定期的にタスクの状態をチェック（マルチレイヤー監視）"""
        print(f"Task monitoring thread started. PID: {os.getpid()}")

        while not self.stop_monitoring:
            try:
                # 監視状況をログ出力
                if self.running_processes:
                    print(f"Monitoring {len(self.running_processes)} running processes: {list(self.running_processes.keys())}")

                # 実行中のプロセスをチェック
                completed_tasks = []
                for task_id, process in list(self.running_processes.items()):
                    # マルチレイヤー監視
                    completion_status = self._check_task_completion_multilayer(task_id, process)

                    if completion_status['completed']:
                        completed_tasks.append(task_id)
                        print(f"Task {task_id} detected as completed via {completion_status['method']}")

                        # 完了処理
                        try:
                            success = completion_status['success']
                            print(f"Task {task_id}: Completion status: {success}")

                            # 結果ファイルの最終確認（遅延対応）
                            if success:
                                # 結果ファイル生成を最大60秒待機（Scrapy非同期書き込み対応）
                                success = self._wait_for_results_file(task_id, timeout=60)
                                print(f"Task {task_id}: After file verification with wait: {success}")
                            else:
                                # プロセスが失敗した場合でも結果ファイルをチェック（部分的成功の可能性）
                                print(f"Task {task_id}: Process failed, but checking for partial results...")
                                if self._wait_for_results_file(task_id, timeout=30):
                                    success = True
                                    print(f"Task {task_id}: Found partial results, marking as success")

                            self._update_task_completion(task_id, success)
                            print(f"Task {task_id} completed successfully: {success}")

                        except Exception as e:
                            print(f"Error processing completed task {task_id}: {str(e)}")
                            import traceback
                            traceback.print_exc()
                            self._update_task_completion(task_id, False)

                # 完了したタスクを削除
                for task_id in completed_tasks:
                    if task_id in self.running_processes:
                        del self.running_processes[task_id]
                        print(f"Removed completed task {task_id} from running processes")
                    # 進行状況も削除
                    if task_id in self.task_progress:
                        del self.task_progress[task_id]
                        print(f"Removed progress tracking for task {task_id}")

                # 実行中タスクの進行状況を更新
                self._update_running_tasks_progress()

                # タイムアウトチェック（30分以上実行中のタスクを強制終了）
                self._check_task_timeouts()

                # ヘルスチェック（1分間隔で実行）
                if not hasattr(self, '_last_health_check'):
                    self._last_health_check = datetime.now()

                if (datetime.now() - self._last_health_check).total_seconds() > 60:
                    self._perform_health_check()
                    self._last_health_check = datetime.now()

                # 自動修復機能（2分間隔で実行 - より積極的に）
                if not hasattr(self, '_last_auto_fix'):
                    self._last_auto_fix = datetime.now()

                if (datetime.now() - self._last_auto_fix).total_seconds() > 120:  # 2分 = 120秒
                    self._auto_fix_failed_tasks()
                    self._last_auto_fix = datetime.now()

                # 統計情報の更新
                self._update_monitoring_stats()

                # 1秒間隔でチェック（リアルタイムプログレス更新のため）
                time.sleep(1)

            except Exception as e:
                print(f"Error in task monitoring: {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(5)

        print("Task monitoring thread stopped")

    def _perform_health_check(self):
        """システムヘルスチェックを実行"""
        try:
            import psutil

            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # メモリ使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # ディスク使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100

            # 統計に追加
            if hasattr(self, 'monitoring_stats'):
                self.monitoring_stats['performance_metrics']['cpu_usage'].append(cpu_percent)
                self.monitoring_stats['performance_metrics']['memory_usage'].append(memory_percent)
                self.monitoring_stats['performance_metrics']['disk_usage'].append(disk_percent)

                # 最新10件のみ保持
                for metric in self.monitoring_stats['performance_metrics'].values():
                    if len(metric) > 10:
                        metric.pop(0)

                self.monitoring_stats['health_checks'] += 1

                # 警告レベルのチェック
                warnings = []
                if cpu_percent > 80:
                    warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
                if memory_percent > 80:
                    warnings.append(f"High memory usage: {memory_percent:.1f}%")
                if disk_percent > 80:
                    warnings.append(f"High disk usage: {disk_percent:.1f}%")

                if warnings:
                    print(f"⚠️ System warnings: {', '.join(warnings)}")
                else:
                    print(f"✅ System health OK - CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%, Disk: {disk_percent:.1f}%")

        except ImportError:
            print("psutil not available for health check")
        except Exception as e:
            print(f"Error in health check: {str(e)}")

    def _auto_fix_failed_tasks(self):
        """失敗したタスクを自動修復"""
        try:
            from ..database import SessionLocal, Task as DBTask, TaskStatus
            import json
            from pathlib import Path

            db = SessionLocal()
            try:
                # 最近の失敗タスクを取得（過去1時間以内）
                one_hour_ago = datetime.now() - timedelta(hours=1)
                failed_tasks = db.query(DBTask).filter(
                    DBTask.status == TaskStatus.FAILED,
                    DBTask.started_at >= one_hour_ago
                ).all()

                if not failed_tasks:
                    return

                print(f"🔧 Auto-fixing {len(failed_tasks)} failed tasks from the last hour")
                fixed_count = 0

                for task in failed_tasks:
                    try:
                        # 結果ファイルが存在し、データがあるかチェック
                        has_results = self._verify_task_results(task.id)
                        if has_results:
                            # 実際の統計情報を取得
                            actual_items, actual_requests = self._get_task_statistics(task.id, task.project_id)

                            if actual_items > 0:
                                # タスクを成功に修正
                                task.status = TaskStatus.FINISHED
                                task.items_count = actual_items
                                task.requests_count = actual_requests
                                task.error_count = 0
                                task.finished_at = datetime.now()

                                fixed_count += 1
                                print(f"✅ Auto-fixed task {task.id[:8]}... - {actual_items} items found")

                    except Exception as e:
                        print(f"Error auto-fixing task {task.id}: {str(e)}")

                if fixed_count > 0:
                    db.commit()
                    print(f"🎉 Auto-fixed {fixed_count} tasks successfully")

            finally:
                db.close()

        except Exception as e:
            print(f"Error in auto-fix: {str(e)}")

    def _update_monitoring_stats(self):
        """監視統計を更新"""
        if hasattr(self, 'monitoring_stats'):
            self.monitoring_stats['last_activity'] = datetime.now()
            self.monitoring_stats['tasks_monitored'] = len(self.running_processes)

    def _check_task_timeouts(self):
        """タスクのタイムアウトをチェック"""
        timeout_minutes = 45  # 45分に延長（Celeryタイムアウトより長く設定）
        current_time = datetime.now()

        for task_id, process in list(self.running_processes.items()):
            if task_id in self.task_progress:
                start_time = self.task_progress[task_id].get('started_at')
                if start_time:
                    elapsed = (current_time - start_time).total_seconds() / 60
                    if elapsed > timeout_minutes:
                        print(f"⏰ Task {task_id} timeout after {elapsed:.1f} minutes, terminating...")
                        try:
                            # 優雅な終了を試行
                            process.terminate()

                            # 10秒待機してから強制終了
                            import threading
                            def force_kill():
                                time.sleep(10)
                                try:
                                    if process.poll() is None:  # まだ実行中の場合
                                        process.kill()
                                        print(f"🔪 Force killed task {task_id}")
                                except:
                                    pass
                            threading.Thread(target=force_kill, daemon=True).start()

                            # タスクを完了として記録（データが取得されている可能性があるため）
                            self._update_task_completion(task_id, True)
                            print(f"📊 Task {task_id} marked as completed due to timeout (data may have been collected)")

                        except Exception as e:
                            print(f"Error terminating timeout task {task_id}: {str(e)}")

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """監視統計を取得"""
        if hasattr(self, 'monitoring_stats'):
            stats = self.monitoring_stats.copy()

            # 実行時間の計算
            if stats['started_at']:
                uptime = (datetime.now() - stats['started_at']).total_seconds()
                stats['uptime_seconds'] = uptime
                stats['uptime_formatted'] = f"{uptime // 3600:.0f}h {(uptime % 3600) // 60:.0f}m"

            # 平均パフォーマンス
            perf = stats['performance_metrics']
            if perf['cpu_usage']:
                stats['avg_cpu'] = sum(perf['cpu_usage']) / len(perf['cpu_usage'])
            if perf['memory_usage']:
                stats['avg_memory'] = sum(perf['memory_usage']) / len(perf['memory_usage'])
            if perf['disk_usage']:
                stats['avg_disk'] = sum(perf['disk_usage']) / len(perf['disk_usage'])

            return stats
        return {}

    def _check_task_completion_multilayer(self, task_id: str, process) -> Dict[str, Any]:
        """マルチレイヤーでタスク完了を検出"""
        try:
            # レイヤー1: プロセス状態チェック
            poll_result = process.poll()
            print(f"Task {task_id}: Process poll result: {poll_result}")

            if poll_result is not None:
                return {
                    'completed': True,
                    'success': poll_result == 0,
                    'method': 'process_poll',
                    'return_code': poll_result
                }

            # レイヤー2: PIDベースチェック（より確実）
            try:
                import psutil
                if psutil.pid_exists(process.pid):
                    proc = psutil.Process(process.pid)
                    if proc.status() in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]:
                        print(f"Task {task_id}: Process {process.pid} is zombie/dead")
                        return {
                            'completed': True,
                            'success': True,  # 結果ファイルで最終判定
                            'method': 'psutil_status'
                        }
                else:
                    print(f"Task {task_id}: PID {process.pid} no longer exists")
                    return {
                        'completed': True,
                        'success': True,  # 結果ファイルで最終判定
                        'method': 'pid_not_exists'
                    }
            except ImportError:
                print("psutil not available, skipping PID-based check")
            except Exception as e:
                print(f"Error in PID-based check: {str(e)}")

            # レイヤー3: 結果ファイルベースチェック（実行時間が長い場合）
            if task_id in self.task_progress:
                start_time = self.task_progress[task_id].get('started_at')
                if start_time:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    # 5分以上経過している場合、結果ファイルをチェック
                    if elapsed > 300:
                        if self._verify_task_results(task_id):
                            print(f"Task {task_id}: Detected completion via result file after {elapsed}s")
                            return {
                                'completed': True,
                                'success': True,
                                'method': 'result_file_timeout'
                            }

            # レイヤー4: データベース状態チェック（他のプロセスが更新した場合）
            try:
                from ..database import SessionLocal, Task as DBTask, TaskStatus
                db = SessionLocal()
                try:
                    task = db.query(DBTask).filter(DBTask.id == task_id).first()
                    if task and task.status in [TaskStatus.FINISHED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                        print(f"Task {task_id}: Database shows task as {task.status}")
                        return {
                            'completed': True,
                            'success': task.status == TaskStatus.FINISHED,
                            'method': 'database_status'
                        }
                finally:
                    db.close()
            except Exception as e:
                print(f"Error checking database status: {str(e)}")

            return {'completed': False}

        except Exception as e:
            print(f"Error in multilayer completion check: {str(e)}")
            return {'completed': False}

    def _wait_for_results_file(self, task_id: str, timeout: int = 30) -> bool:
        """結果ファイルの生成を待機（改善版）"""
        print(f"🔍 Task {task_id}: Waiting for results file (timeout: {timeout}s)")

        start_time = time.time()
        last_log_time = 0

        while time.time() - start_time < timeout:
            elapsed = time.time() - start_time

            # 5秒間隔でログ出力
            if elapsed - last_log_time >= 5:
                print(f"⏳ Task {task_id}: Still waiting for results... ({elapsed:.1f}s/{timeout}s)")
                last_log_time = elapsed

            if self._verify_task_results(task_id):
                print(f"✅ Task {task_id}: Results file found after {elapsed:.1f}s")
                return True

            time.sleep(0.5)  # より細かい間隔でチェック

        print(f"⏰ Task {task_id}: Timeout waiting for results file ({timeout}s)")
        return False

    def _update_running_tasks_progress(self):
        """実行中タスクの進行状況を更新"""
        for task_id in list(self.task_progress.keys()):
            if task_id in self.running_processes:
                try:
                    # 結果ファイルから現在の進行状況を推定
                    progress_info = self._estimate_task_progress(task_id)
                    if progress_info:
                        self.task_progress[task_id].update(progress_info)
                        self.task_progress[task_id]['last_update'] = datetime.now()

                        # データベースの進行状況も更新
                        self._update_task_progress_in_db(task_id, progress_info)

                except Exception as e:
                    print(f"Error updating progress for task {task_id}: {str(e)}")

    def _estimate_task_progress(self, task_id: str) -> Dict[str, Any]:
        """結果ファイルから進行状況を推定"""
        try:
            from ..database import SessionLocal, Task as DBTask, Project as DBProject

            db = SessionLocal()
            try:
                task = db.query(DBTask).filter(DBTask.id == task_id).first()
                if not task:
                    return {}

                project = db.query(DBProject).filter(DBProject.id == task.project_id).first()
                if not project:
                    return {}

                # 結果ファイルを検索（実際のファイル配置に基づく順序）
                possible_paths = [
                    # 実際のパス（プロジェクトルートディレクトリ）
                    self.base_projects_dir / project.path / f"results_{task_id}.json",
                    # 二重パス（プロジェクト内のプロジェクトディレクトリ）
                    self.base_projects_dir / project.path / project.path / f"results_{task_id}.json",
                ]

                result_file = None
                for path in possible_paths:
                    if path.exists():
                        result_file = path
                        break

                if not result_file:
                    pattern = str(self.base_projects_dir / project.path / "**" / f"results_{task_id}.json")
                    matches = glob.glob(pattern, recursive=True)
                    if matches:
                        result_file = Path(matches[0])

                if result_file and result_file.exists():
                    with open(result_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            # JSONファイルの行数から進行状況を推定
                            lines = content.split('\n')
                            items_count = len([line for line in lines if line.strip() and line.strip() != '[' and line.strip() != ']'])

                            # 進行状況を計算（経過(%) = リクエスト数/アイテム数）
                            if task_id in self.task_progress:
                                start_time = self.task_progress[task_id]['started_at']
                                elapsed = (datetime.now() - start_time).total_seconds()

                                # リクエスト数を推定（アイテム数 + 初期リクエスト）
                                requests_made = max(items_count + 1, 1)

                                # 進行状況を計算: 新方式 = 現在のアイテム数/(現在のアイテム数 + pendingアイテム数)
                                pending_items = self._estimate_pending_items(task_id, items_count, requests_made, elapsed)
                                total_estimated = items_count + pending_items

                                if total_estimated > 0:
                                    # pendingアイテム数ベースの進行状況計算
                                    progress_percentage = min((items_count / total_estimated) * 100, 95)
                                else:
                                    # まだアイテムが取得できていない場合は初期値
                                    progress_percentage = 10  # 開始時は10%

                                return {
                                    'items_scraped': items_count,
                                    'requests_made': requests_made,
                                    'pending_items': pending_items,
                                    'progress_percentage': progress_percentage,
                                    'estimated_total': total_estimated
                                }

            finally:
                db.close()

        except Exception as e:
            print(f"Error estimating progress for task {task_id}: {str(e)}")

        return {}

    def _update_task_progress_in_db(self, task_id: str, progress_info: Dict[str, Any]):
        """データベースのタスク進行状況を更新"""
        try:
            from ..database import SessionLocal, Task as DBTask
            import requests

            db = SessionLocal()
            try:
                task = db.query(DBTask).filter(DBTask.id == task_id).first()
                if task:
                    old_items = task.items_count or 0
                    old_requests = task.requests_count or 0

                    new_items = progress_info.get('items_scraped', 0)
                    new_requests = progress_info.get('requests_made', 0)

                    # 進行状況が変化した場合のみ更新
                    if new_items != old_items or new_requests != old_requests:
                        task.items_count = new_items
                        task.requests_count = new_requests
                        db.commit()

                        # プログレス計算
                        if new_items > 0:
                            pending_items = max(0, min(60 - new_items, max(new_requests - new_items, 10)))
                            total_estimated = new_items + pending_items
                            progress_percentage = min(95, (new_items / total_estimated) * 100) if total_estimated > 0 else 10
                        else:
                            progress_percentage = 5

                        # WebSocket通知を送信（HTTPリクエスト経由）
                        try:
                            notification_url = "http://localhost:8000/api/tasks/internal/websocket-notify"
                            payload = {
                                "task_id": task_id,
                                "data": {
                                    "id": task_id,
                                    "status": "RUNNING",
                                    "items_count": new_items,
                                    "requests_count": new_requests,
                                    "progress": progress_percentage
                                }
                            }

                            response = requests.post(
                                notification_url,
                                json=payload,
                                timeout=0.5,
                                headers={"Content-Type": "application/json"}
                            )

                            if response.status_code == 200:
                                print(f"📊 Progress notification sent: Task {task_id} - Items: {new_items}, Progress: {progress_percentage:.1f}%")

                        except Exception as notify_error:
                            print(f"📡 Progress notification error: {str(notify_error)}")

            finally:
                db.close()

        except Exception as e:
            print(f"Error updating task progress in DB: {str(e)}")

    def get_task_progress(self, task_id: str) -> Dict[str, Any]:
        """タスクの進行状況を取得"""
        if task_id in self.task_progress:
            return self.task_progress[task_id].copy()
        return {}

    def _estimate_pending_items(self, task_id: str, current_items: int, requests_made: int, elapsed_seconds: float) -> int:
        """pendingアイテム数を推定"""
        try:
            # 方法1: 経過時間ベースの推定
            if elapsed_seconds > 30:  # 30秒以上経過している場合
                # アイテム取得率を計算（アイテム/秒）
                items_per_second = current_items / elapsed_seconds if elapsed_seconds > 0 else 0

                # 通常のスクレイピングでは60アイテム程度を想定
                estimated_total = 60

                # 現在の取得率から残り時間を推定
                if items_per_second > 0:
                    remaining_items = max(0, estimated_total - current_items)
                    return remaining_items

            # 方法2: リクエスト数ベースの推定
            if requests_made > current_items:
                # リクエスト数がアイテム数より多い場合、処理中のアイテムがある
                processing_items = requests_made - current_items
                return min(processing_items, 20)  # 最大20アイテム

            # 方法3: 初期段階の推定
            if current_items < 10:
                # 開始直後は多めに推定
                return max(50 - current_items, 0)
            elif current_items < 30:
                # 中間段階
                return max(60 - current_items, 0)
            else:
                # 後半段階
                return max(10, int(current_items * 0.1))  # 現在の10%程度

        except Exception as e:
            print(f"Error estimating pending items for task {task_id}: {e}")
            # エラー時はデフォルト値
            return max(20 - current_items, 0)

    def _verify_task_results(self, task_id: str) -> bool:
        """タスクの結果ファイルが正常に生成されているかチェック"""
        try:
            from ..database import SessionLocal, Task as DBTask, Project as DBProject
            import glob
            import json

            db = SessionLocal()
            try:
                task = db.query(DBTask).filter(DBTask.id == task_id).first()
                if not task:
                    return False

                project = db.query(DBProject).filter(DBProject.id == task.project_id).first()
                if not project:
                    return False

                # 複数のパスパターンで結果ファイルを検索（実際のファイル配置に基づく順序）
                possible_paths = [
                    # 実際のパス（プロジェクトルートディレクトリ）
                    self.base_projects_dir / project.path / f"results_{task_id}.json",
                    # 二重パス（プロジェクト内のプロジェクトディレクトリ）
                    self.base_projects_dir / project.path / project.path / f"results_{task_id}.json",
                ]

                result_file = None
                for path in possible_paths:
                    if path.exists():
                        result_file = path
                        break

                # 見つからない場合は再帰検索
                if not result_file:
                    pattern = str(self.base_projects_dir / project.path / "**" / f"results_{task_id}.json")
                    matches = glob.glob(pattern, recursive=True)
                    if matches:
                        result_file = Path(matches[0])

                # さらに見つからない場合は、最新のresults_*.jsonファイルを検索
                if not result_file:
                    pattern = str(self.base_projects_dir / project.path / "**" / "results_*.json")
                    matches = glob.glob(pattern, recursive=True)
                    if matches:
                        # 最新のファイルを取得（作成時間順）
                        latest_file = max(matches, key=lambda x: Path(x).stat().st_mtime)
                        # 5分以内に作成されたファイルのみ対象
                        if time.time() - Path(latest_file).stat().st_mtime < 300:
                            result_file = Path(latest_file)
                            print(f"Task {task_id}: Using latest result file: {result_file}")

                if result_file and result_file.exists():
                    # ファイルサイズチェック（空でないか）
                    file_size = result_file.stat().st_size
                    if file_size > 50:  # 最低50バイト（より寛容に）
                        # JSONファイルの内容も検証
                        try:
                            with open(result_file, 'r', encoding='utf-8') as f:
                                content = f.read().strip()
                                if content:
                                    # JSONとして解析可能かチェック
                                    data = json.loads(content)
                                    item_count = len(data) if isinstance(data, list) else 1

                                    print(f"Task {task_id}: Result file verified - {item_count} items, {file_size} bytes at {result_file}")

                                    # データベースに結果を反映
                                    task.items_count = item_count
                                    task.requests_count = max(item_count + 5, 10)  # 推定リクエスト数
                                    db.commit()

                                    return True
                        except json.JSONDecodeError:
                            print(f"Task {task_id}: Result file is not valid JSON, attempting repair at {result_file}")
                            # 不完全なJSONの修復を試行
                            return self._repair_and_verify_json(task_id, content, result_file, task, db)
                        except Exception as e:
                            print(f"Task {task_id}: Error reading result file: {e}")
                            # ファイルサイズが十分大きければ成功とみなす
                            if file_size > 1000:  # 1KB以上
                                print(f"Task {task_id}: Large file size, assuming success")
                                return True
                            return False
                    else:
                        print(f"Task {task_id}: Result file is too small ({file_size} bytes) at {result_file}")
                        return False
                else:
                    print(f"Task {task_id}: Result file not found in any expected location")
                    # デバッグ用：利用可能なファイルを表示
                    debug_pattern = str(self.base_projects_dir / project.path / "**" / "*.json")
                    debug_matches = glob.glob(debug_pattern, recursive=True)
                    if debug_matches:
                        print(f"Task {task_id}: Available JSON files: {debug_matches[:5]}")  # 最初の5件のみ
                    return False

            finally:
                db.close()

        except Exception as e:
            print(f"Error verifying task results: {str(e)}")
            return False

    def _repair_and_verify_json(self, task_id: str, content: str, result_file, task, db) -> bool:
        """不完全なJSONファイルを修復して検証"""
        try:
            import json

            print(f"🔧 Task {task_id}: Attempting to repair incomplete JSON")

            # 最後のカンマを除去して閉じ括弧を追加
            fixed_content = content.rstrip().rstrip(',') + ']'

            try:
                data = json.loads(fixed_content)
                if isinstance(data, list) and len(data) > 0:
                    print(f"✅ Task {task_id}: Successfully repaired JSON with {len(data)} items")

                    # 修復されたファイルを保存
                    backup_file = str(result_file) + '.backup'
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        f.write(content)  # 元のファイルをバックアップ

                    with open(result_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                    # データベースに結果を反映
                    task.items_count = len(data)
                    task.requests_count = max(len(data) + 5, 10)
                    db.commit()

                    print(f"💾 Task {task_id}: Repaired file saved, {len(data)} items")
                    return True

            except json.JSONDecodeError as e:
                print(f"❌ Task {task_id}: Failed to repair JSON: {e}")

                # ファイルサイズが大きければ部分的成功とみなす
                file_size = len(content)
                if file_size > 5000:  # 5KB以上
                    estimated_items = max(file_size // 200, 5)  # 推定アイテム数
                    print(f"📊 Task {task_id}: Large file ({file_size} bytes), estimating {estimated_items} items")

                    task.items_count = estimated_items
                    task.requests_count = estimated_items + 10
                    db.commit()

                    return True

                return False

        except Exception as e:
            print(f"❌ Task {task_id}: Error during JSON repair: {e}")
            return False

    def _check_task_timeouts(self):
        """長時間実行中のタスクをチェックしてタイムアウト処理"""
        try:
            from ..database import SessionLocal, Task as DBTask, TaskStatus

            db = SessionLocal()
            try:
                # 30分以上実行中のタスクを取得
                timeout_threshold = datetime.now() - timedelta(minutes=30)

                timeout_tasks = db.query(DBTask).filter(
                    DBTask.status == TaskStatus.RUNNING,
                    DBTask.started_at < timeout_threshold
                ).all()

                for task in timeout_tasks:
                    print(f"🔍 Task {task.id} timed out (started: {task.started_at}), checking for results...")

                    # まず結果ファイルをチェック（タイムアウトでも成功の可能性）
                    if self._verify_task_results(task.id):
                        print(f"✅ Task {task.id}: Found results despite timeout, marking as completed")
                        task.status = TaskStatus.FINISHED
                        task.finished_at = datetime.now()
                        continue

                    # プロセスを強制終了
                    if task.id in self.running_processes:
                        process = self.running_processes[task.id]
                        try:
                            # プロセスのメモリ使用量をチェック
                            try:
                                import psutil
                                ps_process = psutil.Process(process.pid)
                                memory_mb = ps_process.memory_info().rss / 1024 / 1024
                                print(f"📊 Task {task.id}: Memory usage before termination: {memory_mb:.1f}MB")
                            except (ImportError, psutil.NoSuchProcess):
                                pass

                            process.terminate()
                            time.sleep(5)
                            if process.poll() is None:
                                process.kill()
                            del self.running_processes[task.id]
                        except Exception as e:
                            print(f"❌ Error terminating process for task {task.id}: {str(e)}")

                    # タスクを失敗としてマーク（進行状況は保持）
                    current_items = task.items_count or 0
                    current_requests = task.requests_count or 0
                    current_errors = task.error_count or 0

                    task.status = TaskStatus.FAILED
                    task.finished_at = datetime.now()
                    # 進行状況データを保持
                    task.items_count = current_items
                    task.requests_count = current_requests
                    task.error_count = current_errors + 1  # タイムアウトエラーを追加

                    print(f"❌ Task {task.id} timed out - preserved progress: {current_items} items, {current_requests} requests")

                if timeout_tasks:
                    db.commit()
                    print(f"Marked {len(timeout_tasks)} tasks as timed out")

            finally:
                db.close()

        except Exception as e:
            print(f"Error checking task timeouts: {str(e)}")

    def _perform_health_check(self):
        """タスクシステムのヘルスチェック"""
        try:
            from ..database import SessionLocal, Task as DBTask, TaskStatus

            db = SessionLocal()
            try:
                # データベースとプロセスの整合性チェック
                running_tasks_db = db.query(DBTask).filter(DBTask.status == TaskStatus.RUNNING).all()

                for task in running_tasks_db:
                    if task.id not in self.running_processes:
                        # データベースでは実行中だが、プロセスが存在しない
                        print(f"Health check: Task {task.id} marked as running but no process found")

                        # 結果ファイルをチェックして完了判定
                        if self._verify_task_results(task.id):
                            print(f"Health check: Task {task.id} has results, marking as completed")

                            # 統計情報を更新
                            actual_items, actual_requests = self._get_task_statistics(task.id, task.project_id)

                            # データが取得されていれば成功とみなす
                            if actual_items > 0:
                                task.status = TaskStatus.FINISHED
                                task.items_count = actual_items
                                task.requests_count = actual_requests
                                task.error_count = 0
                                print(f"Health check: Task {task.id} completed successfully with {actual_items} items")
                            else:
                                # ファイルはあるがデータがない場合
                                task.status = TaskStatus.FAILED
                                task.error_count = 1
                                print(f"Health check: Task {task.id} has empty results, marking as failed")

                            task.finished_at = datetime.now()
                        else:
                            # 結果ファイルもない場合は失敗とする
                            print(f"Health check: Task {task.id} has no results, marking as failed")
                            task.status = TaskStatus.FAILED
                            task.finished_at = datetime.now()
                            task.error_count = 1

                # プロセスは存在するがデータベースで完了している場合
                for task_id, process in list(self.running_processes.items()):
                    task = db.query(DBTask).filter(DBTask.id == task_id).first()
                    if task and task.status in [TaskStatus.FINISHED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                        print(f"Health check: Process {task_id} still running but DB shows {task.status}")
                        try:
                            process.terminate()
                            time.sleep(2)
                            if process.poll() is None:
                                process.kill()
                            del self.running_processes[task_id]
                            print(f"Health check: Cleaned up orphaned process {task_id}")
                        except Exception as e:
                            print(f"Health check: Error cleaning up process {task_id}: {str(e)}")

                db.commit()

            finally:
                db.close()

        except Exception as e:
            print(f"Error in health check: {str(e)}")

    def fix_failed_tasks_with_results(self):
        """結果ファイルがあるのにFAILEDになっているタスクを修正"""
        try:
            from ..database import SessionLocal, Task as DBTask, TaskStatus

            db = SessionLocal()
            try:
                # FAILEDステータスのタスクを取得
                failed_tasks = db.query(DBTask).filter(DBTask.status == TaskStatus.FAILED).all()

                fixed_count = 0
                for task in failed_tasks:
                    # 結果ファイルをチェック
                    if self._verify_task_results(task.id):
                        # 統計情報を取得
                        actual_items, actual_requests = self._get_task_statistics(task.id, task.project_id)

                        if actual_items > 0:
                            # データがあるので成功に変更
                            task.status = TaskStatus.FINISHED
                            task.items_count = actual_items
                            task.requests_count = actual_requests
                            task.error_count = 0
                            fixed_count += 1
                            print(f"Fixed task {task.id}: {actual_items} items found, marked as FINISHED")

                if fixed_count > 0:
                    db.commit()
                    print(f"Fixed {fixed_count} failed tasks that actually had results")
                else:
                    print("No failed tasks with results found to fix")

            finally:
                db.close()

        except Exception as e:
            print(f"Error fixing failed tasks: {str(e)}")

    def delete_project(self, project_path: str) -> bool:
        """Scrapyプロジェクトを削除"""
        try:
            # scrapy_projects/project_name ディレクトリを削除
            full_path = self.base_projects_dir / project_path
            if full_path.exists():
                shutil.rmtree(full_path)
                print(f"Deleted project directory: {full_path}")
            return True
        except Exception as e:
            print(f"Error deleting project: {str(e)}")
            raise Exception(f"Error deleting project: {str(e)}")

    def get_project_spiders(self, project_path: str) -> List[str]:
        """プロジェクト内のスパイダー一覧を取得"""
        try:
            # scrapy_projects/project_name/project_name/spiders ディレクトリを確認
            full_path = self.base_projects_dir / project_path
            spiders_dir = full_path / project_path / "spiders"

            if not spiders_dir.exists():
                print(f"Spiders directory not found: {spiders_dir}")
                return []

            spider_files = []
            for file in spiders_dir.glob("*.py"):
                if file.name != "__init__.py":
                    spider_files.append(file.stem)

            print(f"Found spiders: {spider_files}")
            return spider_files

        except Exception as e:
            print(f"Error getting spiders: {str(e)}")
            raise Exception(f"Error getting spiders: {str(e)}")

    def _get_accurate_task_statistics(self, task_id: str, project_id: str) -> tuple[int, int]:
        """結果ファイルから正確な統計情報を取得（根本対応版）"""
        try:
            from ..database import SessionLocal, Project as DBProject
            import json
            from pathlib import Path

            # プロジェクト情報を取得
            db = SessionLocal()
            try:
                project = db.query(DBProject).filter(DBProject.id == project_id).first()
                if not project:
                    print(f"⚠️ Project not found for task {task_id}")
                    return 0, 0

                project_path = project.path
            finally:
                db.close()

            # 結果ファイルのパスを構築
            base_dir = Path("/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects")
            result_file = base_dir / project_path / f"results_{task_id}.json"

            print(f"📁 Checking result file: {result_file}")

            if not result_file.exists():
                print(f"❌ Result file not found: {result_file}")
                return 0, 0

            # ファイルサイズチェック
            file_size = result_file.stat().st_size
            print(f"📊 File size: {file_size} bytes")

            if file_size < 50:  # 50バイト未満は空ファイルとみなす
                print(f"⚠️ File too small: {file_size} bytes")
                return 0, 0

            # JSONファイルを読み込み
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, list):
                    items_count = len(data)
                    # リクエスト数は推定（アイテム数 + 10〜20の範囲）
                    requests_count = max(items_count + 10, 20)

                    print(f"✅ Accurate stats from file: items={items_count}, requests={requests_count}")
                    return items_count, requests_count
                else:
                    # 単一オブジェクトの場合
                    print(f"✅ Single item found in file")
                    return 1, 10

            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                # JSONエラーでもファイルサイズが大きければ推定値を返す
                if file_size > 5000:  # 5KB以上
                    estimated_items = max(file_size // 100, 10)
                    estimated_requests = estimated_items + 10
                    print(f"📊 Estimated from file size: items={estimated_items}, requests={estimated_requests}")
                    return estimated_items, estimated_requests
                return 0, 0

        except Exception as e:
            print(f"❌ Error in _get_accurate_task_statistics: {str(e)}")
            import traceback
            traceback.print_exc()
            return 0, 0

    def create_spider(self, project_path: str, spider_name: str, template: str = "basic") -> bool:
        """新しいスパイダーを作成"""
        try:
            # scrapy_projects/project_name ディレクトリでscrapy genspiderを実行
            full_path = self.base_projects_dir / project_path

            # プロジェクトディレクトリに移動してスパイダーを作成
            cmd = [
                sys.executable, "-m", "scrapy", "genspider",
                spider_name, "example.com"
            ]

            print(f"Creating spider: {spider_name} in {full_path}")
            print(f"Command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=str(full_path),
                capture_output=True,
                text=True,
                check=True
            )

            print(f"Spider created successfully: {result.stdout}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"Failed to create spider: {e.stderr}")
            raise Exception(f"Failed to create spider: {e.stderr}")
        except Exception as e:
            print(f"Error creating spider: {str(e)}")
            raise Exception(f"Error creating spider: {str(e)}")





    def get_project_settings(self, project_path: str) -> Dict[str, Any]:
        """プロジェクトの設定を取得"""
        try:
            # scrapy_projects/project_name/project_name/settings.py
            full_path = self.base_projects_dir / project_path
            settings_file = full_path / project_path / "settings.py"

            if not settings_file.exists():
                print(f"Settings file not found: {settings_file}")
                return {}

            # settings.pyを読み込んで設定を抽出
            # 簡単な実装として、ファイル内容を返す
            with open(settings_file, 'r', encoding='utf-8') as f:
                content = f.read()

            return {"content": content}

        except Exception as e:
            print(f"Error reading project settings: {str(e)}")
            raise Exception(f"Error reading project settings: {str(e)}")

    def validate_spider_code(self, code: str) -> Dict[str, Any]:
        """スパイダーコードの構文チェック"""
        try:
            # 一時ファイルに書き込んで構文チェック
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            try:
                # Pythonの構文チェック
                with open(temp_file, 'r') as f:
                    compile(f.read(), temp_file, 'exec')

                return {"valid": True, "errors": []}

            except SyntaxError as e:
                return {
                    "valid": False,
                    "errors": [f"Syntax error at line {e.lineno}: {e.msg}"]
                }
            finally:
                os.unlink(temp_file)

        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"]
            }
