#!/bin/bash

# ScrapyUI ポート管理ユーティリティ
# ポート競合の検出、解決、監視を行う

# デフォルトポート設定
DEFAULT_BACKEND_PORT=8000
DEFAULT_FRONTEND_PORT=4000
DEFAULT_NODEJS_PORT=3001
DEFAULT_FLOWER_PORT=5556

# カラー設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# ポートが使用中かチェック
check_port_usage() {
    local port=$1
    if lsof -i:$port >/dev/null 2>&1; then
        return 0  # 使用中
    else
        return 1  # 利用可能
    fi
}

# ポートを使用しているプロセス情報を取得
get_port_process_info() {
    local port=$1
    lsof -i:$port 2>/dev/null | tail -n +2
}

# 利用可能なポートを見つける
find_available_port() {
    local start_port=$1
    local max_attempts=${2:-50}
    
    for ((i=0; i<max_attempts; i++)); do
        local test_port=$((start_port + i))
        if ! check_port_usage $test_port; then
            echo $test_port
            return 0
        fi
    done
    
    return 1
}

# ポート範囲をスキャン
scan_port_range() {
    local start_port=$1
    local end_port=$2
    
    log_info "ポート範囲 $start_port-$end_port をスキャン中..."
    
    for ((port=start_port; port<=end_port; port++)); do
        if check_port_usage $port; then
            local process_info=$(get_port_process_info $port)
            echo "ポート $port: 使用中"
            echo "$process_info" | while read line; do
                echo "  $line"
            done
            echo ""
        fi
    done
}

# ScrapyUI関連ポートの状態確認
check_scrapyui_ports() {
    log_info "ScrapyUI関連ポートの状態確認..."
    
    local ports=($DEFAULT_BACKEND_PORT $DEFAULT_FRONTEND_PORT $DEFAULT_NODEJS_PORT $DEFAULT_FLOWER_PORT)
    local port_names=("Backend" "Frontend" "Node.js" "Flower")
    
    for i in "${!ports[@]}"; do
        local port=${ports[$i]}
        local name=${port_names[$i]}
        
        if check_port_usage $port; then
            log_warn "$name ポート $port は使用中です"
            get_port_process_info $port | while read line; do
                echo "  $line"
            done
        else
            log_success "$name ポート $port は利用可能です"
        fi
        echo ""
    done
}

# ポート競合を解決
resolve_port_conflicts() {
    log_info "ポート競合の自動解決を開始..."
    
    local backend_port=$(find_available_port $DEFAULT_BACKEND_PORT)
    local frontend_port=$(find_available_port $DEFAULT_FRONTEND_PORT)
    local nodejs_port=$(find_available_port $DEFAULT_NODEJS_PORT)
    local flower_port=$(find_available_port $DEFAULT_FLOWER_PORT)
    
    if [ $? -eq 0 ]; then
        log_success "推奨ポート設定:"
        echo "export BACKEND_PORT=$backend_port"
        echo "export FRONTEND_PORT=$frontend_port"
        echo "export NODEJS_PORT=$nodejs_port"
        echo "export FLOWER_PORT=$flower_port"
        
        # .env.portsファイルに保存
        cat > .env.ports << EOF
# ScrapyUI 自動生成ポート設定
# $(date)
BACKEND_PORT=$backend_port
FRONTEND_PORT=$frontend_port
NODEJS_PORT=$nodejs_port
FLOWER_PORT=$flower_port
EOF
        log_success "ポート設定を .env.ports に保存しました"
    else
        log_error "利用可能なポートが見つかりませんでした"
        return 1
    fi
}

# 強制的にポートをクリア
force_clear_ports() {
    log_warn "ScrapyUI関連ポートを強制的にクリアします..."
    
    local ports=($DEFAULT_BACKEND_PORT $DEFAULT_FRONTEND_PORT $DEFAULT_NODEJS_PORT $DEFAULT_FLOWER_PORT)
    
    for port in "${ports[@]}"; do
        if check_port_usage $port; then
            log_info "ポート $port を使用しているプロセスを終了中..."
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
            sleep 1
            
            if ! check_port_usage $port; then
                log_success "ポート $port をクリアしました"
            else
                log_error "ポート $port のクリアに失敗しました"
            fi
        else
            log_info "ポート $port は既に利用可能です"
        fi
    done
}

# ヘルプ表示
show_help() {
    echo "ScrapyUI ポート管理ユーティリティ"
    echo ""
    echo "使用方法:"
    echo "  $0 [コマンド] [オプション]"
    echo ""
    echo "コマンド:"
    echo "  check       - ScrapyUI関連ポートの状態確認"
    echo "  scan        - 指定範囲のポートスキャン"
    echo "  resolve     - ポート競合の自動解決"
    echo "  clear       - ScrapyUI関連ポートの強制クリア"
    echo "  help        - このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0 check                    # ポート状態確認"
    echo "  $0 scan 8000 8010          # ポート8000-8010をスキャン"
    echo "  $0 resolve                 # 競合解決"
    echo "  $0 clear                   # ポート強制クリア"
}

# メイン処理
main() {
    case "${1:-help}" in
        "check")
            check_scrapyui_ports
            ;;
        "scan")
            if [ $# -lt 3 ]; then
                log_error "使用方法: $0 scan <開始ポート> <終了ポート>"
                exit 1
            fi
            scan_port_range $2 $3
            ;;
        "resolve")
            resolve_port_conflicts
            ;;
        "clear")
            force_clear_ports
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# スクリプト実行
main "$@"
