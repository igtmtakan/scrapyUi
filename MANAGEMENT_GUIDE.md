# 🛠️ ScrapyUI 管理ガイド

ScrapyUIの包括的な管理システムの使用方法を説明します。

## 📋 **概要**

ScrapyUIには以下の管理ツールが統合されています：

- **統合管理システム** (`scrapyui_manager.sh`) - メインインターフェース
- **ポート管理システム** (`port_manager.sh`) - ポート競合の検出・解決
- **設定管理システム** (`config_manager.sh`) - 環境変数・設定の管理
- **サービス監視システム** (`service_monitor.sh`) - 自動復旧・監視

## 🚀 **クイックスタート**

### **初回起動（推奨）**
```bash
./scrapyui_manager.sh quick-start
```

このコマンドは以下を自動実行します：
1. 依存関係チェック
2. 設定初期化
3. ポート競合解決
4. サーバー起動

### **通常の起動・停止**
```bash
# 起動
./scrapyui_manager.sh start

# 停止
./scrapyui_manager.sh stop

# 再起動
./scrapyui_manager.sh restart

# 完全停止（全プロセス強制終了）
./scrapyui_manager.sh full-stop
```

## 🔧 **ポート管理**

### **ポート状態確認**
```bash
./scrapyui_manager.sh ports check
```

### **ポート競合解決**
```bash
./scrapyui_manager.sh ports resolve
```

### **ポート強制クリア**
```bash
./scrapyui_manager.sh ports clear
```

### **ポート範囲スキャン**
```bash
./scrapyui_manager.sh ports scan 8000 8010
```

## ⚙️ **設定管理**

### **設定初期化**
```bash
./scrapyui_manager.sh config init
```

### **設定表示**
```bash
# 全設定表示
./scrapyui_manager.sh config show

# カテゴリ別表示
./scrapyui_manager.sh config show ports
./scrapyui_manager.sh config show database
./scrapyui_manager.sh config show celery
./scrapyui_manager.sh config show security
```

### **設定変更**
```bash
# 個別設定変更
./scrapyui_manager.sh config set FLOWER_PORT 5557
./scrapyui_manager.sh config set DATABASE_TYPE mysql

# 設定値取得
./scrapyui_manager.sh config get FLOWER_PORT
```

### **設定検証**
```bash
./scrapyui_manager.sh config validate
```

### **設定リセット**
```bash
# ポート設定のみリセット
./scrapyui_manager.sh config reset ports

# 全設定リセット
./scrapyui_manager.sh config reset all
```

## 📊 **監視・診断**

### **システム状態確認**
```bash
./scrapyui_manager.sh status
```

### **継続的監視開始**
```bash
./scrapyui_manager.sh monitor
```

### **システム診断**
```bash
./scrapyui_manager.sh diagnosis
```

## 🔒 **メンテナンスモード**

### **メンテナンスモード有効化**
```bash
./scrapyui_manager.sh maintenance enable
```

### **メンテナンスモード無効化**
```bash
./scrapyui_manager.sh maintenance disable
```

### **メンテナンスモード状態確認**
```bash
./scrapyui_manager.sh maintenance status
```

## 🌐 **環境変数設定**

### **ポート設定**
```bash
export BACKEND_PORT=8001
export FRONTEND_PORT=4001
export NODEJS_PORT=3002
export FLOWER_PORT=5557
```

### **Flower設定**
```bash
export FLOWER_MODE=standalone    # all, embedded, api, standalone
export AUTO_START_FLOWER=true
```

### **データベース設定**
```bash
export DATABASE_TYPE=mysql
export DATABASE_HOST=localhost
export DATABASE_NAME=scrapy_ui
export DATABASE_USER=scrapy_user
export DATABASE_PASSWORD=your_password
```

## 🔄 **自動復旧機能**

サービス監視システムは以下の機能を提供します：

- **自動健全性チェック** - 30秒間隔でサービス状態を監視
- **自動復旧** - 問題検出時の自動再起動
- **Redis自動起動** - Redis停止時の自動起動
- **包括的ログ** - 全ての監視・復旧活動をログ記録

## 📁 **ファイル構成**

```
scrapyUI/
├── scrapyui_manager.sh      # 統合管理システム
├── port_manager.sh          # ポート管理
├── config_manager.sh        # 設定管理
├── service_monitor.sh       # サービス監視
├── start_servers.sh         # サーバー起動
├── stop_servers.sh          # サーバー停止
├── .env.ports              # 自動生成ポート設定
├── config_backups/         # 設定バックアップ
└── logs/                   # ログファイル
    ├── service_monitor.log
    └── ...
```

## 🚨 **トラブルシューティング**

### **ポート競合エラー**
```bash
# 1. ポート状態確認
./scrapyui_manager.sh ports check

# 2. 競合解決
./scrapyui_manager.sh ports resolve

# 3. 強制クリア（必要に応じて）
./scrapyui_manager.sh ports clear
```

### **設定エラー**
```bash
# 1. 設定検証
./scrapyui_manager.sh config validate

# 2. 設定初期化
./scrapyui_manager.sh config init

# 3. 設定リセット（必要に応じて）
./scrapyui_manager.sh config reset all
```

### **サービス起動失敗**
```bash
# 1. システム診断
./scrapyui_manager.sh diagnosis

# 2. 依存関係確認
# Ubuntu/Debian:
sudo apt update && sudo apt install curl jq lsof redis-server python3 python3-pip nodejs npm

# 3. 完全停止後に再起動
./scrapyui_manager.sh full-stop
./scrapyui_manager.sh quick-start
```

### **Redis接続エラー**
```bash
# Redis起動確認
redis-cli ping

# Redis手動起動
redis-server --daemonize yes
```

## 📝 **ベストプラクティス**

1. **初回起動時は必ずクイックスタートを使用**
   ```bash
   ./scrapyui_manager.sh quick-start
   ```

2. **定期的な設定バックアップ**
   ```bash
   ./scrapyui_manager.sh config backup
   ```

3. **継続的監視の活用**
   ```bash
   # バックグラウンドで監視開始
   nohup ./scrapyui_manager.sh monitor > /dev/null 2>&1 &
   ```

4. **メンテナンス時の適切な手順**
   ```bash
   # メンテナンス開始
   ./scrapyui_manager.sh maintenance enable
   
   # 作業実行
   # ...
   
   # メンテナンス終了
   ./scrapyui_manager.sh maintenance disable
   ./scrapyui_manager.sh start
   ```

## 🔗 **関連ドキュメント**

- [FLOWER_INTEGRATION.md](FLOWER_INTEGRATION.md) - Flower統合ガイド
- [README.md](README.md) - 基本的な使用方法
- [backend/.env.example](backend/.env.example) - 環境変数設定例

## 📞 **サポート**

問題が発生した場合は、以下の情報を収集してください：

```bash
# システム診断情報
./scrapyui_manager.sh diagnosis > diagnosis_report.txt

# ログファイル
tar -czf logs_backup.tar.gz logs/

# 設定ファイル
cp backend/.env config_current.env
```
