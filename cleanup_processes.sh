#!/bin/bash

# ScrapyUI プロセスクリーンアップスクリプト
# 重複プロセスとゾンビプロセスを自動的にクリーンアップします

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_cleanup() {
    echo -e "${PURPLE}[CLEANUP]${NC} $1"
}

# プロセス存在チェック関数
check_process_exists() {
    local pattern="$1"
    pgrep -f "$pattern" >/dev/null 2>&1
}

# 安全なプロセス終了関数
safe_kill_processes() {
    local pattern="$1"
    local description="$2"
    local signal="${3:-TERM}"
    
    if check_process_exists "$pattern"; then
        log_cleanup "Stopping $description processes..."
        
        # プロセスIDを取得
        local pids=$(pgrep -f "$pattern" 2>/dev/null || true)
        
        if [ -n "$pids" ]; then
            echo "$pids" | while read -r pid; do
                if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                    log_cleanup "  Stopping PID $pid ($description)"
                    kill -"$signal" "$pid" 2>/dev/null || true
                fi
            done
            
            # プロセスが終了するまで待機（最大10秒）
            local count=0
            while [ $count -lt 10 ] && check_process_exists "$pattern"; do
                sleep 1
                count=$((count + 1))
            done
            
            # まだ残っている場合は強制終了
            if check_process_exists "$pattern"; then
                log_warning "  Force killing remaining $description processes..."
                pkill -9 -f "$pattern" 2>/dev/null || true
                sleep 1
            fi
            
            log_success "  $description processes stopped"
        fi
    else
        log_info "$description processes not found (already clean)"
    fi
}

# ゾンビプロセスクリーンアップ関数
cleanup_zombie_processes() {
    log_cleanup "Checking for zombie processes..."
    
    # ゾンビプロセスを検索
    local zombies=$(ps aux | awk '$8 ~ /^Z/ { print $2 }' 2>/dev/null || true)
    
    if [ -n "$zombies" ]; then
        log_warning "Found zombie processes: $zombies"
        
        # 親プロセスに SIGCHLD を送信してゾンビを回収させる
        echo "$zombies" | while read -r zombie_pid; do
            if [ -n "$zombie_pid" ]; then
                # 親プロセスIDを取得
                local parent_pid=$(ps -o ppid= -p "$zombie_pid" 2>/dev/null | tr -d ' ' || true)
                
                if [ -n "$parent_pid" ] && [ "$parent_pid" != "1" ]; then
                    log_cleanup "  Sending SIGCHLD to parent process $parent_pid for zombie $zombie_pid"
                    kill -CHLD "$parent_pid" 2>/dev/null || true
                fi
            fi
        done
        
        sleep 2
        
        # まだ残っているゾンビをチェック
        local remaining_zombies=$(ps aux | awk '$8 ~ /^Z/ { print $2 }' 2>/dev/null || true)
        if [ -n "$remaining_zombies" ]; then
            log_warning "Some zombie processes remain: $remaining_zombies"
            log_info "These will be cleaned up by the system eventually"
        else
            log_success "All zombie processes cleaned up"
        fi
    else
        log_success "No zombie processes found"
    fi
}

# 重複Celeryプロセスクリーンアップ関数
cleanup_duplicate_celery() {
    log_cleanup "Checking for duplicate Celery processes..."
    
    # Celeryワーカーの重複チェック
    local worker_count=$(pgrep -f "celery.*worker" 2>/dev/null | wc -l || echo "0")
    local beat_count=$(pgrep -f "celery.*beat" 2>/dev/null | wc -l || echo "0")
    
    if [ "$worker_count" -gt 2 ]; then
        log_warning "Found $worker_count Celery worker processes (expected: 1-2)"
        safe_kill_processes "celery.*worker" "Celery worker"
    fi
    
    if [ "$beat_count" -gt 1 ]; then
        log_warning "Found $beat_count Celery beat processes (expected: 1)"
        safe_kill_processes "celery.*beat" "Celery beat"
    fi
    
    # Flowerプロセスの重複チェック
    local flower_count=$(pgrep -f "celery.*flower" 2>/dev/null | wc -l || echo "0")
    if [ "$flower_count" -gt 1 ]; then
        log_warning "Found $flower_count Flower processes (expected: 0-1)"
        safe_kill_processes "celery.*flower" "Flower"
    fi
}

# ポート占有プロセスクリーンアップ関数
cleanup_port_conflicts() {
    log_cleanup "Checking for port conflicts..."
    
    local ports=("8000" "4000" "3001" "5556")
    
    for port in "${ports[@]}"; do
        local pid=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$pid" ]; then
            local process_name=$(ps -p "$pid" -o comm= 2>/dev/null || echo "unknown")
            log_warning "Port $port is occupied by PID $pid ($process_name)"
            
            # ScrapyUI関連プロセス以外は警告のみ
            if echo "$process_name" | grep -qE "(python|node|uvicorn|celery|flower)"; then
                log_cleanup "  Stopping process on port $port (PID: $pid)"
                kill -TERM "$pid" 2>/dev/null || true
                sleep 2
                
                # まだ残っている場合は強制終了
                if kill -0 "$pid" 2>/dev/null; then
                    kill -9 "$pid" 2>/dev/null || true
                fi
                log_success "  Port $port freed"
            else
                log_info "  Skipping non-ScrapyUI process on port $port"
            fi
        else
            log_success "Port $port is free"
        fi
    done
}

# 古いログファイルクリーンアップ関数
cleanup_old_logs() {
    log_cleanup "Cleaning up old log files..."
    
    # 7日以上古いログファイルを削除
    find . -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true
    find . -name "celerybeat-schedule*" -type f -mtime +7 -delete 2>/dev/null || true
    find . -name "flower.db-*" -type f -mtime +7 -delete 2>/dev/null || true
    
    log_success "Old log files cleaned up"
}

# 一時ファイルクリーンアップ関数
cleanup_temp_files() {
    log_cleanup "Cleaning up temporary files..."
    
    # 古い結果ファイル（24時間以上）
    find . -name "results_*.jsonl" -type f -mtime +1 -delete 2>/dev/null || true
    find . -name "stats_*.json" -type f -mtime +1 -delete 2>/dev/null || true
    
    # 古いPIDファイル
    find . -name "*.pid" -type f -delete 2>/dev/null || true
    
    # 古い一時ディレクトリ
    find /tmp -name "scrapy-*" -type d -mtime +1 -exec rm -rf {} + 2>/dev/null || true
    
    log_success "Temporary files cleaned up"
}

# メイン実行関数
main() {
    echo -e "${CYAN}🧹 ScrapyUI Process Cleanup Starting...${NC}"
    echo "=================================================="
    
    # 1. ゾンビプロセスのクリーンアップ
    cleanup_zombie_processes
    echo ""
    
    # 2. 重複Celeryプロセスのクリーンアップ
    cleanup_duplicate_celery
    echo ""
    
    # 3. ポート競合の解決
    cleanup_port_conflicts
    echo ""
    
    # 4. 古いログファイルのクリーンアップ
    cleanup_old_logs
    echo ""
    
    # 5. 一時ファイルのクリーンアップ
    cleanup_temp_files
    echo ""
    
    echo "=================================================="
    log_success "🎉 Process cleanup completed successfully!"
    echo ""
}

# スクリプト実行
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
