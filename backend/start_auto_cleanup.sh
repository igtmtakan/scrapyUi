#!/bin/bash
# ScrapyUI自動クリーンアップシステム起動スクリプト

set -e

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRAPYUI_ROOT="$(dirname "$SCRIPT_DIR")"

log_info "🤖 Starting ScrapyUI Auto Cleanup System"
log_debug "Script directory: $SCRIPT_DIR"
log_debug "ScrapyUI root: $SCRAPYUI_ROOT"

# Python環境の確認
if ! command -v python &> /dev/null; then
    log_error "Python not found. Please install Python."
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1)
log_info "Python version: $PYTHON_VERSION"

# 必要なモジュールの確認
log_info "📦 Checking required modules..."
python -c "import schedule" 2>/dev/null || {
    log_warn "schedule module not found. Installing..."
    pip install schedule
}

# 権限の確認
if [ ! -w "$SCRAPYUI_ROOT/scrapy_projects" ]; then
    log_error "No write permission to scrapy_projects directory"
    exit 1
fi

# 設定の表示
log_info "⚙️ Configuration:"
log_info "   📁 Projects path: $SCRAPYUI_ROOT/scrapy_projects"
log_info "   🔧 Tool path: $SCRIPT_DIR/jsonl_file_manager.py"
log_info "   📊 Max lines per file: 10,000"
log_info "   📅 Keep sessions: 5"
log_info "   ⏰ Cleanup interval: 6 hours"

# 起動オプションの処理
case "${1:-start}" in
    "analyze")
        log_info "🔍 Running file analysis..."
        cd "$SCRIPT_DIR"
        python auto_file_cleanup_scheduler.py --analyze
        ;;
    "cleanup")
        log_info "🧹 Running one-time cleanup..."
        cd "$SCRIPT_DIR"
        python auto_file_cleanup_scheduler.py --cleanup
        ;;
    "start")
        log_info "🚀 Starting auto cleanup scheduler..."
        cd "$SCRIPT_DIR"
        
        # バックグラウンドで実行
        if [ "${2:-}" = "--background" ] || [ "${2:-}" = "-d" ]; then
            log_info "🌙 Starting in background mode..."
            nohup python auto_file_cleanup_scheduler.py --start > auto_cleanup.log 2>&1 &
            PID=$!
            echo $PID > auto_cleanup.pid
            log_info "✅ Auto cleanup scheduler started with PID: $PID"
            log_info "📄 Log file: $SCRIPT_DIR/auto_cleanup.log"
            log_info "🔍 Check status: ps -p $PID"
            log_info "⏹️ Stop: kill $PID"
        else
            log_info "🖥️ Starting in foreground mode..."
            log_info "⏹️ Press Ctrl+C to stop"
            python auto_file_cleanup_scheduler.py --start
        fi
        ;;
    "stop")
        log_info "⏹️ Stopping auto cleanup scheduler..."
        if [ -f "$SCRIPT_DIR/auto_cleanup.pid" ]; then
            PID=$(cat "$SCRIPT_DIR/auto_cleanup.pid")
            if ps -p $PID > /dev/null 2>&1; then
                kill $PID
                rm -f "$SCRIPT_DIR/auto_cleanup.pid"
                log_info "✅ Auto cleanup scheduler stopped (PID: $PID)"
            else
                log_warn "Process $PID not found"
                rm -f "$SCRIPT_DIR/auto_cleanup.pid"
            fi
        else
            log_warn "PID file not found"
        fi
        ;;
    "status")
        log_info "📊 Checking auto cleanup scheduler status..."
        if [ -f "$SCRIPT_DIR/auto_cleanup.pid" ]; then
            PID=$(cat "$SCRIPT_DIR/auto_cleanup.pid")
            if ps -p $PID > /dev/null 2>&1; then
                log_info "✅ Auto cleanup scheduler is running (PID: $PID)"
                
                # プロセス情報を表示
                ps -p $PID -o pid,ppid,cmd,etime,pcpu,pmem
                
                # ログファイルの最新行を表示
                if [ -f "$SCRIPT_DIR/auto_cleanup.log" ]; then
                    log_info "📄 Recent log entries:"
                    tail -5 "$SCRIPT_DIR/auto_cleanup.log"
                fi
            else
                log_warn "Process $PID not found"
                rm -f "$SCRIPT_DIR/auto_cleanup.pid"
            fi
        else
            log_info "⏹️ Auto cleanup scheduler is not running"
        fi
        ;;
    "install-service")
        log_info "📦 Installing systemd service..."
        
        # サービスファイルをコピー
        sudo cp "$SCRIPT_DIR/scrapyui-auto-cleanup.service" /etc/systemd/system/
        
        # systemdを再読み込み
        sudo systemctl daemon-reload
        
        # サービスを有効化
        sudo systemctl enable scrapyui-auto-cleanup.service
        
        log_info "✅ Service installed successfully"
        log_info "🚀 Start service: sudo systemctl start scrapyui-auto-cleanup"
        log_info "📊 Check status: sudo systemctl status scrapyui-auto-cleanup"
        log_info "📄 View logs: sudo journalctl -u scrapyui-auto-cleanup -f"
        ;;
    "help"|"-h"|"--help")
        echo "ScrapyUI Auto Cleanup System"
        echo ""
        echo "Usage: $0 [COMMAND] [OPTIONS]"
        echo ""
        echo "Commands:"
        echo "  analyze              Analyze JSONL files only"
        echo "  cleanup              Run one-time cleanup"
        echo "  start                Start auto cleanup scheduler (default)"
        echo "  stop                 Stop auto cleanup scheduler"
        echo "  status               Check scheduler status"
        echo "  install-service      Install as systemd service"
        echo "  help                 Show this help message"
        echo ""
        echo "Options for 'start' command:"
        echo "  --background, -d     Run in background"
        echo ""
        echo "Examples:"
        echo "  $0 analyze                    # Analyze files"
        echo "  $0 cleanup                    # Run cleanup once"
        echo "  $0 start                      # Start in foreground"
        echo "  $0 start --background         # Start in background"
        echo "  $0 status                     # Check status"
        echo "  $0 stop                       # Stop scheduler"
        ;;
    *)
        log_error "Unknown command: $1"
        log_info "Use '$0 help' for usage information"
        exit 1
        ;;
esac
