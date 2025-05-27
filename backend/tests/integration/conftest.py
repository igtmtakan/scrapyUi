"""
統合テスト用設定
"""
import pytest
import tempfile
import shutil
from pathlib import Path
import asyncio
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db, User
from app.auth.jwt_handler import create_tokens


# テスト用データベース設定
TEST_DATABASE_URL = "sqlite:///./test_integration.db"
test_engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def event_loop():
    """イベントループフィクスチャ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """テスト用データベースセッション"""
    # テーブル作成
    Base.metadata.create_all(bind=test_engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # テーブル削除
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """テスト用FastAPIクライアント"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db_session):
    """テスト用非同期クライアント"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as async_test_client:
        yield async_test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def temp_dir():
    """一時ディレクトリフィクスチャ"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def test_user(db_session):
    """テストユーザーフィクスチャ"""
    user = User(
        id="test-user-id",
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """認証ヘッダーフィクスチャ"""
    tokens = create_tokens({
        "id": test_user.id,
        "email": test_user.email
    })
    return {
        "Authorization": f"Bearer {tokens['access_token']}"
    }


@pytest.fixture(scope="function")
def mock_scrapy_service():
    """Scrapyサービスモックフィクスチャ"""
    mock_service = MagicMock()
    mock_service.create_project.return_value = True
    mock_service.create_spider.return_value = True
    mock_service.run_spider.return_value = "mock-task-id"
    mock_service.get_projects.return_value = []
    mock_service.get_spiders.return_value = []
    mock_service.get_tasks.return_value = []
    return mock_service


@pytest.fixture(scope="function")
def mock_nodejs_service():
    """Node.jsサービスモックフィクスチャ"""
    mock_service = MagicMock()
    mock_service.generate_pdf.return_value = {
        "success": True,
        "pdf_url": "/tmp/test.pdf"
    }
    mock_service.capture_screenshot.return_value = {
        "success": True,
        "screenshot_url": "/tmp/test.png"
    }
    mock_service.extract_data.return_value = {
        "success": True,
        "data": [{"test": "data"}]
    }
    return mock_service


@pytest.fixture(scope="function")
def mock_websocket():
    """WebSocketモックフィクスチャ"""
    mock_ws = MagicMock()
    mock_ws.accept = MagicMock()
    mock_ws.send_text = MagicMock()
    mock_ws.receive_text = MagicMock(return_value='{"type": "ping"}')
    mock_ws.close = MagicMock()
    return mock_ws


@pytest.fixture(scope="session")
def integration_test_config():
    """統合テスト設定"""
    return {
        "database_url": TEST_DATABASE_URL,
        "test_timeout": 30,
        "max_workers": 4,
        "temp_dir_prefix": "scrapyui_integration_test_",
        "mock_external_services": True,
        "enable_performance_monitoring": True
    }


# テストマーカー設定
def pytest_configure(config):
    """pytest設定"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "websocket: mark test as websocket test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running test"
    )


def pytest_collection_modifyitems(config, items):
    """テストアイテム修正"""
    # 統合テストにマーカーを自動追加
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # 遅いテストのマーカー
        if "performance" in item.name or "load" in item.name:
            item.add_marker(pytest.mark.slow)


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """テスト環境セットアップ"""
    # 環境変数設定
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("NODEJS_SERVICE_URL", "http://localhost:3001")


@pytest.fixture(scope="function")
def performance_monitor():
    """パフォーマンス監視フィクスチャ"""
    import time
    import psutil
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
            self.metrics = []
        
        def start(self):
            self.start_time = time.perf_counter()
            process = psutil.Process()
            self.start_memory = process.memory_info().rss
        
        def stop(self):
            if self.start_time is None:
                return None
            
            end_time = time.perf_counter()
            process = psutil.Process()
            end_memory = process.memory_info().rss
            
            metric = {
                "execution_time": end_time - self.start_time,
                "memory_used": end_memory - self.start_memory,
                "memory_peak": end_memory
            }
            
            self.metrics.append(metric)
            return metric
        
        def get_summary(self):
            if not self.metrics:
                return None
            
            return {
                "total_tests": len(self.metrics),
                "total_time": sum(m["execution_time"] for m in self.metrics),
                "total_memory": sum(m["memory_used"] for m in self.metrics),
                "avg_time": sum(m["execution_time"] for m in self.metrics) / len(self.metrics),
                "max_memory": max(m["memory_peak"] for m in self.metrics)
            }
    
    return PerformanceMonitor()


# テスト実行前後のフック
@pytest.fixture(autouse=True, scope="session")
def setup_integration_test_suite():
    """統合テストスイートセットアップ"""
    print("\n🚀 Starting ScrapyUI Integration Test Suite")
    print("=" * 60)
    
    yield
    
    print("\n" + "=" * 60)
    print("🎉 ScrapyUI Integration Test Suite Completed")


@pytest.fixture(autouse=True)
def test_isolation():
    """テスト分離"""
    # テスト前のクリーンアップ
    yield
    # テスト後のクリーンアップ
    # 必要に応じてリソースをクリーンアップ


# カスタムアサーション
def assert_response_time(response_time, max_time, operation_name):
    """レスポンス時間アサーション"""
    assert response_time < max_time, (
        f"{operation_name} took {response_time:.2f}s "
        f"(expected < {max_time}s)"
    )


def assert_memory_usage(memory_used, max_memory, operation_name):
    """メモリ使用量アサーション"""
    memory_mb = memory_used / 1024 / 1024
    max_mb = max_memory / 1024 / 1024
    assert memory_mb < max_mb, (
        f"{operation_name} used {memory_mb:.2f}MB "
        f"(expected < {max_mb:.2f}MB)"
    )


# テストユーティリティ
class TestDataFactory:
    """テストデータファクトリー"""
    
    @staticmethod
    def create_project_data(name="Test Project", path="/tmp/test"):
        return {
            "name": name,
            "description": f"Test project: {name}",
            "path": path
        }
    
    @staticmethod
    def create_spider_data(name="test_spider"):
        return {
            "name": name,
            "description": f"Test spider: {name}",
            "template": "basic",
            "start_urls": ["http://httpbin.org/json"],
            "code": f'''
import scrapy

class {name.title()}Spider(scrapy.Spider):
    name = '{name}'
    start_urls = ['http://httpbin.org/json']

    def parse(self, response):
        yield response.json()
'''
        }
    
    @staticmethod
    def create_task_data(spider_id):
        return {
            "spider_id": spider_id,
            "settings": {
                "DOWNLOAD_DELAY": 1,
                "CONCURRENT_REQUESTS": 2
            }
        }
    
    @staticmethod
    def create_schedule_data(spider_id, name="Test Schedule"):
        return {
            "name": name,
            "spider_id": spider_id,
            "cron_expression": "0 */6 * * *",
            "is_active": True,
            "settings": {}
        }


# グローバルテストデータファクトリー
@pytest.fixture
def test_data_factory():
    """テストデータファクトリーフィクスチャ"""
    return TestDataFactory()
