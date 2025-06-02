from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn
import os
from pathlib import Path
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# ロギングとエラーハンドリングのインポート
from .utils.logging_config import setup_logging, get_logger
from .middleware.error_middleware import (
    ErrorHandlingMiddleware,
    RequestLoggingMiddleware,
    PerformanceLoggingMiddleware
)

from .api import projects, spiders, tasks, results, schedules, notifications, auth, proxies, ai, admin, script_runner, project_files, performance, system, database_config, settings, timezone
# from .api import shell, extensions  # 一時的に無効化
from .api.routes import nodejs_integration
# from .api import settings
from .database import engine, Base
from .websocket import endpoints as websocket_endpoints

# ロギングシステムの初期化
setup_logging(
    level="INFO",
    log_to_file=True,
    log_to_console=True,
    json_format=False
)

logger = get_logger(__name__)

# データベーステーブルの作成
Base.metadata.create_all(bind=engine)

# カスタムCORSミドルウェア（無効化）
# class CustomCORSMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         # プリフライトリクエストの処理
#         if request.method == "OPTIONS":
#             response = Response(status_code=200)
#             response.headers["Access-Control-Allow-Origin"] = "*"
#             response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
#             response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept, Origin, X-API-Key, X-Retry-After-Refresh"
#             response.headers["Access-Control-Max-Age"] = "3600"
#             response.headers["Access-Control-Allow-Credentials"] = "false"
#             return response

#         # 通常のリクエストの処理
#         response = await call_next(request)
#         response.headers["Access-Control-Allow-Origin"] = "*"
#         response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
#         response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept, Origin, X-API-Key, X-Retry-After-Refresh"
#         response.headers["Access-Control-Allow-Credentials"] = "false"
#         return response

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="ScrapyUI API - 企業レベルWebスクレイピングプラットフォーム",
        version="2.0.0",
        description="""
## ScrapyUI - 企業レベルのWebスクレイピング開発プラットフォーム

ScrapyUIは、Scrapyプロジェクトの開発、管理、監視を行うための包括的なWebインターフェースです。

### 🚀 基本機能

#### プロジェクト管理
- **プロジェクト作成**: Scrapyプロジェクトの自動生成
- **ファイル管理**: リアルタイムファイル編集
- **バージョン管理**: Git統合による変更履歴管理

#### スパイダー管理
- **スパイダー作成**: Playwright対応スパイダーの作成
- **実行監視**: リアルタイムタスク監視
- **結果管理**: スクレイピング結果の可視化

### 🔧 高度な機能

#### Git統合
- **リポジトリ管理**: 自動Git初期化
- **コミット管理**: 変更履歴の追跡
- **ブランチ管理**: 機能別開発ブランチ

#### テンプレート管理
- **カスタムテンプレート**: 再利用可能なスパイダーテンプレート
- **変数置換**: 動的テンプレートレンダリング
- **カテゴリ分類**: 用途別テンプレート整理

#### 設定検証
- **自動検証**: Scrapy設定の構文・セマンティックチェック
- **最適化提案**: パフォーマンス改善提案
- **セキュリティチェック**: 脆弱性の自動検出

### 📊 分析機能

#### パフォーマンス監視
- **リアルタイム監視**: CPU、メモリ、ネットワーク監視
- **メトリクス収集**: Scrapy固有メトリクスの追跡
- **アラート機能**: 閾値ベースの自動警告

#### 使用統計
- **利用状況分析**: 機能利用パターンの可視化
- **ユーザー行動**: 詳細なユーザーアクティビティ追跡
- **インサイト生成**: 自動的な傾向分析

#### 予測分析
- **パフォーマンス予測**: 将来の性能問題予測
- **異常検知**: 3σルールによるリアルタイム異常検知
- **リソース予測**: CPU、メモリ使用量の将来予測

### 🤖 AI統合

#### コード生成
- **スパイダー自動生成**: 要件に基づくPlaywright対応スパイダー生成
- **ミドルウェア生成**: 各種ミドルウェアの自動生成
- **設定最適化**: AI による設定パラメータ最適化

#### 品質分析
- **コード品質分析**: 構文、セマンティック、パフォーマンス分析
- **バグ検出**: セキュリティ、パフォーマンス問題の自動検出
- **ベストプラクティス**: Scrapy固有の最適化提案

### 🔒 セキュリティ

#### アクセス制御
- **JWT認証**: セキュアなユーザー認証
- **ロールベース**: 権限に基づくアクセス制御
- **セッション管理**: 安全なセッション管理

#### データ保護
- **ファイルパス検証**: ディレクトリトラバーサル攻撃防止
- **入力検証**: SQL インジェクション、XSS 対策
- **レート制限**: API 乱用防止

### 🛠 技術仕様

#### フロントエンド
- **React 19**: 最新のReactフレームワーク
- **Next.js 15**: サーバーサイドレンダリング
- **Tailwind CSS**: ユーティリティファーストCSS
- **TypeScript**: 型安全な開発

#### バックエンド
- **FastAPI**: 高性能Python Webフレームワーク
- **SQLAlchemy**: Python ORM
- **Scrapy**: Webスクレイピングフレームワーク
- **Playwright**: ブラウザ自動化

#### データベース
- **SQLite**: デフォルトデータベース
- **MySQL/PostgreSQL**: 本番環境対応
- **MongoDB**: NoSQL対応
- **Elasticsearch**: 検索エンジン統合

#### AI・分析
- **OpenAI API**: GPT統合
- **NumPy/SciPy**: 数値計算
- **Pandas**: データ分析
- **Scikit-learn**: 機械学習

### 📈 パフォーマンス

#### スケーラビリティ
- **水平スケーリング**: 複数インスタンス対応
- **負荷分散**: 効率的なリクエスト分散
- **キャッシュ**: Redis/Memcached対応

#### 最適化
- **非同期処理**: asyncio による高速処理
- **データベース最適化**: インデックス最適化
- **メモリ管理**: 効率的なメモリ使用

### 🔧 開発・運用

#### 開発支援
- **ホットリロード**: 開発時の自動リロード
- **デバッグ機能**: 詳細なログとエラー追跡
- **テスト統合**: 自動テスト実行

#### 運用支援
- **ヘルスチェック**: システム状態監視
- **ログ管理**: 構造化ログ出力
- **メトリクス**: Prometheus/Grafana対応

### 📚 API仕様

このAPIは RESTful 設計に従い、以下の原則を採用しています：

- **統一されたレスポンス形式**: 一貫したJSON形式
- **適切なHTTPステータスコード**: 意味のあるステータス返却
- **包括的なエラーハンドリング**: 詳細なエラー情報
- **バージョニング**: API バージョン管理
- **レート制限**: API 使用量制限
- **認証・認可**: セキュアなアクセス制御

### 🚀 今後の展開

- **クラウド統合**: AWS/GCP/Azure対応
- **CI/CD統合**: GitHub Actions/Jenkins統合
- **マルチテナント**: 企業向けマルチテナント対応
- **API拡張**: GraphQL対応
- **モバイルアプリ**: React Native アプリ開発
        """,
        routes=app.routes,
        contact={
            "name": "ScrapyUI Development Team",
            "url": "https://github.com/scrapyui/scrapyui",
            "email": "support@scrapyui.com"
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        }
    )

    # カスタムロゴとテーマ設定
    openapi_schema["info"]["x-logo"] = {
        "url": "https://raw.githubusercontent.com/scrapyui/scrapyui/main/docs/logo.png",
        "altText": "ScrapyUI Logo"
    }

    # タグの詳細情報を追加
    openapi_schema["tags"] = [
        {
            "name": "projects",
            "description": "**プロジェクト管理** - Scrapyプロジェクトの作成、編集、削除、設定管理",
            "externalDocs": {
                "description": "プロジェクト管理ガイド",
                "url": "https://docs.scrapyui.com/projects"
            }
        },
        {
            "name": "spiders",
            "description": "**スパイダー管理** - スパイダーの作成、編集、実行、監視",
            "externalDocs": {
                "description": "スパイダー開発ガイド",
                "url": "https://docs.scrapyui.com/spiders"
            }
        },
        {
            "name": "tasks",
            "description": "**タスク管理** - スクレイピングタスクの実行、監視、結果管理",
            "externalDocs": {
                "description": "タスク実行ガイド",
                "url": "https://docs.scrapyui.com/tasks"
            }
        },
        {
            "name": "project-files",
            "description": "**ファイル管理** - プロジェクトファイルの編集、バージョン管理、バックアップ",
            "externalDocs": {
                "description": "ファイル管理ガイド",
                "url": "https://docs.scrapyui.com/files"
            }
        },
        {
            "name": "extensions",
            "description": "**拡張機能** - Git統合、テンプレート管理、AI統合、分析機能",
            "externalDocs": {
                "description": "拡張機能ガイド",
                "url": "https://docs.scrapyui.com/extensions"
            }
        },
        {
            "name": "authentication",
            "description": "**認証** - ユーザー認証、アクセス制御、セッション管理",
            "externalDocs": {
                "description": "認証ガイド",
                "url": "https://docs.scrapyui.com/auth"
            }
        },
        {
            "name": "ai-analysis",
            "description": "**AI分析** - コード生成、品質分析、最適化提案、バグ検出",
            "externalDocs": {
                "description": "AI機能ガイド",
                "url": "https://docs.scrapyui.com/ai"
            }
        },
        {
            "name": "results",
            "description": "**結果管理** - スクレイピング結果の表示、エクスポート、分析",
            "externalDocs": {
                "description": "結果管理ガイド",
                "url": "https://docs.scrapyui.com/results"
            }
        },
        {
            "name": "schedules",
            "description": "**スケジュール管理** - 定期実行、cron設定、タスクスケジューリング",
            "externalDocs": {
                "description": "スケジュール設定ガイド",
                "url": "https://docs.scrapyui.com/schedules"
            }
        },
        {
            "name": "notifications",
            "description": "**通知管理** - アラート設定、メール通知、Slack統合",
            "externalDocs": {
                "description": "通知設定ガイド",
                "url": "https://docs.scrapyui.com/notifications"
            }
        },
        {
            "name": "proxies",
            "description": "**プロキシ管理** - プロキシ設定、ローテーション、認証",
            "externalDocs": {
                "description": "プロキシ設定ガイド",
                "url": "https://docs.scrapyui.com/proxies"
            }
        },
        {
            "name": "scrapy-shell",
            "description": "**Scrapyシェル** - インタラクティブデバッグ、テスト実行",
            "externalDocs": {
                "description": "Scrapyシェルガイド",
                "url": "https://docs.scrapyui.com/shell"
            }
        },
        {
            "name": "database-config",
            "description": "**データベース設定** - 接続設定、マイグレーション、バックアップ",
            "externalDocs": {
                "description": "データベース設定ガイド",
                "url": "https://docs.scrapyui.com/database"
            }
        },
        {
            "name": "admin",
            "description": "**管理者機能** - ユーザー管理、システム統計、権限管理",
            "externalDocs": {
                "description": "管理者機能ガイド",
                "url": "https://docs.scrapyui.com/admin"
            }
        },
        {
            "name": "script-runner",
            "description": "**スクリプト実行** - エディターからのスクリプト実行とデータ抽出",
            "externalDocs": {
                "description": "スクリプト実行ガイド",
                "url": "https://docs.scrapyui.com/script-runner"
            }
        },
        {
            "name": "nodejs-integration",
            "description": "**Node.js統合** - Puppeteerを使用したブラウザ自動化、PDF生成、スクリーンショット",
            "externalDocs": {
                "description": "Node.js統合ガイド",
                "url": "https://docs.scrapyui.com/nodejs-integration"
            }
        }
    ]

    # セキュリティスキーム定義
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Bearer Token認証"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API Key認証"
        }
    }

    # グローバルセキュリティ設定
    openapi_schema["security"] = [
        {"BearerAuth": []},
        {"ApiKeyAuth": []}
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app = FastAPI(
    title="Scrapy-Playwright Web UI API",
    description="PySpiderライクなScrapy + Playwright Web UI のバックエンドAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.openapi = custom_openapi

# エラーハンドリングとロギングミドルウェアを追加
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(PerformanceLoggingMiddleware, slow_request_threshold=2.0)

# 強化されたCORSミドルウェア設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:4000",
        "http://localhost:4001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:4000",
        "http://127.0.0.1:4001"
    ],
    allow_credentials=True,
    allow_methods=["*"],  # 全てのHTTPメソッドを許可
    allow_headers=["*"],  # 全てのヘッダーを許可
    expose_headers=["*"],  # 全てのヘッダーを公開
    max_age=86400,  # プリフライトキャッシュ時間（24時間）
)

# APIルーターの登録
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(project_files.router, prefix="/api", tags=["project-files"])
app.include_router(spiders.router, prefix="/api/spiders", tags=["spiders"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(results.router, prefix="/api/results", tags=["results"])
app.include_router(schedules.router, prefix="/api/schedules", tags=["schedules"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(proxies.router, prefix="/api/proxies", tags=["proxies"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai-analysis"])
# app.include_router(shell.router, prefix="/api/shell", tags=["scrapy-shell"])  # 一時的に無効化
app.include_router(database_config.router, prefix="/api/database", tags=["database-config"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
# app.include_router(extensions.router, prefix="/api", tags=["extensions"])  # 一時的に無効化
app.include_router(admin.router, tags=["admin"])
app.include_router(script_runner.router, prefix="/api/script", tags=["script-runner"])
app.include_router(nodejs_integration.router, prefix="/api/nodejs", tags=["nodejs-integration"])
app.include_router(performance.router, prefix="/api", tags=["performance"])
app.include_router(system.router, prefix="/api", tags=["system"])
app.include_router(timezone.router, tags=["timezone"])
# app.include_router(settings.router, prefix="/api/settings", tags=["settings"])

# Terminal WebSocketエンドポイント（先に登録して優先度を上げる）
from .api.websocket.terminal import websocket_endpoint as terminal_websocket_endpoint

@app.websocket("/ws/terminal")
async def websocket_terminal(websocket: WebSocket):
    """Terminal WebSocketエンドポイント"""
    await terminal_websocket_endpoint(websocket)

# WebSocketエンドポイント（一般的なパターンは後に登録）
app.include_router(websocket_endpoints.router, prefix="/ws")

# リアルタイム進捗監視WebSocketエンドポイント
from .services.realtime_websocket_manager import realtime_websocket_manager

@app.websocket("/ws/realtime-progress")
async def websocket_realtime_progress(websocket: WebSocket):
    """リアルタイム進捗監視WebSocketエンドポイント"""
    client_ip = websocket.client.host if websocket.client else "unknown"
    logger.info(f"📡 WebSocket connection attempt from {client_ip}")

    try:
        await websocket.accept()
        logger.info(f"✅ WebSocket connection accepted from {client_ip}")
        realtime_websocket_manager.add_connection(websocket)

        # 接続成功メッセージを送信
        await websocket.send_text("Connected: WebSocket connection established")

        while True:
            # クライアントからのメッセージを待機（接続維持）
            try:
                data = await websocket.receive_text()
                logger.info(f"📨 WebSocket message from {client_ip}: {data}")

                # エコーバック（接続確認）
                await websocket.send_text(f"Connected: {data}")

            except WebSocketDisconnect:
                logger.info(f"🔌 WebSocket client {client_ip} disconnected normally")
                break
            except Exception as msg_error:
                logger.error(f"❌ WebSocket message error from {client_ip}: {msg_error}")
                break

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket client {client_ip} disconnected during handshake")
    except Exception as e:
        logger.error(f"❌ WebSocket error from {client_ip}: {e}")
    finally:
        realtime_websocket_manager.remove_connection(websocket)
        logger.info(f"🧹 WebSocket connection cleaned up for {client_ip}")

# グローバル変数でScrapyServiceを保持
scrapy_service_instance = None

# ScrapyServiceの初期化
@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の初期化処理"""
    global scrapy_service_instance

    try:
        logger.info("🚀 Starting ScrapyUI Application...")

        from .services.scrapy_service import ScrapyPlaywrightService
        from .services.scheduler_service import scheduler_service
        from .services.task_sync_service import task_sync_service

        # ScrapyServiceのシングルトンインスタンスを取得
        scrapy_service_instance = ScrapyPlaywrightService()
        logger.info("✅ ScrapyPlaywrightService initialized")

        # タスク監視システムを開始
        scrapy_service_instance.start_monitoring()
        logger.info("🔍 Task monitoring system started")

        # スケジューラーサービスを開始
        scheduler_service.start()
        logger.info("⏰ Schedule service started")

        # タスクアイテム数同期サービスを開始
        task_sync_service.start()
        logger.info("🔧 Task sync service started")

        # リアルタイムWebSocket管理を開始
        realtime_websocket_manager.start()
        logger.info("📡 Realtime WebSocket Manager started")

        logger.info("✅ ScrapyUI Application started successfully")
        print("✅ ScrapyUI Application started successfully")
        print("🔍 Task monitoring system initialized")
        print("⏰ Schedule service initialized")

    except Exception as e:
        error_msg = f"❌ Error during startup: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        import traceback
        traceback.print_exc()

@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時のクリーンアップ処理"""
    global scrapy_service_instance

    try:
        logger.info("🛑 Shutting down ScrapyUI Application...")

        from .services.scheduler_service import scheduler_service

        if scrapy_service_instance:
            # タスク監視システムを停止
            scrapy_service_instance.stop_monitoring_tasks()
            logger.info("🔍 Task monitoring system stopped")

        # スケジューラーサービスを停止
        scheduler_service.stop()
        logger.info("⏰ Schedule service stopped")

        # タスクアイテム数同期サービスを停止
        from .services.task_sync_service import task_sync_service
        task_sync_service.stop()
        logger.info("🔧 Task sync service stopped")

        logger.info("🛑 ScrapyUI Application shutdown completed")
        print("🛑 ScrapyUI Application shutdown completed")
        print("🔍 Task monitoring system stopped")
        print("⏰ Schedule service stopped")

    except Exception as e:
        error_msg = f"❌ Error during shutdown: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        import traceback
        traceback.print_exc()

@app.get("/")
async def root():
    return {"message": "Scrapy Web UI API"}

@app.get("/health")
async def health_check():
    from datetime import datetime, timezone
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/health")
async def api_health_check():
    from datetime import datetime, timezone
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# OPTIONSハンドラーを削除 - CORSMiddlewareに任せる

def start_server():
    """Start the ScrapyUI server using shell script."""
    import subprocess
    import sys
    from pathlib import Path

    # Get project root (3 levels up from backend/app/main.py)
    project_root = Path(__file__).parent.parent.parent
    start_script = project_root / "start_servers.sh"

    if start_script.exists():
        print("🚀 Starting ScrapyUI servers...")
        try:
            subprocess.run([str(start_script)], cwd=project_root, check=True)
        except KeyboardInterrupt:
            print("\n🛑 Server startup interrupted")
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start servers: {e}")
            sys.exit(1)
    else:
        print("❌ start_servers.sh not found. Starting backend only...")
        uvicorn.run(
            "backend.app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_excludes=["scrapy_projects/*"]
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=["scrapy_projects/*"]
    )
