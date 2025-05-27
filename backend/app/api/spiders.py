from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from ..database import get_db, Spider as DBSpider, Project as DBProject
from ..models.schemas import Spider, SpiderCreate, SpiderUpdate
from ..services.scrapy_service import ScrapyPlaywrightService
from ..services.integrity_service import integrity_service
from .auth import get_current_active_user

router = APIRouter(
    responses={
        404: {"description": "Not found"},
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"}
    }
)

@router.get(
    "/",
    response_model=List[Spider],
    summary="スパイダー一覧取得",
    description="指定されたプロジェクトまたは全てのスパイダーの一覧を取得します。",
    response_description="スパイダーのリスト"
)
async def get_spiders(project_id: str = None, db: Session = Depends(get_db)):
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
    if project_id:
        query = query.filter(DBSpider.project_id == project_id)

    spiders = query.all()
    return spiders

@router.get("/{spider_id}", response_model=Spider)
async def get_spider(spider_id: str, db: Session = Depends(get_db)):
    """特定のスパイダーを取得"""
    spider = db.query(DBSpider).filter(DBSpider.id == spider_id).first()
    if not spider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spider not found"
        )
    return spider

def update_spider_name_in_code(code: str, spider_name: str) -> str:
    """スパイダーコード内のname=とクラス名を更新する（継承関係を保持）"""
    import re

    if not code:
        return code

    updated_code = code

    # 1. name = "..." または name = '...' の形式を検索して置換
    name_patterns = [
        r'name\s*=\s*["\'][^"\']*["\']',  # name = "old_name" または name = 'old_name'
        r'name\s*=\s*"[^"]*"',           # name = "old_name"
        r"name\s*=\s*'[^']*'"            # name = 'old_name'
    ]

    name_updated = False
    for pattern in name_patterns:
        if re.search(pattern, updated_code):
            updated_code = re.sub(pattern, f'name = "{spider_name}"', updated_code)
            name_updated = True
            break

    # name = が見つからない場合、クラス定義の後に追加
    if not name_updated:
        class_pattern = r'(class\s+\w+.*?Spider.*?:)'
        if re.search(class_pattern, updated_code):
            updated_code = re.sub(class_pattern, f'\\1\n    name = "{spider_name}"', updated_code)

    # 2. クラス名を更新（継承関係を確実に保持）
    # より詳細なクラス定義パターンを検出
    class_patterns = [
        # 継承ありのパターン
        r'class\s+(\w+)(\([^)]+\)):\s*',  # class ClassName(scrapy.Spider):
        # 継承なしのパターン（これを修正する）
        r'class\s+(\w+):\s*',             # class ClassName:
    ]

    class_match = None
    inheritance_part = ""

    # 継承ありのパターンを最初にチェック
    for pattern in class_patterns:
        class_match = re.search(pattern, updated_code)
        if class_match:
            if len(class_match.groups()) > 1:
                inheritance_part = class_match.group(2)  # (scrapy.Spider) 部分
            break

    if class_match:
        original_class_name = class_match.group(1)

        # 新しいクラス名を生成（CamelCase）
        new_class_name = ''.join(word.capitalize() for word in spider_name.replace('_', ' ').replace('-', ' ').split())
        if not new_class_name.endswith('Spider'):
            new_class_name += 'Spider'

        # 継承関係を確実に保持
        if not inheritance_part:
            # 継承がない場合は scrapy.Spider を追加
            inheritance_part = "(scrapy.Spider)"
            print(f"🔧 Added missing inheritance: scrapy.Spider")

        # クラス定義を置換
        old_class_pattern = re.escape(class_match.group(0))
        new_class_definition = f'class {new_class_name}{inheritance_part}:\n'
        updated_code = re.sub(old_class_pattern, new_class_definition, updated_code)

        print(f"🔄 Updated class: {original_class_name} -> {new_class_name}{inheritance_part}")

    # 3. scrapy のインポートを確認・追加
    if 'import scrapy' not in updated_code and 'from scrapy' not in updated_code:
        # scrapy のインポートがない場合は追加
        import_lines = []
        if 'import scrapy' not in updated_code:
            import_lines.append('import scrapy')

        if import_lines:
            # ファイルの先頭にインポートを追加
            updated_code = '\n'.join(import_lines) + '\n' + updated_code
            print(f"🔧 Added missing imports: {', '.join(import_lines)}")

    return updated_code

def validate_spider_inheritance(code: str) -> dict:
    """スパイダーコードの継承関係をバリデーションする"""
    import re

    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "fixes_applied": []
    }

    if not code:
        validation_result["valid"] = False
        validation_result["errors"].append("コードが空です")
        return validation_result

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

@router.post("/", response_model=Spider, status_code=status.HTTP_201_CREATED)
async def create_spider(
    spider: SpiderCreate,
    db: Session = Depends(get_db)
    # current_user = Depends(get_current_active_user)  # 一時的に無効化
):
    """新しいスパイダーを作成"""

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

    # スパイダーコード内のname=を確実に更新（継承関係も保持）
    updated_code = update_spider_name_in_code(spider.code, spider.name)
    print(f"DEBUG: Updated spider code name to: {spider.name}")
    print(f"DEBUG: Ensured scrapy.Spider inheritance")

    # バリデーションを実行
    validation_result = validate_spider_inheritance(updated_code)
    if validation_result["warnings"]:
        print(f"DEBUG: Validation warnings: {validation_result['warnings']}")
    if not validation_result["valid"]:
        print(f"DEBUG: Validation errors: {validation_result['errors']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Spider code validation failed: {'; '.join(validation_result['errors'])}"
        )

    # 一時的にデフォルトユーザーIDを使用
    user_id = "admin-user-id"
    print(f"DEBUG: Using default user_id = {user_id}")

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
        # 1. データベースに保存
        db_spider = DBSpider(
            id=str(uuid.uuid4()),
            name=spider.name,
            code=updated_code,
            template=spider.template,
            settings=spider.settings,
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

        # 4. 全て成功した場合のみcommit
        db.commit()
        db.refresh(db_spider)

        print(f"✅ Spider created successfully: {spider.name}")
        return db_spider

    except Exception as e:
        # エラー時のクリーンアップ
        print(f"❌ Error creating spider: {str(e)}")

        # データベースロールバック
        if db_spider:
            db.rollback()

        # ファイル削除
        if file_created and spider_file_path.exists():
            try:
                spider_file_path.unlink()
                print(f"🗑️ Cleaned up file: {spider_file_path}")
            except Exception as cleanup_error:
                print(f"⚠️ Failed to cleanup file: {cleanup_error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create spider: {str(e)}"
        )

@router.put("/{spider_id}", response_model=Spider)
async def update_spider(
    spider_id: str,
    spider_update: SpiderUpdate,
    db: Session = Depends(get_db)
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
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update spider file: {str(e)}"
            )

    return db_spider

@router.delete("/{spider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_spider(spider_id: str, db: Session = Depends(get_db)):
    """スパイダーを削除"""
    db_spider = db.query(DBSpider).filter(DBSpider.id == spider_id).first()
    if not db_spider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spider not found"
        )

    # プロジェクト情報を取得
    project = db.query(DBProject).filter(DBProject.id == db_spider.project_id).first()

    # ファイルシステムからスパイダーファイルを削除
    try:
        scrapy_service = ScrapyPlaywrightService()
        spider_file_path = scrapy_service.base_projects_dir / project.path / "spiders" / f"{db_spider.name}.py"
        if spider_file_path.exists():
            spider_file_path.unlink()
    except Exception as e:
        # ファイル削除に失敗してもデータベースからは削除する
        pass

    db.delete(db_spider)
    db.commit()

    return None

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
        return {"message": "Code saved successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save spider code: {str(e)}"
        )

@router.post("/{spider_id}/validate")
async def validate_spider_code(spider_id: str, code_data: dict, db: Session = Depends(get_db)):
    """スパイダーコードの構文チェック"""
    code = code_data.get("code", "")
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code is required"
        )

    try:
        scrapy_service = ScrapyPlaywrightService()
        result = scrapy_service.validate_spider_code(code)
        return result
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Validation error: {str(e)}"]
        }

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

    # バリデーションを実行
    validation_result = validate_spider_inheritance(updated_code)
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

        # 4. 全て成功した場合のみcommit
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
