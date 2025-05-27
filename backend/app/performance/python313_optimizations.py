"""
Python 3.13の新機能を活用したパフォーマンス最適化
"""
import asyncio
import concurrent.futures
import threading
import time
from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass
from functools import wraps, lru_cache
import weakref
from collections.abc import Coroutine
import sys

from ..utils.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T')
R = TypeVar('R')

@dataclass(slots=True, frozen=True)  # Python 3.13の最適化されたslots
class PerformanceMetrics:
    """パフォーマンスメトリクス（メモリ効率化）"""
    operation: str
    start_time: float
    end_time: float
    memory_usage: int
    thread_id: int

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

class FreeThreadedExecutor:
    """
    Python 3.13のFree-threaded機能を活用した並列実行エンジン
    GILが無効化された環境での真の並列処理
    """

    def __init__(self, max_workers: Optional[int] = None):
        import os
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self._executor = None
        self._metrics: List[PerformanceMetrics] = []
        self._lock = threading.Lock()

        # Python 3.13のfree-threaded機能が有効かチェック
        self.free_threaded_available = hasattr(sys, '_is_gil_enabled') and not sys._is_gil_enabled()

        if self.free_threaded_available:
            logger.info("Free-threaded Python detected - enabling true parallelism")
        else:
            logger.info("Standard Python - using thread pool with GIL")

    def __enter__(self):
        # 常にThreadPoolExecutorを使用（pickle問題を回避）
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="ScrapyUI-OptimizedThread"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._executor:
            self._executor.shutdown(wait=True)

    def submit_cpu_intensive(self, fn: Callable[..., T], *args, **kwargs) -> concurrent.futures.Future[T]:
        """CPU集約的なタスクを並列実行"""
        if not self._executor:
            raise RuntimeError("Executor not initialized. Use with statement.")

        start_time = time.perf_counter()

        def wrapped_fn(*args, **kwargs):
            try:
                result = fn(*args, **kwargs)
                end_time = time.perf_counter()

                # メトリクス記録
                with self._lock:
                    self._metrics.append(PerformanceMetrics(
                        operation=fn.__name__,
                        start_time=start_time,
                        end_time=end_time,
                        memory_usage=sys.getsizeof(result) if result else 0,
                        thread_id=threading.get_ident()
                    ))

                return result
            except Exception as e:
                logger.error(f"Error in {fn.__name__}: {e}")
                raise

        return self._executor.submit(wrapped_fn, *args, **kwargs)

    def map_parallel(self, fn: Callable[[T], R], iterable: List[T], chunk_size: Optional[int] = None) -> List[R]:
        """並列マッピング処理"""
        if not self._executor:
            raise RuntimeError("Executor not initialized. Use with statement.")

        if self.free_threaded_available:
            # Free-threaded環境では細かいチャンクで並列処理
            chunk_size = chunk_size or max(1, len(iterable) // (self.max_workers * 2))
        else:
            # GIL環境では大きなチャンクでプロセス間通信を最小化
            chunk_size = chunk_size or max(1, len(iterable) // self.max_workers)

        futures = []
        for i in range(0, len(iterable), chunk_size):
            chunk = iterable[i:i + chunk_size]
            future = self.submit_cpu_intensive(lambda items: [fn(item) for item in items], chunk)
            futures.append(future)

        results = []
        for future in concurrent.futures.as_completed(futures):
            results.extend(future.result())

        return results

    def get_metrics(self) -> List[PerformanceMetrics]:
        """パフォーマンスメトリクスを取得"""
        with self._lock:
            return self._metrics.copy()

class AsyncOptimizer:
    """
    Python 3.13の改善されたasyncio機能を活用した非同期処理最適化
    """

    def __init__(self):
        self._semaphore_pool: Dict[str, asyncio.Semaphore] = {}
        self._task_groups: List[asyncio.TaskGroup] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 全てのタスクグループの完了を待機
        for task_group in self._task_groups:
            if not task_group._done:
                await task_group.__aexit__(exc_type, exc_val, exc_tb)

    def get_semaphore(self, name: str, limit: int = 10) -> asyncio.Semaphore:
        """名前付きセマフォアを取得（リソース制限）"""
        if name not in self._semaphore_pool:
            self._semaphore_pool[name] = asyncio.Semaphore(limit)
        return self._semaphore_pool[name]

    async def run_with_concurrency_limit(
        self,
        coros: List[Coroutine],
        limit: int = 10,
        group_name: str = "default"
    ) -> List[Any]:
        """
        並行実行数を制限して非同期タスクを実行
        Python 3.13のTaskGroupを活用
        """
        semaphore = self.get_semaphore(group_name, limit)

        async def limited_coro(coro):
            async with semaphore:
                return await coro

        # Python 3.13のTaskGroupを使用
        async with asyncio.TaskGroup() as tg:
            self._task_groups.append(tg)
            tasks = [tg.create_task(limited_coro(coro)) for coro in coros]

        return [task.result() for task in tasks]

    async def batch_process(
        self,
        items: List[T],
        processor: Callable[[T], Coroutine[Any, Any, R]],
        batch_size: int = 50,
        concurrency_limit: int = 10
    ) -> List[R]:
        """バッチ処理で大量データを効率的に処理"""
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            coros = [processor(item) for item in batch]

            batch_results = await self.run_with_concurrency_limit(
                coros,
                limit=concurrency_limit,
                group_name=f"batch_{i//batch_size}"
            )
            results.extend(batch_results)

            # バッチ間で少し待機（リソース負荷軽減）
            await asyncio.sleep(0.01)

        return results

class MemoryOptimizer:
    """
    Python 3.13のメモリ最適化機能を活用
    """

    def __init__(self):
        self._weak_cache: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
        self._lru_caches: Dict[str, Any] = {}

    def cached_property(self, maxsize: int = 128):
        """メモリ効率的なプロパティキャッシュ"""
        def decorator(func):
            cache_name = f"{func.__name__}_cache"
            if cache_name not in self._lru_caches:
                self._lru_caches[cache_name] = lru_cache(maxsize=maxsize)(func)

            @wraps(func)
            def wrapper(self_obj):
                return self._lru_caches[cache_name](self_obj)

            return property(wrapper)
        return decorator

    def weak_cache(self, key: str, factory: Callable[[], T]) -> T:
        """弱参照キャッシュ（メモリリーク防止）"""
        if key in self._weak_cache:
            return self._weak_cache[key]

        value = factory()
        # 弱参照可能なオブジェクトのみキャッシュ
        try:
            self._weak_cache[key] = value
        except TypeError:
            # 弱参照できない場合は通常のキャッシュを使用
            if not hasattr(self, '_regular_cache'):
                self._regular_cache = {}
            self._regular_cache[key] = value
        return value

    def clear_caches(self):
        """全キャッシュをクリア"""
        for cache in self._lru_caches.values():
            if hasattr(cache, 'cache_clear'):
                cache.cache_clear()
        self._weak_cache.clear()
        if hasattr(self, '_regular_cache'):
            self._regular_cache.clear()

class JITOptimizer:
    """
    Python 3.13の実験的JITコンパイラ機能を活用
    """

    @staticmethod
    def enable_jit():
        """JITコンパイラを有効化（実験的機能）"""
        try:
            # Python 3.13の実験的JIT機能
            import sys
            if hasattr(sys, '_enable_jit'):
                sys._enable_jit()
                logger.info("JIT compiler enabled")
                return True
        except Exception as e:
            logger.warning(f"JIT compiler not available: {e}")
        return False

    @staticmethod
    def hot_function(func: Callable) -> Callable:
        """
        頻繁に呼び出される関数をJIT最適化対象としてマーク
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # JIT最適化のヒントを提供
            if hasattr(func, '__code__'):
                func.__code__.co_flags |= 0x1000  # CO_OPTIMIZED flag
            return func(*args, **kwargs)

        wrapper.__jit_optimized__ = True
        return wrapper

# グローバルインスタンス
memory_optimizer = MemoryOptimizer()
jit_optimizer = JITOptimizer()

# JITコンパイラを有効化
jit_optimizer.enable_jit()

def performance_monitor(func: Callable) -> Callable:
    """パフォーマンス監視デコレータ"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        start_memory = sys.getsizeof(args) + sys.getsizeof(kwargs)

        try:
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            end_memory = sys.getsizeof(result) if result else 0

            duration = end_time - start_time
            if duration > 0.1:  # 100ms以上の処理をログ
                logger.info(
                    f"Performance: {func.__name__} took {duration:.3f}s, "
                    f"memory: {start_memory + end_memory} bytes"
                )

            return result
        except Exception as e:
            end_time = time.perf_counter()
            logger.error(
                f"Performance: {func.__name__} failed after {end_time - start_time:.3f}s: {e}"
            )
            raise

    return wrapper
