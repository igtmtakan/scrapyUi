#!/bin/bash

# ScrapyUI サーバー起動スクリプト（安定化版）
# 固定ポート設定:
# - バックエンド: 8000番ポート
# - フロントエンド: 4000番ポート
# - Node.js Puppeteer: 3001番ポート

# ポート設定
BACKEND_PORT=8000
FRONTEND_PORT=4000
NODEJS_PORT=3001

echo "🚀 ScrapyUI サーバーを安定化版で起動しています..."
echo "📊 バックエンドポート: ${BACKEND_PORT}"
echo "🌐 フロントエンドポート: ${FRONTEND_PORT}"
echo "🤖 Node.js Puppeteerポート: ${NODEJS_PORT}"

# 現在のディレクトリを保存
ORIGINAL_DIR=$(pwd)

# プロジェクトルートディレクトリに移動
cd "$(dirname "$0")"

# ログディレクトリを作成
mkdir -p backend/logs
mkdir -p frontend/logs
mkdir -p nodejs-service/logs

# 既存のプロセスを停止
echo "🧹 既存のプロセスをクリーンアップ中..."
./stop_servers.sh > /dev/null 2>&1

# ポートが使用中の場合は強制停止
echo "🔧 ポート ${BACKEND_PORT}, ${FRONTEND_PORT}, ${NODEJS_PORT} をクリアしています..."
lsof -ti:${BACKEND_PORT} | xargs kill -9 2>/dev/null || true
lsof -ti:${FRONTEND_PORT} | xargs kill -9 2>/dev/null || true
lsof -ti:${NODEJS_PORT} | xargs kill -9 2>/dev/null || true

sleep 3

# Redis サーバーの起動確認
echo "🔍 Redis サーバーを確認中..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️ Redis サーバーが動作していません。起動中..."
    redis-server --daemonize yes
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis サーバーが起動しました"
    else
        echo "❌ Redis サーバーの起動に失敗しました"
        exit 1
    fi
else
    echo "✅ Redis サーバーは既に動作中です"
fi

# 依存関係をチェック
echo "📦 依存関係を確認中..."
cd backend
if ! python3 -c "import psutil, requests" > /dev/null 2>&1; then
    echo "📦 必要な依存関係をインストール中..."
    pip install psutil requests
fi

# サーバー管理スクリプトを使用してバックエンドとCeleryを起動
echo "🔧 バックエンドサーバーとCeleryワーカーを起動中..."
python3 server_manager.py start --service backend > logs/server_manager.log 2>&1 &
MANAGER_PID=$!

# 起動確認（最大60秒待機）
echo "⏳ バックエンドサーバーの起動を待機中..."
for i in {1..60}; do
    if curl -s http://localhost:${BACKEND_PORT}/health > /dev/null 2>&1; then
        echo "✅ バックエンドサーバーが起動しました"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "❌ バックエンドサーバーが60秒以内に起動しませんでした"
        exit 1
    fi
    sleep 1
done

# Celeryワーカーを別途起動
echo "⚙️ Celeryワーカーを起動中..."
python3 -m celery -A app.celery_app worker --loglevel=info -Q scrapy,maintenance,monitoring --concurrency=4 --pool=prefork > logs/celery.log 2>&1 &
CELERY_PID=$!

cd ..

sleep 3

# フロントエンドサーバーを起動
echo "🎨 フロントエンドサーバーを起動中 (ポート: ${FRONTEND_PORT})..."
cd frontend
if [ -d "node_modules" ]; then
    npm run dev -- --port ${FRONTEND_PORT} > logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "✅ フロントエンドサーバーが起動しました (PID: $FRONTEND_PID)"
else
    echo "⚠️ フロントエンドの依存関係がインストールされていません。'npm install' を実行してください。"
fi
cd ..

sleep 3

# Node.js Puppeteerサービスを起動
echo "🤖 Node.js Puppeteerサービスを起動中 (ポート: ${NODEJS_PORT})..."
cd nodejs-service
if [ -d "node_modules" ]; then
    npm start > logs/nodejs.log 2>&1 &
    NODEJS_PID=$!
    echo "✅ Node.js Puppeteerサービスが起動しました (PID: $NODEJS_PID)"
else
    echo "⚠️ Node.jsの依存関係がインストールされていません。'npm install' を実行してください。"
fi
cd ..

sleep 5

# 起動確認
echo "✅ サーバー起動状況を確認中..."
echo "📊 バックエンド (http://localhost:${BACKEND_PORT}):"
curl -s "http://localhost:${BACKEND_PORT}/health" | jq . || echo "❌ バックエンドが応答しません"

echo "⚙️ Celeryワーカー:"
ps aux | grep -E "(celery.*worker)" | grep -v grep | head -1 && echo "✅ Celeryワーカーが動作中" || echo "❌ Celeryワーカーが動作していません"

if [ ! -z "$FRONTEND_PID" ]; then
    echo "🌐 フロントエンド (http://localhost:${FRONTEND_PORT}):"
    curl -s -I "http://localhost:${FRONTEND_PORT}" | head -1 || echo "❌ フロントエンドが応答しません"
fi

if [ ! -z "$NODEJS_PID" ]; then
    echo "🤖 Node.js Puppeteer (http://localhost:${NODEJS_PORT}):"
    curl -s "http://localhost:${NODEJS_PORT}/api/health" | jq . || echo "❌ Node.jsサービスが応答しません"
fi

echo ""
echo "🎉 ScrapyUI サーバーが安定化版で起動しました！"
echo "📊 バックエンド: http://localhost:${BACKEND_PORT}"
if [ ! -z "$FRONTEND_PID" ]; then
    echo "🌐 フロントエンド: http://localhost:${FRONTEND_PORT}"
fi
if [ ! -z "$NODEJS_PID" ]; then
    echo "🤖 Node.js Puppeteer: http://localhost:${NODEJS_PORT}"
fi
echo ""
echo "📝 ログファイル:"
echo "   サーバー管理: backend/logs/server_manager.log"
echo "   Celery: backend/logs/celery.log"
if [ ! -z "$FRONTEND_PID" ]; then
    echo "   フロントエンド: frontend/logs/frontend.log"
fi
if [ ! -z "$NODEJS_PID" ]; then
    echo "   Node.js: nodejs-service/logs/nodejs.log"
fi
echo ""
echo "🔍 サーバー状態確認: python backend/server_manager.py status"
echo "🔄 サービス監視開始: python backend/server_manager.py monitor"
echo "🛑 サーバー停止: ./stop_servers.sh"

# プロセスIDを保存
echo $MANAGER_PID > .manager.pid
echo $CELERY_PID > .celery.pid
if [ ! -z "$FRONTEND_PID" ]; then
    echo $FRONTEND_PID > .frontend.pid
fi
if [ ! -z "$NODEJS_PID" ]; then
    echo $NODEJS_PID > .nodejs.pid
fi

# 元のディレクトリに戻る
cd "$ORIGINAL_DIR"

echo ""
echo "✅ 安定化版サーバー起動完了！"
