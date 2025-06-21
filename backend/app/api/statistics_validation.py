"""
統計検証API

管理者が全プロジェクトの統計検証・修正を実行できる
APIエンドポイントを提供します。

機能:
- 全プロジェクト統計検証
- 特定プロジェクト統計修正
- 特定タスク統計修正
- 修正レポート取得
- バッチ処理状態管理
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, Optional
from datetime import datetime

from ..auth.jwt_handler import get_current_admin_user
from ..database import User
from ..services.universal_statistics_validator import universal_validator
from ..services.batch_statistics_fixer import batch_fixer

router = APIRouter(prefix="/api/statistics", tags=["Statistics Validation"])


@router.get("/validate/all")
async def validate_all_statistics(
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """全プロジェクトの統計を検証・修正"""
    try:
        result = universal_validator.validate_all_projects()
        
        return {
            "success": True,
            "message": "All projects statistics validation completed",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/validate/task/{task_id}")
async def validate_task_statistics(
    task_id: str,
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """特定タスクの統計を検証・修正"""
    try:
        result = universal_validator.validate_task_statistics(task_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Task validation failed"))
        
        return {
            "success": True,
            "message": f"Task {task_id} statistics validation completed",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task validation failed: {str(e)}")


@router.post("/fix/comprehensive")
async def run_comprehensive_fix(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """包括的な統計修正を実行"""
    try:
        # バックグラウンドで実行
        background_tasks.add_task(batch_fixer.run_comprehensive_fix)
        
        return {
            "success": True,
            "message": "Comprehensive statistics fix started in background",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comprehensive fix failed: {str(e)}")


@router.post("/fix/project/{project_id}")
async def fix_project_statistics(
    project_id: str,
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """特定プロジェクトの統計を修正"""
    try:
        result = batch_fixer.fix_specific_project(project_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Project fix failed"))
        
        return {
            "success": True,
            "message": f"Project {project_id} statistics fix completed",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Project fix failed: {str(e)}")


@router.get("/report")
async def get_statistics_report(
    days: int = 7,
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """統計修正レポートを取得"""
    try:
        if days < 1 or days > 30:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 30")
        
        report = batch_fixer.get_fix_report(days)
        
        if "error" in report:
            raise HTTPException(status_code=500, detail=report["error"])
        
        return {
            "success": True,
            "message": f"Statistics report for last {days} days",
            "data": report,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/status")
async def get_validation_status(
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """統計検証サービスの状態を取得"""
    try:
        batch_status = batch_fixer.get_status()
        
        return {
            "success": True,
            "message": "Statistics validation status",
            "data": {
                "batch_fixer": batch_status,
                "universal_validator": {
                    "running": universal_validator.running,
                    "validation_interval": universal_validator.validation_interval
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")


@router.post("/batch/start")
async def start_batch_processing(
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """バッチ処理を開始"""
    try:
        batch_fixer.start_batch_processing()
        
        return {
            "success": True,
            "message": "Batch statistics processing started",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch start failed: {str(e)}")


@router.post("/batch/stop")
async def stop_batch_processing(
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """バッチ処理を停止"""
    try:
        batch_fixer.stop_batch_processing()
        
        return {
            "success": True,
            "message": "Batch statistics processing stopped",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch stop failed: {str(e)}")


@router.post("/monitoring/start")
async def start_realtime_monitoring(
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """リアルタイム監視を開始"""
    try:
        universal_validator.start_realtime_monitoring()
        
        return {
            "success": True,
            "message": "Realtime statistics monitoring started",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Monitoring start failed: {str(e)}")


@router.post("/monitoring/stop")
async def stop_realtime_monitoring(
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """リアルタイム監視を停止"""
    try:
        universal_validator.stop_realtime_monitoring()
        
        return {
            "success": True,
            "message": "Realtime statistics monitoring stopped",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Monitoring stop failed: {str(e)}")


@router.get("/detect-files/{task_id}")
async def detect_task_result_files(
    task_id: str,
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """タスクの結果ファイルを検出"""
    try:
        result = universal_validator.detect_result_files(task_id)
        
        return {
            "success": True,
            "message": f"Result files detection for task {task_id}",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File detection failed: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """統計検証サービスのヘルスチェック"""
    try:
        return {
            "success": True,
            "message": "Statistics validation service is healthy",
            "services": {
                "universal_validator": "available",
                "batch_fixer": "available"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "Statistics validation service health check failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
