#!/bin/bash

# ScrapyUI 統合起動スクリプト - 根本的解決版
# 全サービスの起動・停止・監視を統一管理

set -e

# 設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ポート設定
BACKEND_PORT=8000
SPIDER_MANAGER_PORT=8002
TEST_SERVICE_PORT=8005
FRONTEND_PORT=4000
NODEJS_PORT=3001

# ログディレクトリ
LOG_DIR="logs"
PID_DIR="pids"
mkdir -p "$LOG_DIR" "$PID_DIR"

# 色設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# プロセス停止関数
stop_all_processes() {
    log_info "🛑 Stopping all ScrapyUI processes..."
    
    # PIDファイルから停止
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            local service=$(basename "$pid_file" .pid)
            
            if kill -0 "$pid" 2>/dev/null; then
                log_info "Stopping $service (PID: $pid)"
                kill -TERM "$pid" 2>/dev/null || true
                
                # 5秒待機して強制終了
                sleep 5
                if kill -0 "$pid" 2>/dev/null; then
                    kill -KILL "$pid" 2>/dev/null || true
                fi
            fi
            rm -f "$pid_file"
        fi
    done
    
    # プロセス名で停止
    pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
    pkill -f "spider-manager.*simple_main.py" 2>/dev/null || true
    pkill -f "test-service.*simple_server.py" 2>/dev/null || true
    pkill -f "next.*dev" 2>/dev/null || true
    pkill -f "node.*app.js" 2>/dev/null || true
    
    # ポートで停止
    for port in $BACKEND_PORT $SPIDER_MANAGER_PORT $TEST_SERVICE_PORT $FRONTEND_PORT $NODEJS_PORT; do
        if lsof -ti:$port >/dev/null 2>&1; then
            log_info "Killing processes on port $port"
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
        fi
    done
    
    sleep 2
    log_success "✅ All processes stopped"
}

# ヘルスチェック関数
check_health() {
    local url=$1
    local timeout=${2:-30}
    
    for i in $(seq 1 $timeout); do
        if curl -s "$url" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    return 1
}

# サービス起動関数
start_backend() {
    log_info "🚀 Starting Backend Server..."
    
    export PYTHONPATH="$SCRIPT_DIR"
    nohup python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port $BACKEND_PORT \
        > "$LOG_DIR/backend.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_DIR/backend.pid"
    
    if check_health "http://localhost:$BACKEND_PORT/health" 30; then
        log_success "✅ Backend Server started (PID: $pid)"
        return 0
    else
        log_error "❌ Backend Server failed to start"
        return 1
    fi
}

start_spider_manager() {
    log_info "🕷️ Starting Spider Manager..."
    
    cd microservices/spider-manager
    nohup python3 simple_main.py > "../../$LOG_DIR/spider-manager.log" 2>&1 &
    local pid=$!
    echo $pid > "../../$PID_DIR/spider-manager.pid"
    cd "$SCRIPT_DIR"
    
    if check_health "http://localhost:$SPIDER_MANAGER_PORT/health" 15; then
        log_success "✅ Spider Manager started (PID: $pid)"
        return 0
    else
        log_error "❌ Spider Manager failed to start"
        return 1
    fi
}

start_test_service() {
    log_info "🧪 Starting Test Service..."
    
    cd microservices/test-service
    nohup python3 simple_server.py > "../../$LOG_DIR/test-service.log" 2>&1 &
    local pid=$!
    echo $pid > "../../$PID_DIR/test-service.pid"
    cd "$SCRIPT_DIR"
    
    if check_health "http://localhost:$TEST_SERVICE_PORT/health" 15; then
        log_success "✅ Test Service started (PID: $pid)"
        return 0
    else
        log_error "❌ Test Service failed to start"
        return 1
    fi
}

start_frontend() {
    if [ ! -d "frontend" ]; then
        log_warning "⚠️ Frontend directory not found, skipping..."
        return 0
    fi
    
    log_info "🌐 Starting Frontend..."
    
    cd frontend
    nohup npm run dev > "../$LOG_DIR/frontend.log" 2>&1 &
    local pid=$!
    echo $pid > "../$PID_DIR/frontend.pid"
    cd "$SCRIPT_DIR"
    
    # フロントエンドは起動に時間がかかるので長めに待機
    sleep 10
    if check_health "http://localhost:$FRONTEND_PORT" 30; then
        log_success "✅ Frontend started (PID: $pid)"
        return 0
    else
        log_warning "⚠️ Frontend may still be starting..."
        return 0  # フロントエンドは失敗しても続行
    fi
}

start_nodejs_service() {
    if [ ! -d "nodejs-service" ]; then
        log_warning "⚠️ Node.js Service directory not found, skipping..."
        return 0
    fi

    log_info "🟢 Starting Node.js Puppeteer Service..."

    cd nodejs-service
    nohup npm start > "../$LOG_DIR/nodejs-service.log" 2>&1 &
    local pid=$!
    echo $pid > "../$PID_DIR/nodejs-service.pid"
    cd "$SCRIPT_DIR"

    sleep 5
    if check_health "http://localhost:$NODEJS_PORT/api/health" 20; then
        log_success "✅ Node.js Puppeteer Service started (PID: $pid)"
        return 0
    else
        log_warning "⚠️ Node.js Puppeteer Service may still be starting..."
        return 0  # Node.jsサービスは失敗しても続行
    fi
}

# 状態確認関数
show_status() {
    echo ""
    echo "============================================================"
    echo "🔍 ScrapyUI Services Status"
    echo "============================================================"
    
    # Backend
    if check_health "http://localhost:$BACKEND_PORT/health" 2; then
        echo -e "✅ Backend Server       http://localhost:$BACKEND_PORT"
    else
        echo -e "❌ Backend Server       http://localhost:$BACKEND_PORT"
    fi
    
    # Spider Manager
    if check_health "http://localhost:$SPIDER_MANAGER_PORT/health" 2; then
        echo -e "✅ Spider Manager       http://localhost:$SPIDER_MANAGER_PORT"
    else
        echo -e "❌ Spider Manager       http://localhost:$SPIDER_MANAGER_PORT"
    fi
    
    # Test Service
    if check_health "http://localhost:$TEST_SERVICE_PORT/health" 2; then
        echo -e "✅ Test Service         http://localhost:$TEST_SERVICE_PORT"
    else
        echo -e "❌ Test Service         http://localhost:$TEST_SERVICE_PORT"
    fi
    
    # Frontend
    if check_health "http://localhost:$FRONTEND_PORT" 2; then
        echo -e "✅ Frontend             http://localhost:$FRONTEND_PORT"
    else
        echo -e "❌ Frontend             http://localhost:$FRONTEND_PORT"
    fi
    
    # Node.js Puppeteer
    if check_health "http://localhost:$NODEJS_PORT/api/health" 2; then
        echo -e "✅ Node.js Puppeteer    http://localhost:$NODEJS_PORT"
    else
        echo -e "❌ Node.js Puppeteer    http://localhost:$NODEJS_PORT"
    fi
    
    echo "============================================================"
}

# 監視関数
monitor_services() {
    log_info "🔍 Starting service monitoring..."
    
    while true; do
        sleep 30
        
        # バックエンドサーバーの監視（最重要）
        if ! check_health "http://localhost:$BACKEND_PORT/health" 2; then
            log_warning "⚠️ Backend Server health check failed, restarting..."
            start_backend
        fi
        
        # Spider Managerの監視
        if ! check_health "http://localhost:$SPIDER_MANAGER_PORT/health" 2; then
            log_warning "⚠️ Spider Manager health check failed, restarting..."
            start_spider_manager
        fi
        
        # Test Serviceの監視
        if ! check_health "http://localhost:$TEST_SERVICE_PORT/health" 2; then
            log_warning "⚠️ Test Service health check failed, restarting..."
            start_test_service
        fi

        # Node.js Serviceの監視
        if ! check_health "http://localhost:$NODEJS_PORT/api/health" 2; then
            log_warning "⚠️ Node.js Service health check failed, restarting..."
            start_nodejs_service
        fi
    done
}

# メイン処理
main() {
    case "${1:-start}" in
        "start")
            log_info "🚀 Starting ScrapyUI Services..."
            
            # 既存プロセスを停止
            stop_all_processes
            
            # 依存関係順に起動
            if start_backend; then
                # バックエンドが起動したらマイクロサービスを起動
                sleep 2
                start_spider_manager
                start_test_service
                
                # オプションサービス
                start_frontend
                start_nodejs_service
                
                log_success "🎉 ScrapyUI started successfully!"
                show_status
                
                # 監視開始
                log_info "🔍 Starting monitoring (Press Ctrl+C to stop)"
                trap 'log_info "🛑 Stopping services..."; stop_all_processes; exit 0' INT TERM
                monitor_services
            else
                log_error "❌ Failed to start Backend Server"
                exit 1
            fi
            ;;
            
        "stop")
            stop_all_processes
            ;;
            
        "restart")
            stop_all_processes
            sleep 3
            exec "$0" start
            ;;
            
        "status")
            show_status
            ;;
            
        *)
            echo "Usage: $0 {start|stop|restart|status}"
            echo ""
            echo "Commands:"
            echo "  start   - Start all ScrapyUI services"
            echo "  stop    - Stop all ScrapyUI services"
            echo "  restart - Restart all ScrapyUI services"
            echo "  status  - Show service status"
            exit 1
            ;;
    esac
}

# スクリプト実行
main "$@"
