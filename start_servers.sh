#!/bin/bash

# ScrapyUI サーバー起動スクリプト（根本的書き直し版）
# シンプルで確実な起動を保証

set -e  # エラー時に停止

# 固定ポート設定
BACKEND_PORT=8000
FRONTEND_PORT=4000
NODEJS_PORT=3001

# 作業ディレクトリの確認
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 ScrapyUI サーバーを起動しています..."
echo "📊 バックエンドポート: ${BACKEND_PORT}"
echo "🌐 フロントエンドポート: ${FRONTEND_PORT}"
echo "🤖 Node.js Puppeteerポート: ${NODEJS_PORT}"

# 既存プロセスの完全停止
echo "🧹 既存プロセスを停止中..."
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
pkill -f "next.*dev" 2>/dev/null || true
pkill -f "npm.*dev" 2>/dev/null || true
pkill -f "node.*app.js" 2>/dev/null || true
pkill -f "scheduler_service" 2>/dev/null || true

# ポートの強制解放
echo "🔧 ポートをクリア中..."
lsof -ti:${BACKEND_PORT} | xargs kill -9 2>/dev/null || true
lsof -ti:${FRONTEND_PORT} | xargs kill -9 2>/dev/null || true
lsof -ti:${NODEJS_PORT} | xargs kill -9 2>/dev/null || true

sleep 2

# バックエンドサーバーを起動（フォアグラウンドで確認）
echo "🔧 バックエンドサーバーを起動中..."
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${BACKEND_PORT} --reload &
BACKEND_PID=$!

# バックエンドの起動確認
echo "⏳ バックエンドの起動を待機中..."
sleep 5

# バックエンドの起動確認
for i in {1..10}; do
    if curl -s http://localhost:${BACKEND_PORT}/health >/dev/null 2>&1; then
        echo "✅ バックエンドが正常に起動しました"
        break
    fi
    echo "⏳ バックエンドの起動を待機中... ($i/10)"
    sleep 2
done

# 統合スケジューラーを起動（根本対応版）
echo "🕐 統合スケジューラーを起動中..."
cd backend

# 既存のスケジューラープロセスをクリーンアップ
pkill -f "start_unified_scheduler.py" 2>/dev/null || true
sleep 2

# 堅牢性を強化したスケジューラーを起動
nohup python3 start_unified_scheduler.py > unified_scheduler.log 2>&1 &
SCHEDULER_PID=$!
echo "統合スケジューラー PID: $SCHEDULER_PID"

# スケジューラーの起動確認
sleep 3
if ps -p $SCHEDULER_PID > /dev/null; then
    echo "✅ 統合スケジューラーが正常に起動しました"
else
    echo "❌ 統合スケジューラーの起動に失敗しました"
    echo "ログを確認してください: backend/unified_scheduler.log"
fi

cd ..

# Node.js Puppeteerサービスを起動
echo "🤖 Node.js Puppeteerサービスを起動中..."
cd nodejs-service
npm start &
NODEJS_PID=$!
cd ..

# Node.jsの起動確認
echo "⏳ Node.jsサービスの起動を待機中..."
sleep 5

for i in {1..10}; do
    if curl -s http://localhost:${NODEJS_PORT}/api/health >/dev/null 2>&1; then
        echo "✅ Node.jsサービスが正常に起動しました"
        break
    fi
    echo "⏳ Node.jsサービスの起動を待機中... ($i/10)"
    sleep 2
done

# フロントエンドサーバーを起動
echo "🎨 フロントエンドサーバーを起動中..."
cd frontend
npm run dev -- --port ${FRONTEND_PORT} &
FRONTEND_PID=$!
cd ..

# フロントエンドの起動確認
echo "⏳ フロントエンドの起動を待機中..."
sleep 8

# 最終起動確認
echo "✅ 全サーバーの起動状況を確認中..."

echo "📊 バックエンド (http://localhost:${BACKEND_PORT}):"
if curl -s http://localhost:${BACKEND_PORT}/health >/dev/null 2>&1; then
    echo "✅ バックエンドが正常に動作中"
else
    echo "❌ バックエンドが応答しません"
fi

echo "🤖 Node.js Puppeteer (http://localhost:${NODEJS_PORT}):"
if curl -s http://localhost:${NODEJS_PORT}/api/health >/dev/null 2>&1; then
    echo "✅ Node.jsサービスが正常に動作中"
else
    echo "❌ Node.jsサービスが応答しません"
fi

echo "🌐 フロントエンド (http://localhost:${FRONTEND_PORT}):"
if curl -s -I http://localhost:${FRONTEND_PORT} >/dev/null 2>&1; then
    echo "✅ フロントエンドが正常に動作中"
else
    echo "❌ フロントエンドが応答しません"
fi

echo ""
echo "🎉 ScrapyUI サーバーが起動しました！"
echo "📊 バックエンド: http://localhost:${BACKEND_PORT}"
echo "🌐 フロントエンド: http://localhost:${FRONTEND_PORT}"
echo "🤖 Node.js Puppeteer: http://localhost:${NODEJS_PORT}"
echo ""
echo "🛑 サーバーを停止するには Ctrl+C を押してください"

# プロセスIDを保存
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid
echo $NODEJS_PID > .nodejs.pid
echo $SCHEDULER_PID > .scheduler.pid

# 終了シグナルをキャッチしてプロセスを停止
cleanup_processes() {
    echo ""
    echo "🛑 サーバーを停止中..."

    # 全プロセスを停止
    kill $BACKEND_PID $FRONTEND_PID $NODEJS_PID $SCHEDULER_PID 2>/dev/null || true

    # PIDファイルを削除
    rm -f .backend.pid .frontend.pid .nodejs.pid .scheduler.pid

    echo "✅ 全サーバーが停止しました"
    exit 0
}

trap cleanup_processes INT TERM

# プロセスが終了するまで待機
wait
