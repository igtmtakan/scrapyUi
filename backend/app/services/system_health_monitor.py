"""
システムヘルスモニタリングサービス
包括的なシステム状態監視と自動修復機能
"""

import asyncio
import json
import logging
import psutil
import redis.asyncio as redis
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from ..database import SessionLocal, Task, TaskStatus

logger = logging.getLogger(__name__)

class SystemHealthMonitor:
    """システムヘルスモニタリング"""
    
    def __init__(self):
        self.running = False
        self.redis_client = None
        self.base_projects_dir = Path("/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects")
        self.health_stats = {
            'last_check': None,
            'system_status': 'unknown',
            'issues_detected': [],
            'auto_repairs': 0,
            'performance_metrics': {}
        }
        
    async def initialize(self):
        """初期化"""
        try:
            # Redis接続
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("✅ Redis connection established for health monitor")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed for health monitor: {e}")
            self.redis_client = None

    async def start_monitoring(self):
        """監視開始"""
        self.running = True
        logger.info("🔍 System health monitoring started")
        
        # 定期ヘルスチェック
        asyncio.create_task(self._health_check_loop())
        
        # パフォーマンス監視
        asyncio.create_task(self._performance_monitor_loop())
        
        # データ整合性チェック
        asyncio.create_task(self._data_integrity_check_loop())

    async def stop_monitoring(self):
        """監視停止"""
        self.running = False
        if self.redis_client:
            await self.redis_client.close()
        logger.info("🛑 System health monitoring stopped")

    async def _health_check_loop(self):
        """ヘルスチェックループ"""
        while self.running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(60)  # 1分間隔
            except Exception as e:
                logger.error(f"❌ Health check error: {e}")
                await asyncio.sleep(30)

    async def _performance_monitor_loop(self):
        """パフォーマンス監視ループ"""
        while self.running:
            try:
                await self._collect_performance_metrics()
                await asyncio.sleep(300)  # 5分間隔
            except Exception as e:
                logger.error(f"❌ Performance monitoring error: {e}")
                await asyncio.sleep(60)

    async def _data_integrity_check_loop(self):
        """データ整合性チェックループ"""
        while self.running:
            try:
                await self._check_data_integrity()
                await asyncio.sleep(1800)  # 30分間隔
            except Exception as e:
                logger.error(f"❌ Data integrity check error: {e}")
                await asyncio.sleep(300)

    async def _perform_health_check(self):
        """包括的ヘルスチェック"""
        self.health_stats['last_check'] = datetime.now()
        issues = []
        
        # 1. システムリソースチェック
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        if cpu_percent > 80:
            issues.append(f"High CPU usage: {cpu_percent}%")
        
        if memory.percent > 85:
            issues.append(f"High memory usage: {memory.percent}%")
        
        if disk.percent > 90:
            issues.append(f"High disk usage: {disk.percent}%")
        
        # 2. データベース接続チェック
        try:
            with SessionLocal() as db:
                db.execute("SELECT 1")
        except Exception as e:
            issues.append(f"Database connection failed: {e}")
        
        # 3. Redis接続チェック
        if self.redis_client:
            try:
                await self.redis_client.ping()
            except Exception as e:
                issues.append(f"Redis connection failed: {e}")
        
        # 4. マイクロサービスチェック
        services_status = await self._check_microservices()
        for service, status in services_status.items():
            if not status:
                issues.append(f"Microservice {service} is down")
        
        # 5. 長時間実行タスクチェック
        stuck_tasks = await self._check_stuck_tasks()
        if stuck_tasks:
            issues.append(f"Found {len(stuck_tasks)} stuck tasks")
            await self._auto_repair_stuck_tasks(stuck_tasks)
        
        # ステータス更新
        self.health_stats['issues_detected'] = issues
        self.health_stats['system_status'] = 'healthy' if not issues else 'warning'
        
        # Redis に状態を保存
        if self.redis_client:
            await self.redis_client.setex(
                "system:health_status",
                300,  # 5分間有効
                json.dumps(self.health_stats, default=str)
            )
        
        if issues:
            logger.warning(f"⚠️ Health issues detected: {len(issues)}")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.debug("✅ System health check passed")

    async def _collect_performance_metrics(self):
        """パフォーマンスメトリクス収集"""
        metrics = {
            'timestamp': datetime.now(),
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'active_connections': len(psutil.net_connections()),
            'process_count': len(psutil.pids())
        }
        
        # データベースメトリクス
        try:
            with SessionLocal() as db:
                # アクティブタスク数
                active_tasks = db.query(Task).filter(
                    Task.status == TaskStatus.RUNNING
                ).count()
                
                # 最近1時間の完了タスク数
                recent_completed = db.query(Task).filter(
                    Task.status == TaskStatus.FINISHED,
                    Task.finished_at >= datetime.now() - timedelta(hours=1)
                ).count()
                
                metrics.update({
                    'active_tasks': active_tasks,
                    'recent_completed_tasks': recent_completed
                })
                
        except Exception as e:
            logger.error(f"❌ Database metrics collection failed: {e}")
        
        self.health_stats['performance_metrics'] = metrics
        
        # Redis に保存
        if self.redis_client:
            await self.redis_client.lpush(
                "system:performance_history",
                json.dumps(metrics, default=str)
            )
            # 最新100件のみ保持
            await self.redis_client.ltrim("system:performance_history", 0, 99)

    async def _check_data_integrity(self):
        """データ整合性チェック"""
        try:
            with SessionLocal() as db:
                # アイテム数が0のFINISHEDタスクをチェック
                zero_item_tasks = db.query(Task).filter(
                    Task.status == TaskStatus.FINISHED,
                    Task.items_count == 0
                ).limit(10).all()
                
                for task in zero_item_tasks:
                    # 対応する結果ファイルをチェック
                    result_file = self.base_projects_dir / f"*/results_{task.id}.jsonl"
                    result_files = list(self.base_projects_dir.glob(f"*/results_{task.id}.jsonl"))
                    
                    if result_files:
                        file_path = result_files[0]
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                actual_count = sum(1 for line in f if line.strip())
                            
                            if actual_count > 0:
                                # 自動修復
                                task.items_count = actual_count
                                db.commit()
                                self.health_stats['auto_repairs'] += 1
                                logger.info(f"🔧 Auto-repaired task {task.id}: 0 → {actual_count} items")
                                
                        except Exception as e:
                            logger.error(f"❌ File check failed for {task.id}: {e}")
                
        except Exception as e:
            logger.error(f"❌ Data integrity check failed: {e}")

    async def _check_microservices(self) -> Dict[str, bool]:
        """マイクロサービス状態チェック"""
        services = {
            'spider_manager': 'http://localhost:8002/health',
            'test_service': 'http://localhost:8005/health'
        }
        
        status = {}
        for service, url in services.items():
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=5) as response:
                        status[service] = response.status == 200
            except Exception:
                status[service] = False
        
        return status

    async def _check_stuck_tasks(self) -> List[str]:
        """スタックしたタスクをチェック"""
        try:
            with SessionLocal() as db:
                # 1時間以上RUNNINGのタスク
                stuck_threshold = datetime.now() - timedelta(hours=1)
                stuck_tasks = db.query(Task).filter(
                    Task.status == TaskStatus.RUNNING,
                    Task.started_at < stuck_threshold
                ).all()
                
                return [task.id for task in stuck_tasks]
                
        except Exception as e:
            logger.error(f"❌ Stuck task check failed: {e}")
            return []

    async def _auto_repair_stuck_tasks(self, task_ids: List[str]):
        """スタックしたタスクの自動修復"""
        try:
            with SessionLocal() as db:
                for task_id in task_ids:
                    task = db.query(Task).filter(Task.id == task_id).first()
                    if task:
                        # タスクをFAILEDに変更
                        task.status = TaskStatus.FAILED
                        task.finished_at = datetime.now()
                        self.health_stats['auto_repairs'] += 1
                        logger.info(f"🔧 Auto-repaired stuck task: {task_id}")
                
                db.commit()
                
        except Exception as e:
            logger.error(f"❌ Auto-repair failed: {e}")

    async def get_health_status(self) -> Dict[str, Any]:
        """現在のヘルス状態を取得"""
        return self.health_stats.copy()

    async def get_performance_history(self) -> List[Dict]:
        """パフォーマンス履歴を取得"""
        if not self.redis_client:
            return []
        
        try:
            history = await self.redis_client.lrange("system:performance_history", 0, -1)
            return [json.loads(item) for item in history]
        except Exception as e:
            logger.error(f"❌ Performance history retrieval failed: {e}")
            return []

# グローバルインスタンス
system_health_monitor = SystemHealthMonitor()
