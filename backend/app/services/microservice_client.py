#!/usr/bin/env python3
"""
ScrapyUI Microservice Client
マイクロサービスとの通信を管理するクライアント
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional, Callable

import aiohttp
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

class MicroserviceClient:
    """マイクロサービス通信クライアント"""
    
    def __init__(self):
        self.base_urls = {
            "scheduler": "http://localhost:8001",
            "spider_manager": "http://localhost:8002", 
            "result_collector": "http://localhost:8003",
            "api_gateway": "http://localhost:8000",
            "test_service": "http://localhost:8005"
        }
        self.timeout = 30
        
    def _get_service_url(self, service: str) -> str:
        """サービスURLを取得"""
        return self.base_urls.get(service, self.base_urls["test_service"])
    
    async def execute_spider_with_watchdog_async(self, 
                                               project_id: str,
                                               spider_id: str, 
                                               project_path: str,
                                               spider_name: str,
                                               task_id: str = None,
                                               settings: Dict = None) -> Dict:
        """非同期でwatchdog付きスパイダーを実行"""
        try:
            if not task_id:
                task_id = str(uuid.uuid4())
            
            # 出力ファイルパス生成
            output_file = f"/app/scrapy_projects/{project_path}/results_{task_id}.jsonl"
            
            request_data = {
                "task_id": task_id,
                "project_id": project_id,
                "spider_id": spider_id,
                "project_path": project_path,
                "spider_name": spider_name,
                "output_file": output_file,
                "settings": settings or {}
            }
            
            # Spider Managerサービスに送信
            service_url = self._get_service_url("spider_manager")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{service_url}/execute-watchdog",
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ Watchdog spider execution started: {task_id}")
                        return {
                            "success": True,
                            "task_id": task_id,
                            "result": result
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Spider execution failed: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                            "task_id": task_id
                        }
                        
        except Exception as e:
            logger.error(f"❌ Microservice communication error: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": task_id
            }
    
    def execute_spider_with_watchdog_sync(self,
                                        project_id: str,
                                        spider_id: str,
                                        project_path: str, 
                                        spider_name: str,
                                        task_id: str = None,
                                        settings: Dict = None) -> Dict:
        """同期でwatchdog付きスパイダーを実行"""
        try:
            if not task_id:
                task_id = str(uuid.uuid4())
            
            # 出力ファイルパス生成
            output_file = f"/app/scrapy_projects/{project_path}/results_{task_id}.jsonl"
            
            request_data = {
                "task_id": task_id,
                "project_id": project_id,
                "spider_id": spider_id,
                "project_path": project_path,
                "spider_name": spider_name,
                "output_file": output_file,
                "settings": settings or {}
            }
            
            # Spider Managerサービスに送信
            service_url = self._get_service_url("spider_manager")
            
            response = requests.post(
                f"{service_url}/execute-watchdog",
                json=request_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Watchdog spider execution started: {task_id}")
                return {
                    "success": True,
                    "task_id": task_id,
                    "result": result
                }
            else:
                logger.error(f"❌ Spider execution failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "task_id": task_id
                }
                
        except Exception as e:
            logger.error(f"❌ Microservice communication error: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": task_id
            }
    
    async def get_active_watchdog_tasks(self) -> Dict:
        """アクティブなwatchdogタスクを取得"""
        try:
            service_url = self._get_service_url("spider_manager")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{service_url}/watchdog/active",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"active_tasks": [], "count": 0}
                        
        except Exception as e:
            logger.error(f"❌ Failed to get active tasks: {e}")
            return {"active_tasks": [], "count": 0}
    
    async def stop_watchdog_task(self, task_id: str) -> bool:
        """watchdogタスクを停止"""
        try:
            service_url = self._get_service_url("spider_manager")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{service_url}/watchdog/{task_id}/stop",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"❌ Failed to stop task {task_id}: {e}")
            return False
    
    async def get_spider_manager_metrics(self) -> Dict:
        """Spider Managerのメトリクスを取得"""
        try:
            service_url = self._get_service_url("spider_manager")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{service_url}/metrics",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"HTTP {response.status}"}
                        
        except Exception as e:
            logger.error(f"❌ Failed to get metrics: {e}")
            return {"error": str(e)}
    
    def health_check(self, service: str = "spider_manager") -> bool:
        """サービスのヘルスチェック"""
        try:
            service_url = self._get_service_url(service)
            
            response = requests.get(
                f"{service_url}/health",
                timeout=5
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"❌ Health check failed for {service}: {e}")
            return False
    
    def is_microservice_available(self) -> bool:
        """マイクロサービスが利用可能かチェック"""
        # まずテストサービスをチェック
        if self.health_check("test_service"):
            return True
        
        # 次にSpider Managerをチェック
        if self.health_check("spider_manager"):
            return True
        
        return False

# グローバルクライアントインスタンス
microservice_client = MicroserviceClient()

class MicroserviceSpiderExecutor:
    """マイクロサービス版スパイダー実行クラス"""
    
    def __init__(self):
        self.client = microservice_client
        
    async def run_spider_with_watchdog(self,
                                     project_path: str,
                                     spider_name: str,
                                     task_id: str,
                                     settings: Dict = None,
                                     websocket_callback: Optional[Callable] = None) -> Dict:
        """watchdog監視付きでスパイダーを実行（ScrapyServiceの代替）"""
        try:
            logger.info(f"🚀 Starting microservice spider execution: {spider_name}")
            
            # プロジェクト情報を推定（実際の実装では適切に取得）
            project_id = "microservice_project"
            spider_id = "microservice_spider"
            
            # マイクロサービス経由で実行
            result = await self.client.execute_spider_with_watchdog_async(
                project_id=project_id,
                spider_id=spider_id,
                project_path=project_path,
                spider_name=spider_name,
                task_id=task_id,
                settings=settings
            )
            
            if result["success"]:
                logger.info(f"✅ Microservice spider execution completed: {task_id}")
                
                # WebSocketコールバックがある場合は進捗通知をシミュレート
                if websocket_callback:
                    try:
                        websocket_callback({
                            "type": "spider_started",
                            "task_id": task_id,
                            "spider_name": spider_name,
                            "timestamp": datetime.now().isoformat()
                        })
                    except Exception as e:
                        logger.warning(f"⚠️ WebSocket callback error: {e}")
                
                return {
                    "success": True,
                    "task_id": task_id,
                    "message": "Spider executed via microservice"
                }
            else:
                logger.error(f"❌ Microservice spider execution failed: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "task_id": task_id
                }
                
        except Exception as e:
            logger.error(f"❌ Microservice spider execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": task_id
            }
