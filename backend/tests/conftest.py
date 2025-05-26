import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
import tempfile
import os
import shutil
from pathlib import Path
import uuid

from app.main import app
from app.database import Base, get_db
from app.auth.jwt_handler import create_tokens
from app.database import Project, Spider, Task
from app.services.performance_monitor import PerformanceMonitor
from app.services.usage_analytics import UsageAnalytics
from app.services.predictive_analytics import PredictiveAnalytics
from app.services.ai_integration import AICodeAnalyzer
from app.services.git_service import GitService
from app.services.template_service import TemplateService

# テスト用データベース設定
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """テスト用データベースセッション"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def event_loop():
    """イベントループのフィクスチャ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """テスト用データベースのセットアップ"""
    # テーブル作成
    Base.metadata.create_all(bind=engine)

    # テスト用ユーザーを作成（重複を避けるため）
    from app.database import User
    db = TestingSessionLocal()
    try:
        # 既存のユーザーをチェック
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if not existing_user:
            test_user = User(
                id="test-user-id",
                email="test@example.com",
                username="testuser",
                full_name="Test User",
                hashed_password="hashed_password",
                is_active=True,
                is_superuser=False
            )
            db.add(test_user)
            db.commit()
    except Exception as e:
        print(f"Warning: Could not create test user: {e}")
    finally:
        db.close()

    yield
    # テーブル削除
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """データベースセッションのフィクスチャ"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client():
    """テストクライアントのフィクスチャ"""
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
async def async_client():
    """非同期テストクライアントのフィクスチャ"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def test_user_data():
    """テストユーザーデータ"""
    return {
        "email": "newuser@example.com",  # 既存ユーザーと異なるメールアドレス
        "username": "newuser",
        "password": "testpassword123",
        "full_name": "New Test User"
    }

@pytest.fixture
def test_user_tokens(test_user_data):
    """テストユーザーのトークン"""
    return create_tokens({
        "id": "test-user-id",
        "email": test_user_data["email"]
    })

@pytest.fixture
def auth_headers(test_user_tokens):
    """認証ヘッダー"""
    return {
        "Authorization": f"Bearer {test_user_tokens['access_token']}"
    }

@pytest.fixture
def test_project_data():
    """テストプロジェクトデータ"""
    return {
        "name": "Test Project",
        "description": "A test project for integration testing",
        "path": "/tmp/test_project"
    }

@pytest.fixture
def test_spider_data():
    """テストスパイダーデータ"""
    return {
        "name": "test_spider",
        "description": "A test spider",
        "code": '''
import scrapy

class TestSpider(scrapy.Spider):
    name = 'test_spider'
    start_urls = ['http://httpbin.org/json']

    def parse(self, response):
        data = response.json()
        yield {
            'url': response.url,
            'data': data
        }
'''
    }

@pytest.fixture
def test_proxy_data():
    """テストプロキシデータ"""
    return {
        "name": "Test Proxy",
        "host": "127.0.0.1",
        "port": 8080,
        "proxy_type": "http"
    }

@pytest.fixture
def mock_scrapy_results():
    """モックScrapy結果データ"""
    return [
        {
            "id": "result-1",
            "task_id": "task-1",
            "url": "http://example.com/page1",
            "data": {
                "title": "Test Page 1",
                "content": "This is test content 1",
                "price": 100
            },
            "created_at": "2024-01-15T10:00:00Z"
        },
        {
            "id": "result-2",
            "task_id": "task-1",
            "url": "http://example.com/page2",
            "data": {
                "title": "Test Page 2",
                "content": "This is test content 2",
                "price": 200
            },
            "created_at": "2024-01-15T10:05:00Z"
        }
    ]

@pytest.fixture
def temp_export_dir():
    """一時エクスポートディレクトリ"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def temp_dir():
    """一時ディレクトリ"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)

@pytest.fixture(autouse=True)
def setup_test_env():
    """テスト環境のセットアップ"""
    # 環境変数の設定
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["TESTING"] = "true"

    yield

    # クリーンアップ
    if "TESTING" in os.environ:
        del os.environ["TESTING"]

@pytest.fixture
def mock_openai_response():
    """モックOpenAI レスポンス"""
    return {
        "analysis_type": "comprehensive",
        "ai_powered": False,
        "summary": {
            "total_results": 2,
            "unique_domains": 1,
            "common_fields": ["title", "content", "price"]
        },
        "insights": [
            "Data quality appears good",
            "Consistent field structure",
            "No obvious anomalies detected"
        ],
        "recommendations": [
            "Consider adding data validation",
            "Monitor for rate limiting",
            "Implement error handling"
        ]
    }

@pytest.fixture
def websocket_test_data():
    """WebSocketテスト用データ"""
    return {
        "task_update": {
            "type": "task_update",
            "task_id": "test-task-1",
            "data": {
                "status": "RUNNING",
                "items_count": 10,
                "requests_count": 15,
                "error_count": 0
            }
        },
        "log_message": {
            "type": "log",
            "task_id": "test-task-1",
            "data": {
                "level": "INFO",
                "message": "Spider started successfully"
            }
        }
    }
