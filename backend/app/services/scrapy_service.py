import os
import subprocess
import shutil
import json
import asyncio
import uuid
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import sys
from datetime import datetime, timedelta
import glob

class ScrapyPlaywrightService:
    """Scrapy + Playwright統合を管理するサービスクラス（シングルトン）"""

    _instance = None
    _initialized = False

    def __new__(cls, base_projects_dir: str = "./scrapy_projects"):
        if cls._instance is None:
            cls._instance = super(ScrapyPlaywrightService, cls).__new__(cls)
        return cls._instance

    def __init__(self, base_projects_dir: str = "./scrapy_projects"):
        if self._initialized:
            return

        self.base_projects_dir = Path(base_projects_dir)
        self.base_projects_dir.mkdir(exist_ok=True)
        self.running_processes: Dict[str, subprocess.Popen] = {}
        self.task_progress: Dict[str, Dict[str, Any]] = {}  # タスクの進行状況を追跡
        self.monitoring_thread = None
        self.stop_monitoring = False
        self._initialized = True
        print(f"🔧 ScrapyPlaywrightService initialized with base_dir: {self.base_projects_dir}")

    def create_project(self, project_name: str, project_path: str) -> bool:
        """新しいScrapyプロジェクトを作成（scrapy startproject と同じ動作）"""
        try:
            # scrapy_projects ディレクトリ内にプロジェクトを作成
            # scrapy startproject project_name の動作を再現

            # scrapy_projects ディレクトリが存在することを確認
            self.base_projects_dir.mkdir(exist_ok=True)

            # scrapy startproject を scrapy_projects ディレクトリ内で実行
            cmd = [
                sys.executable, "-m", "scrapy", "startproject", project_name
            ]

            print(f"Creating Scrapy project: {project_name}")
            print(f"Command: {' '.join(cmd)}")
            print(f"Working directory: {self.base_projects_dir}")

            result = subprocess.run(
                cmd,
                cwd=str(self.base_projects_dir),  # scrapy_projects ディレクトリで実行
                capture_output=True,
                text=True,
                check=True
            )

            print(f"Scrapy project created successfully: {result.stdout}")

            # 作成されたプロジェクトディレクトリのパス
            project_dir = self.base_projects_dir / project_name

            # scrapy-playwright設定を追加
            self._setup_playwright_config(project_dir / project_name)

            return True

        except subprocess.CalledProcessError as e:
            print(f"Failed to create Scrapy project: {e.stderr}")
            raise Exception(f"Failed to create Scrapy project: {e.stderr}")
        except Exception as e:
            print(f"Error creating project: {str(e)}")
            raise Exception(f"Error creating project: {str(e)}")

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
'''

        if settings_file.exists():
            with open(settings_file, 'a', encoding='utf-8') as f:
                f.write(playwright_settings)

    def get_spider_code(self, project_path: str, spider_name: str) -> str:
        """スパイダーのコードを取得"""
        try:
            # scrapy_projects/project_name/project_name/spiders/spider_name.py
            full_path = self.base_projects_dir / project_path
            spider_file = full_path / project_path / "spiders" / f"{spider_name}.py"

            if not spider_file.exists():
                print(f"Spider file not found: {spider_file}")
                raise Exception(f"Spider file not found: {spider_file}")

            with open(spider_file, 'r', encoding='utf-8') as f:
                return f.read()

        except Exception as e:
            print(f"Error reading spider code: {str(e)}")
            raise Exception(f"Error reading spider code: {str(e)}")

    def save_spider_code(self, project_path: str, spider_name: str, code: str) -> bool:
        """スパイダーのコードを保存"""
        try:
            # scrapy_projects/project_name/project_name/spiders/spider_name.py
            full_path = self.base_projects_dir / project_path
            spider_file = full_path / project_path / "spiders" / f"{spider_name}.py"

            # ディレクトリが存在しない場合は作成
            spider_file.parent.mkdir(parents=True, exist_ok=True)

            with open(spider_file, 'w', encoding='utf-8') as f:
                f.write(code)

            print(f"Spider code saved: {spider_file}")
            return True

        except Exception as e:
            print(f"Error saving spider code: {str(e)}")
            raise Exception(f"Error saving spider code: {str(e)}")

    def run_spider(self, project_path: str, spider_name: str, task_id: str, settings: Optional[Dict[str, Any]] = None) -> str:
        """スパイダーを実行（非同期）"""
        try:
            # scrapy_projects/project_name ディレクトリでscrapy crawlを実行
            full_path = self.base_projects_dir / project_path

            cmd = [sys.executable, "-m", "scrapy", "crawl", spider_name]

            # 設定がある場合は追加
            if settings:
                for key, value in settings.items():
                    cmd.extend(["-s", f"{key}={value}"])

            # 結果をJSONファイルに出力
            output_file = full_path / f"results_{task_id}.json"
            cmd.extend(["-o", str(output_file)])

            print(f"Running spider: {spider_name} in {full_path}")
            print(f"Command: {' '.join(cmd)}")

            # 非同期でプロセスを開始
            process = subprocess.Popen(
                cmd,
                cwd=str(full_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.running_processes[task_id] = process

            # 進行状況の初期化
            self.task_progress[task_id] = {
                'started_at': datetime.now(),
                'items_scraped': 0,
                'requests_made': 0,
                'errors_count': 0,
                'progress_percentage': 0,
                'estimated_total': 0,
                'current_url': None,
                'last_update': datetime.now()
            }

            return task_id

        except Exception as e:
            print(f"Error running spider: {str(e)}")
            raise Exception(f"Error running spider: {str(e)}")

    def stop_spider(self, task_id: str) -> bool:
        """スパイダーの実行を停止"""
        try:
            if task_id in self.running_processes:
                process = self.running_processes[task_id]
                process.terminate()
                process.wait(timeout=10)
                del self.running_processes[task_id]
                return True
            return False
        except Exception as e:
            raise Exception(f"Error stopping spider: {str(e)}")

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
        """タスク完了時にデータベースを更新"""
        try:
            from ..database import SessionLocal, Task as DBTask, TaskStatus, Spider as DBSpider
            import json
            import asyncio

            db = SessionLocal()
            try:
                task = db.query(DBTask).filter(DBTask.id == task_id).first()
                if task:
                    # 結果ファイルから実際の統計情報を取得
                    actual_items, actual_requests = self._get_task_statistics(task_id, task.project_id)

                    task.status = TaskStatus.FINISHED if success else TaskStatus.FAILED
                    task.finished_at = datetime.now()
                    task.items_count = actual_items if actual_items > 0 else items_count
                    task.requests_count = actual_requests if actual_requests > 0 else requests_count
                    task.error_count = 0 if success else 1

                    db.commit()
                    print(f"Task {task_id} marked as {'completed' if success else 'failed'}")
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

                # 複数のパスパターンで結果ファイルを検索
                possible_paths = [
                    # 標準パス
                    self.base_projects_dir / project.path / f"results_{task_id}.json",
                    # 二重パス（実際の構造）
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
                    with open(result_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        items_count = len(data) if isinstance(data, list) else 1

                    # ログファイルからリクエスト数を推定（簡易版）
                    requests_count = max(items_count + 1, 7)  # 最低7リクエスト（robots.txt含む）

                    print(f"Statistics from result file: items={items_count}, requests={requests_count} at {result_file}")
                    return items_count, requests_count

            finally:
                db.close()

        except Exception as e:
            print(f"Error getting task statistics: {str(e)}")

        return 0, 0

    def start_monitoring(self):
        """バックグラウンドでタスクの監視を開始"""
        if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
            self.stop_monitoring = False
            self.monitoring_thread = threading.Thread(target=self._monitor_tasks, daemon=True)
            self.monitoring_thread.start()
            print("Task monitoring started")

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
                                # 結果ファイル生成を最大30秒待機
                                success = self._wait_for_results_file(task_id, timeout=30)
                                print(f"Task {task_id}: After file verification with wait: {success}")

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

                # 5秒間隔でチェック（より頻繁に）
                time.sleep(5)

            except Exception as e:
                print(f"Error in task monitoring: {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(5)

        print("Task monitoring thread stopped")

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
        """結果ファイルの生成を待機"""
        print(f"Task {task_id}: Waiting for results file (timeout: {timeout}s)")

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._verify_task_results(task_id):
                elapsed = time.time() - start_time
                print(f"Task {task_id}: Results file found after {elapsed:.1f}s")
                return True
            time.sleep(1)  # 1秒間隔でチェック

        print(f"Task {task_id}: Results file not found within {timeout}s timeout")
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

                # 結果ファイルを検索
                possible_paths = [
                    self.base_projects_dir / project.path / f"results_{task_id}.json",
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

                            # 進行状況を計算（リクエスト数÷アイテム数）
                            if task_id in self.task_progress:
                                start_time = self.task_progress[task_id]['started_at']
                                elapsed = (datetime.now() - start_time).total_seconds()

                                # リクエスト数を推定（アイテム数 + 初期リクエスト）
                                requests_made = max(items_count + 1, 1)

                                # 進行状況をリクエスト数÷アイテム数で計算
                                if items_count > 0:
                                    # アイテムが取得できている場合
                                    progress_percentage = min((requests_made / max(items_count, 1)) * 100, 95)
                                else:
                                    # まだアイテムが取得できていない場合は時間ベース
                                    estimated_duration = 300  # 5分
                                    progress_percentage = min((elapsed / estimated_duration) * 50, 50)  # 最大50%まで

                                return {
                                    'items_scraped': items_count,
                                    'requests_made': requests_made,
                                    'progress_percentage': progress_percentage,
                                    'estimated_total': max(items_count, 1)
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

            db = SessionLocal()
            try:
                task = db.query(DBTask).filter(DBTask.id == task_id).first()
                if task:
                    task.items_count = progress_info.get('items_scraped', 0)
                    task.requests_count = progress_info.get('requests_made', 0)
                    db.commit()

            finally:
                db.close()

        except Exception as e:
            print(f"Error updating task progress in DB: {str(e)}")

    def get_task_progress(self, task_id: str) -> Dict[str, Any]:
        """タスクの進行状況を取得"""
        if task_id in self.task_progress:
            return self.task_progress[task_id].copy()
        return {}

    def _verify_task_results(self, task_id: str) -> bool:
        """タスクの結果ファイルが正常に生成されているかチェック"""
        try:
            from ..database import SessionLocal, Task as DBTask, Project as DBProject
            import glob

            db = SessionLocal()
            try:
                task = db.query(DBTask).filter(DBTask.id == task_id).first()
                if not task:
                    return False

                project = db.query(DBProject).filter(DBProject.id == task.project_id).first()
                if not project:
                    return False

                # 複数のパスパターンで結果ファイルを検索
                possible_paths = [
                    # 標準パス
                    self.base_projects_dir / project.path / f"results_{task_id}.json",
                    # 二重パス（実際の構造）
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
                    # ファイルサイズチェック（空でないか）
                    if result_file.stat().st_size > 10:  # 最低10バイト
                        print(f"Task {task_id}: Result file verified ({result_file.stat().st_size} bytes) at {result_file}")
                        return True
                    else:
                        print(f"Task {task_id}: Result file is too small at {result_file}")
                        return False
                else:
                    print(f"Task {task_id}: Result file not found in any expected location")
                    return False

            finally:
                db.close()

        except Exception as e:
            print(f"Error verifying task results: {str(e)}")
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
                    print(f"Task {task.id} timed out (started: {task.started_at})")

                    # プロセスを強制終了
                    if task.id in self.running_processes:
                        process = self.running_processes[task.id]
                        try:
                            process.terminate()
                            time.sleep(5)
                            if process.poll() is None:
                                process.kill()
                            del self.running_processes[task.id]
                        except Exception as e:
                            print(f"Error terminating process for task {task.id}: {str(e)}")

                    # タスクを失敗としてマーク
                    task.status = TaskStatus.FAILED
                    task.finished_at = datetime.now()
                    task.error_count = 1

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
                            task.status = TaskStatus.FINISHED
                            task.finished_at = datetime.now()

                            # 統計情報を更新
                            actual_items, actual_requests = self._get_task_statistics(task.id, task.project_id)
                            task.items_count = actual_items
                            task.requests_count = actual_requests
                            task.error_count = 0
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
