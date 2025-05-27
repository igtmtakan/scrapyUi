"""
Python 3.13パフォーマンス最適化API
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import asyncio
import time
from datetime import datetime

from ..database import get_db
from ..models.schemas import Task, TaskCreate
from ..services.scrapy_service import ScrapyPlaywrightService
from ..api.auth import get_current_active_user
from ..performance.python313_optimizations import (
    FreeThreadedExecutor,
    AsyncOptimizer,
    MemoryOptimizer,
    performance_monitor,
    PerformanceMetrics
)
from ..utils.logging_config import get_logger, log_with_context
from ..utils.error_handler import TaskException, ErrorCode

logger = get_logger(__name__)
router = APIRouter(prefix="/performance", tags=["performance"])

# グローバルインスタンス
memory_optimizer = MemoryOptimizer()

@router.post("/tasks/optimized", response_model=Dict[str, Any])
@performance_monitor
async def create_optimized_task(
    task_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Python 3.13最適化版タスク作成
    Free-threaded並列処理を活用
    """
    try:
        log_with_context(
            logger, "INFO",
            "Creating optimized task with Python 3.13 features",
            user_id=current_user.id,
            extra_data={"task_data": task_data}
        )

        scrapy_service = ScrapyPlaywrightService()
        
        # 最適化されたスパイダー実行
        task_id = scrapy_service.run_spider_optimized(
            project_path=task_data["project_path"],
            spider_name=task_data["spider_name"],
            task_id=task_data.get("task_id"),
            settings=task_data.get("settings")
        )

        return {
            "task_id": task_id,
            "status": "started",
            "optimization": "python313",
            "features": ["free_threaded", "jit_optimized", "memory_optimized"]
        }

    except Exception as e:
        logger.error(f"Error creating optimized task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create optimized task: {str(e)}"
        )

@router.post("/tasks/batch", response_model=Dict[str, Any])
@performance_monitor
async def create_batch_tasks(
    tasks_data: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    複数タスクの並列バッチ実行
    Python 3.13のasyncio最適化を活用
    """
    try:
        log_with_context(
            logger, "INFO",
            f"Creating batch tasks: {len(tasks_data)} tasks",
            user_id=current_user.id,
            extra_data={"batch_size": len(tasks_data)}
        )

        scrapy_service = ScrapyPlaywrightService()
        
        # 非同期バッチ処理
        async with AsyncOptimizer() as optimizer:
            # 非同期タスクを作成
            async def create_single_task(task_data):
                return await asyncio.get_event_loop().run_in_executor(
                    None,
                    scrapy_service.run_spider_optimized,
                    task_data["project_path"],
                    task_data["spider_name"],
                    task_data.get("task_id"),
                    task_data.get("settings")
                )
            
            # バッチ処理で実行
            task_ids = await optimizer.batch_process(
                items=tasks_data,
                processor=create_single_task,
                batch_size=5,  # 5タスクずつバッチ処理
                concurrency_limit=3  # 同時実行数制限
            )

        return {
            "task_ids": task_ids,
            "batch_size": len(tasks_data),
            "status": "all_started",
            "optimization": "python313_async_batch"
        }

    except Exception as e:
        logger.error(f"Error creating batch tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch tasks: {str(e)}"
        )

@router.get("/metrics", response_model=Dict[str, Any])
async def get_performance_metrics(
    current_user = Depends(get_current_active_user)
):
    """パフォーマンスメトリクスを取得"""
    try:
        # メモリ使用量の取得
        import psutil
        import sys
        
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Python 3.13固有の情報
        python_info = {
            "version": sys.version,
            "implementation": sys.implementation.name,
            "free_threaded": hasattr(sys, '_is_gil_enabled') and not sys._is_gil_enabled(),
            "jit_enabled": hasattr(sys, '_enable_jit')
        }
        
        # システムリソース
        system_info = {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "memory_percent": psutil.virtual_memory().percent
        }
        
        # プロセス情報
        process_info = {
            "memory_rss": memory_info.rss,
            "memory_vms": memory_info.vms,
            "cpu_percent": process.cpu_percent(),
            "num_threads": process.num_threads(),
            "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
        }

        return {
            "timestamp": datetime.now().isoformat(),
            "python": python_info,
            "system": system_info,
            "process": process_info,
            "optimization_status": {
                "free_threaded_available": python_info["free_threaded"],
                "jit_available": python_info["jit_enabled"],
                "memory_optimizer_active": True,
                "async_optimizer_available": True
            }
        }

    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )

@router.post("/optimize/memory", response_model=Dict[str, Any])
async def optimize_memory(
    current_user = Depends(get_current_active_user)
):
    """メモリ最適化を実行"""
    try:
        log_with_context(
            logger, "INFO",
            "Executing memory optimization",
            user_id=current_user.id
        )

        # メモリキャッシュをクリア
        memory_optimizer.clear_caches()
        
        # ガベージコレクションを実行
        import gc
        collected = gc.collect()
        
        # メモリ使用量を取得
        import psutil
        process = psutil.Process()
        memory_after = process.memory_info()

        return {
            "status": "completed",
            "garbage_collected": collected,
            "memory_rss": memory_after.rss,
            "memory_vms": memory_after.vms,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error optimizing memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize memory: {str(e)}"
        )

@router.get("/benchmark", response_model=Dict[str, Any])
@performance_monitor
async def run_performance_benchmark(
    current_user = Depends(get_current_active_user)
):
    """パフォーマンスベンチマークを実行"""
    try:
        log_with_context(
            logger, "INFO",
            "Running performance benchmark",
            user_id=current_user.id
        )

        results = {}
        
        # CPU集約的タスクのベンチマーク
        with FreeThreadedExecutor(max_workers=4) as executor:
            start_time = time.perf_counter()
            
            # 並列CPU集約的タスク
            def cpu_intensive_task(n):
                return sum(i * i for i in range(n))
            
            futures = [
                executor.submit_cpu_intensive(cpu_intensive_task, 100000)
                for _ in range(4)
            ]
            
            parallel_results = [future.result() for future in futures]
            parallel_time = time.perf_counter() - start_time
            
            # シーケンシャル実行との比較
            start_time = time.perf_counter()
            sequential_results = [cpu_intensive_task(100000) for _ in range(4)]
            sequential_time = time.perf_counter() - start_time
            
            results["cpu_benchmark"] = {
                "parallel_time": parallel_time,
                "sequential_time": sequential_time,
                "speedup": sequential_time / parallel_time if parallel_time > 0 else 0,
                "parallel_results": len(parallel_results),
                "sequential_results": len(sequential_results)
            }

        # 非同期処理のベンチマーク
        async with AsyncOptimizer() as optimizer:
            start_time = time.perf_counter()
            
            async def async_task(delay):
                await asyncio.sleep(delay)
                return delay
            
            coros = [async_task(0.1) for _ in range(10)]
            async_results = await optimizer.run_with_concurrency_limit(
                coros, limit=5, group_name="benchmark"
            )
            async_time = time.perf_counter() - start_time
            
            results["async_benchmark"] = {
                "async_time": async_time,
                "tasks_completed": len(async_results),
                "concurrency_limit": 5
            }

        # メモリ使用量
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        results["memory_usage"] = {
            "rss": memory_info.rss,
            "vms": memory_info.vms,
            "percent": process.memory_percent()
        }

        return {
            "timestamp": datetime.now().isoformat(),
            "benchmark_results": results,
            "python_version": sys.version,
            "optimization_features": {
                "free_threaded": hasattr(sys, '_is_gil_enabled') and not sys._is_gil_enabled(),
                "jit_enabled": hasattr(sys, '_enable_jit')
            }
        }

    except Exception as e:
        logger.error(f"Error running benchmark: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run benchmark: {str(e)}"
        )
