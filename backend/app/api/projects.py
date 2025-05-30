from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import os

from ..database import get_db, Project as DBProject, Spider as DBSpider, User as DBUser, UserRole
from ..models.schemas import Project, ProjectCreate, ProjectUpdate, ProjectWithSpiders, ProjectWithUser, Spider, SpiderCreate
from ..services.scrapy_service import ScrapyPlaywrightService
from ..api.auth import get_current_active_user

# ロギングとエラーハンドリングのインポート
from ..utils.logging_config import get_logger, log_with_context, log_exception
from ..utils.error_handler import (
    ScrapyUIException,
    ProjectException,
    ResourceNotFoundException,
    AuthorizationException,
    ErrorCode,
    handle_exception
)

# ロガーを初期化
logger = get_logger(__name__)

router = APIRouter(
    responses={
        404: {"description": "Not found"},
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"}
    }
)


def sync_project_files_to_database(db, project_id: str, project_path: str, user_id: str):
    """プロジェクト作成時に全ファイルをデータベースに同期"""
    from ..database import ProjectFile
    from pathlib import Path
    from datetime import datetime

    # プロジェクトディレクトリのパス
    project_dir = Path(f"./scrapy_projects/{project_path}")

    if not project_dir.exists():
        logger.warning(f"Project directory not found: {project_dir}")
        return

    # 同期対象のファイルパターン
    file_patterns = [
        # ルートレベルのファイル
        ("scrapy.cfg", "config"),

        # プロジェクトパッケージ内のファイル
        (f"{project_path}/__init__.py", "python"),
        (f"{project_path}/settings.py", "python"),
        (f"{project_path}/items.py", "python"),
        (f"{project_path}/pipelines.py", "python"),
        (f"{project_path}/middlewares.py", "python"),

        # spidersディレクトリ内のファイル
        (f"{project_path}/spiders/__init__.py", "python"),
    ]

    synced_files = []

    for file_path, file_type in file_patterns:
        full_path = project_dir / file_path

        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # ファイル名を取得
                file_name = full_path.name

                # データベースに既存のファイルがあるかチェック（pathで判定）
                existing_file = db.query(ProjectFile).filter(
                    ProjectFile.project_id == project_id,
                    ProjectFile.path == file_path
                ).first()

                if existing_file:
                    # 既存ファイルを更新
                    existing_file.content = content
                    existing_file.updated_at = datetime.now()
                    logger.info(f"Updated existing file in database: {file_path}")
                else:
                    # 新しいファイルを作成
                    db_file = ProjectFile(
                        id=str(uuid.uuid4()),
                        name=file_name,
                        path=file_path,
                        content=content,
                        file_type=file_type,
                        project_id=project_id,
                        user_id=user_id
                    )
                    db.add(db_file)
                    logger.info(f"Added new file to database: {file_path}")

                # 各ファイルを個別にコミット
                try:
                    db.commit()
                    synced_files.append(file_path)
                except Exception as commit_error:
                    db.rollback()
                    logger.error(f"Failed to commit file {file_path}: {str(commit_error)}")

            except Exception as e:
                logger.error(f"Failed to sync file {file_path}: {str(e)}")

    # 最終結果をログ出力
    logger.info(f"Successfully synced {len(synced_files)} files to database: {synced_files}")

@router.get(
    "/",
    response_model=List[ProjectWithUser],
    summary="プロジェクト一覧取得",
    description="登録されているすべてのScrapyプロジェクトの一覧を取得します。",
    response_description="プロジェクトのリスト"
)
async def get_projects(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    ## プロジェクト一覧取得

    登録されているすべてのScrapyプロジェクトの一覧を取得します。

    ### レスポンス
    - **200**: プロジェクトのリストを返します
    - **500**: サーバーエラー
    """
    # 管理者は全プロジェクト、一般ユーザーは自分のプロジェクトのみ
    if current_user.role == UserRole.ADMIN or current_user.role == "admin" or current_user.role == "ADMIN":
        projects = db.query(DBProject).join(DBUser).all()
    else:
        projects = db.query(DBProject).filter(DBProject.user_id == current_user.id).join(DBUser).all()

    # ユーザー名を含むレスポンスを作成
    result = []
    for project in projects:
        project_dict = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "path": project.path,
            "scrapy_version": project.scrapy_version,
            "settings": project.settings,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "user_id": project.user_id,
            "username": project.user.username if project.user else None,
            "is_active": project.is_active  # is_activeフィールドを追加
        }
        result.append(project_dict)

    return result

@router.get("/{project_id}", response_model=ProjectWithSpiders)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    """特定のプロジェクトを取得（スパイダー情報含む）"""
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # 管理者以外は自分のプロジェクトのみアクセス可能
    is_admin = (current_user.role == UserRole.ADMIN or
                current_user.role == "admin" or
                current_user.role == "ADMIN")
    if not is_admin and project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # スパイダー情報も含めて返す
    spiders = db.query(DBSpider).filter(DBSpider.project_id == project_id).all()

    # スパイダー情報を適切にフォーマット
    formatted_spiders = []
    for spider in spiders:
        spider_dict = {
            "id": spider.id,
            "name": spider.name,
            "description": spider.description or "",
            "code": spider.code or "# Empty spider code",  # 空の場合はデフォルトコメントを設定
            "template": spider.template,
            "framework": spider.framework or "scrapy",
            "start_urls": spider.start_urls or [],
            "settings": spider.settings or {},
            "project_id": spider.project_id,
            "created_at": spider.created_at,
            "updated_at": spider.updated_at
        }
        formatted_spiders.append(spider_dict)

    project_dict = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "path": project.path,
        "scrapy_version": project.scrapy_version,
        "settings": project.settings or {},
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "spiders": formatted_spiders
    }

    return project_dict

@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    """新しいプロジェクトを作成"""

    try:
        log_with_context(
            logger, "INFO",
            f"Creating new project: {project.name}",
            extra_data={"project_name": project.name, "description": project.description}
        )

        # プロジェクト名の重複チェック（ユーザー別）
        existing_project = db.query(DBProject).filter(
            DBProject.name == project.name,
            DBProject.user_id == current_user.id
        ).first()
        if existing_project:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"プロジェクト名 '{project.name}' は既に存在します。別の名前を選択してください。"
            )

        # ユーザー名ベースのプロジェクトパスを生成
        # フォーマット: <username>_<projectname>
        username = current_user.username.lower().replace(' ', '_').replace('-', '_')
        project_name_clean = project.name.lower().replace(' ', '_').replace('-', '_')
        project_path = f"{username}_{project_name_clean}"

        # プロジェクトパスの重複チェック（念のため）
        existing_path = db.query(DBProject).filter(DBProject.path == project_path).first()
        if existing_path:
            # 同じユーザーで同じプロジェクト名の場合は既に上でチェック済み
            # 異なるユーザーで同じusername_projectnameになる場合のみここに到達
            project_path = f"{project_path}_{str(uuid.uuid4())[:8]}"

        # Scrapyプロジェクトの作成（scrapy startproject project_name と同じ動作）
        try:
            # テスト環境では実際のScrapyプロジェクト作成をスキップ
            if not os.getenv("TESTING", False):
                scrapy_service = ScrapyPlaywrightService()
                # プロジェクト名（ディレクトリ名）とプロジェクトパス（設定名）を正しく指定
                scrapy_service.create_project(project_path, project_path)
                logger.info(f"Scrapy project created successfully: {project_path}")
            else:
                # テスト環境では単純にディレクトリを作成
                project_dir = f"./scrapy_projects/{project_path}"
                os.makedirs(project_dir, exist_ok=True)
                logger.info(f"Test project directory created: {project_dir}")
        except Exception as e:
            # プロジェクト作成に失敗してもデータベースには保存する（テスト用）
            log_exception(
                logger, f"Warning: Failed to create Scrapy project: {str(e)}",
                extra_data={"project_name": project.name, "project_path": project_path}
            )

        # データベースに保存
        db_project = DBProject(
            id=str(uuid.uuid4()),
            name=project.name,
            description=project.description,
            path=project_path,
            scrapy_version=project.scrapy_version or "2.11.0",
            settings=project.settings or {},
            user_id=current_user.id  # 現在のユーザーIDを設定
        )

        db.add(db_project)
        db.commit()
        db.refresh(db_project)

        # プロジェクトファイルをデータベースに同期（全ファイル）
        try:
            if not os.getenv("TESTING", False):
                sync_project_files_to_database(db, db_project.id, project_path, current_user.id)
                logger.info(f"All project files synced to database for project: {project_path}")
        except Exception as e:
            logger.warning(f"Failed to save project files to database: {str(e)}")

        log_with_context(
            logger, "INFO",
            f"Project created successfully: {project.name}",
            project_id=db_project.id,
            extra_data={"project_path": project_path}
        )

        return db_project

    except HTTPException:
        # HTTPExceptionの場合は再発生
        raise
    except ProjectException:
        # 既にProjectExceptionの場合は再発生
        raise
    except Exception as e:
        error_msg = f"Failed to create project: {str(e)}"
        log_exception(
            logger, error_msg,
            extra_data={"project_name": project.name}
        )
        raise ProjectException(
            message=error_msg,
            error_code=ErrorCode.PROJECT_CREATION_FAILED,
            details={"original_error": str(e)}
        )

@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """プロジェクトを更新"""
    db_project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # 更新データの適用
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)

    db.commit()
    db.refresh(db_project)

    return db_project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """プロジェクトを削除"""
    db_project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Scrapyプロジェクトディレクトリの削除（オプション）
    try:
        scrapy_service = ScrapyPlaywrightService()
        scrapy_service.delete_project(db_project.path)
    except Exception as e:
        # ディレクトリ削除に失敗してもデータベースからは削除する
        pass

    db.delete(db_project)
    db.commit()

    return None


@router.post("/{project_id}/spiders/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_project_spider(
    project_id: str,
    spider_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """プロジェクトにスパイダーを作成"""
    # プロジェクトの存在確認
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # スパイダー名の重複チェック
    spider_name = spider_data.get("name")
    if not spider_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Spider name is required"
        )

    existing_spider = db.query(DBSpider).filter(
        DBSpider.project_id == project_id,
        DBSpider.name == spider_name
    ).first()
    if existing_spider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Spider with this name already exists in the project"
        )

    # データベースに保存
    db_spider = DBSpider(
        id=str(uuid.uuid4()),
        name=spider_name,
        code=spider_data.get("script", spider_data.get("code", "")),
        template=spider_data.get("template"),
        settings=spider_data.get("settings", {}),
        project_id=project_id,
        user_id=current_user.id
    )

    db.add(db_spider)
    db.commit()
    db.refresh(db_spider)

    # ファイルシステムにスパイダーファイルを保存
    try:
        if not os.getenv("TESTING", False):
            scrapy_service = ScrapyPlaywrightService()
            spider_code = spider_data.get("script", spider_data.get("code", ""))
            scrapy_service.save_spider_code(project.path, spider_name, spider_code)
    except Exception as e:
        # データベースからロールバック
        db.delete(db_spider)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save spider file: {str(e)}"
        )

    return {
        "id": db_spider.id,
        "name": db_spider.name,
        "project_id": db_spider.project_id,
        "start_urls": spider_data.get("start_urls", []),
        "created_at": db_spider.created_at.isoformat() if db_spider.created_at else None
    }
