"""
スクリプト実行API
エディターからのスクリプト実行とデータ抽出結果の返却
"""
import asyncio
import tempfile
import subprocess
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
import uuid
from datetime import datetime
import traceback
import re

from ..database import get_db, User, Task
from sqlalchemy.orm import Session
from .auth import get_current_active_user

router = APIRouter()

class ScriptExecutionRequest(BaseModel):
    script_content: str
    spider_name: str
    start_urls: List[str] = ["https://example.com"]
    settings: Dict[str, Any] = {}
    project_id: Optional[str] = None
    spider_id: Optional[str] = None

class ScriptSaveRequest(BaseModel):
    file_name: str
    content: str

class ScriptExecutionResponse(BaseModel):
    execution_id: str
    status: str
    output: List[str]
    errors: List[str]
    extracted_data: List[Dict[str, Any]]
    execution_time: float
    started_at: str
    finished_at: Optional[str] = None

# 実行中のタスクを管理
running_executions: Dict[str, Dict[str, Any]] = {}

# 実行履歴を管理（実際の実装では永続化ストレージを使用）
execution_history: Dict[str, List[Dict[str, Any]]] = {}

def save_execution_history(user_id: int, execution_data: Dict[str, Any]):
    """実行履歴を保存"""
    user_key = str(user_id)
    if user_key not in execution_history:
        execution_history[user_key] = []

    execution_history[user_key].append(execution_data)

    # 最新100件のみ保持
    if len(execution_history[user_key]) > 100:
        execution_history[user_key] = execution_history[user_key][-100:]

def get_execution_history(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """実行履歴を取得"""
    user_key = str(user_id)
    if user_key not in execution_history:
        return []

    # 最新のものから返す
    return execution_history[user_key][-limit:][::-1]

@router.post("/test", response_model=ScriptExecutionResponse)
async def test_script_simple(
    request: ScriptExecutionRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    簡単なテスト用スクリプト実行（Playwrightなし）
    """
    execution_id = str(uuid.uuid4())
    started_at = datetime.now().isoformat()

    try:
        # 簡単なテストデータを返す
        test_data = [
            {
                "url": url,
                "title": f"Test Title for {url}",
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
            for url in request.start_urls
        ]

        finished_at = datetime.now().isoformat()

        return ScriptExecutionResponse(
            execution_id=execution_id,
            status="completed",
            output=[
                f"✅ Test execution started at {started_at}",
                f"📝 Spider name: {request.spider_name}",
                f"🔗 Processing {len(request.start_urls)} URLs",
                f"✅ Test execution completed at {finished_at}"
            ],
            errors=[],
            extracted_data=test_data,
            execution_time=1.0,
            started_at=started_at,
            finished_at=finished_at
        )

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Script execution error: {str(e)}")
        print(f"❌ Error details: {error_details}")

        return ScriptExecutionResponse(
            execution_id=execution_id,
            status="failed",
            output=[],
            errors=[str(e), error_details],
            extracted_data=[],
            execution_time=0.0,
            started_at=started_at,
            finished_at=datetime.now().isoformat()
        )

@router.post("/execute", response_model=ScriptExecutionResponse)
async def execute_script(
    request: ScriptExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    スクリプトを実行してデータを抽出（Celeryタスクを使用してReactor競合回避）
    """
    execution_id = str(uuid.uuid4())
    started_at = datetime.now().isoformat()

    # タスクをデータベースに記録
    project_id = request.project_id or "webui-execution"
    spider_id = request.spider_id or request.spider_name

    task = Task(
        id=execution_id,
        project_id=project_id,
        spider_id=spider_id,
        status="PENDING",
        user_id=current_user.id,
        log_level="INFO",
        settings=request.settings or {}
    )
    db.add(task)
    db.commit()

    # 実行状態を初期化
    execution_state = {
        "status": "pending",
        "output": [],
        "errors": [],
        "extracted_data": [],
        "started_at": started_at,
        "finished_at": None
    }
    running_executions[execution_id] = execution_state

    try:
        print(f"🚀 Starting script execution via Celery: {request.spider_name}")
        print(f"📝 Start URLs: {request.start_urls}")
        print(f"⚙️ Settings: {request.settings}")

        # Celeryタスクでスクリプト実行（Reactor競合回避）
        from ..tasks.script_tasks import run_script_task

        celery_task = run_script_task.delay(
            execution_id=execution_id,
            script_content=request.script_content,
            spider_name=request.spider_name,
            start_urls=request.start_urls,
            settings=request.settings or {},
            user_id=current_user.id
        )

        # CeleryタスクIDを記録
        task.celery_task_id = celery_task.id
        db.commit()

        print(f"✅ Celery script task started: {celery_task.id}")

        # 即座にレスポンスを返す（非同期実行）
        return ScriptExecutionResponse(
            execution_id=execution_id,
            status="pending",
            output=[],
            errors=[],
            extracted_data=[],
            execution_time=0.0,
            started_at=started_at,
            finished_at=None
        )

    except Exception as e:
        execution_state.update({
            "status": "failed",
            "errors": [str(e), traceback.format_exc()],
            "finished_at": datetime.now().isoformat()
        })

        # タスクステータスを更新
        task.status = "FAILED"
        task.finished_at = datetime.now()
        db.commit()

        return ScriptExecutionResponse(
            execution_id=execution_id,
            status="failed",
            output=[],
            errors=[str(e)],
            extracted_data=[],
            execution_time=0.0,
            started_at=started_at,
            finished_at=execution_state["finished_at"]
        )

@router.get("/execution/{execution_id}", response_model=ScriptExecutionResponse)
async def get_execution_status(
    execution_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    実行状態を取得
    """
    if execution_id not in running_executions:
        raise HTTPException(status_code=404, detail="Execution not found")

    state = running_executions[execution_id]

    return ScriptExecutionResponse(
        execution_id=execution_id,
        status=state["status"],
        output=state["output"],
        errors=state["errors"],
        extracted_data=state["extracted_data"],
        execution_time=0.0,  # TODO: 実際の実行時間を計算
        started_at=state["started_at"],
        finished_at=state["finished_at"]
    )

async def execute_scrapy_script(
    script_content: str,
    spider_name: str,
    start_urls: List[str],
    settings: Dict[str, Any],
    use_playwright: bool = False
) -> Dict[str, Any]:
    """
    Scrapyスクリプトを実行してデータを抽出
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

# Playwright追加設定（ハングアップ防止）
PLAYWRIGHT_BROWSER_TYPE = 'chromium'
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True, "args": ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]}
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000
PLAYWRIGHT_PROCESS_REQUEST_HEADERS = None
'''

            settings_content = f"""
BOT_NAME = 'temp_project'
SPIDER_MODULES = ['temp_project.spiders']
NEWSPIDER_MODULE = 'temp_project.spiders'
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = 0.5

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {{
    'Accept-Language': 'ja',
}}

# Feed export encoding
FEED_EXPORT_ENCODING = 'utf-8'

# HTTP Cache settings (for development efficiency)
HTTPCACHE_ENABLED = True
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_EXPIRATION_SECS = 86400  # 1 day

# Proxy settings (optional - configure as needed)
# DOWNLOADER_MIDDLEWARES = {{
#     'scrapy_proxies.RandomProxy': 350,
# }}

# Proxy settings (optional - configure as needed)
# PROXY_LIST = '/path/to/proxy/list.txt'
# PROXY_MODE = 0  # 0: random, 1: round-robin, 2: only once

{playwright_settings}

# ログ設定
LOG_LEVEL = 'INFO'

# タイムアウト設定
DOWNLOAD_TIMEOUT = 30
DOWNLOAD_DELAY = 1

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
            # start_urlsを動的に設定
            urls_str = ",\n        ".join([f'"{url}"' for url in start_urls])

            # スクリプト内のstart_urlsとnameを置換
            modified_script = script_content

            # start_urlsを置換
            if "start_urls = [" in script_content:
                # 既存のstart_urlsを置換
                pattern = r'start_urls\s*=\s*\[.*?\]'
                replacement = f'start_urls = [\n        {urls_str}\n    ]'
                modified_script = re.sub(pattern, replacement, script_content, flags=re.DOTALL)

            # スパイダー名を強制的に設定
            if 'name = "' in modified_script:
                # 既存のnameを置換
                pattern = r'name\s*=\s*["\'][^"\']*["\']'
                replacement = f'name = "{spider_name}"'
                modified_script = re.sub(pattern, replacement, modified_script)
            elif "name = '" in modified_script:
                # シングルクォートの場合
                pattern = r"name\s*=\s*'[^']*'"
                replacement = f"name = '{spider_name}'"
                modified_script = re.sub(pattern, replacement, modified_script)
            else:
                # nameが見つからない場合は、クラス定義の後に追加
                if "class " in modified_script and "Spider" in modified_script:
                    pattern = r'(class\s+\w+.*?Spider.*?:)'
                    replacement = f'\\1\n    name = "{spider_name}"'
                    modified_script = re.sub(pattern, replacement, modified_script, flags=re.MULTILINE)

            # JavaScript風のbooleanをPythonに変換
            modified_script = modified_script.replace('"headless": true', '"headless": True')
            modified_script = modified_script.replace('"headless": false', '"headless": False')
            modified_script = modified_script.replace("'headless': true", "'headless': True")
            modified_script = modified_script.replace("'headless': false", "'headless': False")

            # デバッグ用のprint関数を追加（簡単な方法）
            debug_functions = '''
# デバッグ用関数
import json
import pprint as pp
from datetime import datetime

def debug_print(*args, **kwargs):
    """デバッグ用print関数"""
    message = ' '.join(str(arg) for arg in args)
    timestamp = datetime.now().isoformat()
    print(f"🐛 [DEBUG] {timestamp}: {message}")

def debug_pprint(obj, **kwargs):
    """デバッグ用pprint関数"""
    timestamp = datetime.now().isoformat()
    formatted = pp.pformat(obj, **kwargs)
    print(f"🐛 [PPRINT] {timestamp}:")
    for line in formatted.split('\\n'):
        print(f"🐛   {line}")

'''
            # スクリプトの先頭にデバッグ関数を追加
            modified_script = debug_functions + modified_script

            spider_file = spiders_dir / f"{spider_name}.py"
            spider_file.write_text(modified_script)



            # データ出力用のカスタムパイプラインを作成
            pipeline_content = f"""
import json
import os

class DataCollectionPipeline:
    def __init__(self):
        self.items = []
        self.output_file = os.path.join(r'{temp_dir}', 'scraped_data.json')
        print(f"🔧 Pipeline initialized, output file: {{self.output_file}}")

    def process_item(self, item, spider):
        print(f"🔧 Pipeline processing item: {{type(item)}}")

        # アイテムを辞書に変換
        if hasattr(item, 'keys'):
            item_dict = dict(item)
        elif isinstance(item, dict):
            item_dict = item
        else:
            item_dict = {{'data': str(item)}}

        print(f"🔧 Item converted to dict: {{item_dict}}")
        self.items.append(item_dict)

        # ファイルに保存
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self.items, f, ensure_ascii=False, indent=2, default=str)
            print(f"🔧 Saved {{len(self.items)}} items to file")
        except Exception as e:
            print(f"🔧 Error saving to file: {{e}}")

        return item

    def close_spider(self, spider):
        print(f"🔧 Pipeline closing, total items: {{len(self.items)}}")
        spider.logger.info(f"Collected {{len(self.items)}} items")
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
            print(f"📁 Working directory: {temp_path}")
            print(f"🌍 PYTHONPATH: {temp_path}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "PYTHONPATH": str(temp_path)}
            )

            # タイムアウト付きでプロセスを実行（300秒 = 5分）
            try:
                print(f"⏳ Waiting for process to complete (timeout: 300s)")
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=300.0
                )
                print(f"✅ Process completed with return code: {process.returncode}")
            except asyncio.TimeoutError:
                print(f"⏰ Process timed out after 300 seconds")
                # プロセスを強制終了
                process.kill()
                await process.wait()
                raise Exception("Script execution timed out after 300 seconds")
            except Exception as e:
                print(f"❌ Process execution error: {str(e)}")
                raise

            # 出力を処理
            print(f"📝 Processing stdout ({len(stdout) if stdout else 0} bytes)")
            if stdout:
                output_lines = stdout.decode('utf-8', errors='ignore').split('\n')
                output_lines = [line for line in output_lines if line.strip()]
                print(f"📝 Stdout lines: {len(output_lines)}")

            print(f"📝 Processing stderr ({len(stderr) if stderr else 0} bytes)")
            if stderr:
                stderr_lines = stderr.decode('utf-8', errors='ignore').split('\n')
                stderr_lines = [line for line in stderr_lines if line.strip()]
                print(f"📝 Stderr lines: {len(stderr_lines)}")

                # stderrの内容を適切に分類
                for line in stderr_lines:
                    # 実際のエラーのみをエラーとして分類
                    if any(level in line for level in ['ERROR', 'CRITICAL']) or 'Traceback' in line:
                        error_lines.append(line)
                    # INFO、DEBUG、WARNINGは出力として分類
                    elif any(level in line for level in ['INFO', 'DEBUG', 'WARNING']):
                        output_lines.append(line)
                    # その他の行も出力として分類
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

            # デバッグ出力は標準出力に含まれているので、特別な処理は不要
            # 🐛 マークが付いた行がデバッグ出力として識別される

            # 実行時間を計算
            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "output": output_lines,
                "errors": error_lines,
                "extracted_data": extracted_data,
                "execution_time": execution_time
            }

    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        return {
            "output": output_lines,
            "errors": error_lines + [str(e), traceback.format_exc()],
            "extracted_data": extracted_data,
            "execution_time": execution_time
        }

@router.delete("/execution/{execution_id}")
async def cancel_execution(
    execution_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    実行をキャンセル
    """
    if execution_id in running_executions:
        running_executions[execution_id]["status"] = "cancelled"
        return {"message": "Execution cancelled"}
    else:
        raise HTTPException(status_code=404, detail="Execution not found")

@router.get("/execution/{execution_id}/export/{format}")
async def export_execution_data(
    execution_id: str,
    format: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    実行結果をエクスポート (CSV, JSON, Excel)
    """
    if execution_id not in running_executions:
        raise HTTPException(status_code=404, detail="Execution not found")

    execution_data = running_executions[execution_id]
    extracted_data = execution_data.get("extracted_data", [])

    if not extracted_data:
        raise HTTPException(status_code=400, detail="No data to export")

    if format.lower() == "json":
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=extracted_data,
            headers={"Content-Disposition": f"attachment; filename=scraped_data_{execution_id[:8]}.json"}
        )

    elif format.lower() == "csv":
        import csv
        import io
        from fastapi.responses import StreamingResponse

        # CSVデータを生成
        output = io.StringIO()
        if extracted_data:
            # 全てのキーを収集
            all_keys = set()
            for item in extracted_data:
                if isinstance(item, dict):
                    all_keys.update(item.keys())

            fieldnames = list(all_keys)
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            for item in extracted_data:
                if isinstance(item, dict):
                    # ネストされたオブジェクトを文字列に変換
                    flattened_item = {}
                    for key, value in item.items():
                        if isinstance(value, (dict, list)):
                            flattened_item[key] = json.dumps(value, ensure_ascii=False)
                        else:
                            flattened_item[key] = value
                    writer.writerow(flattened_item)

        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=scraped_data_{execution_id[:8]}.csv"}
        )

    elif format.lower() == "excel":
        import pandas as pd
        import io
        from fastapi.responses import StreamingResponse

        # DataFrameを作成
        df = pd.json_normalize(extracted_data)

        # Excelファイルを生成
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Scraped Data', index=False)

        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=scraped_data_{execution_id[:8]}.xlsx"}
        )

    elif format.lower() == "xml":
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        import io
        from fastapi.responses import StreamingResponse

        # XMLルート要素を作成
        root = ET.Element("scraped_data")
        root.set("execution_id", execution_id)
        root.set("total_items", str(len(extracted_data)))
        root.set("generated_at", datetime.now().isoformat())

        # メタデータ要素を追加
        metadata = ET.SubElement(root, "metadata")
        ET.SubElement(metadata, "execution_id").text = execution_id
        ET.SubElement(metadata, "total_items").text = str(len(extracted_data))
        ET.SubElement(metadata, "generated_at").text = datetime.now().isoformat()
        ET.SubElement(metadata, "format_version").text = "1.0"

        # アイテムコンテナを作成
        items_container = ET.SubElement(root, "items")

        # 各アイテムをXML要素として追加
        for index, item in enumerate(extracted_data):
            item_element = ET.SubElement(items_container, "item")
            item_element.set("index", str(index + 1))

            # アイテムのデータを再帰的にXML要素に変換
            def dict_to_xml(parent, data, name="data"):
                if isinstance(data, dict):
                    for key, value in data.items():
                        # キー名をXML要素名として使用（無効な文字を置換）
                        safe_key = str(key).replace(" ", "_").replace("-", "_")
                        safe_key = "".join(c for c in safe_key if c.isalnum() or c == "_")
                        if not safe_key or safe_key[0].isdigit():
                            safe_key = f"field_{safe_key}"

                        child = ET.SubElement(parent, safe_key)
                        dict_to_xml(child, value, safe_key)
                elif isinstance(data, list):
                    for i, item in enumerate(data):
                        child = ET.SubElement(parent, f"{name}_item")
                        child.set("index", str(i))
                        dict_to_xml(child, item, f"{name}_item")
                else:
                    parent.text = str(data) if data is not None else ""

            dict_to_xml(item_element, item)

        # XMLを文字列に変換（整形付き）
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")

        # UTF-8 BOMを除去し、適切なXMLヘッダーを追加
        if pretty_xml.startswith('<?xml version="1.0" ?>'):
            pretty_xml = '<?xml version="1.0" encoding="UTF-8"?>' + pretty_xml[22:]

        # XMLコメントを追加
        xml_comment = f"""
<!--
  ScrapyUI Exported Data
  Generated: {datetime.now().isoformat()}
  Execution ID: {execution_id}
  Total Items: {len(extracted_data)}
  Format: XML v1.0
-->
"""
        # XMLヘッダーの後にコメントを挿入
        if pretty_xml.startswith('<?xml'):
            header_end = pretty_xml.find('?>') + 2
            pretty_xml = pretty_xml[:header_end] + xml_comment + pretty_xml[header_end:]

        return StreamingResponse(
            io.BytesIO(pretty_xml.encode('utf-8')),
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename=scraped_data_{execution_id[:8]}.xml"}
        )

    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'json', 'csv', 'excel', or 'xml'")

@router.post("/test", response_model=ScriptExecutionResponse)
async def test_script(
    request: ScriptExecutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    スクリプトをテスト実行（短時間実行）
    """
    execution_id = str(uuid.uuid4())
    started_at = datetime.now().isoformat()

    # タスクをデータベースに記録
    project_id = request.project_id or "webui-test"
    # spider_idが提供されていない場合は、spider_nameをそのまま使用
    spider_id = request.spider_id or request.spider_name

    task = Task(
        id=execution_id,
        project_id=project_id,
        spider_id=spider_id,
        status="RUNNING",
        user_id=current_user.id,
        log_level="INFO",
        settings=request.settings or {}
    )
    db.add(task)
    db.commit()

    # 実行状態を初期化
    running_executions[execution_id] = {
        "status": "running",
        "output": [],
        "errors": [],
        "extracted_data": [],
        "started_at": started_at,
        "finished_at": None
    }

    try:
        print(f"🧪 Starting test script execution: {request.spider_name}")
        print(f"📝 Start URLs: {request.start_urls}")
        print(f"⚙️ Settings: {request.settings}")

        # スクリプトを実行（テスト用に短時間）
        use_playwright = "scrapy_playwright" in request.script_content or "playwright" in str(request.settings)
        print(f"🎭 Playwright detection: {use_playwright}")

        result = await execute_scrapy_script(
            request.script_content,
            request.spider_name,
            request.start_urls,
            request.settings or {},
            use_playwright=use_playwright
        )

        # 実行状態を更新
        finished_at = datetime.now().isoformat()
        running_executions[execution_id].update({
            "status": "completed",
            "output": result["output"],
            "errors": result["errors"],
            "extracted_data": result["extracted_data"],
            "finished_at": finished_at
        })

        # データベースのタスクを更新
        task.status = "FINISHED"
        task.finished_at = datetime.now()
        task.items_count = len(result["extracted_data"])
        db.commit()

        return ScriptExecutionResponse(
            execution_id=execution_id,
            status="completed",
            output=result["output"],
            errors=result["errors"],
            extracted_data=result["extracted_data"],
            execution_time=result["execution_time"],
            started_at=started_at,
            finished_at=finished_at
        )

    except Exception as e:
        # エラー時の処理
        error_message = str(e)
        finished_at = datetime.now().isoformat()

        running_executions[execution_id].update({
            "status": "failed",
            "errors": [error_message],
            "finished_at": finished_at
        })

        # データベースのタスクを更新
        task.status = "FAILED"
        task.finished_at = datetime.now()
        task.error_message = error_message
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Script test execution failed: {error_message}"
        )

@router.get("/history")
async def get_user_execution_history(
    limit: int = 20,
    current_user: User = Depends(get_current_active_user)
):
    """
    ユーザーの実行履歴を取得
    """
    history = get_execution_history(current_user.id, limit)
    return {"history": history}

@router.post("/save")
async def save_script(
    request: ScriptSaveRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    エディターのスクリプトを保存
    """
    try:
        # ユーザー専用のディレクトリを作成
        user_scripts_dir = Path(f"user_scripts/{current_user.id}")
        user_scripts_dir.mkdir(parents=True, exist_ok=True)

        # ファイル名の検証
        if not request.file_name.endswith('.py'):
            request.file_name += '.py'

        # 安全なファイル名に変換
        safe_filename = "".join(c for c in request.file_name if c.isalnum() or c in '._-')
        if not safe_filename:
            safe_filename = "script.py"

        # ファイルパス
        file_path = user_scripts_dir / safe_filename

        # ファイルに保存
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(request.content)

        return {
            "message": "Script saved successfully",
            "file_name": safe_filename,
            "file_path": str(file_path)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save script: {str(e)}"
        )

@router.get("/files")
async def get_user_scripts(
    current_user: User = Depends(get_current_active_user)
):
    """
    ユーザーの保存済みスクリプト一覧を取得
    """
    try:
        user_scripts_dir = Path(f"user_scripts/{current_user.id}")

        if not user_scripts_dir.exists():
            return {"files": []}

        files = []
        for file_path in user_scripts_dir.glob("*.py"):
            try:
                stat = file_path.stat()
                files.append({
                    "name": file_path.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "path": str(file_path.relative_to(user_scripts_dir))
                })
            except Exception:
                continue

        # 更新日時でソート
        files.sort(key=lambda x: x["modified"], reverse=True)

        return {"files": files}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get script files: {str(e)}"
        )

@router.get("/files/{file_name}")
async def get_script_content(
    file_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    保存済みスクリプトの内容を取得
    """
    try:
        # ファイル名の検証
        if '..' in file_name or '/' in file_name:
            raise HTTPException(status_code=400, detail="Invalid file name")

        user_scripts_dir = Path(f"user_scripts/{current_user.id}")
        file_path = user_scripts_dir / file_name

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "file_name": file_name,
            "content": content
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read script file: {str(e)}"
        )
