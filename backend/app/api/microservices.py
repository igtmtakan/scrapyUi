#!/usr/bin/env python3
"""
ScrapyUI Microservices API
マイクロサービス統合API
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..api.auth import get_current_active_user
from ..services.microservice_client import microservice_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/microservices", tags=["microservices"])

class WatchdogExecutionRequest(BaseModel):
    project_id: str
    spider_id: str
    project_path: str
    spider_name: str
    task_id: Optional[str] = None
    settings: Optional[Dict] = None

class WatchdogExecutionResponse(BaseModel):
    success: bool
    task_id: str
    message: str
    error: Optional[str] = None

@router.get("/health")
async def microservices_health_check():
    """マイクロサービス全体のヘルスチェック"""
    try:
        health_status = {}
        
        # 各サービスのヘルスチェック
        services = ["test_service", "spider_manager", "scheduler", "result_collector"]
        
        for service in services:
            try:
                is_healthy = microservice_client.health_check(service)
                health_status[service] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "url": microservice_client._get_service_url(service)
                }
            except Exception as e:
                health_status[service] = {
                    "status": "error",
                    "error": str(e),
                    "url": microservice_client._get_service_url(service)
                }
        
        # 全体ステータス判定
        all_healthy = all(
            status["status"] == "healthy" 
            for status in health_status.values()
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "services": health_status,
            "timestamp": datetime.now().isoformat(),
            "available": microservice_client.is_microservice_available()
        }
        
    except Exception as e:
        logger.error(f"❌ Microservices health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_microservices_stats():
    """マイクロサービス統計情報取得"""
    try:
        stats = {
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }
        
        # Spider Manager統計
        try:
            spider_stats = await microservice_client.get_spider_manager_metrics()
            stats["services"]["spider_manager"] = spider_stats
        except Exception as e:
            stats["services"]["spider_manager"] = {"error": str(e)}
        
        # アクティブタスク情報
        try:
            active_tasks = await microservice_client.get_active_watchdog_tasks()
            stats["services"]["active_watchdog_tasks"] = active_tasks
        except Exception as e:
            stats["services"]["active_watchdog_tasks"] = {"error": str(e)}
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Failed to get microservices stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/spider-manager/execute-watchdog", response_model=WatchdogExecutionResponse)
async def execute_spider_with_watchdog(
    request: WatchdogExecutionRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """watchdog監視付きスパイダー実行"""
    try:
        logger.info(f"🚀 Executing spider with watchdog: {request.spider_name}")
        
        # マイクロサービス経由で実行
        result = microservice_client.execute_spider_with_watchdog_sync(
            project_id=request.project_id,
            spider_id=request.spider_id,
            project_path=request.project_path,
            spider_name=request.spider_name,
            task_id=request.task_id,
            settings=request.settings
        )
        
        if result["success"]:
            return WatchdogExecutionResponse(
                success=True,
                task_id=result["task_id"],
                message="Spider execution started successfully"
            )
        else:
            return WatchdogExecutionResponse(
                success=False,
                task_id=result.get("task_id", "unknown"),
                message="Spider execution failed",
                error=result.get("error")
            )
            
    except Exception as e:
        logger.error(f"❌ Spider execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/spider-manager/metrics")
async def get_spider_manager_metrics():
    """Spider Managerメトリクス取得"""
    try:
        metrics = await microservice_client.get_spider_manager_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Failed to get spider manager metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/spider-manager/watchdog/active")
async def get_active_watchdog_tasks():
    """アクティブなwatchdogタスク取得"""
    try:
        active_tasks = await microservice_client.get_active_watchdog_tasks()
        return active_tasks
        
    except Exception as e:
        logger.error(f"❌ Failed to get active watchdog tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/spider-manager/watchdog/{task_id}/stop")
async def stop_watchdog_task(
    task_id: str,
    current_user = Depends(get_current_active_user)
):
    """watchdogタスク停止"""
    try:
        success = await microservice_client.stop_watchdog_task(task_id)
        
        if success:
            return {
                "message": "Watchdog task stopped successfully",
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Task not found or already stopped")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to stop watchdog task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/migration/status")
async def get_migration_status():
    """Celeryからマイクロサービスへの移行状況"""
    try:
        # Celeryプロセス確認
        import subprocess
        import psutil
        
        celery_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'celery' in cmdline.lower() or 'flower' in cmdline.lower():
                    celery_processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cmdline": cmdline[:100]  # 最初の100文字
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # マイクロサービス状況
        microservice_available = microservice_client.is_microservice_available()
        
        # 移行状況判定
        if len(celery_processes) == 0 and microservice_available:
            migration_status = "completed"
            message = "Migration completed: Celery processes removed, microservices available"
        elif len(celery_processes) > 0 and microservice_available:
            migration_status = "in_progress"
            message = "Migration in progress: Both Celery and microservices running"
        elif len(celery_processes) == 0 and not microservice_available:
            migration_status = "incomplete"
            message = "Migration incomplete: Celery removed but microservices not available"
        else:
            migration_status = "not_started"
            message = "Migration not started: Only Celery processes running"
        
        return {
            "migration_status": migration_status,
            "message": message,
            "celery_processes": celery_processes,
            "celery_count": len(celery_processes),
            "microservice_available": microservice_available,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get migration status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/migration/complete")
async def complete_migration(
    current_user = Depends(get_current_active_user)
):
    """移行完了処理"""
    try:
        # 残存Celeryプロセスを停止
        import subprocess
        import psutil
        
        stopped_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'celery' in cmdline.lower() or 'flower' in cmdline.lower():
                    proc.terminate()
                    stopped_processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # マイクロサービス確認
        microservice_available = microservice_client.is_microservice_available()
        
        return {
            "message": "Migration completion attempted",
            "stopped_processes": stopped_processes,
            "microservice_available": microservice_available,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to complete migration: {e}")
        raise HTTPException(status_code=500, detail=str(e))
