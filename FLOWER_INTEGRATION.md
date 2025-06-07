# 🌸 Flower統合ガイド

ScrapyUIにFlower監視システムが統合されました。3つのオプションから選択して、Celeryタスクの包括的な監視が可能です。

## 📋 **統合オプション**

### **Option 1: 埋め込みFlower**
- ScrapyUIバックエンド内でFlowerを直接実行
- 最も軽量で統合された監視
- 内部APIを使用した高速データアクセス

### **Option 2: Flower API利用**
- 外部で起動されたFlowerのAPIを利用
- 既存のFlower環境との連携
- RESTful APIによる柔軟なデータ取得

### **Option 3: スタンドアロンFlower**
- 独立したFlowerプロセスとして起動
- 完全なFlower Web UIアクセス
- 最も包括的な監視機能

## 🚀 **起動方法**

### **自動起動（推奨）**
```bash
# デフォルト設定で全オプション有効
./start_servers.sh

# 特定のFlowerモードを指定
FLOWER_MODE=standalone ./start_servers.sh
FLOWER_MODE=embedded ./start_servers.sh
FLOWER_MODE=api ./start_servers.sh
```

### **環境変数設定**
```bash
# Flower自動起動の制御
export AUTO_START_FLOWER=true    # true/false

# Flowerモードの選択
export FLOWER_MODE=all           # all/standalone/embedded/api

# Flower設定
export FLOWER_PORT=5555
export FLOWER_HOST=127.0.0.1
```

### **手動起動**
```bash
# バックエンドのみ起動（埋め込みFlower含む）
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# スタンドアロンFlowerを手動起動
cd backend
FLOWER_UNAUTHENTICATED_API=true python3 -m celery -A app.celery_app flower \
    --port=5555 \
    --address=127.0.0.1 \
    --url_prefix=/flower \
    --persistent=True \
    --enable_events
```

## 🌐 **アクセス方法**

### **ScrapyUI統合ダッシュボード**
- **URL**: http://localhost:4000/flower
- **機能**: 
  - 統合Flowerダッシュボード
  - サービス状態管理
  - 統計表示とリアルタイム更新

### **Flower Web UI（スタンドアロンモード）**
- **URL**: http://localhost:5555/flower
- **機能**:
  - 完全なFlower Web インターフェース
  - タスク詳細表示
  - ワーカー管理
  - リアルタイム監視

### **API エンドポイント**
```bash
# 統計取得
curl http://localhost:8000/api/flower/stats

# ダッシュボード統計
curl http://localhost:8000/api/flower/dashboard

# サービス状態確認
curl http://localhost:8000/api/flower/services/status

# ヘルスチェック
curl http://localhost:8000/api/flower/health
```

## 📊 **機能一覧**

### **統計監視**
- ✅ 総タスク数
- ✅ 待機中タスク数
- ✅ 実行中タスク数
- ✅ 成功タスク数
- ✅ 失敗タスク数
- ✅ 取り消しタスク数
- ✅ ワーカー統計（総数/アクティブ/オフライン）

### **サービス管理**
- ✅ 全Flowerサービスの起動/停止
- ✅ サービス状態のリアルタイム監視
- ✅ 自動フェイルオーバー（最適なソース選択）

### **統合機能**
- ✅ 既存ダッシュボードの統計置き換え
- ✅ リアルタイム自動更新（30秒間隔）
- ✅ エラー時のフォールバック機能

## 🔧 **設定ファイル**

### **backend/.env**
```env
# Celery設定
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Flower設定
AUTO_START_FLOWER=true
FLOWER_MODE=all
FLOWER_PORT=5556
FLOWER_HOST=127.0.0.1
FLOWER_UNAUTHENTICATED_API=true
```

### **start_servers.sh設定**
```bash
# ポート設定
BACKEND_PORT=8000
FRONTEND_PORT=4000
NODEJS_PORT=3001
FLOWER_PORT=5556

# Flower設定
FLOWER_MODE=${FLOWER_MODE:-"all"}
AUTO_START_FLOWER=${AUTO_START_FLOWER:-"true"}
```

## 🛠️ **トラブルシューティング**

### **Flowerが起動しない場合**
```bash
# 1. 依存関係の確認
pip install flower==2.0.1

# 2. Celeryアプリケーションの確認
cd backend
python3 -c "from app.celery_app import celery_app; print('Celery OK')"

# 3. 手動起動テスト
FLOWER_UNAUTHENTICATED_API=true python3 -m celery -A app.celery_app flower --port=5556
```

### **API接続エラーの場合**
```bash
# 1. Flowerプロセス確認
ps aux | grep flower

# 2. ポート確認
lsof -i:5556

# 3. API接続テスト
curl http://localhost:5555/flower/api/workers
```

### **統計が表示されない場合**
```bash
# 1. Celeryワーカー起動確認
ps aux | grep "celery.*worker"

# 2. Redis接続確認
redis-cli ping

# 3. バックエンドログ確認
tail -f backend/logs/app.log
```

## 📈 **パフォーマンス最適化**

### **推奨設定**
- **小規模環境**: `FLOWER_MODE=embedded`
- **中規模環境**: `FLOWER_MODE=standalone`
- **大規模環境**: `FLOWER_MODE=api` + 外部Flower

### **メモリ使用量**
- **埋め込み**: +50MB
- **スタンドアロン**: +100MB
- **API**: +10MB（外部Flower除く）

## 🔄 **アップグレード**

### **既存環境からの移行**
1. 既存のFlowerプロセスを停止
2. 新しいstart_servers.shを実行
3. 統計データの自動移行確認

### **設定の変更**
```bash
# 実行時にモード変更
FLOWER_MODE=standalone ./start_servers.sh

# 永続的な変更
echo "export FLOWER_MODE=standalone" >> ~/.bashrc
```

## 🎯 **ベストプラクティス**

1. **本番環境**: `FLOWER_MODE=standalone` を推奨
2. **開発環境**: `FLOWER_MODE=all` で全機能テスト
3. **CI/CD**: `AUTO_START_FLOWER=false` で無効化
4. **監視**: `/api/flower/health` でヘルスチェック
5. **ログ**: Flowerログを定期的に確認

## 📞 **サポート**

問題が発生した場合：
1. ログファイルを確認
2. ヘルスチェックAPIを実行
3. プロセス状態を確認
4. 設定ファイルを検証

---

**🎉 Flower統合により、ScrapyUIでCeleryタスクの包括的な監視が可能になりました！**
