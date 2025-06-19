#!/bin/bash

# ScrapyUI サーバー停止スクリプト
# 固定ポート設定:
# - バックエンド: 8000番ポート
# - フロントエンド: 4000番ポート
# - Node.js Puppeteer: 3001番ポート

# ポート設定（環境変数で上書き可能）
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-4000}
NODEJS_PORT=${NODEJS_PORT:-3001}
TEST_SERVICE_PORT=${TEST_SERVICE_PORT:-8005}
SPIDER_MANAGER_PORT=${SPIDER_MANAGER_PORT:-8002}
PLAYWRIGHT_SERVICE_PORT=${PLAYWRIGHT_SERVICE_PORT:-8004}

echo "🛑 ScrapyUI サーバーを停止しています..."

# プロセスクリーンアップの実行
echo "🧹 プロセスクリーンアップを実行中..."
if [ -f "./cleanup_processes.sh" ]; then
    ./cleanup_processes.sh
fi
echo "📊 バックエンドポート: ${BACKEND_PORT}"
echo "🌐 フロントエンドポート: ${FRONTEND_PORT}"
echo "🤖 Node.js Puppeteerポート: ${NODEJS_PORT}"
echo "🧪 Test Serviceポート: ${TEST_SERVICE_PORT}"
echo "🕷️ Spider Managerポート: ${SPIDER_MANAGER_PORT}"
echo "🎭 Playwright Serviceポート: ${PLAYWRIGHT_SERVICE_PORT}"

# プロセスIDファイルから停止
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid 2>/dev/null || echo "")
    if [ ! -z "$BACKEND_PID" ]; then
        echo "🔧 バックエンドプロセス (PID: ${BACKEND_PID}) を停止中..."
        kill ${BACKEND_PID} 2>/dev/null || true
    fi
    rm -f .backend.pid
fi

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    echo "🎨 フロントエンドプロセス (PID: ${FRONTEND_PID}) を停止中..."
    kill ${FRONTEND_PID} 2>/dev/null || true
    rm -f .frontend.pid
fi

if [ -f .nodejs.pid ]; then
    NODEJS_PID=$(cat .nodejs.pid)
    echo "🤖 Node.js Puppeteerプロセス (PID: ${NODEJS_PID}) を停止中..."
    kill ${NODEJS_PID} 2>/dev/null || true
    rm -f .nodejs.pid
fi

# Celery関連は廃止済み（マイクロサービス化により不要）
echo "🗑️ 廃止済みCelery関連PIDファイルをクリーンアップ中..."
rm -f .celery.pid .celery_beat.pid .celery_monitor.pid .celery_beat_monitor.pid .flower.pid

# マイクロサービス停止
if [ -f .test_service.pid ]; then
    TEST_SERVICE_PID=$(cat .test_service.pid)
    echo "🧪 テストサービスプロセス (PID: ${TEST_SERVICE_PID}) を停止中..."
    kill ${TEST_SERVICE_PID} 2>/dev/null || true
    rm -f .test_service.pid
fi

if [ -f .spider_manager.pid ]; then
    SPIDER_MANAGER_PID=$(cat .spider_manager.pid)
    echo "🕷️ Spider Managerプロセス (PID: ${SPIDER_MANAGER_PID}) を停止中..."
    kill ${SPIDER_MANAGER_PID} 2>/dev/null || true
    rm -f .spider_manager.pid
fi

if [ -f .playwright_service.pid ]; then
    PLAYWRIGHT_SERVICE_PID=$(cat .playwright_service.pid)
    echo "🎭 Playwright専用サービスプロセス (PID: ${PLAYWRIGHT_SERVICE_PID}) を停止中..."
    kill ${PLAYWRIGHT_SERVICE_PID} 2>/dev/null || true
    rm -f .playwright_service.pid
fi

# マイクロサービスポート停止
echo "🚀 マイクロサービスポートを停止中..."
for port in 8001 8002 8003 8004 8005; do
    if lsof -ti:${port} >/dev/null 2>&1; then
        echo "🔧 ポート ${port} を使用中のプロセスを停止中..."
        lsof -ti:${port} | xargs kill -9 2>/dev/null || true
    fi
done

if [ -f .scheduler.pid ]; then
    SCHEDULER_PID=$(cat .scheduler.pid)
    echo "📅 統一スケジューラープロセス (PID: ${SCHEDULER_PID}) を停止中..."
    kill ${SCHEDULER_PID} 2>/dev/null || true
    rm -f .scheduler.pid
fi



# プロセス名で停止
echo "📋 関連プロセスを停止中..."
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
pkill -f "next.*dev" 2>/dev/null || true
pkill -f "npm.*dev" 2>/dev/null || true
pkill -f "node.*app.js" 2>/dev/null || true
pkill -f "nodemon.*app.js" 2>/dev/null || true
pkill -f "scheduler_service" 2>/dev/null || true
pkill -f "test-service.*main.py" 2>/dev/null || true
pkill -f "spider-manager.*simple_main.py" 2>/dev/null || true
pkill -f "playwright-service.*app.py" 2>/dev/null || true

# ポートを使用しているプロセスを強制停止
echo "🔧 全ポートを使用中のプロセスを停止中..."
lsof -ti:${BACKEND_PORT} | xargs kill -9 2>/dev/null || true
lsof -ti:${FRONTEND_PORT} | xargs kill -9 2>/dev/null || true
lsof -ti:${NODEJS_PORT} | xargs kill -9 2>/dev/null || true
lsof -ti:${TEST_SERVICE_PORT} | xargs kill -9 2>/dev/null || true
lsof -ti:${SPIDER_MANAGER_PORT} | xargs kill -9 2>/dev/null || true
lsof -ti:${PLAYWRIGHT_SERVICE_PORT} | xargs kill -9 2>/dev/null || true

sleep 2

# 停止確認
echo "✅ 停止状況を確認中..."
if lsof -i:${BACKEND_PORT} >/dev/null 2>&1; then
    echo "❌ ポート ${BACKEND_PORT} がまだ使用中です"
else
    echo "✅ ポート ${BACKEND_PORT} が解放されました"
fi

if lsof -i:${FRONTEND_PORT} >/dev/null 2>&1; then
    echo "❌ ポート ${FRONTEND_PORT} がまだ使用中です"
else
    echo "✅ ポート ${FRONTEND_PORT} が解放されました"
fi

if lsof -i:${NODEJS_PORT} >/dev/null 2>&1; then
    echo "❌ ポート ${NODEJS_PORT} がまだ使用中です"
else
    echo "✅ ポート ${NODEJS_PORT} が解放されました"
fi

if lsof -i:${TEST_SERVICE_PORT} >/dev/null 2>&1; then
    echo "❌ ポート ${TEST_SERVICE_PORT} がまだ使用中です"
else
    echo "✅ ポート ${TEST_SERVICE_PORT} が解放されました"
fi

if lsof -i:${SPIDER_MANAGER_PORT} >/dev/null 2>&1; then
    echo "❌ ポート ${SPIDER_MANAGER_PORT} がまだ使用中です"
else
    echo "✅ ポート ${SPIDER_MANAGER_PORT} が解放されました"
fi

if lsof -i:${PLAYWRIGHT_SERVICE_PORT} >/dev/null 2>&1; then
    echo "❌ ポート ${PLAYWRIGHT_SERVICE_PORT} がまだ使用中です"
else
    echo "✅ ポート ${PLAYWRIGHT_SERVICE_PORT} が解放されました"
fi



echo ""
echo "🎉 ScrapyUI サーバーが停止しました！"
echo "🚀 再起動するには ./start_servers.sh を実行してください"
