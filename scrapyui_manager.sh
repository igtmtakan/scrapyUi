#!/bin/bash

# ScrapyUI 統合管理スクリプト
# 全ての管理機能を統合したメインインターフェース

# カラー設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ロゴ表示
show_logo() {
    echo -e "${CYAN}"
    echo "  ____                            _   _ ___ "
    echo " / ___|  ___ _ __ __ _ _ __  _   _| | | |_ _|"
    echo " \___ \ / __| '__/ _\` | '_ \| | | | | | || | "
    echo "  ___) | (__| | | (_| | |_) | |_| | |_| || | "
    echo " |____/ \___|_|  \__,_| .__/ \__, |\___/|___|"
    echo "                     |_|    |___/           "
    echo -e "${NC}"
    echo -e "${BLUE}ScrapyUI 統合管理システム v2.0${NC}"
    echo ""
}

# ログ関数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

# 依存関係チェック
check_dependencies() {
    local missing_deps=()
    
    # 必要なコマンドをチェック
    local required_commands=("curl" "jq" "lsof" "redis-cli" "python3" "npm")
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "以下の依存関係が不足しています:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        echo ""
        echo "Ubuntu/Debianの場合:"
        echo "  sudo apt update && sudo apt install curl jq lsof redis-server python3 python3-pip nodejs npm"
        echo ""
        return 1
    fi
    
    return 0
}

# システム状態の表示
show_system_status() {
    log_info "ScrapyUI システム状態"
    echo "=================================="
    
    # 設定状態
    if [ -f "./config_manager.sh" ]; then
        echo -e "${CYAN}設定状態:${NC}"
        ./config_manager.sh validate >/dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "  ✅ 設定は正常です"
        else
            echo "  ⚠️ 設定に問題があります"
        fi
    fi
    
    # ポート状態
    if [ -f "./port_manager.sh" ]; then
        echo -e "${CYAN}ポート状態:${NC}"
        ./port_manager.sh check 2>/dev/null | grep -E "(✅|❌|⚠️)" | head -4
    fi
    
    # サービス状態
    if [ -f "./service_monitor.sh" ]; then
        echo -e "${CYAN}サービス状態:${NC}"
        ./service_monitor.sh check 2>/dev/null | grep -E "(正常|応答なし|プロセスなし)" | head -7
    fi
    
    echo "=================================="
}

# クイックスタート
quick_start() {
    log_info "ScrapyUI クイックスタートを実行中..."
    
    # 依存関係チェック
    if ! check_dependencies; then
        log_error "依存関係が不足しています。インストール後に再実行してください。"
        return 1
    fi
    
    # 設定初期化
    if [ -f "./config_manager.sh" ]; then
        log_info "設定を初期化中..."
        ./config_manager.sh init
    fi
    
    # ポート競合解決
    if [ -f "./port_manager.sh" ]; then
        log_info "ポート競合を解決中..."
        ./port_manager.sh resolve
    fi
    
    # サーバー起動
    log_info "サーバーを起動中..."
    ./start_servers.sh
}

# 完全停止
full_stop() {
    log_info "ScrapyUI を完全停止中..."
    
    # 通常の停止スクリプト実行
    if [ -f "./stop_servers.sh" ]; then
        ./stop_servers.sh
    fi
    
    # 追加のクリーンアップ
    log_info "追加のクリーンアップを実行中..."
    
    # 全関連プロセスを強制終了
    pkill -f "uvicorn.*app.main" 2>/dev/null || true
    pkill -f "next.*dev" 2>/dev/null || true
    pkill -f "node.*app.js" 2>/dev/null || true
    pkill -f "celery.*" 2>/dev/null || true
    pkill -f "flower" 2>/dev/null || true
    pkill -f "redis-server" 2>/dev/null || true
    
    # ポートクリア
    if [ -f "./port_manager.sh" ]; then
        ./port_manager.sh clear
    fi
    
    # 一時ファイル削除
    rm -f .*.pid 2>/dev/null || true
    
    log_success "ScrapyUI が完全に停止されました"
}

# システム診断
system_diagnosis() {
    log_info "システム診断を実行中..."
    echo ""
    
    # 基本情報
    echo -e "${CYAN}=== システム情報 ===${NC}"
    echo "OS: $(uname -s) $(uname -r)"
    echo "Python: $(python3 --version 2>/dev/null || echo 'Not found')"
    echo "Node.js: $(node --version 2>/dev/null || echo 'Not found')"
    echo "Redis: $(redis-cli --version 2>/dev/null || echo 'Not found')"
    echo ""
    
    # 依存関係チェック
    echo -e "${CYAN}=== 依存関係チェック ===${NC}"
    check_dependencies
    echo ""
    
    # ディスク使用量
    echo -e "${CYAN}=== ディスク使用量 ===${NC}"
    df -h . | tail -1
    echo ""
    
    # メモリ使用量
    echo -e "${CYAN}=== メモリ使用量 ===${NC}"
    free -h | head -2
    echo ""
    
    # ネットワーク接続
    echo -e "${CYAN}=== ネットワーク接続 ===${NC}"
    if command -v ss >/dev/null 2>&1; then
        ss -tulpn | grep -E ":(8000|4000|3001|5556|6379)" | head -10
    else
        netstat -tulpn 2>/dev/null | grep -E ":(8000|4000|3001|5556|6379)" | head -10
    fi
    echo ""
    
    # ログファイル確認
    echo -e "${CYAN}=== ログファイル ===${NC}"
    if [ -d "logs" ]; then
        ls -la logs/ | head -10
    else
        echo "ログディレクトリが見つかりません"
    fi
    echo ""
    
    # 設定ファイル確認
    echo -e "${CYAN}=== 設定ファイル ===${NC}"
    local config_files=("backend/.env" "backend/.env.example" ".env.ports")
    for file in "${config_files[@]}"; do
        if [ -f "$file" ]; then
            echo "✅ $file"
        else
            echo "❌ $file (見つかりません)"
        fi
    done
}

# メンテナンスモード
maintenance_mode() {
    local action=${1:-status}
    
    case $action in
        "enable")
            log_info "メンテナンスモードを有効化中..."
            touch .maintenance_mode
            # サービス停止
            ./stop_servers.sh >/dev/null 2>&1
            log_success "メンテナンスモードが有効になりました"
            ;;
        "disable")
            log_info "メンテナンスモードを無効化中..."
            rm -f .maintenance_mode
            log_success "メンテナンスモードが無効になりました"
            ;;
        "status")
            if [ -f ".maintenance_mode" ]; then
                log_warn "メンテナンスモードが有効です"
            else
                log_info "メンテナンスモードは無効です"
            fi
            ;;
    esac
}

# ヘルプ表示
show_help() {
    show_logo
    echo "ScrapyUI 統合管理システム"
    echo ""
    echo -e "${YELLOW}使用方法:${NC}"
    echo "  $0 [コマンド] [オプション]"
    echo ""
    echo -e "${YELLOW}主要コマンド:${NC}"
    echo "  start           - サーバーを起動"
    echo "  stop            - サーバーを停止"
    echo "  restart         - サーバーを再起動"
    echo "  status          - システム状態を表示"
    echo "  quick-start     - クイックスタート（推奨）"
    echo "  full-stop       - 完全停止（全プロセス終了）"
    echo ""
    echo -e "${YELLOW}管理コマンド:${NC}"
    echo "  config [cmd]    - 設定管理 (init/show/validate/reset)"
    echo "  ports [cmd]     - ポート管理 (check/resolve/clear)"
    echo "  monitor         - サービス監視開始"
    echo "  diagnosis       - システム診断"
    echo "  maintenance     - メンテナンスモード (enable/disable/status)"
    echo ""
    echo -e "${YELLOW}例:${NC}"
    echo "  $0 quick-start              # 初回起動（推奨）"
    echo "  $0 config show ports        # ポート設定表示"
    echo "  $0 ports resolve            # ポート競合解決"
    echo "  $0 diagnosis                # システム診断"
    echo "  $0 maintenance enable       # メンテナンスモード有効化"
}

# メイン処理
main() {
    # メンテナンスモードチェック
    if [ -f ".maintenance_mode" ] && [ "$1" != "maintenance" ] && [ "$1" != "help" ]; then
        log_warn "メンテナンスモードが有効です。無効化するには: $0 maintenance disable"
        exit 1
    fi
    
    case "${1:-help}" in
        "start")
            ./start_servers.sh
            ;;
        "stop")
            ./stop_servers.sh
            ;;
        "restart")
            ./stop_servers.sh
            sleep 3
            ./start_servers.sh
            ;;
        "status")
            show_system_status
            ;;
        "quick-start")
            quick_start
            ;;
        "full-stop")
            full_stop
            ;;
        "config")
            if [ -f "./config_manager.sh" ]; then
                shift
                ./config_manager.sh "$@"
            else
                log_error "config_manager.sh が見つかりません"
            fi
            ;;
        "ports")
            if [ -f "./port_manager.sh" ]; then
                shift
                ./port_manager.sh "$@"
            else
                log_error "port_manager.sh が見つかりません"
            fi
            ;;
        "monitor")
            if [ -f "./service_monitor.sh" ]; then
                ./service_monitor.sh monitor
            else
                log_error "service_monitor.sh が見つかりません"
            fi
            ;;
        "diagnosis")
            system_diagnosis
            ;;
        "maintenance")
            maintenance_mode "$2"
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

main "$@"
