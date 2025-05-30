"""
Celeryタスク: スクリプト実行
"""
import asyncio
import tempfile
import json
import os
import sys
import re
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from celery import Celery
from sqlalchemy.orm import Session

from ..database import SessionLocal, Task as DBTask, TaskStatus
from ..api.script_runner import running_executions, save_execution_history

# Celeryアプリケーションを取得
from ..celery_app import celery_app

@celery_app.task(bind=True)
def run_script_task(
    self,
    execution_id: str,
    script_content: str,
    spider_name: str,
    start_urls: List[str],
    settings: Dict[str, Any],
    user_id: str
):
    """
    スクリプトをCeleryタスクで実行（Reactor競合回避）
    """
    print(f"🚀 Starting Celery script task: {execution_id}")
    print(f"📝 Spider name: {spider_name}")
    print(f"🌐 Start URLs: {start_urls}")
    print(f"⚙️ Settings: {settings}")

    # データベースセッションを作成
    db = SessionLocal()
    
    try:
        # タスクを取得
        db_task = db.query(DBTask).filter(DBTask.id == execution_id).first()
        if not db_task:
            raise Exception(f"Task {execution_id} not found in database")

        # タスクを実行中に更新
        db_task.status = TaskStatus.RUNNING
        db_task.started_at = datetime.now()
        db.commit()

        print(f"✅ Task {execution_id} marked as RUNNING")

        # 実行状態を更新
        if execution_id in running_executions:
            running_executions[execution_id].update({
                "status": "running",
                "started_at": datetime.now().isoformat()
            })

        # スクリプトを実行
        use_playwright = "scrapy_playwright" in script_content or "playwright" in str(settings)
        print(f"🎭 Playwright detection: {use_playwright}")

        # 非同期実行のためのイベントループ
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                execute_scrapy_script_celery(
                    script_content,
                    spider_name,
                    start_urls,
                    settings,
                    use_playwright=use_playwright
                )
            )
        finally:
            loop.close()

        # 結果を処理
        items_count = len(result["extracted_data"])
        
        # タスクを完了に更新
        db_task.status = TaskStatus.FINISHED
        db_task.finished_at = datetime.now()
        db_task.items_count = items_count
        db_task.requests_count = result.get("requests_count", 0)
        db_task.error_count = len(result["errors"])
        db.commit()

        print(f"✅ Task {execution_id} completed successfully")
        print(f"📊 Items: {items_count}, Errors: {len(result['errors'])}")

        # 実行状態を更新
        finished_at = datetime.now().isoformat()
        if execution_id in running_executions:
            running_executions[execution_id].update({
                "status": "completed",
                "output": result["output"],
                "errors": result["errors"],
                "extracted_data": result["extracted_data"],
                "finished_at": finished_at
            })

        # 実行履歴に保存
        save_execution_history(user_id, {
            "execution_id": execution_id,
            "spider_name": spider_name,
            "status": "completed",
            "start_urls": start_urls,
            "extracted_count": items_count,
            "execution_time": result["execution_time"],
            "started_at": db_task.started_at.isoformat() if db_task.started_at else None,
            "finished_at": finished_at
        })

        return {
            "execution_id": execution_id,
            "status": "completed",
            "items_count": items_count,
            "execution_time": result["execution_time"]
        }

    except Exception as e:
        print(f"❌ Script execution error: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        traceback.print_exc()

        # タスクを失敗に更新
        if db_task:
            db_task.status = TaskStatus.FAILED
            db_task.finished_at = datetime.now()
            db_task.error_count = 1
            db.commit()

        # 実行状態を更新
        finished_at = datetime.now().isoformat()
        if execution_id in running_executions:
            running_executions[execution_id].update({
                "status": "failed",
                "errors": [str(e), traceback.format_exc()],
                "finished_at": finished_at
            })

        # 実行履歴に保存
        save_execution_history(user_id, {
            "execution_id": execution_id,
            "spider_name": spider_name,
            "status": "failed",
            "start_urls": start_urls,
            "extracted_count": 0,
            "execution_time": 0.0,
            "started_at": db_task.started_at.isoformat() if db_task and db_task.started_at else None,
            "finished_at": finished_at
        })

        raise

    finally:
        db.close()

async def execute_scrapy_script_celery(
    script_content: str,
    spider_name: str,
    start_urls: List[str],
    settings: Dict[str, Any],
    use_playwright: bool = False
) -> Dict[str, Any]:
    """
    Scrapyスクリプトを実行してデータを抽出（Celery用）
    """
    start_time = datetime.now()
    output_lines = []
    error_lines = []
    extracted_data = []

    try:
        print(f"🔧 Creating temporary directory for script execution")

        # 一時ディレクトリを作成
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            print(f"📁 Temp directory: {temp_path}")

            # Scrapyプロジェクトの基本構造を作成
            project_dir = temp_path / "temp_project"
            project_dir.mkdir()
            print(f"📁 Project directory: {project_dir}")

            spiders_dir = project_dir / "spiders"
            spiders_dir.mkdir()

            # __init__.pyファイルを作成
            (project_dir / "__init__.py").write_text("")
            (spiders_dir / "__init__.py").write_text("")

            # items.pyを作成
            items_content = """
import scrapy

class TempProjectItem(scrapy.Item):
    pass
"""
            (project_dir / "items.py").write_text(items_content)

            # settings.pyを作成
            playwright_settings = ""
            if use_playwright:
                playwright_settings = '''
# Playwright設定
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Playwright追加設定
PLAYWRIGHT_BROWSER_TYPE = 'chromium'
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True, "args": ["--no-sandbox", "--disable-setuid-sandbox"]}
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000
'''

            settings_content = f"""
BOT_NAME = 'temp_project'
SPIDER_MODULES = ['temp_project.spiders']
NEWSPIDER_MODULE = 'temp_project.spiders'
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 1

DEFAULT_REQUEST_HEADERS = {{
    'Accept-Language': 'ja',
}}

FEED_EXPORT_ENCODING = 'utf-8'

{playwright_settings}

LOG_LEVEL = 'INFO'
DOWNLOAD_TIMEOUT = 30

# カスタム設定
{json.dumps(settings, indent=4) if settings else ''}
"""
            (project_dir / "settings.py").write_text(settings_content)

            # scrapy.cfgを作成
            scrapy_cfg_content = f"""
[settings]
default = temp_project.settings

[deploy]
project = temp_project
"""
            (temp_path / "scrapy.cfg").write_text(scrapy_cfg_content)

            # スパイダーファイルを作成
            urls_str = ",\n        ".join([f'"{url}"' for url in start_urls])
            modified_script = script_content

            # start_urlsを置換
            if "start_urls = [" in script_content:
                pattern = r'start_urls\s*=\s*\[.*?\]'
                replacement = f'start_urls = [\n        {urls_str}\n    ]'
                modified_script = re.sub(pattern, replacement, script_content, flags=re.DOTALL)

            # スパイダー名を設定
            if 'name = "' in modified_script:
                pattern = r'name\s*=\s*["\'][^"\']*["\']'
                replacement = f'name = "{spider_name}"'
                modified_script = re.sub(pattern, replacement, modified_script)

            spider_file = spiders_dir / f"{spider_name}.py"
            spider_file.write_text(modified_script)

            # データ出力用パイプラインを作成
            pipeline_content = f"""
import json
import os

class DataCollectionPipeline:
    def __init__(self):
        self.items = []
        self.output_file = os.path.join(r'{temp_dir}', 'scraped_data.json')

    def process_item(self, item, spider):
        if hasattr(item, 'keys'):
            item_dict = dict(item)
        elif isinstance(item, dict):
            item_dict = item
        else:
            item_dict = {{'data': str(item)}}

        self.items.append(item_dict)

        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self.items, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"Error saving to file: {{e}}")

        return item
"""
            (project_dir / "pipelines.py").write_text(pipeline_content)

            # settings.pyにパイプラインを追加
            with open(project_dir / "settings.py", "a") as f:
                f.write(f"\nITEM_PIPELINES = {{'temp_project.pipelines.DataCollectionPipeline': 300}}\n")

            # Scrapyを実行
            cmd = [
                sys.executable, "-m", "scrapy", "crawl", spider_name,
                "-s", "LOG_LEVEL=INFO"
            ]

            print(f"🚀 Executing command: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "PYTHONPATH": str(temp_path)}
            )

            # タイムアウト付きでプロセスを実行
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=300.0
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise Exception("Script execution timed out after 300 seconds")

            # 出力を処理
            if stdout:
                output_lines = stdout.decode('utf-8', errors='ignore').split('\n')
                output_lines = [line for line in output_lines if line.strip()]

            if stderr:
                stderr_lines = stderr.decode('utf-8', errors='ignore').split('\n')
                stderr_lines = [line for line in stderr_lines if line.strip()]

                for line in stderr_lines:
                    if any(level in line for level in ['ERROR', 'CRITICAL']) or 'Traceback' in line:
                        error_lines.append(line)
                    else:
                        output_lines.append(line)

            # 抽出されたデータを読み込み
            data_file = temp_path / "scraped_data.json"
            if data_file.exists():
                try:
                    with open(data_file, 'r', encoding='utf-8') as f:
                        extracted_data = json.load(f)
                except Exception as e:
                    error_lines.append(f"Error reading scraped data: {str(e)}")

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "output": output_lines,
                "errors": error_lines,
                "extracted_data": extracted_data,
                "execution_time": execution_time,
                "requests_count": len(output_lines)  # 簡易的な計算
            }

    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        return {
            "output": output_lines,
            "errors": error_lines + [str(e), traceback.format_exc()],
            "extracted_data": extracted_data,
            "execution_time": execution_time,
            "requests_count": 0
        }
