#!/bin/bash

# ScrapyUI 設定管理ユーティリティ
# 環境変数、ポート設定、サービス設定の統合管理

# 設定ファイルパス
ENV_FILE="backend/.env"
ENV_EXAMPLE="backend/.env.example"
ENV_PORTS=".env.ports"
CONFIG_BACKUP_DIR="config_backups"

# カラー設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

# 設定バックアップ
backup_config() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    mkdir -p "$CONFIG_BACKUP_DIR"
    
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$CONFIG_BACKUP_DIR/.env_$timestamp"
        log_success "設定をバックアップしました: $CONFIG_BACKUP_DIR/.env_$timestamp"
    fi
}

# 設定の初期化
init_config() {
    log_info "ScrapyUI設定を初期化中..."
    
    # バックアップ作成
    backup_config
    
    # .envファイルが存在しない場合は.env.exampleからコピー
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$ENV_EXAMPLE" ]; then
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            log_success ".env.exampleから.envを作成しました"
        else
            log_error ".env.exampleが見つかりません"
            return 1
        fi
    fi
    
    # ポート設定の統合
    if [ -f "$ENV_PORTS" ]; then
        log_info "ポート設定を統合中..."
        
        # .env.portsの内容を.envに追加/更新
        while IFS='=' read -r key value; do
            if [[ $key =~ ^[A-Z_]+$ ]] && [[ ! $key =~ ^# ]]; then
                if grep -q "^$key=" "$ENV_FILE"; then
                    # 既存の設定を更新
                    sed -i "s/^$key=.*/$key=$value/" "$ENV_FILE"
                    log_info "更新: $key=$value"
                else
                    # 新しい設定を追加
                    echo "$key=$value" >> "$ENV_FILE"
                    log_info "追加: $key=$value"
                fi
            fi
        done < "$ENV_PORTS"
        
        log_success "ポート設定を統合しました"
    fi
}

# 設定値の取得
get_config() {
    local key=$1
    if [ -f "$ENV_FILE" ]; then
        grep "^$key=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"'
    fi
}

# 設定値の設定
set_config() {
    local key=$1
    local value=$2
    
    if [ ! -f "$ENV_FILE" ]; then
        log_error ".envファイルが存在しません。init_configを実行してください。"
        return 1
    fi
    
    backup_config
    
    if grep -q "^$key=" "$ENV_FILE"; then
        sed -i "s/^$key=.*/$key=$value/" "$ENV_FILE"
        log_success "更新: $key=$value"
    else
        echo "$key=$value" >> "$ENV_FILE"
        log_success "追加: $key=$value"
    fi
}

# 設定の表示
show_config() {
    local category=${1:-all}
    
    if [ ! -f "$ENV_FILE" ]; then
        log_error ".envファイルが存在しません"
        return 1
    fi
    
    case $category in
        "ports")
            log_info "ポート設定:"
            grep -E "^(BACKEND_PORT|FRONTEND_PORT|NODEJS_PORT|FLOWER_PORT)=" "$ENV_FILE" || echo "ポート設定が見つかりません"
            ;;
        "database")
            log_info "データベース設定:"
            grep -E "^(DATABASE_|MYSQL_|POSTGRESQL_).*=" "$ENV_FILE" || echo "データベース設定が見つかりません"
            ;;
        "celery")
            log_info "Celery設定:"
            grep -E "^(CELERY_|FLOWER_|AUTO_START_).*=" "$ENV_FILE" || echo "Celery設定が見つかりません"
            ;;
        "security")
            log_info "セキュリティ設定:"
            grep -E "^(JWT_|SECRET_|CORS_|ALLOWED_).*=" "$ENV_FILE" || echo "セキュリティ設定が見つかりません"
            ;;
        "all"|*)
            log_info "全設定:"
            cat "$ENV_FILE"
            ;;
    esac
}

# 設定の検証
validate_config() {
    log_info "設定を検証中..."
    
    local errors=0
    
    # 必須設定のチェック
    local required_vars=("SECRET_KEY" "DATABASE_TYPE" "JWT_SECRET_KEY")
    
    for var in "${required_vars[@]}"; do
        local value=$(get_config "$var")
        if [ -z "$value" ] || [ "$value" = "your-secret-key-here" ] || [ "$value" = "your-jwt-secret-key" ]; then
            log_error "必須設定が未設定または初期値のままです: $var"
            ((errors++))
        fi
    done
    
    # ポート設定のチェック
    local port_vars=("BACKEND_PORT" "FRONTEND_PORT" "NODEJS_PORT" "FLOWER_PORT")
    
    for var in "${port_vars[@]}"; do
        local port=$(get_config "$var")
        if [ -n "$port" ]; then
            if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1024 ] || [ "$port" -gt 65535 ]; then
                log_error "無効なポート番号: $var=$port"
                ((errors++))
            fi
        fi
    done
    
    # データベース設定のチェック
    local db_type=$(get_config "DATABASE_TYPE")
    if [ "$db_type" = "mysql" ]; then
        local required_db_vars=("DATABASE_HOST" "DATABASE_NAME" "DATABASE_USER" "DATABASE_PASSWORD")
        for var in "${required_db_vars[@]}"; do
            local value=$(get_config "$var")
            if [ -z "$value" ]; then
                log_error "MySQL設定が不完全です: $var"
                ((errors++))
            fi
        done
    fi
    
    if [ $errors -eq 0 ]; then
        log_success "設定検証が完了しました。エラーはありません。"
        return 0
    else
        log_error "設定検証で $errors 個のエラーが見つかりました。"
        return 1
    fi
}

# 設定のリセット
reset_config() {
    local category=${1:-all}
    
    log_warn "設定をリセットします: $category"
    read -p "続行しますか? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "キャンセルしました"
        return 0
    fi
    
    backup_config
    
    case $category in
        "ports")
            sed -i '/^.*_PORT=/d' "$ENV_FILE"
            log_success "ポート設定をリセットしました"
            ;;
        "all")
            if [ -f "$ENV_EXAMPLE" ]; then
                cp "$ENV_EXAMPLE" "$ENV_FILE"
                log_success "全設定を初期値にリセットしました"
            else
                log_error ".env.exampleが見つかりません"
                return 1
            fi
            ;;
        *)
            log_error "不明なカテゴリ: $category"
            return 1
            ;;
    esac
}

# ヘルプ表示
show_help() {
    echo "ScrapyUI 設定管理ユーティリティ"
    echo ""
    echo "使用方法:"
    echo "  $0 [コマンド] [オプション]"
    echo ""
    echo "コマンド:"
    echo "  init                    - 設定の初期化"
    echo "  show [category]         - 設定の表示"
    echo "  set <key> <value>       - 設定値の変更"
    echo "  get <key>               - 設定値の取得"
    echo "  validate                - 設定の検証"
    echo "  reset [category]        - 設定のリセット"
    echo "  backup                  - 設定のバックアップ"
    echo ""
    echo "カテゴリ:"
    echo "  all, ports, database, celery, security"
    echo ""
    echo "例:"
    echo "  $0 init                           # 設定初期化"
    echo "  $0 show ports                     # ポート設定表示"
    echo "  $0 set FLOWER_PORT 5557           # Flowerポート変更"
    echo "  $0 validate                       # 設定検証"
    echo "  $0 reset ports                    # ポート設定リセット"
}

# メイン処理
main() {
    case "${1:-help}" in
        "init")
            init_config
            ;;
        "show")
            show_config "$2"
            ;;
        "set")
            if [ $# -lt 3 ]; then
                log_error "使用方法: $0 set <key> <value>"
                exit 1
            fi
            set_config "$2" "$3"
            ;;
        "get")
            if [ $# -lt 2 ]; then
                log_error "使用方法: $0 get <key>"
                exit 1
            fi
            get_config "$2"
            ;;
        "validate")
            validate_config
            ;;
        "reset")
            reset_config "$2"
            ;;
        "backup")
            backup_config
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

main "$@"
