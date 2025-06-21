from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
import uuid

from ..database import get_db, Spider as DBSpider, Project as DBProject, User as DBUser, UserRole, ProjectFile
from ..models.schemas import Spider, SpiderCreate, SpiderUpdate
from ..services.scrapy_service import ScrapyPlaywrightService
from ..services.integrity_service import integrity_service
from ..services.default_settings_service import default_settings_service
from .auth import get_current_active_user

router = APIRouter(
    responses={
        404: {"description": "Not found"},
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"}
    }
)

# Pydanticモデル定義
class RunSpiderWithWatchdogRequest(BaseModel):
    settings: Dict[str, Any] = {}

class PuppeteerSpiderRequest(BaseModel):
    spider_name: str
    start_urls: List[str]
    spider_type: str = "spa"  # "spa" or "dynamic"
    puppeteer_config: Dict[str, Any] = {}
    extract_data: Dict[str, Any] = {}
    actions: List[Dict[str, Any]] = []  # for dynamic spiders
    custom_settings: Dict[str, Any] = {}


def sync_spider_file_to_database(db, project_id: str, project_path: str, spider_name: str, spider_code: str, user_id: str):
    """スパイダーファイルをデータベースに同期"""
    from datetime import datetime

    try:
        # スパイダーファイルのパス
        spider_file_path = f"{project_path}/spiders/{spider_name}.py"

        # データベースに既存のファイルがあるかチェック
        existing_file = db.query(ProjectFile).filter(
            ProjectFile.project_id == project_id,
            ProjectFile.path == spider_file_path
        ).first()

        if existing_file:
            # 既存ファイルを更新
            existing_file.content = spider_code
            existing_file.updated_at = datetime.now()
            print(f"✅ Updated spider file in database: {spider_file_path}")
        else:
            # 新しいファイルを作成
            db_file = ProjectFile(
                id=str(uuid.uuid4()),
                name=f"{spider_name}.py",
                path=spider_file_path,
                content=spider_code,
                file_type="python",
                project_id=project_id,
                user_id=user_id
            )
            db.add(db_file)
            print(f"✅ Added spider file to database: {spider_file_path}")

        # 変更をコミット
        db.commit()
        print(f"✅ Spider file synced to database: {spider_file_path}")
        return True

    except Exception as e:
        db.rollback()
        print(f"❌ Failed to sync spider file to database: {str(e)}")
        return False

@router.get(
    "/",
    response_model=List[Spider],
    summary="スパイダー一覧取得",
    description="指定されたプロジェクトまたは全てのスパイダーの一覧を取得します。",
    response_description="スパイダーのリスト"
)
async def get_spiders(
    project_id: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    ## スパイダー一覧取得

    指定されたプロジェクトまたは全てのスパイダーの一覧を取得します。

    ### パラメータ
    - **project_id** (optional): プロジェクトIDでフィルタリング

    ### レスポンス
    - **200**: スパイダーのリストを返します
    - **500**: サーバーエラー
    """
    query = db.query(DBSpider)

    # 管理者は全スパイダー、一般ユーザーは自分のスパイダーのみ
    is_admin = (current_user.role == UserRole.ADMIN or
                current_user.role == "ADMIN" or
                current_user.role == "admin")
    if not is_admin:
        query = query.filter(DBSpider.user_id == current_user.id)

    if project_id:
        query = query.filter(DBSpider.project_id == project_id)

    spiders = query.all()

    # 空のcodeフィールドを持つスパイダーにデフォルト値を設定
    for spider in spiders:
        if not spider.code or spider.code.strip() == "":
            spider.code = '''import scrapy

class DefaultSpider(scrapy.Spider):
    name = "default"

    def start_requests(self):
        urls = [
            "https://example.com",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        yield {
            "title": response.css("title::text").get(),
            "url": response.url,
        }
'''

    return spiders

@router.get("/{spider_id}", response_model=Spider)
async def get_spider(
    spider_id: str,
    db: Session = Depends(get_db)
    # current_user = Depends(get_current_active_user)  # 一時的に無効化
):
    """特定のスパイダーを取得"""
    spider = db.query(DBSpider).filter(DBSpider.id == spider_id).first()
    if not spider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spider not found"
        )

    # 一時的に権限チェックを無効化
    print(f"🔍 Spider access check temporarily disabled for spider {spider_id}")

    # 管理者以外は自分のスパイダーのみアクセス可能
    # is_admin = (current_user.role == UserRole.ADMIN or
    #             current_user.role == "ADMIN" or
    #             current_user.role == "admin")
    #
    # if not is_admin and spider.user_id != current_user.id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Access denied"
    #     )

    # 空のcodeフィールドを持つスパイダーにデフォルト値を設定
    if not spider.code or spider.code.strip() == "":
        spider.code = '''import scrapy

class DefaultSpider(scrapy.Spider):
    name = "default"

    def start_requests(self):
        urls = [
            "https://example.com",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        yield {
            "title": response.css("title::text").get(),
            "url": response.url,
        }
'''

    return spider

def update_spider_name_in_code(code: str, spider_name: str) -> str:
    """スパイダーコード内のname=とクラス名を更新する（継承関係を保持）"""
    import re

    if not code:
        return code

    updated_code = code

    # 1. name = "..." または name = '...' の形式を検索して置換（インデント保持）
    name_patterns = [
        r'(\s*)name\s*=\s*["\'][^"\']*["\']',  # インデントを含むname = "old_name"
        r'(\s*)name\s*=\s*"[^"]*"',           # インデントを含むname = "old_name"
        r"(\s*)name\s*=\s*'[^']*'"            # インデントを含むname = 'old_name'
    ]

    name_updated = False
    for pattern in name_patterns:
        match = re.search(pattern, updated_code)
        if match:
            # 元のインデントを保持して置換
            indent = match.group(1)
            # 既に正しい名前の場合はスキップ
            current_name_match = re.search(r'name\s*=\s*["\']([^"\']*)["\']', match.group(0))
            if current_name_match and current_name_match.group(1) == spider_name:
                print(f"🔄 Name attribute already correct: {spider_name}")
                name_updated = True
                break

            updated_code = re.sub(pattern, f'{indent}name = "{spider_name}"', updated_code)
            name_updated = True

    # 2. クラス名を更新（重要：これが欠けていた）
    class_name = spider_name_to_class_name(spider_name)

    # 既存のクラス定義を検索
    class_pattern = r'class\s+(\w+)\s*\([^)]*\):'
    class_match = re.search(class_pattern, updated_code)

    if class_match:
        old_class_name = class_match.group(1)
        # クラス名を新しい名前に置換
        updated_code = re.sub(
            r'class\s+' + re.escape(old_class_name) + r'\s*\(',
            f'class {class_name}(',
            updated_code
        )
        print(f"🔄 Updated class name: {old_class_name} -> {class_name}")
    else:
        print(f"⚠️ No class definition found in spider code")

    # name属性が見つからない場合の処理を追加
    if not name_updated:
        print(f"⚠️ Name attribute not found, adding it")
        # クラス定義の後に name 属性を追加
        class_pattern = r'(class\s+\w+.*?:)'
        if re.search(class_pattern, updated_code):
            updated_code = re.sub(class_pattern, f'\\1\n    name = "{spider_name}"', updated_code)
            print(f"🔧 Added missing name attribute")

    return updated_code

def spider_name_to_class_name(spider_name: str) -> str:
    """スパイダー名からクラス名を生成"""
    # アンダースコアを削除してキャメルケースに変換
    parts = spider_name.split('_')
    class_name = ''.join(word.capitalize() for word in parts)

    # Spiderサフィックスを追加（まだない場合）
    if not class_name.endswith('Spider'):
        class_name += 'Spider'

    return class_name

def auto_fix_spider_indentation(code: str) -> tuple[str, list[str]]:
    """スパイダーコードのインデントエラーを自動修正する"""
    import re

    if not code:
        return code, []

    lines = code.split('\n')
    fixed_lines = []
    fixes_applied = []
    in_class = False
    in_method = False
    current_method_indent = 0

    for i, line in enumerate(lines):
        line_num = i + 1

        # 空行やコメント行はそのまま
        if not line.strip() or line.strip().startswith('#'):
            fixed_lines.append(line)
            continue

        # import文やfrom文はクラス外
        if re.match(r'^(import|from)\s+', line):
            in_class = False
            in_method = False
            fixed_lines.append(line)
            continue

        # 関数定義（クラス外）
        if re.match(r'^def\s+', line):
            in_class = False
            in_method = False
            fixed_lines.append(line)
            continue

        # クラス定義を検出
        if re.match(r'^class\s+\w+.*?:', line):
            in_class = True
            in_method = False
            fixed_lines.append(line)
            print(f"🔍 Found class definition at line {line_num}: {line.strip()}")
            continue

        # 新しいクラス定義（前のクラス終了）
        if re.match(r'^class\s+', line):
            in_class = True
            in_method = False
            fixed_lines.append(line)
            continue

        # クラス内の処理
        if in_class:
            # メソッド定義
            if re.match(r'^\s*def\s+', line):
                in_method = True
                stripped_line = line.lstrip()
                expected_indent = '    '  # 4スペース

                # インデントが正しくない場合のみ修正
                if not line.startswith(expected_indent) and line.strip().startswith('def '):
                    fixed_line = expected_indent + stripped_line
                    fixed_lines.append(fixed_line)
                    fixes_applied.append(f"Line {line_num}: Fixed indentation for method definition")
                    print(f"🔧 Fixed line {line_num}: method definition")
                    continue
                else:
                    # 既に正しいインデント
                    fixed_lines.append(line)
                    continue

            # クラス属性（name, allowed_domains, start_urls, custom_settings など）
            elif re.match(r'^\s*(name|allowed_domains|start_urls|custom_settings|handle_httpstatus_list|target_items_per_page|target_pages|total_target_items)\s*=', line):
                in_method = False
                stripped_line = line.lstrip()
                expected_indent = '    '  # 4スペース

                # インデントが正しくない場合のみ修正
                if not line.startswith(expected_indent) and not line.startswith('        '):
                    fixed_line = expected_indent + stripped_line
                    fixed_lines.append(fixed_line)
                    fixes_applied.append(f"Line {line_num}: Fixed indentation for class attribute: {stripped_line.split('=')[0].strip()}")
                    print(f"🔧 Fixed line {line_num}: '{line.strip()}' -> '{fixed_line.strip()}'")
                    continue
                else:
                    # 既に正しいインデント
                    fixed_lines.append(line)
                    continue

            # その他のクラス内コード（既に適切にインデントされている場合はそのまま）
            elif line.strip():
                # 既に適切にインデントされている行はそのまま保持
                if line.startswith('    ') or line.startswith('        '):
                    fixed_lines.append(line)
                    continue

                # インデントされていない行（トップレベル）が見つかった場合、クラス外に出たと判断
                elif not line.startswith(' ') and not line.startswith('\t'):
                    in_class = False
                    in_method = False
                    fixed_lines.append(line)
                    continue

                # その他の場合はそのまま
                else:
                    fixed_lines.append(line)
                    continue

        # クラス外のコード
        else:
            fixed_lines.append(line)

    fixed_code = '\n'.join(fixed_lines)
    return fixed_code, fixes_applied

def validate_spider_inheritance(code: str, auto_fix: bool = False) -> dict:
    """スパイダーコードの継承関係とインデントをバリデーションする（自動修正オプション付き）"""
    import re

    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "fixes_applied": [],
        "fixed_code": code
    }

    if not code:
        validation_result["valid"] = False
        validation_result["errors"].append("コードが空です")
        return validation_result

    # まず元のコードでエラーを検出
    original_lines = code.split('\n')
    for i, line in enumerate(original_lines, 1):
        # name = の行をチェック
        if re.match(r'^\s*name\s*=', line):
            # クラス内の属性なので、インデントが必要
            if not line.startswith('    ') and not line.startswith('\t'):
                validation_result["errors"].append(f"Line {i}: 'name' attribute must be indented (class attribute)")

        # クラス定義内の他の属性もチェック
        if re.match(r'^\s*(allowed_domains|start_urls|custom_settings)\s*=', line):
            if not line.startswith('    ') and not line.startswith('\t'):
                validation_result["warnings"].append(f"Line {i}: Class attribute should be indented")

    # 自動修正を実行
    if auto_fix:
        fixed_code, fixes_applied = auto_fix_spider_indentation(code)
        validation_result["fixed_code"] = fixed_code
        validation_result["fixes_applied"].extend(fixes_applied)

        # 修正後のコードで再検証
        if fixes_applied:
            fixed_lines = fixed_code.split('\n')
            remaining_errors = []
            remaining_warnings = []

            for i, line in enumerate(fixed_lines, 1):
                # name = の行をチェック
                if re.match(r'^\s*name\s*=', line):
                    if not line.startswith('    ') and not line.startswith('\t'):
                        remaining_errors.append(f"Line {i}: 'name' attribute must be indented (class attribute)")

                # クラス定義内の他の属性もチェック
                if re.match(r'^\s*(allowed_domains|start_urls|custom_settings)\s*=', line):
                    if not line.startswith('    ') and not line.startswith('\t'):
                        remaining_warnings.append(f"Line {i}: Class attribute should be indented")

            # 修正後にエラーが残っていない場合は有効とする
            if not remaining_errors:
                validation_result["valid"] = True
                validation_result["errors"] = []
            else:
                validation_result["valid"] = False
                validation_result["errors"] = remaining_errors

            validation_result["warnings"] = remaining_warnings
    else:
        # 自動修正しない場合、エラーがあれば無効
        if validation_result["errors"]:
            validation_result["valid"] = False

    # 1. scrapy のインポートをチェック
    has_scrapy_import = 'import scrapy' in code or 'from scrapy' in code
    if not has_scrapy_import:
        validation_result["warnings"].append("scrapy のインポートが見つかりません")

    # 2. クラス定義をチェック
    class_patterns = [
        r'class\s+(\w+)\(scrapy\.Spider\):\s*',  # class ClassName(scrapy.Spider):
        r'class\s+(\w+)\(Spider\):\s*',          # class ClassName(Spider):
        r'class\s+(\w+):\s*',                    # class ClassName: (継承なし)
    ]

    class_found = False
    has_inheritance = False
    class_name = None

    for i, pattern in enumerate(class_patterns):
        match = re.search(pattern, code)
        if match:
            class_found = True
            class_name = match.group(1)
            if i < 2:  # 最初の2つのパターンは継承あり
                has_inheritance = True
            break

    if not class_found:
        validation_result["valid"] = False
        validation_result["errors"].append("スパイダークラスが見つかりません")
    elif not has_inheritance:
        validation_result["warnings"].append(f"クラス '{class_name}' が scrapy.Spider を継承していません")

    # 3. name 属性をチェック
    name_pattern = r'name\s*=\s*["\'][^"\']+["\']'
    if not re.search(name_pattern, code):
        validation_result["warnings"].append("name 属性が見つかりません")

    # 4. parse メソッドをチェック
    parse_pattern = r'def\s+parse\s*\('
    if not re.search(parse_pattern, code):
        validation_result["warnings"].append("parse メソッドが見つかりません")

    return validation_result

def update_project_imports_in_code(code: str, old_project_name: str, new_project_name: str) -> str:
    """スパイダーコード内のプロジェクト名を含むインポート文を更新する"""
    import re

    if not code or old_project_name == new_project_name:
        return code

    updated_code = code

    # プロジェクト名を含むインポート文を検索して置換
    # 例: from old_project.items import -> from new_project.items import
    import_patterns = [
        rf'from\s+{re.escape(old_project_name)}\.(\w+)\s+import',
        rf'import\s+{re.escape(old_project_name)}\.(\w+)',
    ]

    for pattern in import_patterns:
        matches = re.finditer(pattern, updated_code)
        for match in matches:
            old_import = match.group(0)
            if 'from' in old_import:
                # from old_project.module import -> from new_project.module import
                new_import = re.sub(rf'{re.escape(old_project_name)}\.', f'{new_project_name}.', old_import)
            else:
                # import old_project.module -> import new_project.module
                new_import = re.sub(rf'{re.escape(old_project_name)}\.', f'{new_project_name}.', old_import)

            updated_code = updated_code.replace(old_import, new_import)
            print(f"🔄 Updated import: {old_import} -> {new_import}")

    return updated_code

@router.post("/puppeteer", response_model=Spider, status_code=status.HTTP_201_CREATED)
async def create_puppeteer_spider(
    request: PuppeteerSpiderRequest,
    project_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Puppeteerスパイダーを作成"""

    # プロジェクトの存在確認
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # 管理者以外は自分のプロジェクトのみアクセス可能
    is_admin = (current_user.role == UserRole.ADMIN or
                current_user.role == "ADMIN" or
                current_user.role == "admin")
    if not is_admin and project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # スパイダー名の重複チェック
    existing_spider = db.query(DBSpider).filter(
        DBSpider.project_id == project_id,
        DBSpider.name == request.spider_name
    ).first()

    if existing_spider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Spider '{request.spider_name}' already exists in this project"
        )

    try:
        # Puppeteerスパイダーコードを生成
        try:
            from backend.app.templates.advanced_puppeteer_spider import get_puppeteer_spider_template
            spider_code = get_puppeteer_spider_template(
                request.spider_name,
                project.path,
                request.start_urls
            )
        except ImportError:
            # フォールバック: 従来の方法
            spider_code = generate_puppeteer_spider_code(request)

        # データベースにスパイダーを作成
        db_spider = DBSpider(
            id=str(uuid.uuid4()),
            name=request.spider_name,
            code=spider_code,
            template="puppeteer",
            project_id=project_id,
            user_id=current_user.id
        )

        db.add(db_spider)
        db.commit()
        db.refresh(db_spider)

        print(f"✅ Puppeteer spider created successfully: {request.spider_name}")
        return db_spider

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating Puppeteer spider: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Puppeteer spider: {str(e)}"
        )

def generate_puppeteer_spider_code(request: PuppeteerSpiderRequest) -> str:
    """Puppeteerスパイダーのコードを生成"""

    # クラス名を生成
    class_name = ''.join(word.capitalize() for word in request.spider_name.replace('_', ' ').replace('-', ' ').split())
    if not class_name.endswith('Spider'):
        class_name += 'Spider'

    # start_urlsの文字列を生成
    start_urls_str = ',\n        '.join([f'"{url}"' for url in request.start_urls])

    # extractDataの設定を生成
    extract_data_str = ""
    if request.extract_data:
        import json
        extract_data_str = f"""
                extractData={json.dumps(request.extract_data, indent=16).replace('    ', '')},"""

    # actionsの設定を生成（dynamicタイプの場合）
    actions_str = ""
    if request.spider_type == "dynamic" and request.actions:
        import json
        actions_str = f"""
            actions = {json.dumps(request.actions, indent=12).replace('    ', '')}

            yield self.make_dynamic_request(
                url=url,
                actions=actions,
                extract_after={json.dumps(request.extract_data, indent=16).replace('    ', '') if request.extract_data else 'None'}
            )"""
    else:
        actions_str = f"""yield self.make_puppeteer_request(
                url=url,{extract_data_str}
                screenshot=False,
                waitFor=3000
            )"""

    # カスタム設定を生成
    custom_settings_str = ""
    if request.custom_settings:
        import json
        custom_settings_str = f"""
    custom_settings = {json.dumps(request.custom_settings, indent=8).replace('    ', '')}"""

    # Puppeteerスパイダーコードテンプレート
    spider_code = f'''"""
{request.spider_name} - Puppeteerスパイダー
Generated by ScrapyUI
"""

import scrapy
import json
from datetime import datetime


class {class_name}(scrapy.Spider):
    """
    Puppeteerを使用したスパイダー
    JavaScript重要なSPAサイトやダイナミックコンテンツの取得
    """

    name = "{request.spider_name}"
    start_urls = [
        {start_urls_str}
    ]

    # Puppeteerサービスの設定
    puppeteer_service_url = 'http://localhost:3001'{custom_settings_str}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.puppeteer_config = {json.dumps(request.puppeteer_config, indent=12).replace('    ', '') if request.puppeteer_config else '{}'}

    def start_requests(self):
        """開始リクエストを生成"""
        for url in self.start_urls:
            {actions_str}

    def make_puppeteer_request(self, url, **kwargs):
        """Puppeteerを使用したリクエストを作成"""
        config = {{**self.puppeteer_config, **kwargs}}

        puppeteer_data = {{
            'url': url,
            'viewport': config.get('viewport', {{'width': 1920, 'height': 1080}}),
            'userAgent': config.get('userAgent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
            'timeout': config.get('timeout', 30000),
            'waitFor': config.get('waitFor', 3000),
            'extractData': config.get('extractData'),
            'screenshot': config.get('screenshot', False),
        }}

        puppeteer_data = {{k: v for k, v in puppeteer_data.items() if v is not None}}

        return scrapy.Request(
            url=f"{{self.puppeteer_service_url}}/api/scraping/spa",
            method='POST',
            headers={{'Content-Type': 'application/json'}},
            body=json.dumps(puppeteer_data),
            callback=self.parse_puppeteer_response,
            meta={{'original_url': url, 'puppeteer_data': puppeteer_data}}
        )

    def make_dynamic_request(self, url, actions, extract_after=None, **kwargs):
        """動的コンテンツ用のPuppeteerリクエストを作成"""
        config = {{**self.puppeteer_config, **kwargs}}

        puppeteer_data = {{
            'url': url,
            'actions': actions,
            'extractAfter': extract_after,
            'timeout': config.get('timeout', 30000),
        }}

        return scrapy.Request(
            url=f"{{self.puppeteer_service_url}}/api/scraping/dynamic",
            method='POST',
            headers={{'Content-Type': 'application/json'}},
            body=json.dumps(puppeteer_data),
            callback=self.parse_dynamic_response,
            meta={{'original_url': url, 'puppeteer_data': puppeteer_data}}
        )

    def parse_puppeteer_response(self, response):
        """Puppeteerサービスからのレスポンスを解析"""
        try:
            data = json.loads(response.text)

            if not data.get('success'):
                self.logger.error(f"Puppeteer scraping failed: {{data.get('message', 'Unknown error')}}")
                return

            scraping_data = data.get('data', {{}})
            original_url = response.meta.get('original_url')

            item = {{
                'url': original_url,
                'scraped_url': scraping_data.get('url'),
                'title': scraping_data.get('pageInfo', {{}}).get('title'),
                'timestamp': scraping_data.get('timestamp'),
                'scraped_at': datetime.now().isoformat(),
            }}

            # 抽出されたデータを追加
            if 'extractedData' in scraping_data:
                item.update(scraping_data['extractedData'])

            # カスタムJavaScriptの結果を追加
            if 'customData' in scraping_data:
                item['custom_data'] = scraping_data['customData']

            yield item

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Puppeteer response: {{e}}")
        except Exception as e:
            self.logger.error(f"Error processing Puppeteer response: {{e}}")

    def parse_dynamic_response(self, response):
        """動的コンテンツのレスポンスを解析"""
        try:
            data = json.loads(response.text)

            if not data.get('success'):
                self.logger.error(f"Dynamic scraping failed: {{data.get('message', 'Unknown error')}}")
                return

            original_url = response.meta.get('original_url')

            item = {{
                'url': original_url,
                'scraped_url': data.get('url'),
                'title': data.get('pageInfo', {{}}).get('title'),
                'timestamp': data.get('timestamp'),
                'actions_executed': data.get('actionsExecuted', 0),
                'scraped_at': datetime.now().isoformat(),
            }}

            # 抽出されたデータを追加
            if 'data' in data:
                item.update(data['data'])

            # カスタムJavaScriptの結果を追加
            if 'customData' in data:
                item['custom_data'] = data['customData']

            yield item

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse dynamic response: {{e}}")
        except Exception as e:
            self.logger.error(f"Error processing dynamic response: {{e}}")
'''

    return spider_code

@router.post("/", response_model=Spider, status_code=status.HTTP_201_CREATED)
async def create_spider(
    spider: SpiderCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """新しいスパイダーを作成"""

    try:
        print(f"DEBUG: Received spider creation request:")
        print(f"  name: {spider.name}")
        print(f"  project_id: {spider.project_id}")
        print(f"  template: {spider.template}")
        print(f"  code_length: {len(spider.code) if spider.code else 0}")
        print(f"  settings: {spider.settings}")

        # プロジェクトの存在確認
        project = db.query(DBProject).filter(DBProject.id == spider.project_id).first()
        if not project:
            print(f"DEBUG: Project not found: {spider.project_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
    except Exception as e:
        print(f"❌ Error in spider creation initial validation: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Spider creation validation failed: {str(e)}"
        )

    # スパイダー名の重複チェック
    existing_spider = db.query(DBSpider).filter(
        DBSpider.project_id == spider.project_id,
        DBSpider.name == spider.name
    ).first()
    if existing_spider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Spider with this name already exists in the project"
        )

    # デフォルト設定を適用（JSONL形式対応）
    spider_type = spider.template or "basic"
    default_settings = default_settings_service.get_spider_default_settings(spider_type)

    # 既存の設定とマージ
    merged_settings = default_settings.copy()
    if spider.settings:
        merged_settings.update(spider.settings)

    print(f"DEBUG: Applied default settings for spider type: {spider_type}")
    print(f"DEBUG: Default feed format: {merged_settings.get('FEEDS', {}).get('results.jsonl', {}).get('format', 'unknown')}")

    # スパイダーコード内のname=を確実に更新（継承関係も保持）
    updated_code = update_spider_name_in_code(spider.code, spider.name)
    print(f"DEBUG: Updated spider code name to: {spider.name}")
    print(f"DEBUG: Ensured scrapy.Spider inheritance")

    # まず基本的なバリデーションを実行（自動修正なし）
    validation_result = validate_spider_inheritance(updated_code, auto_fix=False)

    # 重大なエラーがある場合のみ自動修正を実行
    if validation_result["errors"]:
        print(f"DEBUG: Found validation errors, attempting auto-fix: {validation_result['errors']}")
        validation_result = validate_spider_inheritance(updated_code, auto_fix=True)
        if validation_result["fixes_applied"]:
            print(f"DEBUG: Auto-fixed issues: {validation_result['fixes_applied']}")
            updated_code = validation_result["fixed_code"]

    if validation_result["warnings"]:
        print(f"DEBUG: Validation warnings: {validation_result['warnings']}")

    if not validation_result["valid"]:
        print(f"DEBUG: Validation errors: {validation_result['errors']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Spider code validation failed: {'; '.join(validation_result['errors'])}"
        )

    # user_idの設定（認証されたユーザーから取得）
    user_id = current_user.id
    print(f"DEBUG: Using authenticated user_id = {user_id} (user: {current_user.email})")

    # ファイルシステムでの重複チェック
    scrapy_service = ScrapyPlaywrightService()
    spider_file_path = scrapy_service.base_projects_dir / project.path / project.path / "spiders" / f"{spider.name}.py"
    if spider_file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Spider file '{spider.name}.py' already exists in filesystem"
        )

    # トランザクション開始
    db_spider = None
    file_created = False

    try:
        # 1. データベースに保存（デフォルト設定適用）
        db_spider = DBSpider(
            id=str(uuid.uuid4()),
            name=spider.name,
            code=updated_code,
            template=spider.template,
            settings=merged_settings,  # デフォルト設定を適用
            project_id=spider.project_id,
            user_id=user_id
        )

        db.add(db_spider)
        db.flush()  # IDを取得するためにflush（commitはまだしない）

        # 2. ファイルシステムに保存
        scrapy_service.save_spider_code(project.path, spider.name, updated_code)
        file_created = True

        # 3. 整合性チェック
        if not spider_file_path.exists():
            raise Exception("File was not created successfully")

        # 4. スパイダーファイルをデータベースに同期
        try:
            sync_spider_file_to_database(
                db, spider.project_id, project.path, spider.name, updated_code, user_id
            )
            print(f"✅ Spider file synced to database: {spider.name}")
        except Exception as sync_error:
            print(f"⚠️ Failed to sync spider file to database: {sync_error}")
            # ファイル同期失敗は警告のみ（メイン処理は継続）

        # 5. 全て成功した場合のみcommit
        db.commit()
        db.refresh(db_spider)

        print(f"✅ Spider created successfully: {spider.name}")
        return db_spider

    except HTTPException:
        # HTTPExceptionはそのまま再発生
        raise
    except Exception as e:
        # エラー時のクリーンアップ
        print(f"❌ Error creating spider: {str(e)}")
        import traceback
        traceback.print_exc()

        # データベースロールバック
        try:
            if db_spider:
                db.rollback()
        except Exception as rollback_error:
            print(f"⚠️ Failed to rollback database: {rollback_error}")

        # ファイル削除
        try:
            if file_created and spider_file_path.exists():
                spider_file_path.unlink()
                print(f"🗑️ Cleaned up file: {spider_file_path}")
        except Exception as cleanup_error:
            print(f"⚠️ Failed to cleanup file: {cleanup_error}")

        # 詳細なエラー情報を含めて再発生
        error_detail = f"Failed to create spider: {str(e)}"
        if "validation" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_detail
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_detail
            )

@router.put("/{spider_id}", response_model=Spider)
async def update_spider(
    spider_id: str,
    spider_update: SpiderUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """スパイダーを更新"""
    db_spider = db.query(DBSpider).filter(DBSpider.id == spider_id).first()
    if not db_spider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spider not found"
        )

    # プロジェクト情報を取得
    project = db.query(DBProject).filter(DBProject.id == db_spider.project_id).first()

    # 更新データの適用
    update_data = spider_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_spider, field, value)

    db.commit()
    db.refresh(db_spider)

    # ファイルシステムのスパイダーファイルも更新
    if 'code' in update_data:
        try:
            scrapy_service = ScrapyPlaywrightService()
            scrapy_service.save_spider_code(project.path, db_spider.name, db_spider.code)

            # データベースのProjectFileテーブルも同期
            sync_spider_file_to_database(
                db, db_spider.project_id, project.path, db_spider.name, db_spider.code, db_spider.user_id
            )
            print(f"✅ Spider file updated and synced: {db_spider.name}")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update spider file: {str(e)}"
            )

    return db_spider

@router.delete("/{spider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_spider(
    spider_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """スパイダーを削除"""
    db_spider = db.query(DBSpider).filter(DBSpider.id == spider_id).first()
    if not db_spider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spider not found"
        )

    # プロジェクト情報を取得
    project = db.query(DBProject).filter(DBProject.id == db_spider.project_id).first()

    # スパイダーに関連するスケジュールを削除
    try:
        from ..database import Schedule as DBSchedule
        related_schedules = db.query(DBSchedule).filter(DBSchedule.spider_id == spider_id).all()

        if related_schedules:
            print(f"🗑️ Deleting {len(related_schedules)} schedules related to spider {db_spider.name}")
            for schedule in related_schedules:
                print(f"  - Deleting schedule: {schedule.name} (ID: {schedule.id})")
                db.delete(schedule)

        # 変更をコミット（スケジュール削除）
        db.commit()
        print(f"✅ Successfully deleted {len(related_schedules)} related schedules")

    except Exception as e:
        print(f"⚠️ Error deleting related schedules: {str(e)}")
        db.rollback()
        # スケジュール削除に失敗してもスパイダー削除は続行

    # ファイルシステムからスパイダーファイルを削除
    try:
        scrapy_service = ScrapyPlaywrightService()
        spider_file_path = scrapy_service.base_projects_dir / project.path / "spiders" / f"{db_spider.name}.py"
        if spider_file_path.exists():
            spider_file_path.unlink()
    except Exception as e:
        # ファイル削除に失敗してもデータベースからは削除する
        pass

    # ProjectFileテーブルからもスパイダーファイルを削除
    try:
        spider_file_path_db = f"{project.path}/spiders/{db_spider.name}.py"
        project_file = db.query(ProjectFile).filter(
            ProjectFile.project_id == db_spider.project_id,
            ProjectFile.path == spider_file_path_db
        ).first()
        if project_file:
            db.delete(project_file)
            print(f"✅ Removed spider file from database: {spider_file_path_db}")
    except Exception as e:
        print(f"⚠️ Failed to remove spider file from database: {str(e)}")

    db.delete(db_spider)
    db.commit()

    return None

@router.get("/{spider_id}/sync-from-filesystem")
async def sync_spider_code_from_filesystem(spider_id: str, db: Session = Depends(get_db)):
    """実際のファイルシステムからスパイダーのコードを取得"""
    try:
        db_spider = db.query(DBSpider).filter(DBSpider.id == spider_id).first()
        if not db_spider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Spider not found"
            )

        # プロジェクト情報を取得
        project = db.query(DBProject).filter(DBProject.id == db_spider.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # ScrapyPlaywrightServiceを使用して実際のファイルから読み取り
        scrapy_service = ScrapyPlaywrightService()
        code = scrapy_service.get_spider_code(project.path, db_spider.name)

        print(f"✅ Read spider code from filesystem: {db_spider.name}.py ({len(code)} chars)")

        return {
            "spider_id": spider_id,
            "spider_name": db_spider.name,
            "project_path": project.path,
            "code": code,
            "size": len(code.encode('utf-8'))
        }

    except Exception as e:
        print(f"❌ Failed to read spider code from filesystem: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read spider code from filesystem: {str(e)}"
        )

@router.get("/{spider_id}/code")
async def get_spider_code(spider_id: str, db: Session = Depends(get_db)):
    """スパイダーのコードを取得"""
    db_spider = db.query(DBSpider).filter(DBSpider.id == spider_id).first()
    if not db_spider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spider not found"
        )

    # プロジェクト情報を取得
    project = db.query(DBProject).filter(DBProject.id == db_spider.project_id).first()

    try:
        scrapy_service = ScrapyPlaywrightService()
        code = scrapy_service.get_spider_code(project.path, db_spider.name)
        return {"code": code}
    except Exception as e:
        # ファイルが見つからない場合はデータベースのコードを返す
        return {"code": db_spider.code}

@router.post("/{spider_id}/save")
async def save_spider_code(
    spider_id: str,
    code_data: dict,
    db: Session = Depends(get_db)
):
    """スパイダーのコードを保存"""
    db_spider = db.query(DBSpider).filter(DBSpider.id == spider_id).first()
    if not db_spider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spider not found"
        )

    code = code_data.get("code", "")
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code is required"
        )

    # プロジェクト情報を取得
    project = db.query(DBProject).filter(DBProject.id == db_spider.project_id).first()

    # データベースを更新
    db_spider.code = code
    db.commit()

    # ファイルシステムに保存
    try:
        scrapy_service = ScrapyPlaywrightService()
        scrapy_service.save_spider_code(project.path, db_spider.name, code)

        # データベースのProjectFileテーブルも同期
        sync_spider_file_to_database(
            db, db_spider.project_id, project.path, db_spider.name, code, db_spider.user_id
        )
        print(f"✅ Spider code saved and synced: {db_spider.name}")

        return {"message": "Code saved successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save spider code: {str(e)}"
        )

@router.post("/{spider_id}/validate")
async def validate_spider_code(spider_id: str, code_data: dict, db: Session = Depends(get_db)):
    """スパイダーコードの構文チェック（強化版）"""
    code = code_data.get("code", "")
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code is required"
        )

    try:
        scrapy_service = ScrapyPlaywrightService()

        # 基本的な構文チェック
        basic_result = scrapy_service.validate_spider_code(code)

        # 追加の構文チェック（括弧の不一致など）
        enhanced_result = validate_enhanced_syntax(code)

        # 結果をマージ
        result = {
            "valid": basic_result["valid"] and enhanced_result["valid"],
            "errors": basic_result["errors"] + enhanced_result["errors"],
            "warnings": enhanced_result.get("warnings", []),
            "suggestions": enhanced_result.get("suggestions", [])
        }

        return result
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Validation error: {str(e)}"]
        }

def validate_enhanced_syntax(code: str) -> dict:
    """強化された構文チェック"""
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "suggestions": []
    }

    if not code.strip():
        result["valid"] = False
        result["errors"].append("Code is empty")
        return result

    lines = code.split('\n')

    # 括弧の不一致チェック
    bracket_stack = []
    bracket_pairs = {'(': ')', '[': ']', '{': '}'}

    for line_num, line in enumerate(lines, 1):
        for char_pos, char in enumerate(line):
            if char in bracket_pairs:
                bracket_stack.append((char, line_num, char_pos))
            elif char in bracket_pairs.values():
                if not bracket_stack:
                    result["valid"] = False
                    result["errors"].append(f"Line {line_num}: Unmatched closing bracket '{char}'")
                else:
                    open_bracket, _, _ = bracket_stack.pop()
                    if bracket_pairs[open_bracket] != char:
                        result["valid"] = False
                        result["errors"].append(f"Line {line_num}: Mismatched bracket. Expected '{bracket_pairs[open_bracket]}' but found '{char}'")

    # 未閉じの括弧チェック
    if bracket_stack:
        for bracket, line_num, _ in bracket_stack:
            result["valid"] = False
            result["errors"].append(f"Line {line_num}: Unclosed bracket '{bracket}'")

    # 引用符の不一致チェック
    for line_num, line in enumerate(lines, 1):
        in_string = False
        quote_char = None
        i = 0
        while i < len(line):
            char = line[i]
            if char in ['"', "'"]:
                if not in_string:
                    in_string = True
                    quote_char = char
                elif char == quote_char:
                    # エスケープされていない場合のみ
                    if i == 0 or line[i-1] != '\\':
                        in_string = False
                        quote_char = None
            i += 1

        if in_string:
            result["warnings"].append(f"Line {line_num}: Unclosed string literal")

    # インデントの一貫性チェック
    indent_levels = []
    for line_num, line in enumerate(lines, 1):
        if line.strip():  # 空行は無視
            leading_spaces = len(line) - len(line.lstrip())
            if leading_spaces > 0:
                indent_levels.append((line_num, leading_spaces))

    # 4の倍数でないインデントを警告
    for line_num, indent in indent_levels:
        if indent % 4 != 0:
            result["warnings"].append(f"Line {line_num}: Indentation is not a multiple of 4 spaces")

    # 基本的なPython構文チェック
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError as e:
        result["valid"] = False
        result["errors"].append(f"Line {e.lineno}: {e.msg}")
    except Exception as e:
        result["warnings"].append(f"Compilation warning: {str(e)}")

    return result

@router.get(
    "/integrity/check",
    summary="整合性チェック",
    description="データベースとファイルシステムの整合性をチェックします。"
)
async def check_integrity():
    """データベースとファイルシステムの整合性をチェック"""
    try:
        result = integrity_service.check_integrity()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Integrity check failed: {str(e)}"
        )

@router.post(
    "/integrity/fix",
    summary="整合性修復",
    description="データベースとファイルシステムの整合性を修復します。"
)
async def fix_integrity(auto_fix: bool = False):
    """データベースとファイルシステムの整合性を修復"""
    try:
        result = integrity_service.fix_integrity_issues(auto_fix=auto_fix)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Integrity fix failed: {str(e)}"
        )

@router.get(
    "/integrity/report",
    summary="整合性レポート",
    description="データベースとファイルシステムの整合性レポートを取得します。"
)
async def get_integrity_report():
    """整合性レポートを取得"""
    try:
        report = integrity_service.generate_integrity_report()
        return {"report": report}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}"
        )

@router.post(
    "/{spider_id}/copy",
    response_model=Spider,
    status_code=status.HTTP_201_CREATED,
    summary="スパイダーコピー",
    description="既存のスパイダーをコピーして新しいスパイダーを作成します。整合性保証付き。"
)
async def copy_spider(
    spider_id: str,
    copy_data: dict,
    db: Session = Depends(get_db)
):
    """スパイダーをコピー（整合性保証付き）"""

    new_name = copy_data.get("name", "").strip()
    if not new_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New spider name is required"
        )

    # 元のスパイダーを取得
    original_spider = db.query(DBSpider).filter(DBSpider.id == spider_id).first()
    if not original_spider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original spider not found"
        )

    # プロジェクト情報を取得
    project = db.query(DBProject).filter(DBProject.id == original_spider.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # 重複チェック（データベース）
    existing_spider = db.query(DBSpider).filter(
        DBSpider.project_id == original_spider.project_id,
        DBSpider.name == new_name
    ).first()
    if existing_spider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Spider with name '{new_name}' already exists in this project"
        )

    # ファイルシステムでの重複チェック
    scrapy_service = ScrapyPlaywrightService()
    new_spider_file_path = scrapy_service.base_projects_dir / project.path / project.path / "spiders" / f"{new_name}.py"
    if new_spider_file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Spider file '{new_name}.py' already exists in filesystem"
        )

    # コード内のname=とクラス名を新しい名前に更新（継承関係も保持）
    updated_code = update_spider_name_in_code(original_spider.code, new_name)
    print(f"DEBUG: Updated copied spider code name to: {new_name}")
    print(f"DEBUG: Ensured scrapy.Spider inheritance in copied spider")

    # バリデーションと自動修正を実行
    validation_result = validate_spider_inheritance(updated_code, auto_fix=True)
    if validation_result["fixes_applied"]:
        print(f"DEBUG: Auto-fixed issues in copied spider: {validation_result['fixes_applied']}")
        updated_code = validation_result["fixed_code"]

    if validation_result["warnings"]:
        print(f"DEBUG: Copy validation warnings: {validation_result['warnings']}")
    if not validation_result["valid"]:
        print(f"DEBUG: Copy validation errors: {validation_result['errors']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Copied spider code validation failed: {'; '.join(validation_result['errors'])}"
        )

    # プロジェクト間でのコピーの場合、インポート文も更新
    # （現在は同一プロジェクト内のコピーのみサポートしているが、将来の拡張のため）
    # updated_code = update_project_imports_in_code(updated_code, old_project_name, new_project_name)

    # トランザクション開始
    new_spider = None
    file_created = False

    try:
        # 1. データベースに新しいスパイダーを作成
        new_spider = DBSpider(
            id=str(uuid.uuid4()),
            name=new_name,
            code=updated_code,
            template=original_spider.template,
            settings=original_spider.settings,
            project_id=original_spider.project_id,
            user_id=original_spider.user_id
        )

        db.add(new_spider)
        db.flush()  # IDを取得するためにflush（commitはまだしない）

        # 2. ファイルシステムに保存
        scrapy_service.save_spider_code(project.path, new_name, updated_code)
        file_created = True

        # 3. 整合性チェック
        if not new_spider_file_path.exists():
            raise Exception("File was not created successfully")

        # 4. スパイダーファイルをデータベースに同期
        try:
            sync_spider_file_to_database(
                db, original_spider.project_id, project.path, new_name, updated_code, original_spider.user_id
            )
            print(f"✅ Copied spider file synced to database: {new_name}")

            # 同期確認
            spider_file_path_db = f"{project.path}/spiders/{new_name}.py"
            synced_file = db.query(ProjectFile).filter(
                ProjectFile.project_id == original_spider.project_id,
                ProjectFile.path == spider_file_path_db
            ).first()
            if synced_file:
                print(f"✅ Copied spider file sync confirmed: {spider_file_path_db}")
            else:
                print(f"⚠️ Copied spider file sync verification failed: {spider_file_path_db}")
                # 同期確認失敗時は再試行
                sync_spider_file_to_database(
                    db, original_spider.project_id, project.path, new_name, updated_code, original_spider.user_id
                )
                print(f"🔄 Retried spider file sync for: {new_name}")
        except Exception as sync_error:
            print(f"❌ Failed to sync copied spider file to database: {sync_error}")
            # コピー時の同期失敗は重要なので、エラーとして扱う
            raise Exception(f"Database sync failed for copied spider: {sync_error}")

        # 5. 全て成功した場合のみcommit
        db.commit()
        db.refresh(new_spider)

        print(f"✅ Spider copied successfully: {original_spider.name} -> {new_name}")

        # 5. 整合性チェックを実行
        integrity_result = integrity_service.check_integrity()
        if not integrity_result['summary']['integrity_ok']:
            print(f"⚠️ Integrity check failed after copy operation")

        return new_spider

    except Exception as e:
        # エラー時のクリーンアップ
        print(f"❌ Error copying spider: {str(e)}")

        # データベースロールバック
        if new_spider:
            db.rollback()

        # ファイル削除
        if file_created and new_spider_file_path.exists():
            try:
                new_spider_file_path.unlink()
                print(f"🗑️ Cleaned up file: {new_spider_file_path}")
            except Exception as cleanup_error:
                print(f"⚠️ Failed to cleanup file: {cleanup_error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to copy spider: {str(e)}"
        )

@router.post(
    "/check-all-indentation",
    summary="全スパイダーファイルのインデントチェック",
    description="すべてのスパイダーファイルのインデントをチェックし、必要に応じて自動修正します。"
)
async def check_all_spider_indentation(
    auto_fix: bool = False,
    db: Session = Depends(get_db)
):
    """全スパイダーファイルのインデントチェックと自動修正"""

    try:
        scrapy_service = ScrapyPlaywrightService()
        results = {
            "total_spiders": 0,
            "checked_spiders": 0,
            "spiders_with_issues": 0,
            "spiders_fixed": 0,
            "details": []
        }

        # データベースからすべてのスパイダーを取得
        all_spiders = db.query(DBSpider).all()
        results["total_spiders"] = len(all_spiders)

        for spider in all_spiders:
            try:
                # プロジェクト情報を取得
                project = db.query(DBProject).filter(DBProject.id == spider.project_id).first()
                if not project:
                    continue

                # スパイダーファイルのパスを構築
                spider_file_path = scrapy_service.base_projects_dir / project.path / project.path / "spiders" / f"{spider.name}.py"

                spider_result = {
                    "spider_name": spider.name,
                    "project_name": project.name,
                    "file_path": str(spider_file_path),
                    "exists": spider_file_path.exists(),
                    "issues_found": [],
                    "fixes_applied": [],
                    "status": "checked"
                }

                # ファイルが存在する場合のみチェック
                if spider_file_path.exists():
                    try:
                        # ファイルからコードを読み取り
                        with open(spider_file_path, 'r', encoding='utf-8') as f:
                            file_code = f.read()

                        # バリデーションと自動修正を実行
                        validation_result = validate_spider_inheritance(file_code, auto_fix=auto_fix)

                        spider_result["issues_found"] = validation_result["errors"] + validation_result["warnings"]
                        spider_result["fixes_applied"] = validation_result["fixes_applied"]

                        if validation_result["errors"] or validation_result["warnings"]:
                            results["spiders_with_issues"] += 1

                        # 自動修正が適用された場合、ファイルを更新
                        if auto_fix and validation_result["fixes_applied"]:
                            try:
                                # ファイルシステムに保存
                                scrapy_service.save_spider_code(project.path, spider.name, validation_result["fixed_code"])

                                # データベースも更新
                                spider.code = validation_result["fixed_code"]
                                db.commit()

                                results["spiders_fixed"] += 1
                                spider_result["status"] = "fixed"

                                print(f"✅ Fixed spider: {spider.name} ({len(validation_result['fixes_applied'])} fixes)")

                            except Exception as save_error:
                                spider_result["status"] = "fix_failed"
                                spider_result["error"] = f"Failed to save fixes: {str(save_error)}"
                                print(f"❌ Failed to save fixes for {spider.name}: {save_error}")

                    except Exception as read_error:
                        spider_result["status"] = "read_error"
                        spider_result["error"] = f"Failed to read file: {str(read_error)}"
                        print(f"❌ Failed to read {spider.name}: {read_error}")

                else:
                    spider_result["status"] = "file_not_found"
                    spider_result["error"] = "Spider file not found in filesystem"

                results["details"].append(spider_result)
                results["checked_spiders"] += 1

            except Exception as spider_error:
                print(f"❌ Error processing spider {spider.name}: {spider_error}")
                results["details"].append({
                    "spider_name": spider.name,
                    "status": "error",
                    "error": str(spider_error)
                })

        # サマリーを出力
        print(f"📊 Indentation Check Summary:")
        print(f"   Total spiders: {results['total_spiders']}")
        print(f"   Checked: {results['checked_spiders']}")
        print(f"   With issues: {results['spiders_with_issues']}")
        print(f"   Fixed: {results['spiders_fixed']}")

        return results

    except Exception as e:
        print(f"❌ Error in check_all_spider_indentation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check spider indentation: {str(e)}"
        )

@router.post("/{spider_id}/run-with-watchdog")
async def run_spider_with_watchdog(
    spider_id: str,
    request: RunSpiderWithWatchdogRequest,
    project_id: str = Query(..., description="Project ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """watchdog監視付きでスパイダーを実行"""
    try:
        print(f"🚀 watchdog監視付きスパイダー実行開始: {spider_id}")
        print(f"📋 Project ID: {project_id}")
        print(f"👤 User: {current_user.email}")
        print(f"📦 Request data: {request}")
        print(f"⚙️ Settings: {request.settings}")

        # スパイダーの存在確認
        spider = db.query(DBSpider).filter(
            DBSpider.id == spider_id,
            DBSpider.project_id == project_id,
            DBSpider.user_id == current_user.id
        ).first()

        if not spider:
            raise HTTPException(status_code=404, detail="Spider not found")

        # プロジェクトの存在確認
        project = db.query(DBProject).filter(
            DBProject.id == project_id,
            DBProject.user_id == current_user.id
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # watchdog監視付きタスクを開始
        # Celeryタスクの代わりに直接実行（一時的な解決策）
        import uuid
        import asyncio
        from ..services.scrapy_watchdog_monitor import ScrapyWatchdogMonitor
        from pathlib import Path

        # タスクIDを生成
        task_id = str(uuid.uuid4())

        # プロジェクトパスを構築
        scrapy_service = ScrapyPlaywrightService()
        project_path = scrapy_service.base_projects_dir / project.path

        # データベースパスを絶対パスで指定
        import os
        # backend/app/api/spiders.py から backend/database/scrapy_ui.db へのパス
        current_file = os.path.abspath(__file__)  # backend/app/api/spiders.py
        app_dir = os.path.dirname(current_file)  # backend/app/api
        backend_dir = os.path.dirname(os.path.dirname(app_dir))  # backend/app -> backend
        db_path = os.path.join(backend_dir, "database", "scrapy_ui.db")

        # watchdog監視クラスを作成
        monitor = ScrapyWatchdogMonitor(
            task_id=task_id,
            project_path=str(project_path),
            spider_name=spider.name,
            db_path=db_path
        )

        # バックグラウンドで実行開始
        import threading
        def run_spider_background():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    monitor.execute_spider_with_monitoring(request.settings)
                )
                print(f"✅ Spider execution completed: {result}")
            except Exception as e:
                print(f"❌ Background spider execution error: {e}")
            finally:
                loop.close()

        # バックグラウンドスレッドで実行
        thread = threading.Thread(target=run_spider_background)
        thread.daemon = True
        thread.start()

        return {
            "task_id": task_id,
            "celery_task_id": task_id,
            "status": "started_with_watchdog",
            "monitoring": "jsonl_file_watchdog",
            "spider_name": spider.name,
            "project_name": project.name,
            "message": f"Spider {spider.name} started with watchdog monitoring"
        }

    except Exception as e:
        print(f"❌ Error running spider with watchdog: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/commands/available")
async def get_available_commands(
    project_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """プロジェクトで利用可能なScrapyコマンドを取得"""
    try:
        # プロジェクトの存在確認
        project = db.query(DBProject).filter(
            DBProject.id == project_id,
            DBProject.user_id == current_user.id
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # プロジェクトパスを構築
        from pathlib import Path
        scrapy_service = ScrapyPlaywrightService()
        project_path = scrapy_service.base_projects_dir / project.path
        commands_dir = project_path / project.path / "commands"

        available_commands = {
            "standard_commands": [
                {
                    "name": "crawl",
                    "description": "Run a spider",
                    "usage": "scrapy crawl <spider_name>",
                    "watchdog_support": False
                }
            ],
            "custom_commands": [],
            "watchdog_available": False
        }

        # watchdogライブラリの確認
        try:
            import watchdog
            available_commands["watchdog_available"] = True
        except ImportError:
            available_commands["watchdog_available"] = False

        # カスタムコマンドの確認
        if commands_dir.exists():
            crawlwithwatchdog_file = commands_dir / "crawlwithwatchdog.py"
            if crawlwithwatchdog_file.exists():
                available_commands["custom_commands"].append({
                    "name": "crawlwithwatchdog",
                    "description": "Run a spider with watchdog monitoring for real-time DB insertion",
                    "usage": "scrapy crawlwithwatchdog <spider_name> -o results.jsonl --task-id=<task_id>",
                    "watchdog_support": True,
                    "file_path": str(crawlwithwatchdog_file),
                    "requirements": ["watchdog"] if not available_commands["watchdog_available"] else []
                })

        return available_commands

    except Exception as e:
        print(f"❌ Error getting available commands: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
