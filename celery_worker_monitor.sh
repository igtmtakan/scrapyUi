#!/bin/bash

# Celeryワーカー監視・自動復旧スクリプト
# 5秒ごとにCeleryワーカーの状態をチェックし、停止している場合は自動復旧

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
PID_FILE="$BACKEND_DIR/celery_worker.pid"
LOG_FILE="$BACKEND_DIR/celery_worker_monitor.log"
WORKER_LOG_FILE="$BACKEND_DIR/celery_worker.log"

# ログ関数
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Celeryワーカーの状態チェック
check_worker_status() {
    # PIDファイルが存在するかチェック
    if [ ! -f "$PID_FILE" ]; then
        return 1
    fi
    
    # PIDファイルからPIDを読み取り
    local pid=$(cat "$PID_FILE" 2>/dev/null)
    if [ -z "$pid" ]; then
        return 1
    fi
    
    # プロセスが実際に動作しているかチェック
    if ps -p "$pid" > /dev/null 2>&1; then
        # Celeryワーカーのプロセスかどうかを確認
        if ps -p "$pid" -o cmd= | grep -q "celery.*worker"; then
            return 0
        else
            return 1
        fi
    else
        return 1
    fi
}

# Celeryワーカーの起動
start_worker() {
    log_message "🚀 Celeryワーカーを起動中..."
    
    cd "$BACKEND_DIR"
    
    # 環境変数設定
    export CELERY_WORKER_HIJACK_ROOT_LOGGER=False
    export CELERY_WORKER_LOG_COLOR=False
    export CELERY_WORKER_REDIRECT_STDOUTS=True
    export CELERY_WORKER_REDIRECT_STDOUTS_LEVEL=INFO
    export CELERY_WORKER_PROC_ALIVE_TIMEOUT=10.0
    export CELERY_WORKER_CANCEL_LONG_RUNNING_TASKS_ON_CONNECTION_LOSS=True
    export CELERY_WORKER_ENABLE_REMOTE_CONTROL=True
    export CELERY_WORKER_POOL=prefork
    export CELERY_WORKER_LOST_WAIT=10.0
    export CELERY_WORKER_SHUTDOWN_TIMEOUT=30
    export CELERY_WORKER_TIMER_PRECISION=1.0
    
    # Celeryワーカー起動
    python3 -m celery -A app.celery_app worker \
        --loglevel=info \
        --concurrency=1 \
        --queues=scrapy,maintenance,monitoring \
        --pool=prefork \
        --optimization=fair \
        --max-tasks-per-child=50 \
        --max-memory-per-child=300000 \
        --time-limit=3600 \
        --soft-time-limit=3300 \
        --without-gossip \
        --without-mingle \
        --without-heartbeat \
        --prefetch-multiplier=1 \
        --autoscale=1,1 \
        --statedb=celery_worker_state.db \
        --pidfile=celery_worker.pid \
        --logfile=celery_worker.log \
        --detach
    
    local start_result=$?
    cd "$SCRIPT_DIR"
    
    if [ $start_result -eq 0 ]; then
        sleep 3
        if check_worker_status; then
            local pid=$(cat "$PID_FILE" 2>/dev/null)
            log_message "✅ Celeryワーカーが正常に起動しました (PID: $pid)"
            return 0
        else
            log_message "❌ Celeryワーカーの起動に失敗しました（プロセス確認失敗）"
            return 1
        fi
    else
        log_message "❌ Celeryワーカーの起動コマンドが失敗しました (exit code: $start_result)"
        return 1
    fi
}

# 古いPIDファイルのクリーンアップ
cleanup_pid_file() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$pid" ] && ! ps -p "$pid" > /dev/null 2>&1; then
            log_message "🧹 古いPIDファイルを削除: $PID_FILE (PID: $pid)"
            rm -f "$PID_FILE"
        fi
    fi
}

# メイン監視ループ
main_monitor_loop() {
    log_message "🔍 Celeryワーカー監視を開始します"
    
    local consecutive_failures=0
    local max_consecutive_failures=3
    
    while true; do
        if check_worker_status; then
            if [ $consecutive_failures -gt 0 ]; then
                log_message "✅ Celeryワーカーが復旧しました"
                consecutive_failures=0
            fi
        else
            consecutive_failures=$((consecutive_failures + 1))
            log_message "⚠️ Celeryワーカーが停止しています (連続失敗: $consecutive_failures/$max_consecutive_failures)"
            
            # 古いPIDファイルをクリーンアップ
            cleanup_pid_file
            
            # ワーカーを再起動
            if start_worker; then
                consecutive_failures=0
            else
                if [ $consecutive_failures -ge $max_consecutive_failures ]; then
                    log_message "❌ Celeryワーカーの復旧に連続で失敗しました。30秒待機します。"
                    sleep 30
                    consecutive_failures=0
                fi
            fi
        fi
        
        sleep 5
    done
}

# シグナルハンドラー
cleanup_and_exit() {
    log_message "🛑 監視スクリプトを停止中..."
    exit 0
}

trap cleanup_and_exit INT TERM

# 初期化
log_message "🚀 Celeryワーカー監視スクリプトを開始"

# 初回起動チェック
if ! check_worker_status; then
    log_message "🔄 初回起動: Celeryワーカーが停止しているため起動します"
    cleanup_pid_file
    start_worker
fi

# メイン監視ループ開始
main_monitor_loop
