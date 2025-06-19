from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import os
from datetime import datetime

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
    """プロジェクト作成時に全ファイルをデータベースに同期（完全スキャン版）"""
    from ..database import ProjectFile
    from pathlib import Path
    from datetime import datetime
    import os

    # 絶対パスでプロジェクトディレクトリを指定
    # backend/app/api/projects.py から backend/ まで2つ上がって、さらに1つ上がってプロジェクトルート
    base_dir = Path(__file__).parent.parent.parent.parent  # backend/app/api/ から4つ上がってプロジェクトルート
    scrapy_projects_dir = base_dir / "scrapy_projects"

    # プロジェクトディレクトリのパス（Scrapyプロジェクトの構造に対応）
    # scrapy_projects/project_name/project_name/ の形式
    project_dir = scrapy_projects_dir / project_path / project_path

    # フォールバック: 古い形式も試す
    if not project_dir.exists():
        project_dir = scrapy_projects_dir / project_path

    if not project_dir.exists():
        logger.warning(f"Project directory not found: {project_dir}")
        logger.info(f"   Checked paths:")
        logger.info(f"     - {scrapy_projects_dir / project_path / project_path}")
        logger.info(f"     - {scrapy_projects_dir / project_path}")
        logger.info(f"   Base directory: {base_dir}")
        logger.info(f"   Scrapy projects directory: {scrapy_projects_dir}")
        logger.info(f"   Current working directory: {os.getcwd()}")
        return

    logger.info(f"🔍 Starting complete file sync for project: {project_path}")
    logger.info(f"   Project directory: {project_dir}")

    synced_files = []

    try:
        # プロジェクトディレクトリ内のすべてのファイルを再帰的に検索
        for file_path in project_dir.rglob("*"):
            if file_path.is_file():
                # 相対パスを計算
                relative_path = file_path.relative_to(project_dir)
                relative_path_str = str(relative_path).replace("\\", "/")  # Windows対応

                # ファイルタイプを判定
                if file_path.suffix == ".py":
                    file_type = "python"
                elif file_path.suffix == ".cfg":
                    file_type = "config"
                elif file_path.suffix in [".txt", ".md", ".rst"]:
                    file_type = "text"
                elif file_path.suffix in [".json", ".yaml", ".yml"]:
                    file_type = "config"
                else:
                    file_type = "other"

                logger.info(f"   📄 Processing file: {relative_path_str} (type: {file_type})")

                try:
                    # ファイル内容を読み取り
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # データベースに既存のファイルがあるかチェック
                    existing_file = db.query(ProjectFile).filter(
                        ProjectFile.project_id == project_id,
                        ProjectFile.path == relative_path_str
                    ).first()

                    if existing_file:
                        # 既存ファイルを更新
                        existing_file.content = content
                        existing_file.updated_at = datetime.now()
                        logger.info(f"      ✅ Updated existing file in database")
                    else:
                        # 新しいファイルを作成
                        db_file = ProjectFile(
                            id=str(uuid.uuid4()),
                            name=file_path.name,
                            path=relative_path_str,
                            content=content,
                            file_type=file_type,
                            project_id=project_id,
                            user_id=user_id,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        db.add(db_file)
                        logger.info(f"      ✅ Added new file to database")

                    # 各ファイルを個別にコミット
                    try:
                        db.commit()
                        synced_files.append(relative_path_str)
                        logger.info(f"      💾 Committed to database")
                    except Exception as commit_error:
                        db.rollback()
                        logger.error(f"      ❌ Failed to commit file: {str(commit_error)}")

                except UnicodeDecodeError:
                    # バイナリファイルの場合はスキップ
                    logger.info(f"      ⏭️ Skipped binary file: {relative_path_str}")
                except Exception as e:
                    logger.error(f"      ❌ Failed to process file: {str(e)}")

    except Exception as e:
        logger.error(f"❌ Failed to scan project directory: {str(e)}")

    # 最終結果をログ出力
    logger.info(f"✅ Successfully synced {len(synced_files)} files to database")
    logger.info(f"   Synced files: {synced_files}")

    # 特別にcommands関連ファイルを確認
    commands_files = [f for f in synced_files if 'commands' in f]
    if commands_files:
        logger.info(f"🔧 Commands files synced: {commands_files}")
    else:
        logger.warning(f"⚠️ No commands files found in synced files")

    # settings.pyの確認
    settings_files = [f for f in synced_files if f.endswith('settings.py')]
    if settings_files:
        logger.info(f"⚙️ Settings files synced: {settings_files}")
    else:
        logger.warning(f"⚠️ No settings.py found in synced files")


def sync_spider_file_to_database(db, project_id: str, project_path: str, spider_name: str, spider_code: str, user_id: str):
    """スパイダーファイルをデータベースに同期"""
    from ..database import ProjectFile
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
            logger.info(f"Updated spider file in database: {spider_file_path}")
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
            logger.info(f"Added spider file to database: {spider_file_path}")

        # データベースにコミット
        db.commit()
        logger.info(f"Successfully synced spider file to database: {spider_name}")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to sync spider file to database: {str(e)}")
        raise







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
    try:
        # 管理者は全プロジェクト、一般ユーザーは自分のプロジェクトのみ
        # LEFT JOINを使用してユーザーが削除されたプロジェクトも取得
        if current_user.role == UserRole.ADMIN or current_user.role == "admin" or current_user.role == "ADMIN":
            projects = db.query(DBProject).outerjoin(DBUser).filter(DBProject.is_active == True).all()
        else:
            projects = db.query(DBProject).outerjoin(DBUser).filter(
                DBProject.user_id == current_user.id,
                DBProject.is_active == True
            ).all()

        # ユーザー名を含むレスポンスを作成
        result = []
        for project in projects:
            try:
                project_dict = {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "path": project.path,
                    "scrapy_version": project.scrapy_version,
                    "settings": project.settings or {},
                    "db_save_enabled": project.db_save_enabled,
                    "created_at": project.created_at,
                    "updated_at": project.updated_at,
                    "user_id": project.user_id,
                    "username": project.user.username if project.user else "Unknown User",
                    "is_active": project.is_active
                }
                result.append(project_dict)
            except Exception as e:
                print(f"⚠️ Error processing project {project.id}: {str(e)}")
                # 個別のプロジェクト処理エラーは無視して続行
                continue

        print(f"📊 Retrieved {len(result)} active projects for user {current_user.username}")
        return result

    except Exception as e:
        print(f"❌ Error in get_projects: {str(e)}")
        # エラーが発生した場合は空のリストを返す（フロントエンドの表示を維持）
        return []

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

    # 同期状態チェックは削除されました（自動同期により不要）

    project_dict = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "path": project.path,
        "scrapy_version": project.scrapy_version,
        "settings": project.settings or {},
        "db_save_enabled": project.db_save_enabled,
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
                # 新アーキテクチャ: クリーンなScrapyサービスを使用
                scrapy_service = ScrapyPlaywrightService()  # 名前は保持、内部はクリーン
                # プロジェクト名（ディレクトリ名）とプロジェクトパス（設定名）、DB保存設定を正しく指定
                # フロントエンドからdb_save_enabledが送信されない場合はデフォルトでTrueに設定
                db_save_enabled = getattr(project, 'db_save_enabled', True)
                scrapy_service.create_project(project_path, project_path, db_save_enabled)
                logger.info(f"Clean Scrapy project created successfully (new architecture): {project_path}")
            else:
                # テスト環境でもScrapyプロジェクトを作成（WebUI表示のため）
                scrapy_service = ScrapyPlaywrightService()  # 名前は保持、内部はクリーン
                db_save_enabled = getattr(project, 'db_save_enabled', True)
                scrapy_service.create_project(project_path, project_path, db_save_enabled)
                logger.info(f"Test clean Scrapy project created successfully (new architecture): {project_path}")
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
            db_save_enabled=getattr(project, 'db_save_enabled', True),
            user_id=current_user.id  # 現在のユーザーIDを設定
        )

        db.add(db_project)
        db.commit()
        db.refresh(db_project)

        # プロジェクトファイルをデータベースに同期（全ファイル）
        try:
            # TESTING環境でも同期を実行（WebUI表示のため）
            # 少し待ってからファイル同期（ファイル作成完了を確実にする）
            import time
            time.sleep(1.0)  # 待機時間を延長

            # まず通常のファイル同期を実行
            sync_project_files_to_database(db, db_project.id, project_path, current_user.id)
            logger.info(f"All project files synced to database for project: {project_path}")

            # pipelines.pyの特別な同期は不要になったため削除

            # 同期後の確認
            from ..database import ProjectFile
            synced_count = db.query(ProjectFile).filter(ProjectFile.project_id == db_project.id).count()
            pipelines_count = db.query(ProjectFile).filter(
                ProjectFile.project_id == db_project.id,
                ProjectFile.name == "pipelines.py"
            ).count()
            logger.info(f"Total files synced to database: {synced_count}")
            logger.info(f"pipelines.py files in database: {pipelines_count}")

            # pipelines.pyの内容を検証
            if pipelines_count > 0:
                pipelines_file = db.query(ProjectFile).filter(
                    ProjectFile.project_id == db_project.id,
                    ProjectFile.name == "pipelines.py"
                ).first()
                if pipelines_file:
                    try:
                        content = pipelines_file.content
                        if isinstance(content, bytes):
                            content = content.decode('utf-8')
                        has_scrapy_ui = 'ScrapyUIDatabasePipeline' in content
                        expected_has_scrapy_ui = db_project.db_save_enabled
                        if has_scrapy_ui == expected_has_scrapy_ui:
                            logger.info(f"✅ pipelines.py content verification passed: DB save={expected_has_scrapy_ui}, Has ScrapyUI={has_scrapy_ui}")
                        else:
                            logger.warning(f"⚠️ pipelines.py content verification failed: DB save={expected_has_scrapy_ui}, Has ScrapyUI={has_scrapy_ui}")
                    except Exception as e:
                        logger.error(f"Error verifying pipelines.py content in project creation: {e}")
                        has_scrapy_ui = False
        except Exception as e:
            logger.error(f"Failed to save project files to database: {str(e)}")
            # ファイル同期失敗は警告のみ（プロジェクト作成は成功とする）

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
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    """プロジェクトを削除（論理削除）"""
    try:
        db_project = db.query(DBProject).filter(DBProject.id == project_id).first()
        if not db_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # 管理者以外は自分のプロジェクトのみ削除可能
        is_admin = (current_user.role == UserRole.ADMIN or
                    current_user.role == "admin" or
                    current_user.role == "ADMIN")
        if not is_admin and db_project.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        print(f"🗑️ Deleting project: {db_project.name} (ID: {project_id})")

        # プロジェクトに関連するスケジュールを削除
        try:
            from ..database import Schedule as DBSchedule
            related_schedules = db.query(DBSchedule).filter(DBSchedule.project_id == project_id).all()

            if related_schedules:
                print(f"🗑️ Deleting {len(related_schedules)} schedules related to project {db_project.name}")
                for schedule in related_schedules:
                    print(f"  - Deleting schedule: {schedule.name} (ID: {schedule.id})")
                    db.delete(schedule)

            # 変更をコミット（スケジュール削除）
            db.commit()
            print(f"✅ Successfully deleted {len(related_schedules)} related schedules")

        except Exception as e:
            print(f"⚠️ Error deleting related schedules: {str(e)}")
            db.rollback()
            # スケジュール削除に失敗してもプロジェクト削除は続行

        # 論理削除（is_activeをFalseに設定）
        db_project.is_active = False
        db.commit()

        print(f"✅ Project {db_project.name} marked as inactive (logical deletion)")

        # 物理的なディレクトリ削除は行わない（データ保護のため）
        # 必要に応じて管理者が手動で削除可能

        return None

    except HTTPException:
        # HTTPExceptionの場合は再発生
        raise
    except Exception as e:
        print(f"❌ Error in delete_project: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )


# 手動同期エンドポイントは削除されました
# プロジェクト作成時に自動同期されるため、手動同期は不要です


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

            # スパイダーファイルをデータベースに同期
            try:
                sync_spider_file_to_database(db, project.id, project.path, spider_name, spider_code, current_user.id)
                logger.info(f"Spider file synced to database: {spider_name}")

                # 同期確認
                from ..database import ProjectFile
                spider_file_path = f"{project.path}/spiders/{spider_name}.py"
                synced_file = db.query(ProjectFile).filter(
                    ProjectFile.project_id == project.id,
                    ProjectFile.path == spider_file_path
                ).first()
                if synced_file:
                    logger.info(f"Spider file sync confirmed: {spider_file_path}")
                else:
                    logger.warning(f"Spider file sync verification failed: {spider_file_path}")
            except Exception as sync_error:
                logger.error(f"Failed to sync spider file to database: {sync_error}")
                # 同期失敗は警告のみ（スパイダー作成は成功とする）
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
