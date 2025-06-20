from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db, Project as DBProject, Spider as DBSpider

router = APIRouter()

@router.get("/projects/{project_id}")
async def get_project_internal(
    project_id: str,
    db: Session = Depends(get_db)
):
    """内部API: プロジェクト情報取得（認証不要）"""
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return {
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
        "is_active": project.is_active
    }

@router.get("/spiders/{spider_id}")
async def get_spider_internal(
    spider_id: str,
    db: Session = Depends(get_db)
):
    """内部API: スパイダー情報取得（認証不要）"""
    spider = db.query(DBSpider).filter(DBSpider.id == spider_id).first()
    if not spider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spider not found"
        )
    
    return {
        "id": spider.id,
        "name": spider.name,
        "description": spider.description,
        "code": spider.code,
        "template": spider.template,
        "framework": spider.framework,
        "start_urls": spider.start_urls or [],
        "settings": spider.settings or {},
        "project_id": spider.project_id,
        "user_id": spider.user_id,
        "created_at": spider.created_at,
        "updated_at": spider.updated_at
    }

@router.get("/health")
async def internal_health():
    """内部API: ヘルスチェック"""
    return {"status": "ok", "service": "internal_api"}
