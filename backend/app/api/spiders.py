from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from ..database import get_db, Spider as DBSpider, Project as DBProject
from ..models.schemas import Spider, SpiderCreate, SpiderUpdate
from ..services.scrapy_service import ScrapyPlaywrightService
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

    # 一時的にデフォルトユーザーIDを使用
    user_id = "admin-user-id"
    print(f"DEBUG: Using default user_id = {user_id}")

    # データベースに保存
    db_spider = DBSpider(
        id=str(uuid.uuid4()),
        name=spider.name,
        code=spider.code,
        template=spider.template,
        settings=spider.settings,
        project_id=spider.project_id,
        user_id=user_id
    )

    db.add(db_spider)
    db.commit()
    db.refresh(db_spider)

    # ファイルシステムにスパイダーファイルを保存
    try:
        scrapy_service = ScrapyPlaywrightService()
        scrapy_service.save_spider_code(project.path, spider.name, spider.code)
    except Exception as e:
        # データベースからロールバック
        db.delete(db_spider)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save spider file: {str(e)}"
        )

    return db_spider

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
