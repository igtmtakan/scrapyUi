from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

from .auth import get_current_active_user
from ..database import User, UserRole
from ..config.database_config import get_database_config, db_config_manager, DatabaseType
from ..services.database_service import get_database_service

router = APIRouter()

def require_admin_role(current_user: User = Depends(get_current_active_user)):
    """管理者権限を要求するデコレータ"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    return current_user

class DatabaseConfigResponse(BaseModel):
    type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    charset: Optional[str] = None
    # パスワードは返さない

    class Config:
        # 型変換を許可
        str_strip_whitespace = True

class DatabaseHealthResponse(BaseModel):
    type: str
    status: str
    message: str
    timestamp: datetime

class DatabaseConfigUpdate(BaseModel):
    type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    echo: Optional[bool] = None
    pool_size: Optional[int] = None
    max_overflow: Optional[int] = None
    charset: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

@router.get("/config", response_model=DatabaseConfigResponse)
async def get_current_database_config(
    current_user: User = Depends(require_admin_role)
):
    """
    現在のデータベース設定を取得
    """
    try:
        config = get_database_config()

        return DatabaseConfigResponse(
            type=config.type.value,
            host=config.host,
            port=config.port,
            database=str(config.database) if config.database is not None else None,
            username=config.username,
            echo=config.echo,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            charset=config.charset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database config: {str(e)}")

@router.get("/configs", response_model=Dict[str, DatabaseConfigResponse])
async def get_all_database_configs(
    current_user: User = Depends(require_admin_role)
):
    """
    全データベース設定を取得
    """
    try:
        configs = db_config_manager.get_all_configs()

        response = {}
        for env_name, config in configs.items():
            response[env_name] = DatabaseConfigResponse(
                type=config.type.value,
                host=config.host,
                port=config.port,
                database=str(config.database) if config.database is not None else None,
                username=config.username,
                echo=config.echo,
                pool_size=config.pool_size,
                max_overflow=config.max_overflow,
                charset=config.charset
            )

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database configs: {str(e)}")

@router.get("/health", response_model=List[DatabaseHealthResponse])
async def check_database_health(
    current_user: User = Depends(require_admin_role)
):
    """
    データベース接続状況をチェック
    """
    health_results = []

    # メインデータベース（SQLAlchemy）
    try:
        config = get_database_config()
        from app.database import engine

        # 接続テスト
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        health_results.append(DatabaseHealthResponse(
            type=config.type.value,
            status="healthy",
            message="Connection successful",
            timestamp=datetime.now()
        ))
    except Exception as e:
        health_results.append(DatabaseHealthResponse(
            type=config.type.value,
            status="unhealthy",
            message=str(e),
            timestamp=datetime.now()
        ))

    # NoSQLデータベース
    for db_type in [DatabaseType.MONGODB, DatabaseType.ELASTICSEARCH, DatabaseType.REDIS]:
        try:
            service = await get_database_service(db_type)
            if service:
                is_healthy = await service.health_check()
                health_results.append(DatabaseHealthResponse(
                    type=db_type.value,
                    status="healthy" if is_healthy else "unhealthy",
                    message="Connection successful" if is_healthy else "Connection failed",
                    timestamp=datetime.now()
                ))
        except Exception as e:
            health_results.append(DatabaseHealthResponse(
                type=db_type.value,
                status="error",
                message=str(e),
                timestamp=datetime.now()
            ))

    return health_results

@router.get("/types", response_model=List[str])
async def get_supported_database_types():
    """
    サポートするデータベースタイプ一覧を取得
    """
    return [db_type.value for db_type in DatabaseType]

@router.post("/test-connection")
async def test_database_connection(
    config_data: DatabaseConfigUpdate,
    current_user: User = Depends(require_admin_role)
):
    """
    データベース接続をテスト
    """
    try:
        from app.config.database_config import DatabaseConfig, DatabaseType

        # 設定オブジェクトを作成
        db_type = DatabaseType(config_data.type)
        test_config = DatabaseConfig(
            type=db_type,
            host=config_data.host,
            port=config_data.port,
            database=config_data.database,
            username=config_data.username,
            password=config_data.password,
            echo=config_data.echo or False,
            pool_size=config_data.pool_size or 5,
            max_overflow=config_data.max_overflow or 10,
            charset=config_data.charset,
            options=config_data.options
        )

        # 設定の妥当性をチェック
        db_config_manager.validate_config(test_config)

        # 接続テスト
        if db_type in [DatabaseType.SQLITE, DatabaseType.MYSQL, DatabaseType.POSTGRESQL]:
            from sqlalchemy import create_engine, text

            connection_url = test_config.get_connection_url()
            test_engine = create_engine(connection_url, echo=False)

            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            test_engine.dispose()

        elif db_type in [DatabaseType.MONGODB, DatabaseType.ELASTICSEARCH, DatabaseType.REDIS]:
            from app.services.database_service import DatabaseServiceFactory

            service = DatabaseServiceFactory.create_service(test_config)
            await service.connect()

            is_healthy = await service.health_check()
            if not is_healthy:
                raise Exception("Health check failed")

            await service.disconnect()

        return {
            "status": "success",
            "message": "Connection test successful",
            "timestamp": datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection test failed: {str(e)}")

@router.get("/statistics")
async def get_database_statistics(
    current_user: User = Depends(require_admin_role)
):
    """
    データベース統計情報を取得
    """
    try:
        from app.database import SessionLocal, Project, Spider, Task, Result, User as UserModel

        db = SessionLocal()
        try:
            stats = {
                "users": db.query(UserModel).count(),
                "projects": db.query(Project).count(),
                "spiders": db.query(Spider).count(),
                "tasks": db.query(Task).count(),
                "results": db.query(Result).count(),
            }

            # タスクステータス別統計
            from app.database import TaskStatus
            task_stats = {}
            for status in TaskStatus:
                count = db.query(Task).filter(Task.status == status).count()
                task_stats[status.value] = count

            stats["task_status"] = task_stats

            return {
                "database_type": get_database_config().type.value,
                "statistics": stats,
                "timestamp": datetime.now()
            }

        finally:
            db.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database statistics: {str(e)}")

@router.post("/migrate")
async def migrate_database(
    target_config: DatabaseConfigUpdate,
    current_user: User = Depends(require_admin_role)
):
    """
    データベースマイグレーション（注意：実装は慎重に）
    """
    # 注意: この機能は本番環境では慎重に実装する必要があります
    raise HTTPException(
        status_code=501,
        detail="Database migration is not implemented yet. Please use manual migration scripts."
    )

@router.post("/backup")
async def backup_database(
    current_user: User = Depends(require_admin_role)
):
    """
    データベースバックアップ
    """
    try:
        config = get_database_config()

        if config.type == DatabaseType.SQLITE:
            import shutil
            from pathlib import Path

            source_file = Path(config.database)
            if source_file.exists():
                backup_file = Path(f"{config.database}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                shutil.copy2(source_file, backup_file)

                return {
                    "status": "success",
                    "message": f"Backup created: {backup_file}",
                    "backup_file": str(backup_file),
                    "timestamp": datetime.now()
                }
            else:
                raise Exception(f"Database file not found: {config.database}")

        else:
            raise HTTPException(
                status_code=501,
                detail=f"Backup not implemented for {config.type.value}"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

@router.delete("/cache")
async def clear_database_cache(
    current_user: User = Depends(require_admin_role)
):
    """
    データベースキャッシュをクリア
    """
    try:
        # Redis キャッシュクリア
        redis_service = await get_database_service(DatabaseType.REDIS)
        if redis_service:
            # 全キーを取得してクリア（注意：本番環境では慎重に）
            await redis_service.client.flushdb()

        # SQLAlchemy セッションプールクリア
        from app.database import engine
        engine.dispose()

        return {
            "status": "success",
            "message": "Database cache cleared",
            "timestamp": datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")
