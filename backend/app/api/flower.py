#!/usr/bin/env python3
"""
Flower統合API
3つのオプション全てを提供するAPIエンドポイント
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .auth import get_current_active_user
from ..database import User as DBUser
from ..services.flower_service import get_flower_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flower", tags=["flower"])

@router.get(
    "/stats",
    summary="Flower統計取得",
    description="全てのFlowerサービスから統計情報を取得します。"
)
async def get_flower_stats(
    source: Optional[str] = Query(None, description="統計ソース (api, embedded, standalone, best)"),
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    ## Flower統計取得
    
    3つのFlowerオプション全てから統計を取得し、最適なデータを提供します。
    
    ### パラメータ
    - **source**: 特定のソースを指定 (api, embedded, standalone, best)
    
    ### レスポンス
    - **200**: 統計データを返します
    - **500**: サーバーエラー
    """
    try:
        flower_service = get_flower_service()
        comprehensive_stats = flower_service.get_comprehensive_stats()
        
        if source and source in comprehensive_stats.get('services', {}):
            # 特定のソースを返す
            return {
                'source': source,
                'data': comprehensive_stats['services'][source],
                'timestamp': comprehensive_stats['timestamp']
            }
        elif source == 'best':
            # 最適な統計を返す
            return comprehensive_stats['best']
        else:
            # 全ての統計を返す
            return comprehensive_stats
            
    except Exception as e:
        logger.error(f"❌ Failed to get Flower stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get Flower stats: {str(e)}")

@router.get(
    "/dashboard",
    summary="Flowerダッシュボード統計",
    description="ダッシュボード表示用の統計データを取得します。"
)
async def get_flower_dashboard_stats(
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    ## Flowerダッシュボード統計
    
    フロントエンドのダッシュボード表示用に最適化された統計データを提供します。
    
    ### レスポンス
    - **200**: ダッシュボード統計を返します
    - **500**: サーバーエラー
    """
    try:
        flower_service = get_flower_service()
        comprehensive_stats = flower_service.get_comprehensive_stats()
        best_stats = comprehensive_stats.get('best', {})
        
        # ダッシュボード用にフォーマット
        dashboard_stats = {
            'total_tasks': best_stats.get('tasks', {}).get('total_tasks', 0),
            'pending_tasks': best_stats.get('tasks', {}).get('pending_tasks', 0),
            'running_tasks': best_stats.get('tasks', {}).get('running_tasks', 0),
            'successful_tasks': best_stats.get('tasks', {}).get('successful_tasks', 0),
            'failed_tasks': best_stats.get('tasks', {}).get('failed_tasks', 0),
            'revoked_tasks': best_stats.get('tasks', {}).get('revoked_tasks', 0),
            'total_workers': best_stats.get('workers', {}).get('total_workers', 0),
            'active_workers': best_stats.get('workers', {}).get('active_workers', 0),
            'offline_workers': best_stats.get('workers', {}).get('offline_workers', 0),
            'source': best_stats.get('source', 'none'),
            'flower_url': best_stats.get('flower_url'),
            'timestamp': comprehensive_stats.get('timestamp'),
            'error': best_stats.get('error')
        }
        
        return dashboard_stats
        
    except Exception as e:
        logger.error(f"❌ Failed to get Flower dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

@router.get(
    "/services/status",
    summary="Flowerサービス状態",
    description="全てのFlowerサービスの状態を確認します。"
)
async def get_flower_services_status(
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    ## Flowerサービス状態
    
    3つのFlowerオプション全ての状態を確認します。
    
    ### レスポンス
    - **200**: サービス状態を返します
    - **500**: サーバーエラー
    """
    try:
        flower_service = get_flower_service()
        
        status = {
            'embedded': {
                'running': flower_service.embedded.is_running,
                'url': f"http://{flower_service.embedded.host}:{flower_service.embedded.port}/flower" if flower_service.embedded.is_running else None
            },
            'api': {
                'available': flower_service.api.is_flower_available(),
                'url': flower_service.api.flower_url
            },
            'standalone': {
                'running': flower_service.standalone.is_running,
                'process_id': flower_service.standalone.process.pid if flower_service.standalone.process else None,
                'url': f"http://{flower_service.standalone.host}:{flower_service.standalone.port}/flower" if flower_service.standalone.is_running else None
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return status
        
    except Exception as e:
        logger.error(f"❌ Failed to get Flower services status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get services status: {str(e)}")

@router.post(
    "/services/start",
    summary="Flowerサービス起動",
    description="全てのFlowerサービスを起動します。"
)
async def start_flower_services(
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    ## Flowerサービス起動
    
    3つのFlowerオプション全てを起動します。
    
    ### レスポンス
    - **200**: 起動結果を返します
    - **500**: サーバーエラー
    """
    try:
        # 管理者権限チェック
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        flower_service = get_flower_service()
        results = flower_service.start_all_services()
        
        return {
            'message': 'Flower services start initiated',
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to start Flower services: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start services: {str(e)}")

@router.post(
    "/services/stop",
    summary="Flowerサービス停止",
    description="全てのFlowerサービスを停止します。"
)
async def stop_flower_services(
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    ## Flowerサービス停止
    
    3つのFlowerオプション全てを停止します。
    
    ### レスポンス
    - **200**: 停止完了を返します
    - **500**: サーバーエラー
    """
    try:
        # 管理者権限チェック
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        flower_service = get_flower_service()
        flower_service.stop_all_services()
        
        return {
            'message': 'All Flower services stopped',
            'timestamp': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to stop Flower services: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop services: {str(e)}")

@router.get(
    "/tasks/{task_id}",
    summary="タスク詳細取得",
    description="Flower APIから特定タスクの詳細を取得します。"
)
async def get_flower_task_details(
    task_id: str,
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    ## タスク詳細取得
    
    Flower APIから特定タスクの詳細情報を取得します。
    
    ### パラメータ
    - **task_id**: タスクID
    
    ### レスポンス
    - **200**: タスク詳細を返します
    - **404**: タスクが見つからない
    - **500**: サーバーエラー
    """
    try:
        flower_service = get_flower_service()
        task_details = flower_service.api.get_task_details(task_id)
        
        if 'error' in task_details:
            raise HTTPException(status_code=404, detail=task_details['error'])
        
        return task_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get task details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task details: {str(e)}")

@router.get(
    "/workers/{worker_name}",
    summary="ワーカー詳細取得",
    description="Flower APIから特定ワーカーの詳細を取得します。"
)
async def get_flower_worker_details(
    worker_name: str,
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    ## ワーカー詳細取得
    
    Flower APIから特定ワーカーの詳細情報を取得します。
    
    ### パラメータ
    - **worker_name**: ワーカー名
    
    ### レスポンス
    - **200**: ワーカー詳細を返します
    - **404**: ワーカーが見つからない
    - **500**: サーバーエラー
    """
    try:
        flower_service = get_flower_service()
        worker_details = flower_service.api.get_worker_details(worker_name)
        
        if 'error' in worker_details:
            raise HTTPException(status_code=404, detail=worker_details['error'])
        
        return worker_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get worker details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get worker details: {str(e)}")

@router.get(
    "/ui",
    summary="Flower UI リダイレクト",
    description="利用可能なFlower UIにリダイレクトします。"
)
async def redirect_to_flower_ui(
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    ## Flower UI リダイレクト
    
    利用可能なFlower UIにリダイレクトします。
    
    ### レスポンス
    - **302**: Flower UIにリダイレクト
    - **404**: 利用可能なFlower UIがない
    """
    try:
        flower_service = get_flower_service()
        comprehensive_stats = flower_service.get_comprehensive_stats()
        best_stats = comprehensive_stats.get('best', {})
        
        flower_url = best_stats.get('flower_url')
        if flower_url:
            return RedirectResponse(url=flower_url)
        else:
            raise HTTPException(status_code=404, detail="No Flower UI available")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to redirect to Flower UI: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to redirect: {str(e)}")

@router.get(
    "/health",
    summary="Flowerヘルスチェック",
    description="Flowerサービスのヘルスチェックを実行します。"
)
async def flower_health_check():
    """
    ## Flowerヘルスチェック
    
    認証不要でFlowerサービスの状態を確認します。
    
    ### レスポンス
    - **200**: ヘルス状態を返します
    """
    try:
        flower_service = get_flower_service()
        
        health = {
            'embedded': flower_service.embedded.is_running,
            'api': flower_service.api.is_flower_available(),
            'standalone': flower_service.standalone.is_running,
            'timestamp': datetime.now().isoformat()
        }
        
        # 少なくとも1つのサービスが利用可能かチェック
        any_available = any([health['embedded'], health['api'], health['standalone']])
        
        return {
            'status': 'healthy' if any_available else 'unhealthy',
            'services': health,
            'message': 'At least one Flower service is available' if any_available else 'No Flower services available'
        }
        
    except Exception as e:
        logger.error(f"❌ Flower health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
