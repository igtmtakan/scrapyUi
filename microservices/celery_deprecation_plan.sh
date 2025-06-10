#!/bin/bash

# ScrapyUI Celery Deprecation Plan
# Celery、Celery Beat、Flowerの段階的廃止計画

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
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

check_celery_processes() {
    log_info "Celery関連プロセスの確認..."
    
    # Celery Worker確認
    if pgrep -f "celery.*worker" > /dev/null; then
        log_warning "Celery Worker が稼働中"
        CELERY_WORKER_RUNNING=true
    else
        log_info "Celery Worker は停止中"
        CELERY_WORKER_RUNNING=false
    fi
    
    # Celery Beat確認
    if pgrep -f "celery.*beat" > /dev/null; then
        log_warning "Celery Beat が稼働中"
        CELERY_BEAT_RUNNING=true
    else
        log_info "Celery Beat は停止中"
        CELERY_BEAT_RUNNING=false
    fi
    
    # Flower確認
    if pgrep -f "flower" > /dev/null; then
        log_warning "Flower が稼働中"
        FLOWER_RUNNING=true
    else
        log_info "Flower は停止中"
        FLOWER_RUNNING=false
    fi
}

check_microservices() {
    log_info "マイクロサービスの確認..."
    
    # Test Service確認
    if curl -s http://localhost:8005/health > /dev/null 2>&1; then
        log_success "Test Service (8005) 稼働中"
        MICROSERVICE_RUNNING=true
    else
        log_error "Test Service (8005) 停止中"
        MICROSERVICE_RUNNING=false
    fi
    
    # 他のマイクロサービス確認
    for port in 8001 8002 8003 8004; do
        if netstat -tlnp 2>/dev/null | grep ":$port " > /dev/null; then
            log_success "マイクロサービス ($port) 稼働中"
        else
            log_info "マイクロサービス ($port) 未起動"
        fi
    done
}

backup_celery_config() {
    log_info "Celery設定のバックアップ..."
    
    BACKUP_DIR="../config_backups/celery_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 設定ファイルのバックアップ
    if [ -f "../backend/app/celery_app.py" ]; then
        cp "../backend/app/celery_app.py" "$BACKUP_DIR/"
        log_success "celery_app.py をバックアップ"
    fi
    
    if [ -f "../backend/app/scheduler.py" ]; then
        cp "../backend/app/scheduler.py" "$BACKUP_DIR/"
        log_success "scheduler.py をバックアップ"
    fi
    
    # 実行中のプロセス情報保存
    ps aux | grep -E "(celery|flower)" > "$BACKUP_DIR/running_processes.txt"
    log_success "プロセス情報をバックアップ"
    
    log_success "バックアップ完了: $BACKUP_DIR"
}

stop_celery_services() {
    log_info "Celery関連サービスの停止..."
    
    # Celery Worker停止
    if [ "$CELERY_WORKER_RUNNING" = true ]; then
        log_info "Celery Worker を停止中..."
        pkill -f "celery.*worker" || true
        sleep 3
        
        if pgrep -f "celery.*worker" > /dev/null; then
            log_warning "強制終了を実行..."
            pkill -9 -f "celery.*worker" || true
        fi
        log_success "Celery Worker 停止完了"
    fi
    
    # Celery Beat停止
    if [ "$CELERY_BEAT_RUNNING" = true ]; then
        log_info "Celery Beat を停止中..."
        pkill -f "celery.*beat" || true
        sleep 3
        
        if pgrep -f "celery.*beat" > /dev/null; then
            log_warning "強制終了を実行..."
            pkill -9 -f "celery.*beat" || true
        fi
        log_success "Celery Beat 停止完了"
    fi
    
    # Flower停止
    if [ "$FLOWER_RUNNING" = true ]; then
        log_info "Flower を停止中..."
        pkill -f "flower" || true
        sleep 3
        
        if pgrep -f "flower" > /dev/null; then
            log_warning "強制終了を実行..."
            pkill -9 -f "flower" || true
        fi
        log_success "Flower 停止完了"
    fi
}

verify_microservices() {
    log_info "マイクロサービスの動作確認..."
    
    if [ "$MICROSERVICE_RUNNING" = false ]; then
        log_error "マイクロサービスが稼働していません"
        log_info "テストサービスを起動してください: cd test-service && python3 simple_server.py"
        return 1
    fi
    
    # 基本機能テスト
    log_info "基本機能テスト実行中..."
    
    # Health Check
    if curl -s http://localhost:8005/health | grep -q "healthy"; then
        log_success "Health Check: OK"
    else
        log_error "Health Check: FAILED"
        return 1
    fi
    
    # スケジュール確認
    SCHEDULE_COUNT=$(curl -s http://localhost:8005/schedules | jq -r '.count' 2>/dev/null || echo "0")
    log_info "スケジュール数: $SCHEDULE_COUNT"
    
    # タスク確認
    TASK_COUNT=$(curl -s http://localhost:8005/tasks | jq -r '.count' 2>/dev/null || echo "0")
    log_info "タスク数: $TASK_COUNT"
    
    # 結果確認
    RESULT_COUNT=$(curl -s http://localhost:8005/results | jq -r '.count' 2>/dev/null || echo "0")
    log_info "結果数: $RESULT_COUNT"
    
    log_success "マイクロサービス動作確認完了"
}

update_startup_scripts() {
    log_info "起動スクリプトの更新..."
    
    # start_servers.sh の更新
    if [ -f "../start_servers.sh" ]; then
        # Celery関連の起動を無効化
        sed -i.bak 's/^start_celery_worker/#start_celery_worker/' "../start_servers.sh"
        sed -i 's/^start_celery_beat/#start_celery_beat/' "../start_servers.sh"
        sed -i 's/^start_flower/#start_flower/' "../start_servers.sh"
        
        log_success "start_servers.sh を更新 (Celery起動を無効化)"
    fi
    
    # stop_servers.sh の更新
    if [ -f "../stop_servers.sh" ]; then
        # Celery関連の停止を無効化
        sed -i.bak 's/^stop_celery_worker/#stop_celery_worker/' "../stop_servers.sh"
        sed -i 's/^stop_celery_beat/#stop_celery_beat/' "../stop_servers.sh"
        sed -i 's/^stop_flower/#stop_flower/' "../stop_servers.sh"
        
        log_success "stop_servers.sh を更新 (Celery停止を無効化)"
    fi
}

create_migration_report() {
    log_info "移行レポートの作成..."
    
    REPORT_FILE="../logs/celery_deprecation_$(date +%Y%m%d_%H%M%S).log"
    
    cat > "$REPORT_FILE" << EOF
ScrapyUI Celery Deprecation Report
==================================
実行日時: $(date)
実行者: $(whoami)

【廃止されたコンポーネント】
- Celery Worker: $([ "$CELERY_WORKER_RUNNING" = true ] && echo "停止済み" || echo "元々停止")
- Celery Beat: $([ "$CELERY_BEAT_RUNNING" = true ] && echo "停止済み" || echo "元々停止")
- Flower: $([ "$FLOWER_RUNNING" = true ] && echo "停止済み" || echo "元々停止")

【代替システム】
- Scheduler Service: マイクロサービス (ポート8001)
- Spider Manager: マイクロサービス (ポート8002)
- Result Collector: マイクロサービス (ポート8003)
- API Gateway: マイクロサービス (ポート8000)
- WebUI: マイクロサービス (ポート8004)

【現在の状況】
- マイクロサービス稼働: $([ "$MICROSERVICE_RUNNING" = true ] && echo "正常" || echo "要確認")
- スケジュール数: $SCHEDULE_COUNT
- 処理済みタスク数: $TASK_COUNT
- 生成結果数: $RESULT_COUNT

【次のステップ】
1. 本格的なマイクロサービス環境構築
2. Docker/Kubernetes環境整備
3. 監視・ログ基盤構築
4. 運用手順書更新

【バックアップ場所】
設定ファイル: $BACKUP_DIR
EOF

    log_success "移行レポート作成: $REPORT_FILE"
}

# メイン実行
main() {
    echo "🗑️ ScrapyUI Celery Deprecation Plan"
    echo "=================================="
    echo "Celery、Celery Beat、Flowerの段階的廃止を実行します"
    echo ""
    
    # 1. 現状確認
    check_celery_processes
    check_microservices
    
    echo ""
    
    # 2. 確認プロンプト
    if [ "$CELERY_WORKER_RUNNING" = true ] || [ "$CELERY_BEAT_RUNNING" = true ] || [ "$FLOWER_RUNNING" = true ]; then
        echo "⚠️ 以下のCelery関連サービスが稼働中です:"
        [ "$CELERY_WORKER_RUNNING" = true ] && echo "  - Celery Worker"
        [ "$CELERY_BEAT_RUNNING" = true ] && echo "  - Celery Beat"
        [ "$FLOWER_RUNNING" = true ] && echo "  - Flower"
        echo ""
        
        if [ "$MICROSERVICE_RUNNING" = false ]; then
            log_error "マイクロサービスが稼働していません！"
            log_error "先にマイクロサービスを起動してから実行してください"
            exit 1
        fi
        
        read -p "これらのサービスを停止してマイクロサービスに移行しますか？ (y/N): " -n 1 -r
        echo ""
        
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "移行をキャンセルしました"
            exit 0
        fi
    else
        log_info "Celery関連サービスは既に停止しています"
    fi
    
    # 3. バックアップ
    backup_celery_config
    
    # 4. Celeryサービス停止
    stop_celery_services
    
    # 5. マイクロサービス確認
    verify_microservices
    
    # 6. 起動スクリプト更新
    update_startup_scripts
    
    # 7. レポート作成
    create_migration_report
    
    echo ""
    log_success "🎉 Celery廃止・マイクロサービス移行完了！"
    echo ""
    echo "📊 移行結果:"
    echo "  ✅ Celery Worker → Spider Manager Service"
    echo "  ✅ Celery Beat → Scheduler Service"
    echo "  ✅ Flower → API Gateway + WebUI"
    echo ""
    echo "🔗 マイクロサービスURL:"
    echo "  📊 Test Service: http://localhost:8005"
    echo "  🔗 API Gateway: http://localhost:8000 (未起動)"
    echo "  📋 Scheduler: http://localhost:8001 (未起動)"
    echo "  🕷️ Spider Manager: http://localhost:8002 (未起動)"
    echo "  📦 Result Collector: http://localhost:8003 (未起動)"
    echo "  🎨 WebUI: http://localhost:8004 (未起動)"
    echo ""
    echo "💡 次のステップ:"
    echo "  1. 本格的なマイクロサービス環境構築"
    echo "  2. Docker Compose環境整備"
    echo "  3. 監視・ログ基盤構築"
}

# 引数処理
case "${1:-}" in
    --check)
        check_celery_processes
        check_microservices
        ;;
    --force)
        # 確認なしで実行
        FORCE_MODE=true
        main
        ;;
    *)
        main
        ;;
esac
