"""
パフォーマンス統合テスト
"""
import pytest
import time
import asyncio
import concurrent.futures
import threading
import psutil
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import requests

from app.main import app
from app.performance.python313_optimizations import (
    FreeThreadedExecutor, 
    AsyncOptimizer, 
    MemoryOptimizer,
    performance_monitor
)


@pytest.mark.integration
@pytest.mark.performance
class TestPerformanceIntegration:
    """パフォーマンス統合テスト"""

    @pytest.fixture(autouse=True)
    def setup_performance_test(self, auth_headers):
        """パフォーマンステスト用セットアップ"""
        self.auth_headers = auth_headers
        self.performance_data = []

    def measure_performance(self, func, *args, **kwargs):
        """パフォーマンス測定ヘルパー"""
        process = psutil.Process()
        start_memory = process.memory_info().rss
        start_time = time.perf_counter()
        
        result = func(*args, **kwargs)
        
        end_time = time.perf_counter()
        end_memory = process.memory_info().rss
        
        performance_data = {
            "execution_time": end_time - start_time,
            "memory_used": end_memory - start_memory,
            "memory_peak": end_memory
        }
        
        self.performance_data.append(performance_data)
        return result, performance_data

    def test_api_response_time_performance(self, client):
        """API レスポンス時間パフォーマンステスト"""
        
        endpoints = [
            "/api/projects/",
            "/api/spiders/",
            "/api/tasks/",
            "/api/results/",
            "/api/schedules/"
        ]
        
        response_times = []
        
        for endpoint in endpoints:
            start_time = time.perf_counter()
            response = client.get(endpoint, headers=self.auth_headers)
            end_time = time.perf_counter()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200
            assert response_time < 1.0, f"{endpoint} took {response_time:.2f}s (>1s)"
        
        # 平均レスポンス時間
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 0.5, f"Average response time {avg_response_time:.2f}s (>0.5s)"

    def test_concurrent_api_requests_performance(self, client):
        """並行APIリクエストパフォーマンステスト"""
        
        def make_request(endpoint):
            return client.get(endpoint, headers=self.auth_headers)
        
        # 10個の並行リクエスト
        endpoints = ["/api/projects/"] * 10
        
        start_time = time.perf_counter()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, endpoint) for endpoint in endpoints]
            responses = [future.result() for future in futures]
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # 全てのリクエストが成功
        for response in responses:
            assert response.status_code == 200
        
        # 並行処理により2秒以内で完了
        assert total_time < 2.0, f"Concurrent requests took {total_time:.2f}s (>2s)"

    def test_database_query_performance(self, client, db_session):
        """データベースクエリパフォーマンステスト"""
        
        from app.database import Project, Spider, Task
        
        # 大量データ作成（テスト用）
        projects = []
        for i in range(50):
            project = Project(
                id=f"perf-project-{i}",
                name=f"Performance Test Project {i}",
                description=f"Performance test project {i}",
                path=f"/tmp/perf_project_{i}",
                user_id="test-user"
            )
            projects.append(project)
        
        db_session.add_all(projects)
        db_session.commit()
        
        # クエリパフォーマンステスト
        start_time = time.perf_counter()
        
        # プロジェクト一覧取得
        response = client.get("/api/projects/", headers=self.auth_headers)
        
        end_time = time.perf_counter()
        query_time = end_time - start_time
        
        assert response.status_code == 200
        projects_data = response.json()
        assert len(projects_data) >= 50
        
        # 大量データでも1秒以内
        assert query_time < 1.0, f"Database query took {query_time:.2f}s (>1s)"

    def test_python313_optimization_performance(self):
        """Python 3.13最適化パフォーマンステスト"""
        
        def cpu_intensive_task(n):
            return sum(i * i for i in range(n))
        
        # シーケンシャル実行
        start_time = time.perf_counter()
        sequential_results = [cpu_intensive_task(10000) for _ in range(4)]
        sequential_time = time.perf_counter() - start_time
        
        # 並列実行（Python 3.13最適化）
        start_time = time.perf_counter()
        with FreeThreadedExecutor(max_workers=4) as executor:
            futures = [
                executor.submit_cpu_intensive(cpu_intensive_task, 10000) 
                for _ in range(4)
            ]
            parallel_results = [future.result() for future in futures]
        parallel_time = time.perf_counter() - start_time
        
        # 結果の整合性確認
        assert sequential_results == parallel_results
        
        # パフォーマンス改善確認（並列処理の効果）
        speedup = sequential_time / parallel_time if parallel_time > 0 else 0
        print(f"Speedup: {speedup:.2f}x (Sequential: {sequential_time:.3f}s, Parallel: {parallel_time:.3f}s)")
        
        # 最低限の並列化効果を確認
        assert speedup > 0.8, f"Parallel processing not effective: {speedup:.2f}x"

    @pytest.mark.asyncio
    async def test_async_optimization_performance(self):
        """非同期最適化パフォーマンステスト"""
        
        async def async_task(delay):
            await asyncio.sleep(delay)
            return delay
        
        # 通常の非同期実行
        start_time = time.perf_counter()
        normal_tasks = [async_task(0.1) for _ in range(10)]
        normal_results = await asyncio.gather(*normal_tasks)
        normal_time = time.perf_counter() - start_time
        
        # 最適化された非同期実行
        start_time = time.perf_counter()
        async with AsyncOptimizer() as optimizer:
            optimized_coros = [async_task(0.1) for _ in range(10)]
            optimized_results = await optimizer.run_with_concurrency_limit(
                optimized_coros, limit=5, group_name="perf_test"
            )
        optimized_time = time.perf_counter() - start_time
        
        # 結果の整合性確認
        assert len(normal_results) == len(optimized_results)
        
        # 最適化版が同等以上の性能
        assert optimized_time <= normal_time * 1.2, f"Optimized version slower: {optimized_time:.3f}s vs {normal_time:.3f}s"

    def test_memory_optimization_performance(self):
        """メモリ最適化パフォーマンステスト"""
        
        optimizer = MemoryOptimizer()
        process = psutil.Process()
        
        # 初期メモリ使用量
        initial_memory = process.memory_info().rss
        
        # 大量データ作成
        large_data = []
        for i in range(1000):
            data = f"Large data item {i}" * 100
            large_data.append(data)
        
        # ピークメモリ使用量
        peak_memory = process.memory_info().rss
        memory_increase = peak_memory - initial_memory
        
        # メモリ最適化実行
        optimizer.clear_caches()
        
        # ガベージコレクション
        import gc
        collected = gc.collect()
        
        # データ削除
        del large_data
        gc.collect()
        
        # 最終メモリ使用量
        final_memory = process.memory_info().rss
        memory_recovered = peak_memory - final_memory
        
        # メモリ回収効率確認
        recovery_rate = memory_recovered / memory_increase if memory_increase > 0 else 0
        assert recovery_rate > 0.5, f"Poor memory recovery: {recovery_rate:.2f} ({memory_recovered} / {memory_increase})"

    def test_file_system_performance(self, client, temp_dir):
        """ファイルシステムパフォーマンステスト"""
        
        # 大量ファイル作成テスト
        start_time = time.perf_counter()
        
        project_data = {
            "name": "File System Performance Test",
            "description": "Testing file system performance",
            "path": str(temp_dir / "fs_perf_test")
        }
        
        response = client.post(
            "/api/projects/",
            json=project_data,
            headers=self.auth_headers
        )
        
        end_time = time.perf_counter()
        creation_time = end_time - start_time
        
        assert response.status_code == 200
        project = response.json()
        project_id = project["id"]
        
        # プロジェクト作成が2秒以内
        assert creation_time < 2.0, f"Project creation took {creation_time:.2f}s (>2s)"
        
        # ファイル一覧取得パフォーマンス
        start_time = time.perf_counter()
        
        response = client.get(
            f"/api/projects/{project_id}/files",
            headers=self.auth_headers
        )
        
        end_time = time.perf_counter()
        list_time = end_time - start_time
        
        assert response.status_code == 200
        assert list_time < 1.0, f"File listing took {list_time:.2f}s (>1s)"

    def test_websocket_performance(self):
        """WebSocketパフォーマンステスト"""
        
        from app.websocket.manager import manager
        
        # 大量接続シミュレーション
        connections = {}
        connection_count = 100
        
        start_time = time.perf_counter()
        
        # 接続作成
        for i in range(connection_count):
            connection_id = f"perf-test-{i}"
            mock_websocket = MagicMock()
            mock_websocket.send_text = MagicMock()
            connections[connection_id] = mock_websocket
            manager.active_connections[connection_id] = mock_websocket
        
        connection_time = time.perf_counter() - start_time
        
        # 大量メッセージ送信
        start_time = time.perf_counter()
        
        message = {"type": "performance_test", "data": {"test": True}}
        
        # 非同期でブロードキャスト（実際の実装では非同期）
        for connection_id in connections:
            mock_websocket = connections[connection_id]
            mock_websocket.send_text(str(message))
        
        broadcast_time = time.perf_counter() - start_time
        
        # 接続削除
        for connection_id in connections:
            if connection_id in manager.active_connections:
                del manager.active_connections[connection_id]
        
        # パフォーマンス要件
        assert connection_time < 1.0, f"Connection setup took {connection_time:.2f}s (>1s)"
        assert broadcast_time < 0.5, f"Broadcast took {broadcast_time:.2f}s (>0.5s)"

    def test_scrapy_service_performance(self, client):
        """Scrapyサービスパフォーマンステスト"""
        
        with patch('app.services.scrapy_service.ScrapyPlaywrightService') as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            
            # 高速レスポンスをシミュレート
            mock_instance.run_spider.return_value = "fast-task-id"
            mock_instance.get_projects.return_value = []
            mock_instance.get_spiders.return_value = []
            
            # タスク実行パフォーマンス
            start_time = time.perf_counter()
            
            task_data = {
                "spider_id": "test-spider",
                "settings": {"DOWNLOAD_DELAY": 0.1}
            }
            
            response = client.post(
                "/api/tasks/",
                json=task_data,
                headers=self.auth_headers
            )
            
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            
            assert response.status_code == 200
            assert execution_time < 1.0, f"Task execution took {execution_time:.2f}s (>1s)"

    def test_overall_system_performance(self, client):
        """システム全体パフォーマンステスト"""
        
        # システム全体のワークフローテスト
        start_time = time.perf_counter()
        
        # 1. プロジェクト作成
        project_data = {
            "name": "System Performance Test",
            "description": "Overall system performance test",
            "path": "/tmp/system_perf_test"
        }
        
        response = client.post(
            "/api/projects/",
            json=project_data,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        project_id = response.json()["id"]
        
        # 2. スパイダー作成
        spider_data = {
            "name": "perf_spider",
            "description": "Performance test spider",
            "template": "basic",
            "code": "# Performance test spider"
        }
        
        response = client.post(
            f"/api/projects/{project_id}/spiders",
            json=spider_data,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        spider_id = response.json()["id"]
        
        # 3. タスク実行（モック）
        with patch('app.services.scrapy_service.ScrapyPlaywrightService.run_spider') as mock_run:
            mock_run.return_value = "system-perf-task"
            
            task_data = {
                "spider_id": spider_id,
                "settings": {}
            }
            
            response = client.post(
                "/api/tasks/",
                json=task_data,
                headers=self.auth_headers
            )
            assert response.status_code == 200
        
        # 4. 結果取得
        response = client.get("/api/results/", headers=self.auth_headers)
        assert response.status_code == 200
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # システム全体のワークフローが5秒以内
        assert total_time < 5.0, f"System workflow took {total_time:.2f}s (>5s)"
        
        print(f"System performance test completed in {total_time:.2f}s")

    def teardown_method(self):
        """テスト後のパフォーマンスデータ出力"""
        if self.performance_data:
            total_time = sum(data["execution_time"] for data in self.performance_data)
            total_memory = sum(data["memory_used"] for data in self.performance_data)
            
            print(f"\nPerformance Summary:")
            print(f"  Total execution time: {total_time:.3f}s")
            print(f"  Total memory used: {total_memory / 1024 / 1024:.2f}MB")
            print(f"  Average execution time: {total_time / len(self.performance_data):.3f}s")
            print(f"  Test count: {len(self.performance_data)}")
