#!/bin/bash

# ScrapyUI サーバー停止スクリプト
# 固定ポート設定:
# - バックエンド: 8000番ポート
# - フロントエンド: 4000番ポート
# - Node.js Puppeteer: 3001番ポート

# ポート設定
BACKEND_PORT=8000
FRONTEND_PORT=4000
NODEJS_PORT=3001

echo "🛑 ScrapyUI サーバーを停止しています..."
echo "📊 バックエンドポート: ${BACKEND_PORT}"
echo "🌐 フロントエンドポート: ${FRONTEND_PORT}"
echo "🤖 Node.js Puppeteerポート: ${NODEJS_PORT}"

# プロセスIDファイルから停止
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    echo "🔧 バックエンドプロセス (PID: ${BACKEND_PID}) を停止中..."
    kill ${BACKEND_PID} 2>/dev/null || true
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

# プロセス名で停止
echo "📋 関連プロセスを停止中..."
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
pkill -f "next.*dev" 2>/dev/null || true
pkill -f "npm.*dev" 2>/dev/null || true
pkill -f "node.*app.js" 2>/dev/null || true
pkill -f "nodemon.*app.js" 2>/dev/null || true

# ポートを使用しているプロセスを強制停止
echo "🔧 ポート ${BACKEND_PORT}, ${FRONTEND_PORT}, ${NODEJS_PORT} を使用中のプロセスを停止中..."
lsof -ti:${BACKEND_PORT} | xargs kill -9 2>/dev/null || true
lsof -ti:${FRONTEND_PORT} | xargs kill -9 2>/dev/null || true
lsof -ti:${NODEJS_PORT} | xargs kill -9 2>/dev/null || true

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

echo ""
echo "🎉 ScrapyUI サーバーが停止しました！"
echo "🚀 再起動するには ./start_servers.sh を実行してください"
