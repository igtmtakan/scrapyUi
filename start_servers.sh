#!/bin/bash

# ScrapyUI サーバー起動スクリプト
# 固定ポート設定:
# - バックエンド: 8000番ポート
# - フロントエンド: 4000番ポート
# - Node.js Puppeteer: 3001番ポート

# ポート設定
BACKEND_PORT=8000
FRONTEND_PORT=4000
NODEJS_PORT=3001

echo "🚀 ScrapyUI サーバーを起動しています..."
echo "📊 バックエンドポート: ${BACKEND_PORT}"
echo "🌐 フロントエンドポート: ${FRONTEND_PORT}"
echo "🤖 Node.js Puppeteerポート: ${NODEJS_PORT}"

# 既存のプロセスを停止
echo "📋 既存のプロセスを確認中..."
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
pkill -f "next.*dev" 2>/dev/null || true
pkill -f "npm.*dev" 2>/dev/null || true
pkill -f "node.*app.js" 2>/dev/null || true
pkill -f "nodemon.*app.js" 2>/dev/null || true

# ポートが使用中の場合は強制停止
echo "🔧 ポート ${BACKEND_PORT}, ${FRONTEND_PORT}, ${NODEJS_PORT} をクリアしています..."
lsof -ti:${BACKEND_PORT} | xargs kill -9 2>/dev/null || true
lsof -ti:${FRONTEND_PORT} | xargs kill -9 2>/dev/null || true
lsof -ti:${NODEJS_PORT} | xargs kill -9 2>/dev/null || true

sleep 3

# バックエンドサーバーを起動
echo "🔧 バックエンドサーバーを起動中 (ポート: ${BACKEND_PORT})..."
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT} --reload &
BACKEND_PID=$!
cd ..

sleep 3

# フロントエンドサーバーを起動
echo "🎨 フロントエンドサーバーを起動中 (ポート: ${FRONTEND_PORT})..."
cd frontend
npm run dev -- --port ${FRONTEND_PORT} &
FRONTEND_PID=$!
cd ..

sleep 3

# Node.js Puppeteerサービスを起動
echo "🤖 Node.js Puppeteerサービスを起動中 (ポート: ${NODEJS_PORT})..."
cd nodejs-service
npm start &
NODEJS_PID=$!
cd ..

sleep 5

# 起動確認
echo "✅ サーバー起動状況を確認中..."
echo "📊 バックエンド (http://localhost:${BACKEND_PORT}):"
curl -s "http://localhost:${BACKEND_PORT}/health" | jq . || echo "❌ バックエンドが応答しません"

echo "🌐 フロントエンド (http://localhost:${FRONTEND_PORT}):"
curl -s -I "http://localhost:${FRONTEND_PORT}" | head -1 || echo "❌ フロントエンドが応答しません"

echo "🤖 Node.js Puppeteer (http://localhost:${NODEJS_PORT}):"
curl -s "http://localhost:${NODEJS_PORT}/api/health" | jq . || echo "❌ Node.jsサービスが応答しません"

echo "🔄 プロキシ経由 (http://localhost:${FRONTEND_PORT}/api/health):"
curl -s "http://localhost:${FRONTEND_PORT}/api/health" | jq . || echo "❌ プロキシが動作していません"

echo ""
echo "🎉 ScrapyUI サーバーが起動しました！"
echo "📊 バックエンド: http://localhost:${BACKEND_PORT}"
echo "🌐 フロントエンド: http://localhost:${FRONTEND_PORT}"
echo "🤖 Node.js Puppeteer: http://localhost:${NODEJS_PORT}"
echo "📋 プロジェクト: http://localhost:${FRONTEND_PORT}/projects/9b9dd8cc-65c1-48c1-b819-36ff5db2f36f/spiders"
echo ""
echo "🛑 サーバーを停止するには Ctrl+C を押してください"

# プロセスIDを保存
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid
echo $NODEJS_PID > .nodejs.pid

# 終了シグナルをキャッチしてプロセスを停止
trap 'echo "🛑 サーバーを停止中..."; kill $BACKEND_PID $FRONTEND_PID $NODEJS_PID 2>/dev/null; rm -f .backend.pid .frontend.pid .nodejs.pid; exit' INT TERM

# プロセスが終了するまで待機
wait
