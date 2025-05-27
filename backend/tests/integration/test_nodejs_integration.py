"""
Node.js サービス統合テスト
"""
import pytest
import requests
import json
import time
import asyncio
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import tempfile
from pathlib import Path

from app.main import app


@pytest.mark.integration
class TestNodeJSIntegration:
    """Node.js サービス統合テスト"""

    @pytest.fixture(autouse=True)
    def setup_nodejs_test(self, auth_headers):
        """Node.js統合テスト用セットアップ"""
        self.auth_headers = auth_headers
        self.nodejs_base_url = "http://localhost:3001"
        self.api_base_url = "http://localhost:8000"

    def test_nodejs_service_health_check(self):
        """Node.js サービスヘルスチェック"""
        try:
            response = requests.get(f"{self.nodejs_base_url}/api/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                assert "status" in health_data
                assert health_data["status"] == "healthy"
                assert "service" in health_data
                assert "uptime" in health_data
            else:
                pytest.skip("Node.js service not available")
        except requests.exceptions.ConnectionError:
            pytest.skip("Node.js service not running")

    def test_nodejs_pdf_generation_integration(self, client):
        """PDF生成統合テスト"""
        
        # Node.js サービスのモック
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "pdf_url": "/tmp/generated.pdf",
                "file_size": 12345,
                "generation_time": 1.5
            }
            mock_post.return_value = mock_response
            
            pdf_data = {
                "url": "https://example.com",
                "options": {
                    "format": "A4",
                    "margin": {
                        "top": "1cm",
                        "right": "1cm",
                        "bottom": "1cm",
                        "left": "1cm"
                    },
                    "printBackground": True
                }
            }
            
            response = client.post(
                "/api/nodejs/pdf/generate",
                json=pdf_data,
                headers=self.auth_headers
            )
            
            assert response.status_code == 200
            result = response.json()
            assert "pdf_url" in result
            assert "file_size" in result

    def test_nodejs_screenshot_integration(self, client):
        """スクリーンショット統合テスト"""
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "screenshot_url": "/tmp/screenshot.png",
                "file_size": 54321,
                "dimensions": {"width": 1920, "height": 1080}
            }
            mock_post.return_value = mock_response
            
            screenshot_data = {
                "url": "https://example.com",
                "options": {
                    "width": 1920,
                    "height": 1080,
                    "fullPage": True,
                    "type": "png"
                }
            }
            
            response = client.post(
                "/api/nodejs/screenshot/capture",
                json=screenshot_data,
                headers=self.auth_headers
            )
            
            assert response.status_code == 200
            result = response.json()
            assert "screenshot_url" in result
            assert "dimensions" in result

    def test_nodejs_scraping_integration(self, client):
        """Node.js スクレイピング統合テスト"""
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "data": [
                    {"title": "Example Title 1", "url": "https://example.com/1"},
                    {"title": "Example Title 2", "url": "https://example.com/2"}
                ],
                "metadata": {
                    "total_items": 2,
                    "execution_time": 2.3,
                    "pages_scraped": 1
                }
            }
            mock_post.return_value = mock_response
            
            scraping_data = {
                "url": "https://example.com",
                "selectors": {
                    "title": "h1",
                    "links": "a[href]"
                },
                "options": {
                    "waitFor": "networkidle0",
                    "timeout": 30000
                }
            }
            
            response = client.post(
                "/api/nodejs/scraping/extract",
                json=scraping_data,
                headers=self.auth_headers
            )
            
            assert response.status_code == 200
            result = response.json()
            assert "data" in result
            assert "metadata" in result
            assert len(result["data"]) == 2

    def test_nodejs_workflow_integration(self, client):
        """Node.js ワークフロー統合テスト"""
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "workflow_id": "workflow-123",
                "status": "completed",
                "results": {
                    "steps_completed": 3,
                    "total_steps": 3,
                    "execution_time": 5.7,
                    "outputs": [
                        {"step": "navigate", "success": True},
                        {"step": "extract", "success": True, "data_count": 10},
                        {"step": "screenshot", "success": True, "file_path": "/tmp/final.png"}
                    ]
                }
            }
            mock_post.return_value = mock_response
            
            workflow_data = {
                "name": "E-commerce Product Scraping",
                "steps": [
                    {
                        "type": "navigate",
                        "url": "https://example-shop.com/products"
                    },
                    {
                        "type": "extract",
                        "selectors": {
                            "product_name": ".product-title",
                            "price": ".price",
                            "image": ".product-image img"
                        }
                    },
                    {
                        "type": "screenshot",
                        "options": {"fullPage": True}
                    }
                ]
            }
            
            response = client.post(
                "/api/nodejs/workflows/execute",
                json=workflow_data,
                headers=self.auth_headers
            )
            
            assert response.status_code == 200
            result = response.json()
            assert "workflow_id" in result
            assert "results" in result
            assert result["results"]["steps_completed"] == 3

    def test_nodejs_batch_processing_integration(self, client):
        """Node.js バッチ処理統合テスト"""
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "batch_id": "batch-456",
                "status": "processing",
                "total_urls": 5,
                "completed": 0,
                "failed": 0,
                "estimated_completion": "2024-01-01T12:30:00Z"
            }
            mock_post.return_value = mock_response
            
            batch_data = {
                "urls": [
                    "https://example.com/page1",
                    "https://example.com/page2",
                    "https://example.com/page3",
                    "https://example.com/page4",
                    "https://example.com/page5"
                ],
                "action": "screenshot",
                "options": {
                    "width": 1920,
                    "height": 1080,
                    "format": "png"
                },
                "concurrency": 2
            }
            
            response = client.post(
                "/api/nodejs/batch/process",
                json=batch_data,
                headers=self.auth_headers
            )
            
            assert response.status_code == 200
            result = response.json()
            assert "batch_id" in result
            assert "total_urls" in result
            assert result["total_urls"] == 5

    def test_nodejs_metrics_integration(self, client):
        """Node.js メトリクス統合テスト"""
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "system": {
                    "uptime": 3600,
                    "memory_usage": {
                        "used": 256000000,
                        "total": 1024000000,
                        "percentage": 25.0
                    },
                    "cpu_usage": 15.5
                },
                "service": {
                    "total_requests": 1250,
                    "successful_requests": 1200,
                    "failed_requests": 50,
                    "average_response_time": 1.2,
                    "active_browser_instances": 3,
                    "max_browser_instances": 5
                },
                "performance": {
                    "pdf_generations": 45,
                    "screenshots_taken": 120,
                    "pages_scraped": 85,
                    "workflows_executed": 12
                }
            }
            mock_get.return_value = mock_response
            
            response = client.get(
                "/api/nodejs/metrics",
                headers=self.auth_headers
            )
            
            assert response.status_code == 200
            metrics = response.json()
            assert "system" in metrics
            assert "service" in metrics
            assert "performance" in metrics
            assert metrics["service"]["total_requests"] == 1250

    def test_nodejs_error_handling_integration(self, client):
        """Node.js エラーハンドリング統合テスト"""
        
        # タイムアウトエラーのテスト
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 408
            mock_response.json.return_value = {
                "success": False,
                "error": "Request timeout",
                "error_code": "TIMEOUT_ERROR",
                "details": "Page load exceeded 30 seconds"
            }
            mock_post.return_value = mock_response
            
            pdf_data = {
                "url": "https://very-slow-site.com",
                "options": {"timeout": 1000}  # 1秒タイムアウト
            }
            
            response = client.post(
                "/api/nodejs/pdf/generate",
                json=pdf_data,
                headers=self.auth_headers
            )
            
            assert response.status_code == 408
            error = response.json()
            assert "error" in error
            assert "error_code" in error

    def test_nodejs_browser_pool_integration(self, client):
        """Node.js ブラウザプール統合テスト"""
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "pool_status": {
                    "total_instances": 5,
                    "active_instances": 2,
                    "idle_instances": 3,
                    "max_instances": 10,
                    "queue_length": 0
                },
                "instances": [
                    {
                        "id": "browser-1",
                        "status": "active",
                        "created_at": "2024-01-01T10:00:00Z",
                        "last_used": "2024-01-01T10:05:00Z",
                        "pages_count": 2
                    },
                    {
                        "id": "browser-2",
                        "status": "idle",
                        "created_at": "2024-01-01T10:01:00Z",
                        "last_used": "2024-01-01T10:03:00Z",
                        "pages_count": 0
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            response = client.get(
                "/api/nodejs/browser-pool/status",
                headers=self.auth_headers
            )
            
            assert response.status_code == 200
            pool_status = response.json()
            assert "pool_status" in pool_status
            assert "instances" in pool_status
            assert pool_status["pool_status"]["total_instances"] == 5

    @pytest.mark.asyncio
    async def test_nodejs_async_integration(self, async_client):
        """Node.js 非同期統合テスト"""
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "task_id": "async-task-123",
                "status": "processing"
            }
            mock_post.return_value = mock_response
            
            # 非同期タスクの開始
            async_task_data = {
                "type": "bulk_screenshot",
                "urls": [f"https://example.com/page{i}" for i in range(10)],
                "options": {"format": "png", "width": 1920, "height": 1080}
            }
            
            response = await async_client.post(
                "/api/nodejs/async/start",
                json=async_task_data,
                headers=self.auth_headers
            )
            
            assert response.status_code == 200
            result = response.json()
            assert "task_id" in result

    def test_nodejs_security_integration(self, client):
        """Node.js セキュリティ統合テスト"""
        
        # 不正なURLでのアクセステスト
        malicious_data = {
            "url": "javascript:alert('xss')",
            "options": {}
        }
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "success": False,
                "error": "Invalid URL scheme",
                "error_code": "SECURITY_ERROR"
            }
            mock_post.return_value = mock_response
            
            response = client.post(
                "/api/nodejs/pdf/generate",
                json=malicious_data,
                headers=self.auth_headers
            )
            
            assert response.status_code == 400
            error = response.json()
            assert "error" in error

    def test_nodejs_performance_integration(self, client):
        """Node.js パフォーマンス統合テスト"""
        
        start_time = time.time()
        
        # 複数の並列リクエスト
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "execution_time": 0.5
            }
            mock_post.return_value = mock_response
            
            # 5つの並列PDF生成リクエスト
            for i in range(5):
                pdf_data = {
                    "url": f"https://example.com/page{i}",
                    "options": {"format": "A4"}
                }
                
                response = client.post(
                    "/api/nodejs/pdf/generate",
                    json=pdf_data,
                    headers=self.auth_headers
                )
                assert response.status_code == 200
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # パフォーマンス要件（3秒以内）
        assert total_time < 3.0, f"Performance test took {total_time:.2f} seconds"
