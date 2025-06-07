#!/bin/bash

# ScrapyUI サーバー起動スクリプト
# 固定ポート設定:
# - バックエンド: 8000番ポート
# - フロントエンド: 4000番ポート
# - Node.js Puppeteer: 3001番ポート

# ポート設定（環境変数で上書き可能）
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-4000}
NODEJS_PORT=${NODEJS_PORT:-3001}
FLOWER_PORT=${FLOWER_PORT:-5556}

# ポート競合回避機能
check_port_available() {
    local port=$1
    if lsof -i:$port >/dev/null 2>&1; then
        return 1  # ポートが使用中
    else
        return 0  # ポートが利用可能
    fi
}

# 代替ポートを見つける関数
find_alternative_port() {
    local base_port=$1
    local max_attempts=10

    for ((i=0; i<max_attempts; i++)); do
        local test_port=$((base_port + i))
        if check_port_available $test_port; then
            echo $test_port
            return 0
        fi
    done

    echo $base_port  # 見つからない場合は元のポートを返す
    return 1
}

# プロセスクリーンアップの実行
echo "🧹 プロセスクリーンアップを実行中..."
if [ -f "./cleanup_processes.sh" ]; then
    ./cleanup_processes.sh
else
    echo "⚠️ cleanup_processes.sh が見つかりません。手動クリーンアップを実行します..."
    # 基本的なクリーンアップ
    pkill -f "celery.*worker" 2>/dev/null || true
    pkill -f "celery.*beat" 2>/dev/null || true
    pkill -f "celery.*flower" 2>/dev/null || true
    pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
    pkill -f "next.*dev" 2>/dev/null || true
    pkill -f "node.*app.js" 2>/dev/null || true

    # ゾンビプロセスの親プロセスにSIGCHLDを送信
    ps aux | awk '$8 ~ /^Z/ { print $2 }' | while read zombie_pid; do
        if [ -n "$zombie_pid" ]; then
            parent_pid=$(ps -o ppid= -p "$zombie_pid" 2>/dev/null | tr -d ' ' || true)
            if [ -n "$parent_pid" ] && [ "$parent_pid" != "1" ]; then
                kill -CHLD "$parent_pid" 2>/dev/null || true
            fi
        fi
    done
fi

# ポート競合チェックと自動調整
echo "🔍 ポート競合をチェック中..."
if ! check_port_available $BACKEND_PORT; then
    NEW_BACKEND_PORT=$(find_alternative_port $BACKEND_PORT)
    echo "⚠️ ポート $BACKEND_PORT が使用中です。代替ポート $NEW_BACKEND_PORT を使用します。"
    BACKEND_PORT=$NEW_BACKEND_PORT
fi

if ! check_port_available $FRONTEND_PORT; then
    NEW_FRONTEND_PORT=$(find_alternative_port $FRONTEND_PORT)
    echo "⚠️ ポート $FRONTEND_PORT が使用中です。代替ポート $NEW_FRONTEND_PORT を使用します。"
    FRONTEND_PORT=$NEW_FRONTEND_PORT
fi

if ! check_port_available $NODEJS_PORT; then
    NEW_NODEJS_PORT=$(find_alternative_port $NODEJS_PORT)
    echo "⚠️ ポート $NODEJS_PORT が使用中です。代替ポート $NEW_NODEJS_PORT を使用します。"
    NODEJS_PORT=$NEW_NODEJS_PORT
fi

if ! check_port_available $FLOWER_PORT; then
    NEW_FLOWER_PORT=$(find_alternative_port $FLOWER_PORT)
    echo "⚠️ ポート $FLOWER_PORT が使用中です。代替ポート $NEW_FLOWER_PORT を使用します。"
    FLOWER_PORT=$NEW_FLOWER_PORT
fi

# Flower設定
FLOWER_MODE=${FLOWER_MODE:-"all"}  # all, embedded, api, standalone
AUTO_START_FLOWER=${AUTO_START_FLOWER:-"true"}

# 設定管理システムの統合
if [ -f "./config_manager.sh" ]; then
    echo "🔧 設定を初期化中..."
    ./config_manager.sh init

    # 設定検証
    if ! ./config_manager.sh validate; then
        echo "⚠️ 設定に問題があります。続行しますか? (y/N)"
        read -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ 起動をキャンセルしました"
            exit 1
        fi
    fi
fi

# ポート管理システムの統合
if [ -f "./port_manager.sh" ]; then
    echo "🔍 ポート競合をチェック中..."
    if ! ./port_manager.sh check >/dev/null 2>&1; then
        echo "⚠️ ポート競合が検出されました。自動解決を実行しますか? (y/N)"
        read -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ./port_manager.sh resolve
            # 解決されたポート設定を読み込み
            if [ -f ".env.ports" ]; then
                source .env.ports
            fi
        fi
    fi
fi

echo "🚀 ScrapyUI サーバーを起動しています..."
echo "📊 バックエンドポート: ${BACKEND_PORT}"
echo "🌐 フロントエンドポート: ${FRONTEND_PORT}"
echo "🤖 Node.js Puppeteerポート: ${NODEJS_PORT}"
echo "🌸 Flowerポート: ${FLOWER_PORT}"
echo "🔧 Flowerモード: ${FLOWER_MODE}"

# 既存のプロセスを停止
echo "📋 既存のプロセスを確認中..."
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
pkill -f "next.*dev" 2>/dev/null || true
pkill -f "npm.*dev" 2>/dev/null || true
pkill -f "node.*app.js" 2>/dev/null || true
pkill -f "nodemon.*app.js" 2>/dev/null || true
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "celery.*beat" 2>/dev/null || true
pkill -f "celery.*flower" 2>/dev/null || true
pkill -f "start_celery_worker.py" 2>/dev/null || true
pkill -f "celery_monitor.py" 2>/dev/null || true

# ポートが使用中の場合は強制停止
echo "🔧 ポート ${BACKEND_PORT}, ${FRONTEND_PORT}, ${NODEJS_PORT}, ${FLOWER_PORT} をクリアしています..."
lsof -ti:${BACKEND_PORT} | xargs kill -9 2>/dev/null || true
lsof -ti:${FRONTEND_PORT} | xargs kill -9 2>/dev/null || true
lsof -ti:${NODEJS_PORT} | xargs kill -9 2>/dev/null || true
lsof -ti:${FLOWER_PORT} | xargs kill -9 2>/dev/null || true

sleep 3

# バックエンドサーバーを起動
echo "🔧 バックエンドサーバーを起動中 (ポート: ${BACKEND_PORT})..."
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT} --reload --reload-dir app --reload-dir database &
BACKEND_PID=$!
cd ..

sleep 3

# Celeryワーカーを起動（安定性向上設定）
echo "⚙️ Celeryワーカーを起動中（安定性向上設定）..."
cd backend
python3 -m celery -A app.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=scrapy,maintenance,monitoring \
    --pool=prefork \
    --optimization=fair \
    --max-tasks-per-child=200 \
    --max-memory-per-child=500000 \
    --time-limit=3600 \
    --soft-time-limit=3300 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat \
    --prefetch-multiplier=1 &
CELERY_PID=$!
cd ..

sleep 3

# Celery Beatスケジューラを起動（安定性向上設定）
echo "📅 Celery Beatスケジューラを起動中（安定性向上設定）..."
cd backend
python3 -m celery -A app.celery_app beat \
    --scheduler app.scheduler:DatabaseScheduler \
    --loglevel=info \
    --max-interval=60 \
    --schedule=celerybeat-schedule.db &
CELERY_BEAT_PID=$!
cd ..

sleep 3

# Flower監視サービスを起動
if [ "$AUTO_START_FLOWER" = "true" ]; then
    echo "🌸 Flower監視サービスを起動中..."

    # Flower起動関数
    start_flower_service() {
        local mode=$1
        case $mode in
            "standalone"|"all")
                echo "🌸 スタンドアロンFlowerを起動中 (ポート: ${FLOWER_PORT})..."
                cd backend
                FLOWER_UNAUTHENTICATED_API=true python3 -m celery -A app.celery_app flower \
                    --port=${FLOWER_PORT} \
                    --address=127.0.0.1 \
                    --url_prefix=/flower \
                    --persistent=True \
                    --db=flower.db \
                    --max_tasks=10000 \
                    --enable_events \
                    --auto_refresh=True \
                    --loglevel=info &
                FLOWER_PID=$!
                cd ..
                echo "✅ スタンドアロンFlower起動完了 (PID: $FLOWER_PID)"
                ;;
            "embedded")
                echo "🌸 埋め込みFlowerは自動起動されます（バックエンド内）"
                ;;
            "api")
                echo "🌸 外部FlowerAPIを使用します"
                ;;
        esac
    }

    # Flowerモードに応じて起動
    start_flower_service "$FLOWER_MODE"

    sleep 3
else
    echo "🌸 Flower自動起動が無効です (AUTO_START_FLOWER=false)"
fi

# Node.js Puppeteerサービスを起動
echo "🤖 Node.js Puppeteerサービスを起動中 (ポート: ${NODEJS_PORT})..."
cd nodejs-service
npm start &
NODEJS_PID=$!
cd ..

sleep 5

# フロントエンドサーバーを起動（最後）
echo "🎨 フロントエンドサーバーを起動中 (ポート: ${FRONTEND_PORT})..."
cd frontend
npm run dev -- --port ${FRONTEND_PORT} &
FRONTEND_PID=$!
cd ..

sleep 5

# Celery監視・自動復旧を起動
echo "🔍 Celery監視・自動復旧を起動中..."
cd backend
python3 celery_monitor.py &
CELERY_MONITOR_PID=$!
cd ..

sleep 3

# 起動確認
echo "✅ サーバー起動状況を確認中..."
echo "📊 バックエンド (http://localhost:${BACKEND_PORT}):"
curl -s "http://localhost:${BACKEND_PORT}/health" | jq . || echo "❌ バックエンドが応答しません"

echo "⚙️ Celeryワーカー:"
ps aux | grep -E "(celery.*worker|start_celery_worker)" | grep -v grep | head -1 && echo "✅ Celeryワーカーが動作中" || echo "❌ Celeryワーカーが動作していません"

echo "📅 Celery Beatスケジューラ:"
ps aux | grep -E "celery.*beat" | grep -v grep | head -1 && echo "✅ Celery Beatが動作中" || echo "❌ Celery Beatが動作していません"

echo "🔍 Celery監視システム:"
ps aux | grep -E "celery_monitor.py" | grep -v grep | head -1 && echo "✅ Celery監視が動作中" || echo "❌ Celery監視が動作していません"

echo "🌸 Flower監視サービス:"
if [ "$AUTO_START_FLOWER" = "true" ]; then
    case $FLOWER_MODE in
        "standalone"|"all")
            ps aux | grep -E "celery.*flower" | grep -v grep | head -1 && echo "✅ スタンドアロンFlowerが動作中" || echo "❌ スタンドアロンFlowerが動作していません"
            curl -s "http://localhost:${FLOWER_PORT}/flower/api/workers" >/dev/null 2>&1 && echo "✅ Flower APIが応答中" || echo "❌ Flower APIが応答しません"
            ;;
        "embedded")
            curl -s "http://localhost:${BACKEND_PORT}/api/flower/health" | jq . 2>/dev/null && echo "✅ 埋め込みFlowerが動作中" || echo "❌ 埋め込みFlowerが動作していません"
            ;;
        "api")
            curl -s "http://localhost:${BACKEND_PORT}/api/flower/health" | jq . 2>/dev/null && echo "✅ Flower APIサービスが動作中" || echo "❌ Flower APIサービスが動作していません"
            ;;
    esac
else
    echo "⚪ Flower自動起動が無効です"
fi

echo "🤖 Node.js Puppeteer (http://localhost:${NODEJS_PORT}):"
curl -s "http://localhost:${NODEJS_PORT}/api/health" | jq . || echo "❌ Node.jsサービスが応答しません"

echo "🌐 フロントエンド (http://localhost:${FRONTEND_PORT}):"
curl -s -I "http://localhost:${FRONTEND_PORT}" | head -1 || echo "❌ フロントエンドが応答しません"

echo "🔄 プロキシ経由 (http://localhost:${FRONTEND_PORT}/api/health):"
curl -s "http://localhost:${FRONTEND_PORT}/api/health" | jq . || echo "❌ プロキシが動作していません"

echo ""
echo "🎉 ScrapyUI サーバーが起動しました！"
echo "📊 バックエンド: http://localhost:${BACKEND_PORT}"
echo "🌐 フロントエンド: http://localhost:${FRONTEND_PORT}"
echo "🤖 Node.js Puppeteer: http://localhost:${NODEJS_PORT}"

# Flower URL表示
if [ "$AUTO_START_FLOWER" = "true" ]; then
    case $FLOWER_MODE in
        "standalone"|"all")
            echo "🌸 Flower監視: http://localhost:${FLOWER_PORT}/flower"
            ;;
        "embedded"|"api")
            echo "🌸 Flower統合: http://localhost:${FRONTEND_PORT}/flower"
            ;;
    esac
    echo "🌸 Flower API: http://localhost:${BACKEND_PORT}/api/flower/stats"
fi

echo "📋 プロジェクト: http://localhost:${FRONTEND_PORT}/projects/9b9dd8cc-65c1-48c1-b819-36ff5db2f36f/spiders"
echo ""
echo "🛑 サーバーを停止するには Ctrl+C を押してください"

# プロセスIDを保存
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid
echo $NODEJS_PID > .nodejs.pid
echo $CELERY_PID > .celery.pid
echo $CELERY_BEAT_PID > .celery_beat.pid
echo $CELERY_MONITOR_PID > .celery_monitor.pid

# FlowerプロセスIDを保存（存在する場合）
if [ ! -z "$FLOWER_PID" ]; then
    echo $FLOWER_PID > .flower.pid
fi

# 終了シグナルをキャッチしてプロセスを停止
cleanup_processes() {
    echo "🛑 サーバーを停止中..."

    # 全プロセスを停止
    kill $BACKEND_PID $FRONTEND_PID $NODEJS_PID $CELERY_PID $CELERY_BEAT_PID $CELERY_MONITOR_PID 2>/dev/null

    # Flowerプロセスも停止
    if [ ! -z "$FLOWER_PID" ]; then
        kill $FLOWER_PID 2>/dev/null
    fi

    # Flower関連プロセスを強制停止
    pkill -f "celery.*flower" 2>/dev/null || true

    # PIDファイルを削除
    rm -f .backend.pid .frontend.pid .nodejs.pid .celery.pid .celery_beat.pid .celery_monitor.pid .flower.pid

    echo "✅ 全サーバーが停止しました"
    exit
}

trap cleanup_processes INT TERM

# プロセスが終了するまで待機
wait
