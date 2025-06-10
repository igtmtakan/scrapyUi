"""
軽量プログレス表示API

ファイルベースの統計を読み取り、WebSocket経由でリアルタイム更新を提供
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# アクティブなWebSocket接続を管理
active_connections: Dict[str, WebSocket] = {}


@router.websocket("/ws/lightweight-progress/{task_id}")
async def lightweight_progress_websocket(websocket: WebSocket, task_id: str):
    """軽量プログレス表示用WebSocket"""
    await websocket.accept()
    active_connections[task_id] = websocket
    
    try:
        logger.info(f"🔌 Lightweight progress WebSocket connected for task: {task_id}")
        
        # 統計ファイルパス
        stats_file = os.path.join(os.getcwd(), 'scrapy_projects', 'stats', f"{task_id}_stats.json")
        
        # 初期統計を送信
        await send_initial_stats(websocket, stats_file)
        
        # 定期的に統計を更新
        while True:
            try:
                stats = read_stats_file(stats_file)
                if stats:
                    await websocket.send_json({
                        "type": "progress_update",
                        "data": stats
                    })
                
                # 2秒間隔で更新
                await asyncio.sleep(2)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"❌ Error in lightweight progress WebSocket: {e}")
                await asyncio.sleep(5)  # エラー時は少し長めに待機
                
    except WebSocketDisconnect:
        logger.info(f"🔌 Lightweight progress WebSocket disconnected for task: {task_id}")
    except Exception as e:
        logger.error(f"❌ Lightweight progress WebSocket error: {e}")
    finally:
        if task_id in active_connections:
            del active_connections[task_id]


async def send_initial_stats(websocket: WebSocket, stats_file: str):
    """初期統計を送信"""
    try:
        stats = read_stats_file(stats_file)
        if stats:
            await websocket.send_json({
                "type": "initial_stats",
                "data": stats
            })
        else:
            # デフォルト統計を送信
            default_stats = {
                'requests_count': 0,
                'responses_count': 0,
                'items_count': 0,
                'errors_count': 0,
                'start_time': None,
                'last_update': None,
                'spider_name': '',
                'task_id': '',
                'status': 'STARTING'
            }
            await websocket.send_json({
                "type": "initial_stats",
                "data": default_stats
            })
    except Exception as e:
        logger.error(f"❌ Error sending initial stats: {e}")


def read_stats_file(stats_file: str) -> Optional[Dict[str, Any]]:
    """統計ファイルを読み取り"""
    try:
        if os.path.exists(stats_file):
            with open(stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"❌ Error reading stats file {stats_file}: {e}")
        return None


@router.get("/api/lightweight-progress/{task_id}")
async def get_lightweight_progress(task_id: str):
    """軽量プログレス統計を取得"""
    try:
        stats_file = os.path.join(os.getcwd(), 'scrapy_projects', 'stats', f"{task_id}_stats.json")
        stats = read_stats_file(stats_file)
        
        if stats:
            return JSONResponse(content={
                "success": True,
                "data": stats
            })
        else:
            return JSONResponse(content={
                "success": False,
                "message": "Statistics not found"
            }, status_code=404)
            
    except Exception as e:
        logger.error(f"❌ Error getting lightweight progress: {e}")
        return JSONResponse(content={
            "success": False,
            "message": str(e)
        }, status_code=500)


@router.get("/api/lightweight-progress")
async def list_active_progress():
    """アクティブなプログレス統計を一覧表示"""
    try:
        stats_dir = os.path.join(os.getcwd(), 'scrapy_projects', 'stats')
        active_stats = []
        
        if os.path.exists(stats_dir):
            for filename in os.listdir(stats_dir):
                if filename.endswith('_stats.json'):
                    task_id = filename.replace('_stats.json', '')
                    stats_file = os.path.join(stats_dir, filename)
                    stats = read_stats_file(stats_file)
                    
                    if stats and stats.get('status') == 'RUNNING':
                        active_stats.append({
                            'task_id': task_id,
                            'spider_name': stats.get('spider_name', ''),
                            'requests_count': stats.get('requests_count', 0),
                            'responses_count': stats.get('responses_count', 0),
                            'items_count': stats.get('items_count', 0),
                            'errors_count': stats.get('errors_count', 0),
                            'start_time': stats.get('start_time'),
                            'last_update': stats.get('last_update')
                        })
        
        return JSONResponse(content={
            "success": True,
            "data": active_stats
        })
        
    except Exception as e:
        logger.error(f"❌ Error listing active progress: {e}")
        return JSONResponse(content={
            "success": False,
            "message": str(e)
        }, status_code=500)


@router.delete("/api/lightweight-progress/{task_id}")
async def cleanup_progress_stats(task_id: str):
    """プログレス統計をクリーンアップ"""
    try:
        stats_file = os.path.join(os.getcwd(), 'scrapy_projects', 'stats', f"{task_id}_stats.json")
        
        if os.path.exists(stats_file):
            os.remove(stats_file)
            logger.info(f"🗑️ Cleaned up progress stats for task: {task_id}")
            
        # WebSocket接続もクリーンアップ
        if task_id in active_connections:
            del active_connections[task_id]
            
        return JSONResponse(content={
            "success": True,
            "message": "Progress stats cleaned up"
        })
        
    except Exception as e:
        logger.error(f"❌ Error cleaning up progress stats: {e}")
        return JSONResponse(content={
            "success": False,
            "message": str(e)
        }, status_code=500)


# 統計ディレクトリの初期化
def init_stats_directory():
    """統計ディレクトリを初期化"""
    try:
        stats_dir = os.path.join(os.getcwd(), 'scrapy_projects', 'stats')
        os.makedirs(stats_dir, exist_ok=True)
        logger.info(f"📁 Stats directory initialized: {stats_dir}")
    except Exception as e:
        logger.error(f"❌ Error initializing stats directory: {e}")


# アプリケーション起動時に統計ディレクトリを初期化
init_stats_directory()
