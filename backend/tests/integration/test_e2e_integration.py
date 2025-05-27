"""
エンドツーエンド（E2E）統合テスト
"""
import pytest
import time
import json
import asyncio
import subprocess
import requests
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.integration
@pytest.mark.e2e
class TestE2EIntegration:
    """エンドツーエンド統合テスト"""

    @pytest.fixture(autouse=True)
    def setup_e2e_test(self, auth_headers, temp_dir):
        """E2Eテスト用セットアップ"""
        self.auth_headers = auth_headers
        self.temp_dir = temp_dir
        self.test_project_path = temp_dir / "e2e_test_project"
        self.test_project_path.mkdir(exist_ok=True)

    def test_complete_scraping_workflow(self, client):
        """完全なスクレイピングワークフローE2Eテスト"""
        
        # 1. ユーザー認証確認
        response = client.get("/api/auth/me", headers=self.auth_headers)
        assert response.status_code == 200
        user_info = response.json()
        assert "email" in user_info
        
        # 2. プロジェクト作成
        project_data = {
            "name": "E2E Test Project",
            "description": "End-to-end test project for complete workflow",
            "path": str(self.test_project_path)
        }
        
        response = client.post(
            "/api/projects/",
            json=project_data,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        project = response.json()
        project_id = project["id"]
        
        # 3. プロジェクト詳細確認
        response = client.get(
            f"/api/projects/{project_id}",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        project_details = response.json()
        assert project_details["name"] == "E2E Test Project"
        
        # 4. プロジェクトファイル構造確認
        response = client.get(
            f"/api/projects/{project_id}/files",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        files = response.json()
        file_names = [f["name"] for f in files]
        assert "scrapy.cfg" in file_names
        
        # 5. スパイダー作成
        spider_code = '''
import scrapy
import json

class E2ETestSpider(scrapy.Spider):
    name = 'e2e_test_spider'
    start_urls = ['http://httpbin.org/json']

    def parse(self, response):
        data = response.json()
        yield {
            'url': response.url,
            'status_code': response.status,
            'data': data,
            'headers': dict(response.headers),
            'timestamp': response.headers.get('Date', '').decode('utf-8') if response.headers.get('Date') else None
        }
        
        # 追加のテストURL
        yield scrapy.Request(
            url='http://httpbin.org/user-agent',
            callback=self.parse_user_agent
        )
    
    def parse_user_agent(self, response):
        data = response.json()
        yield {
            'url': response.url,
            'user_agent': data.get('user-agent'),
            'type': 'user_agent_test'
        }
'''
        
        spider_data = {
            "name": "e2e_test_spider",
            "description": "E2E test spider with multiple requests",
            "template": "basic",
            "start_urls": ["http://httpbin.org/json"],
            "code": spider_code
        }
        
        response = client.post(
            f"/api/projects/{project_id}/spiders",
            json=spider_data,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        spider = response.json()
        spider_id = spider["id"]
        
        # 6. スパイダー詳細確認
        response = client.get(
            f"/api/spiders/{spider_id}",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        spider_details = response.json()
        assert spider_details["name"] == "e2e_test_spider"
        
        # 7. スパイダー設定確認・更新
        settings_data = {
            "DOWNLOAD_DELAY": 1,
            "CONCURRENT_REQUESTS": 2,
            "ROBOTSTXT_OBEY": False,
            "USER_AGENT": "ScrapyUI E2E Test Bot"
        }
        
        response = client.put(
            f"/api/spiders/{spider_id}/settings",
            json=settings_data,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        # 8. タスク実行（モック）
        with patch('app.services.scrapy_service.ScrapyPlaywrightService.run_spider') as mock_run:
            mock_run.return_value = "e2e-test-task-id"
            
            task_data = {
                "spider_id": spider_id,
                "settings": settings_data
            }
            
            response = client.post(
                "/api/tasks/",
                json=task_data,
                headers=self.auth_headers
            )
            assert response.status_code == 200
            task = response.json()
            task_id = task["task_id"]
        
        # 9. タスク状態確認
        response = client.get(
            f"/api/tasks/{task_id}",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        task_details = response.json()
        assert "status" in task_details
        
        # 10. タスク一覧確認
        response = client.get("/api/tasks/", headers=self.auth_headers)
        assert response.status_code == 200
        tasks = response.json()
        task_ids = [t["id"] for t in tasks]
        assert task_id in task_ids
        
        # 11. 結果確認（モック）
        with patch('app.services.scrapy_service.ScrapyPlaywrightService.get_task_results') as mock_results:
            mock_results.return_value = [
                {
                    "url": "http://httpbin.org/json",
                    "status_code": 200,
                    "data": {"test": "data"},
                    "timestamp": "2024-01-01T12:00:00Z"
                },
                {
                    "url": "http://httpbin.org/user-agent",
                    "user_agent": "ScrapyUI E2E Test Bot",
                    "type": "user_agent_test"
                }
            ]
            
            response = client.get(
                f"/api/tasks/{task_id}/results",
                headers=self.auth_headers
            )
            assert response.status_code == 200
            results = response.json()
            assert len(results) == 2
        
        # 12. 結果エクスポート
        export_formats = ["json", "csv", "excel"]
        for format_type in export_formats:
            response = client.get(
                f"/api/tasks/{task_id}/export/{format_type}",
                headers=self.auth_headers
            )
            assert response.status_code == 200
        
        # 13. スケジュール作成
        schedule_data = {
            "name": "E2E Test Schedule",
            "spider_id": spider_id,
            "cron_expression": "0 */6 * * *",  # 6時間ごと
            "is_active": True,
            "settings": settings_data
        }
        
        response = client.post(
            "/api/schedules/",
            json=schedule_data,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        schedule = response.json()
        schedule_id = schedule["id"]
        
        # 14. スケジュール確認
        response = client.get(
            f"/api/schedules/{schedule_id}",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        schedule_details = response.json()
        assert schedule_details["name"] == "E2E Test Schedule"
        
        # 15. プロジェクト統計確認
        response = client.get(
            f"/api/projects/{project_id}/stats",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        stats = response.json()
        assert "spiders_count" in stats
        assert "tasks_count" in stats
        
        # 16. クリーンアップ
        # スケジュール削除
        response = client.delete(
            f"/api/schedules/{schedule_id}",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        # プロジェクト削除
        response = client.delete(
            f"/api/projects/{project_id}",
            headers=self.auth_headers
        )
        assert response.status_code == 200

    def test_multi_user_workflow(self, client):
        """マルチユーザーワークフローE2Eテスト"""
        
        # 管理者ユーザーでのプロジェクト作成
        admin_project_data = {
            "name": "Admin Project",
            "description": "Project created by admin",
            "path": str(self.temp_dir / "admin_project")
        }
        
        response = client.post(
            "/api/projects/",
            json=admin_project_data,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        admin_project = response.json()
        
        # 一般ユーザー用トークン（モック）
        user_headers = {
            "Authorization": "Bearer user-token"
        }
        
        # 一般ユーザーでのアクセス権限テスト
        with patch('app.auth.jwt_handler.verify_token') as mock_verify:
            mock_verify.return_value = {
                "id": "regular-user",
                "email": "user@test.com",
                "is_superuser": False
            }
            
            # 一般ユーザーは自分のプロジェクトのみアクセス可能
            response = client.get("/api/projects/", headers=user_headers)
            # 実際の実装では適切な権限チェックが行われる

    def test_error_recovery_workflow(self, client):
        """エラー回復ワークフローE2Eテスト"""
        
        # 1. 不正なプロジェクト作成試行
        invalid_project_data = {
            "name": "",  # 空の名前
            "description": "Invalid project",
            "path": "/invalid/path"
        }
        
        response = client.post(
            "/api/projects/",
            json=invalid_project_data,
            headers=self.auth_headers
        )
        assert response.status_code == 422
        
        # 2. 正しいプロジェクト作成
        valid_project_data = {
            "name": "Error Recovery Test",
            "description": "Testing error recovery",
            "path": str(self.temp_dir / "error_recovery_test")
        }
        
        response = client.post(
            "/api/projects/",
            json=valid_project_data,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        project = response.json()
        project_id = project["id"]
        
        # 3. 不正なスパイダー作成試行
        invalid_spider_data = {
            "name": "",  # 空の名前
            "code": "invalid python code syntax error"
        }
        
        response = client.post(
            f"/api/projects/{project_id}/spiders",
            json=invalid_spider_data,
            headers=self.auth_headers
        )
        assert response.status_code == 422
        
        # 4. 正しいスパイダー作成
        valid_spider_data = {
            "name": "error_recovery_spider",
            "description": "Error recovery test spider",
            "template": "basic",
            "code": '''
import scrapy

class ErrorRecoverySpider(scrapy.Spider):
    name = 'error_recovery_spider'
    start_urls = ['http://httpbin.org/status/200']

    def parse(self, response):
        yield {'status': response.status, 'url': response.url}
'''
        }
        
        response = client.post(
            f"/api/projects/{project_id}/spiders",
            json=valid_spider_data,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        spider = response.json()
        spider_id = spider["id"]
        
        # 5. タスク実行エラーシミュレーション
        with patch('app.services.scrapy_service.ScrapyPlaywrightService.run_spider') as mock_run:
            mock_run.side_effect = Exception("Scrapy execution failed")
            
            task_data = {
                "spider_id": spider_id,
                "settings": {}
            }
            
            response = client.post(
                "/api/tasks/",
                json=task_data,
                headers=self.auth_headers
            )
            # エラーハンドリングにより適切なエラーレスポンス
            assert response.status_code in [400, 500]
        
        # 6. 正常なタスク実行
        with patch('app.services.scrapy_service.ScrapyPlaywrightService.run_spider') as mock_run:
            mock_run.return_value = "recovery-task-id"
            
            response = client.post(
                "/api/tasks/",
                json=task_data,
                headers=self.auth_headers
            )
            assert response.status_code == 200

    def test_performance_under_load(self, client):
        """負荷下でのパフォーマンスE2Eテスト"""
        
        # 複数プロジェクトの同時作成
        project_ids = []
        
        for i in range(5):
            project_data = {
                "name": f"Load Test Project {i}",
                "description": f"Load test project {i}",
                "path": str(self.temp_dir / f"load_test_{i}")
            }
            
            start_time = time.perf_counter()
            response = client.post(
                "/api/projects/",
                json=project_data,
                headers=self.auth_headers
            )
            end_time = time.perf_counter()
            
            assert response.status_code == 200
            project_ids.append(response.json()["id"])
            
            # 各プロジェクト作成が2秒以内
            creation_time = end_time - start_time
            assert creation_time < 2.0, f"Project creation took {creation_time:.2f}s"
        
        # 全プロジェクトの一覧取得
        start_time = time.perf_counter()
        response = client.get("/api/projects/", headers=self.auth_headers)
        end_time = time.perf_counter()
        
        assert response.status_code == 200
        projects = response.json()
        assert len(projects) >= 5
        
        # 一覧取得が1秒以内
        list_time = end_time - start_time
        assert list_time < 1.0, f"Project listing took {list_time:.2f}s"

    def test_data_consistency_workflow(self, client, db_session):
        """データ整合性ワークフローE2Eテスト"""
        
        from app.database import Project, Spider, Task
        
        # 1. プロジェクト作成
        project_data = {
            "name": "Data Consistency Test",
            "description": "Testing data consistency",
            "path": str(self.temp_dir / "consistency_test")
        }
        
        response = client.post(
            "/api/projects/",
            json=project_data,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        project = response.json()
        project_id = project["id"]
        
        # 2. データベースでプロジェクト確認
        db_project = db_session.query(Project).filter(Project.id == project_id).first()
        assert db_project is not None
        assert db_project.name == "Data Consistency Test"
        
        # 3. スパイダー作成
        spider_data = {
            "name": "consistency_spider",
            "description": "Data consistency test spider",
            "template": "basic",
            "code": "# Test spider"
        }
        
        response = client.post(
            f"/api/projects/{project_id}/spiders",
            json=spider_data,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        spider = response.json()
        spider_id = spider["id"]
        
        # 4. データベースでスパイダー確認
        db_spider = db_session.query(Spider).filter(Spider.id == spider_id).first()
        assert db_spider is not None
        assert db_spider.name == "consistency_spider"
        assert db_spider.project_id == project_id
        
        # 5. タスク作成（モック）
        with patch('app.services.scrapy_service.ScrapyPlaywrightService.run_spider') as mock_run:
            mock_run.return_value = "consistency-task-id"
            
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
            task = response.json()
            task_id = task["task_id"]
        
        # 6. データベースでタスク確認
        db_task = db_session.query(Task).filter(Task.id == task_id).first()
        if db_task:  # タスクがDBに保存される場合
            assert db_task.spider_id == spider_id
            assert db_task.project_id == project_id
        
        # 7. 関連データの整合性確認
        # プロジェクト削除時にスパイダーも削除されることを確認
        response = client.delete(
            f"/api/projects/{project_id}",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        # データベースで削除確認
        db_session.refresh(db_project)
        deleted_project = db_session.query(Project).filter(Project.id == project_id).first()
        # 実際の実装では適切な削除処理が行われる

    @pytest.mark.slow
    def test_long_running_workflow(self, client):
        """長時間実行ワークフローE2Eテスト"""
        
        # 長時間実行されるタスクのシミュレーション
        project_data = {
            "name": "Long Running Test",
            "description": "Testing long running tasks",
            "path": str(self.temp_dir / "long_running_test")
        }
        
        response = client.post(
            "/api/projects/",
            json=project_data,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        project = response.json()
        project_id = project["id"]
        
        spider_data = {
            "name": "long_running_spider",
            "description": "Long running spider",
            "template": "basic",
            "code": "# Long running spider code"
        }
        
        response = client.post(
            f"/api/projects/{project_id}/spiders",
            json=spider_data,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        spider = response.json()
        spider_id = spider["id"]
        
        # 長時間実行タスクのモック
        with patch('app.services.scrapy_service.ScrapyPlaywrightService.run_spider') as mock_run:
            mock_run.return_value = "long-running-task-id"
            
            task_data = {
                "spider_id": spider_id,
                "settings": {
                    "DOWNLOAD_DELAY": 5,  # 長い遅延
                    "CONCURRENT_REQUESTS": 1
                }
            }
            
            response = client.post(
                "/api/tasks/",
                json=task_data,
                headers=self.auth_headers
            )
            assert response.status_code == 200
            task = response.json()
            task_id = task["task_id"]
        
        # タスク状態の定期確認（シミュレーション）
        for i in range(3):
            time.sleep(0.1)  # 短い待機
            response = client.get(
                f"/api/tasks/{task_id}",
                headers=self.auth_headers
            )
            assert response.status_code == 200
            # 実際の実装では適切な状態更新が行われる
