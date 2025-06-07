#!/usr/bin/env python3
"""
Flower統合サービス
Option 1: Flower埋め込み
Option 2: Flower API利用
Option 3: 別サービスとして起動
"""

import os
import subprocess
import time
import requests
from typing import Dict, Any
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FlowerEmbeddedService:
    """Option 1: Flower埋め込みサービス"""
    
    def __init__(self):
        self.flower_app = None
        self.flower_thread = None
        self.is_running = False
        self.port = int(os.getenv('FLOWER_PORT', '5556'))
        self.host = os.getenv('FLOWER_HOST', '127.0.0.1')
        
    def start_embedded_flower(self):
        """埋め込みFlowerを起動（簡素化版）"""
        try:
            # 埋め込みFlowerは複雑なため、一旦無効化
            logger.info("🌸 Embedded Flower is disabled (using API/standalone instead)")
            self.is_running = False
            return False

        except ImportError:
            logger.error("❌ Flower not installed. Run: pip install flower")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to start embedded Flower: {e}")
            return False
    
    def stop_embedded_flower(self):
        """埋め込みFlowerを停止"""
        try:
            if self.flower_app:
                self.flower_app.stop()
            self.is_running = False
            logger.info("🛑 Embedded Flower stopped")
        except Exception as e:
            logger.error(f"❌ Failed to stop embedded Flower: {e}")
    
    def get_embedded_stats(self) -> Dict[str, Any]:
        """埋め込みFlowerから統計を取得"""
        if not self.is_running:
            return {"error": "Embedded Flower not running"}
        
        try:
            # 埋め込みFlowerが利用できない場合はAPIフォールバック
            if not self.is_running:
                return {"error": "Embedded Flower not running"}

            # 簡単な統計を返す（実装を簡素化）
            return {
                'source': 'embedded',
                'timestamp': datetime.now().isoformat(),
                'tasks': {
                    'total_tasks': 0,
                    'pending_tasks': 0,
                    'running_tasks': 0,
                    'successful_tasks': 0,
                    'failed_tasks': 0,
                    'revoked_tasks': 0
                },
                'workers': {
                    'total_workers': 0,
                    'active_workers': 0,
                    'offline_workers': 0
                },
                'flower_url': f"http://{self.host}:{self.port}/flower"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get embedded stats: {e}")
            return {"error": str(e)}


class FlowerAPIService:
    """Option 2: Flower API利用サービス"""
    
    def __init__(self, flower_url: str = None):
        if flower_url is None:
            flower_port = os.getenv('FLOWER_PORT', '5556')
            flower_host = os.getenv('FLOWER_HOST', 'localhost')
            flower_url = f"http://{flower_host}:{flower_port}/flower"
        self.flower_url = flower_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 10
        
    def is_flower_available(self) -> bool:
        """FlowerのAPIが利用可能かチェック"""
        try:
            response = self.session.get(f"{self.flower_url}/api/workers")
            return response.status_code == 200
        except Exception:
            return False
    
    def get_api_stats(self) -> Dict[str, Any]:
        """Flower APIから統計を取得"""
        try:
            if not self.is_flower_available():
                return {"error": "Flower API not available"}
            
            # タスク統計を取得
            tasks_response = self.session.get(f"{self.flower_url}/api/tasks")
            tasks_data = tasks_response.json() if tasks_response.status_code == 200 else {}
            
            # ワーカー統計を取得
            workers_response = self.session.get(f"{self.flower_url}/api/workers")
            workers_data = workers_response.json() if workers_response.status_code == 200 else {}
            
            # タスク統計を計算
            task_stats = {
                'total_tasks': len(tasks_data),
                'pending_tasks': len([t for t in tasks_data.values() if t.get('state') == 'PENDING']),
                'running_tasks': len([t for t in tasks_data.values() if t.get('state') == 'STARTED']),
                'successful_tasks': len([t for t in tasks_data.values() if t.get('state') == 'SUCCESS']),
                'failed_tasks': len([t for t in tasks_data.values() if t.get('state') == 'FAILURE']),
                'revoked_tasks': len([t for t in tasks_data.values() if t.get('state') == 'REVOKED'])
            }
            
            # ワーカー統計を計算
            worker_stats = {
                'total_workers': len(workers_data),
                'active_workers': len([w for w in workers_data.values() if w.get('status')]),
                'offline_workers': len([w for w in workers_data.values() if not w.get('status')])
            }
            
            return {
                'source': 'api',
                'timestamp': datetime.now().isoformat(),
                'tasks': task_stats,
                'workers': worker_stats,
                'flower_url': self.flower_url
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get API stats: {e}")
            return {"error": str(e)}
    
    def get_task_details(self, task_id: str) -> Dict[str, Any]:
        """特定タスクの詳細を取得"""
        try:
            response = self.session.get(f"{self.flower_url}/api/task/info/{task_id}")
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Task {task_id} not found"}
        except Exception as e:
            logger.error(f"❌ Failed to get task details: {e}")
            return {"error": str(e)}
    
    def get_worker_details(self, worker_name: str) -> Dict[str, Any]:
        """特定ワーカーの詳細を取得"""
        try:
            response = self.session.get(f"{self.flower_url}/api/worker/info/{worker_name}")
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Worker {worker_name} not found"}
        except Exception as e:
            logger.error(f"❌ Failed to get worker details: {e}")
            return {"error": str(e)}


class FlowerStandaloneService:
    """Option 3: 別サービスとして起動"""
    
    def __init__(self):
        self.process = None
        self.port = int(os.getenv('FLOWER_PORT', '5556'))
        self.host = os.getenv('FLOWER_HOST', '127.0.0.1')
        self.is_running = False
        
    def start_standalone_flower(self) -> bool:
        """スタンドアロンFlowerを起動"""
        try:
            # Celeryアプリケーションのパスを設定
            celery_app_path = "app.celery_app:celery_app"
            
            # Flower起動コマンド
            cmd = [
                "celery",
                "-A", celery_app_path,
                "flower",
                f"--port={self.port}",
                f"--address={self.host}",
                "--url_prefix=/flower",
                "--persistent=True",
                "--db=flower.db",
                "--max_tasks=10000",
                "--enable_events",
                "--auto_refresh=True"
            ]
            
            # 環境変数を設定
            env = os.environ.copy()
            env.update({
                'CELERY_BROKER_URL': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
                'CELERY_RESULT_BACKEND': os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
                'FLOWER_UNAUTHENTICATED_API': 'true'  # API認証を無効化
            })
            
            logger.info(f"🌸 Starting standalone Flower: {' '.join(cmd)}")
            
            # プロセスを起動
            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path(__file__).parent.parent.parent
            )
            
            # 起動確認
            time.sleep(3)
            if self.process.poll() is None:
                self.is_running = True
                logger.info(f"✅ Standalone Flower started on {self.host}:{self.port}")
                return True
            else:
                stdout, stderr = self.process.communicate()
                logger.error(f"❌ Standalone Flower failed to start:")
                logger.error(f"STDOUT: {stdout.decode()}")
                logger.error(f"STDERR: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start standalone Flower: {e}")
            return False
    
    def stop_standalone_flower(self):
        """スタンドアロンFlowerを停止"""
        try:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=10)
                logger.info("🛑 Standalone Flower stopped")
            self.is_running = False
        except Exception as e:
            logger.error(f"❌ Failed to stop standalone Flower: {e}")
    
    def get_standalone_status(self) -> Dict[str, Any]:
        """スタンドアロンFlowerの状態を取得"""
        return {
            'source': 'standalone',
            'is_running': self.is_running,
            'process_id': self.process.pid if self.process else None,
            'flower_url': f"http://{self.host}:{self.port}/flower" if self.is_running else None,
            'timestamp': datetime.now().isoformat()
        }


class FlowerIntegratedService:
    """統合Flowerサービス - 3つのオプションを管理"""
    
    def __init__(self):
        self.embedded = FlowerEmbeddedService()
        self.api = FlowerAPIService()
        self.standalone = FlowerStandaloneService()
        self.preferred_mode = os.getenv('FLOWER_MODE', 'api')  # api, embedded, standalone
        
    def start_all_services(self):
        """全てのFlowerサービスを起動"""
        results = {}
        
        # Option 1: 埋め込み
        try:
            results['embedded'] = self.embedded.start_embedded_flower()
        except Exception as e:
            logger.error(f"❌ Embedded Flower start failed: {e}")
            results['embedded'] = False
        
        # Option 3: スタンドアロン
        try:
            results['standalone'] = self.standalone.start_standalone_flower()
        except Exception as e:
            logger.error(f"❌ Standalone Flower start failed: {e}")
            results['standalone'] = False
        
        # Option 2: API (外部Flowerが起動している場合)
        results['api'] = self.api.is_flower_available()
        
        logger.info(f"🌸 Flower services started: {results}")
        return results
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """全てのFlowerサービスから統計を取得"""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'services': {}
        }
        
        # 埋め込みFlowerから統計取得
        try:
            embedded_stats = self.embedded.get_embedded_stats()
            stats['services']['embedded'] = embedded_stats
        except Exception as e:
            stats['services']['embedded'] = {'error': str(e)}
        
        # API Flowerから統計取得
        try:
            api_stats = self.api.get_api_stats()
            stats['services']['api'] = api_stats
        except Exception as e:
            stats['services']['api'] = {'error': str(e)}
        
        # スタンドアロンFlowerの状態取得
        try:
            standalone_status = self.standalone.get_standalone_status()
            stats['services']['standalone'] = standalone_status
        except Exception as e:
            stats['services']['standalone'] = {'error': str(e)}
        
        # 最適な統計を選択
        best_stats = self._select_best_stats(stats['services'])
        stats['best'] = best_stats
        
        return stats
    
    def _select_best_stats(self, services: Dict[str, Any]) -> Dict[str, Any]:
        """最も信頼できる統計データを選択"""
        # 優先順位: API > 埋め込み > スタンドアロン
        for source in ['api', 'embedded', 'standalone']:
            service_data = services.get(source, {})
            if 'error' not in service_data and 'tasks' in service_data:
                return service_data
        
        # フォールバック: エラー情報を返す
        return {
            'source': 'none',
            'error': 'No Flower service available',
            'tasks': {
                'total_tasks': 0,
                'pending_tasks': 0,
                'running_tasks': 0,
                'successful_tasks': 0,
                'failed_tasks': 0
            },
            'workers': {
                'total_workers': 0,
                'active_workers': 0,
                'offline_workers': 0
            }
        }
    
    def stop_all_services(self):
        """全てのFlowerサービスを停止"""
        try:
            self.embedded.stop_embedded_flower()
        except Exception as e:
            logger.error(f"❌ Failed to stop embedded Flower: {e}")
        
        try:
            self.standalone.stop_standalone_flower()
        except Exception as e:
            logger.error(f"❌ Failed to stop standalone Flower: {e}")
        
        logger.info("🛑 All Flower services stopped")


# グローバルインスタンス
flower_service = FlowerIntegratedService()

def get_flower_service() -> FlowerIntegratedService:
    """Flower統合サービスのインスタンスを取得"""
    return flower_service
