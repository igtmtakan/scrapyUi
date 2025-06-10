# ScrapyUI マイクロサービス アーキテクチャ

## 🏗️ サービス構成 (pyspider inspired)

### Core Services

#### 1. **Scheduler Service** (Port: 8001)
```
責務: スケジュール管理・タスク配信
- Cron式スケジュール管理
- タスクキューへの配信
- 実行状態監視
- 負荷分散
```

#### 2. **Spider Manager Service** (Port: 8002)  
```
責務: スパイダー実行・プロセス管理
- Scrapyプロセス起動
- 実行監視・ログ収集
- リソース管理
- 異常検知・復旧
```

#### 3. **Result Collector Service** (Port: 8003)
```
責務: 結果収集・データ処理
- JSONLファイル監視
- データベース保存
- 重複除去
- 統計情報生成
```

#### 4. **WebUI Service** (Port: 8004)
```
責務: ユーザーインターフェース
- プロジェクト管理
- スケジュール設定
- 実行監視
- 結果表示
```

#### 5. **API Gateway** (Port: 8000)
```
責務: 統一エンドポイント・認証
- リクエストルーティング
- 認証・認可
- レート制限
- ログ集約
```

### Support Services

#### 6. **Message Queue Service** (Port: 6379)
```
Redis/RabbitMQ
- サービス間通信
- タスクキュー
- 状態共有
- イベント配信
```

#### 7. **Database Service** (Port: 3306)
```
MySQL/PostgreSQL
- メタデータ保存
- 結果データ保存
- ユーザー情報
- 設定情報
```

#### 8. **File Storage Service** (Port: 9000)
```
MinIO/S3
- スパイダーファイル保存
- 結果ファイル保存
- ログファイル保存
- バックアップ
```

## 🔄 データフロー

```
1. WebUI → API Gateway → Scheduler Service
2. Scheduler Service → Message Queue → Spider Manager
3. Spider Manager → Scrapy Process → Result Files
4. Result Collector → File Monitor → Database
5. WebUI → API Gateway → Result Collector → Display
```

## 📡 通信プロトコル

### Inter-Service Communication
- **HTTP/REST**: 同期通信
- **Message Queue**: 非同期通信  
- **WebSocket**: リアルタイム通信
- **gRPC**: 高性能通信（オプション）

### Message Format
```json
{
  "service": "scheduler",
  "action": "execute_spider",
  "payload": {
    "schedule_id": "uuid",
    "project_id": "uuid", 
    "spider_id": "uuid",
    "settings": {}
  },
  "timestamp": "2025-06-10T03:32:00Z",
  "correlation_id": "uuid"
}
```

## 🛡️ 障害対応

### Service Discovery
- **Consul/etcd**: サービス登録・発見
- **Health Check**: 定期的ヘルスチェック
- **Circuit Breaker**: 障害時の迂回

### Monitoring
- **Prometheus**: メトリクス収集
- **Grafana**: 可視化
- **Jaeger**: 分散トレーシング
- **ELK Stack**: ログ集約

## 🚀 デプロイメント

### Container Strategy
```yaml
# docker-compose.yml
version: '3.8'
services:
  api-gateway:
    image: scrapyui/api-gateway:latest
    ports: ["8000:8000"]
    
  scheduler:
    image: scrapyui/scheduler:latest
    ports: ["8001:8001"]
    
  spider-manager:
    image: scrapyui/spider-manager:latest
    ports: ["8002:8002"]
    
  result-collector:
    image: scrapyui/result-collector:latest
    ports: ["8003:8003"]
    
  webui:
    image: scrapyui/webui:latest
    ports: ["8004:8004"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scheduler-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: scheduler
  template:
    metadata:
      labels:
        app: scheduler
    spec:
      containers:
      - name: scheduler
        image: scrapyui/scheduler:latest
        ports:
        - containerPort: 8001
        env:
        - name: REDIS_URL
          value: "redis://redis:6379"
        - name: DATABASE_URL
          value: "mysql://user:pass@mysql:3306/scrapyui"
```

## 📊 スケーラビリティ

### Horizontal Scaling
- **Scheduler**: 複数インスタンス（リーダー選出）
- **Spider Manager**: 複数インスタンス（負荷分散）
- **Result Collector**: 複数インスタンス（パーティション）
- **WebUI**: 複数インスタンス（ロードバランサー）

### Vertical Scaling
- **CPU**: 計算集約的サービス
- **Memory**: データ処理サービス
- **Storage**: ファイル保存サービス
- **Network**: 通信集約的サービス

## 🔧 開発・運用

### Development
- **Service Template**: 統一開発テンプレート
- **API Contract**: OpenAPI仕様
- **Testing**: 単体・統合・E2Eテスト
- **CI/CD**: 自動ビルド・デプロイ

### Operations
- **Configuration**: 環境変数・設定ファイル
- **Secrets**: 機密情報管理
- **Backup**: データ・設定バックアップ
- **Disaster Recovery**: 障害復旧手順
