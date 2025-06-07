#!/bin/bash

# ScrapyUI サービス監視・自動復旧システム
# 全サービスの健全性を監視し、問題を検出した場合に自動復旧を実行

# 設定
MONITOR_INTERVAL=30  # 監視間隔（秒）
MAX_RESTART_ATTEMPTS=3  # 最大再起動試行回数
RESTART_COOLDOWN=60  # 再起動間隔（秒）
LOG_FILE="logs/service_monitor.log"

# カラー設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ログディレクトリ作成
mkdir -p logs

# ログ関数
log_with_timestamp() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() { log_with_timestamp "INFO" "$1"; }
log_warn() { log_with_timestamp "WARN" "$1"; }
log_error() { log_with_timestamp "ERROR" "$1"; }
log_success() { log_with_timestamp "SUCCESS" "$1"; }

# 設定読み込み
load_config() {
    if [ -f "backend/.env" ]; then
        export $(grep -v '^#' backend/.env | xargs)
    fi
    
    # デフォルト値設定
    BACKEND_PORT=${BACKEND_PORT:-8000}
    FRONTEND_PORT=${FRONTEND_PORT:-4000}
    NODEJS_PORT=${NODEJS_PORT:-3001}
    FLOWER_PORT=${FLOWER_PORT:-5556}
}

# サービス健全性チェック関数
check_backend_health() {
    curl -s -f "http://localhost:$BACKEND_PORT/health" >/dev/null 2>&1
}

check_frontend_health() {
    curl -s -f "http://localhost:$FRONTEND_PORT" >/dev/null 2>&1
}

check_nodejs_health() {
    curl -s -f "http://localhost:$NODEJS_PORT/api/health" >/dev/null 2>&1
}

check_flower_health() {
    curl -s -f "http://localhost:$FLOWER_PORT/flower/api/workers" >/dev/null 2>&1
}

check_celery_worker() {
    pgrep -f "celery.*worker" >/dev/null 2>&1
}

check_celery_beat() {
    pgrep -f "celery.*beat" >/dev/null 2>&1
}

check_redis() {
    redis-cli ping >/dev/null 2>&1
}

# サービス再起動関数
restart_backend() {
    log_warn "バックエンドサービスを再起動中..."
    pkill -f "uvicorn.*app.main:app"
    sleep 3
    
    cd backend
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload --reload-dir app --reload-dir database &
    cd ..
    
    # 起動確認
    for i in {1..30}; do
        if check_backend_health; then
            log_success "バックエンドサービスが復旧しました"
            return 0
        fi
        sleep 1
    done
    
    log_error "バックエンドサービスの復旧に失敗しました"
    return 1
}

restart_frontend() {
    log_warn "フロントエンドサービスを再起動中..."
    pkill -f "next.*dev"
    sleep 3
    
    cd frontend
    npm run dev -- --port $FRONTEND_PORT &
    cd ..
    
    # 起動確認（フロントエンドは起動に時間がかかるため長めに待機）
    sleep 10
    for i in {1..60}; do
        if check_frontend_health; then
            log_success "フロントエンドサービスが復旧しました"
            return 0
        fi
        sleep 1
    done
    
    log_error "フロントエンドサービスの復旧に失敗しました"
    return 1
}

restart_nodejs() {
    log_warn "Node.jsサービスを再起動中..."
    pkill -f "node.*app.js"
    sleep 3
    
    cd nodejs-service
    npm start &
    cd ..
    
    # 起動確認
    for i in {1..30}; do
        if check_nodejs_health; then
            log_success "Node.jsサービスが復旧しました"
            return 0
        fi
        sleep 1
    done
    
    log_error "Node.jsサービスの復旧に失敗しました"
    return 1
}

restart_flower() {
    log_warn "Flowerサービスを再起動中..."
    pkill -f "celery.*flower"
    sleep 3
    
    cd backend
    FLOWER_UNAUTHENTICATED_API=true python3 -m celery -A app.celery_app flower \
        --port=$FLOWER_PORT \
        --address=127.0.0.1 \
        --url_prefix=/flower \
        --persistent=True \
        --db=flower.db \
        --max_tasks=10000 \
        --enable_events \
        --auto_refresh=True &
    cd ..
    
    # 起動確認
    for i in {1..30}; do
        if check_flower_health; then
            log_success "Flowerサービスが復旧しました"
            return 0
        fi
        sleep 1
    done
    
    log_error "Flowerサービスの復旧に失敗しました"
    return 1
}

restart_celery_worker() {
    log_warn "Celeryワーカーを再起動中..."
    pkill -f "celery.*worker"
    sleep 3
    
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
    cd ..
    
    sleep 5
    if check_celery_worker; then
        log_success "Celeryワーカーが復旧しました"
        return 0
    else
        log_error "Celeryワーカーの復旧に失敗しました"
        return 1
    fi
}

restart_celery_beat() {
    log_warn "Celery Beatを再起動中..."
    pkill -f "celery.*beat"
    sleep 3
    
    cd backend
    python3 -m celery -A app.celery_app beat \
        --loglevel=info \
        --scheduler=app.scheduler.DatabaseScheduler &
    cd ..
    
    sleep 5
    if check_celery_beat; then
        log_success "Celery Beatが復旧しました"
        return 0
    else
        log_error "Celery Beatの復旧に失敗しました"
        return 1
    fi
}

# Redis自動起動
start_redis_if_needed() {
    if ! check_redis; then
        log_warn "Redisが動作していません。起動中..."
        redis-server --daemonize yes
        sleep 2
        
        if check_redis; then
            log_success "Redisが起動しました"
            return 0
        else
            log_error "Redisの起動に失敗しました"
            return 1
        fi
    fi
    return 0
}

# 包括的な健全性チェック
comprehensive_health_check() {
    local issues=0
    
    log_info "包括的な健全性チェックを実行中..."
    
    # Redis チェック
    if ! check_redis; then
        log_error "Redis: 応答なし"
        start_redis_if_needed
        ((issues++))
    else
        log_info "Redis: 正常"
    fi
    
    # バックエンド チェック
    if ! check_backend_health; then
        log_error "Backend: 応答なし (ポート: $BACKEND_PORT)"
        ((issues++))
    else
        log_info "Backend: 正常 (ポート: $BACKEND_PORT)"
    fi
    
    # フロントエンド チェック
    if ! check_frontend_health; then
        log_error "Frontend: 応答なし (ポート: $FRONTEND_PORT)"
        ((issues++))
    else
        log_info "Frontend: 正常 (ポート: $FRONTEND_PORT)"
    fi
    
    # Node.js チェック
    if ! check_nodejs_health; then
        log_error "Node.js: 応答なし (ポート: $NODEJS_PORT)"
        ((issues++))
    else
        log_info "Node.js: 正常 (ポート: $NODEJS_PORT)"
    fi
    
    # Flower チェック
    if ! check_flower_health; then
        log_error "Flower: 応答なし (ポート: $FLOWER_PORT)"
        ((issues++))
    else
        log_info "Flower: 正常 (ポート: $FLOWER_PORT)"
    fi
    
    # Celery Worker チェック
    if ! check_celery_worker; then
        log_error "Celery Worker: プロセスなし"
        ((issues++))
    else
        log_info "Celery Worker: 正常"
    fi
    
    # Celery Beat チェック
    if ! check_celery_beat; then
        log_error "Celery Beat: プロセスなし"
        ((issues++))
    else
        log_info "Celery Beat: 正常"
    fi
    
    if [ $issues -eq 0 ]; then
        log_success "全サービスが正常に動作しています"
    else
        log_warn "$issues 個のサービスに問題があります"
    fi
    
    return $issues
}

# 監視ループ
monitor_loop() {
    log_info "サービス監視を開始します (間隔: ${MONITOR_INTERVAL}秒)"
    
    # 再起動カウンター
    declare -A restart_counts
    declare -A last_restart_time
    
    while true; do
        comprehensive_health_check
        local issues=$?
        
        if [ $issues -gt 0 ]; then
            log_warn "問題が検出されました。自動復旧を試行します..."
            
            # 各サービスの個別復旧
            if ! check_backend_health; then
                restart_backend
            fi
            
            if ! check_celery_worker; then
                restart_celery_worker
            fi
            
            if ! check_celery_beat; then
                restart_celery_beat
            fi
            
            if ! check_flower_health; then
                restart_flower
            fi
            
            if ! check_nodejs_health; then
                restart_nodejs
            fi
            
            if ! check_frontend_health; then
                restart_frontend
            fi
        fi
        
        sleep $MONITOR_INTERVAL
    done
}

# シグナルハンドラー
cleanup() {
    log_info "監視を停止しています..."
    exit 0
}

trap cleanup SIGINT SIGTERM

# メイン処理
main() {
    case "${1:-monitor}" in
        "monitor")
            load_config
            monitor_loop
            ;;
        "check")
            load_config
            comprehensive_health_check
            ;;
        "help")
            echo "ScrapyUI サービス監視・自動復旧システム"
            echo ""
            echo "使用方法:"
            echo "  $0 [コマンド]"
            echo ""
            echo "コマンド:"
            echo "  monitor  - 継続的な監視を開始 (デフォルト)"
            echo "  check    - 一回限りの健全性チェック"
            echo "  help     - このヘルプを表示"
            ;;
        *)
            echo "不明なコマンド: $1"
            echo "ヘルプを表示するには: $0 help"
            exit 1
            ;;
    esac
}

main "$@"
