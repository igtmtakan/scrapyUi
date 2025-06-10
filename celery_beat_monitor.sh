#!/bin/bash

# Celery Beat監視・自動復旧スクリプト
# 5分間隔でCelery Beatの状態を監視し、必要に応じて自動復旧を行う

# ログファイル設定
LOG_FILE="logs/celery_beat_monitor.log"
mkdir -p logs

# ログ関数
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $1" | tee -a "$LOG_FILE"
}

# Celery Beat状態チェック関数
check_celery_beat() {
    if pgrep -f "celery.*beat" > /dev/null; then
        return 0  # 実行中
    else
        return 1  # 停止中
    fi
}

# Celery Beat起動関数
start_celery_beat() {
    log_info "Celery Beatを起動中..."
    
    # 既存プロセスを停止
    pkill -f "celery.*beat" 2>/dev/null || true
    sleep 3
    
    # バックエンドディレクトリに移動
    cd backend
    
    # Celery Beat起動
    python3 -m celery -A app.celery_app beat \
        --scheduler=app.scheduler:DatabaseScheduler \
        --loglevel=info \
        --max-interval=5 \
        --pidfile=celery_beat.pid \
        --logfile=celery_beat.log \
        --detach
    
    cd ..
    
    # 起動確認
    sleep 5
    if check_celery_beat; then
        log_success "Celery Beatが正常に起動しました"
        return 0
    else
        log_error "Celery Beatの起動に失敗しました"
        return 1
    fi
}

# Redis状態チェック関数
check_redis() {
    if redis-cli ping > /dev/null 2>&1; then
        return 0  # 実行中
    else
        return 1  # 停止中
    fi
}

# Redis起動関数
start_redis() {
    log_warn "Redisが停止しています。起動中..."
    redis-server --daemonize yes
    sleep 3
    
    if check_redis; then
        log_success "Redisが正常に起動しました"
        return 0
    else
        log_error "Redisの起動に失敗しました"
        return 1
    fi
}

# データベース接続チェック関数
check_database() {
    cd backend
    python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('database/scrapy_ui.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM schedules WHERE is_active = 1')
    count = cursor.fetchone()[0]
    conn.close()
    print(f'Active schedules: {count}')
    exit(0)
except Exception as e:
    print(f'Database error: {e}')
    exit(1)
" > /dev/null 2>&1
    local result=$?
    cd ..
    return $result
}

# メイン監視ループ
main_monitor() {
    log_info "🔍 Celery Beat監視・自動復旧を開始します"
    log_info "📊 監視間隔: 5分"
    log_info "🔧 自動復旧: 有効"
    
    while true; do
        # Redis状態チェック
        if ! check_redis; then
            log_warn "⚠️ Redisが停止しています"
            start_redis
        fi
        
        # データベース接続チェック
        if ! check_database; then
            log_warn "⚠️ データベース接続に問題があります"
        fi
        
        # Celery Beat状態チェック
        if check_celery_beat; then
            log_info "✅ Celery Beatは正常に動作中です"
        else
            log_warn "⚠️ Celery Beatが停止しています。自動復旧を開始..."
            
            # 自動復旧試行
            if start_celery_beat; then
                log_success "🎉 Celery Beatの自動復旧が完了しました"
            else
                log_error "❌ Celery Beatの自動復旧に失敗しました"
                
                # 緊急対応: 強制再起動
                log_warn "🚨 緊急対応: 強制再起動を実行中..."
                pkill -9 -f "celery.*beat" 2>/dev/null || true
                sleep 5
                
                if start_celery_beat; then
                    log_success "🎉 強制再起動による復旧が完了しました"
                else
                    log_error "❌ 強制再起動による復旧も失敗しました"
                fi
            fi
        fi
        
        # プロセス情報をログに記録
        BEAT_PID=$(pgrep -f "celery.*beat" | head -1)
        if [ ! -z "$BEAT_PID" ]; then
            log_info "📊 Celery Beat PID: $BEAT_PID"
        fi
        
        # 5分間待機
        log_info "⏳ 次回チェックまで5分間待機..."
        sleep 300
    done
}

# シグナルハンドラー
cleanup() {
    log_info "🛑 Celery Beat監視を停止中..."
    exit 0
}

trap cleanup SIGTERM SIGINT

# メイン実行
log_info "🚀 Celery Beat監視・自動復旧スクリプトを開始します"
main_monitor
