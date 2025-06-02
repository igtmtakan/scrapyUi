# ScrapyUI 認証設定ガイド

ScrapyUIの認証システムでは、JWTトークンベースの認証を使用しており、アクセストークンとリフレッシュトークンの有効期限を柔軟に設定できます。

## 🔑 認証設定の概要

### 設定の優先順位

認証設定は以下の優先順位で決定されます：

1. **コマンドライン引数** (最優先)
2. **環境変数**
3. **設定ファイル** (`default_settings.json`)
4. **デフォルト値**

### デフォルト設定

- **アクセストークン有効期限**: 360分（6時間）
- **リフレッシュトークン有効期限**: 7日
- **暗号化アルゴリズム**: HS256
- **パスワードハッシュ**: bcrypt + argon2

## ⚙️ 設定方法

### 1️⃣ **設定ファイルでの設定**

`backend/config/default_settings.json`で認証設定を管理：

```json
{
  "auth": {
    "access_token_expire_minutes": 360,
    "refresh_token_expire_days": 7,
    "secret_key_env": "SECRET_KEY",
    "algorithm": "HS256",
    "password_hash_schemes": ["bcrypt", "argon2"],
    "bcrypt_rounds": 12,
    "session_timeout_minutes": 360,
    "auto_refresh_threshold_minutes": 30
  }
}
```

### 2️⃣ **コマンドライン引数での指定**

```bash
# アクセストークンを12時間に設定
python scrapyui_cli.py --token-expire-minutes 720

# リフレッシュトークンを14日に設定
python scrapyui_cli.py --refresh-token-expire-days 14

# 両方を同時に設定
python scrapyui_cli.py --token-expire-minutes 480 --refresh-token-expire-days 30

# 設定確認
python scrapyui_cli.py --token-expire-minutes 360 --check-config
```

### 3️⃣ **環境変数での指定**

```bash
# 環境変数で設定
export ACCESS_TOKEN_EXPIRE_MINUTES=720  # 12時間
export REFRESH_TOKEN_EXPIRE_DAYS=14     # 14日
export SECRET_KEY="your-super-secret-key-here"

# 一時的に指定
ACCESS_TOKEN_EXPIRE_MINUTES=480 python scrapyui_cli.py
```

## 🎯 使用例

### 基本的な使用方法

```bash
# 標準設定（6時間）で起動
python scrapyui_cli.py

# 12時間のアクセストークンで起動
python scrapyui_cli.py --token-expire-minutes 720

# 本番環境用（24時間アクセス、30日リフレッシュ）
python scrapyui_cli.py --token-expire-minutes 1440 --refresh-token-expire-days 30

# 開発環境用（短い有効期限でテスト）
python scrapyui_cli.py --token-expire-minutes 60 --refresh-token-expire-days 1
```

### セキュリティレベル別設定

#### 🔒 **高セキュリティ環境**
```bash
# 短い有効期限でセキュリティを強化
python scrapyui_cli.py --token-expire-minutes 60 --refresh-token-expire-days 1
```

#### ⚖️ **バランス型（推奨）**
```bash
# デフォルト設定（6時間アクセス、7日リフレッシュ）
python scrapyui_cli.py --token-expire-minutes 360 --refresh-token-expire-days 7
```

#### 🔓 **利便性重視**
```bash
# 長い有効期限で利便性を向上
python scrapyui_cli.py --token-expire-minutes 1440 --refresh-token-expire-days 30
```

## 📋 API エンドポイント

### 認証設定情報取得

```bash
# 現在の認証設定を確認
curl http://localhost:8000/api/auth/settings
```

**レスポンス例:**
```json
{
  "access_token_expire_minutes": 360,
  "refresh_token_expire_days": 7,
  "access_token_expire_hours": 6.0,
  "session_timeout_minutes": 360,
  "auto_refresh_threshold_minutes": 30,
  "algorithm": "HS256",
  "password_hash_schemes": ["bcrypt", "argon2"]
}
```

### トークン関連API

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/auth/login` | POST | ログイン（トークン取得） |
| `/api/auth/refresh` | POST | トークンリフレッシュ |
| `/api/auth/logout` | POST | ログアウト |
| `/api/auth/me` | GET | 現在のユーザー情報 |
| `/api/auth/settings` | GET | 認証設定情報 |

## 🛠️ 便利なコマンド

### 設定確認

```bash
# 現在の設定を確認
python scrapyui_cli.py --check-config

# 特定の設定で確認
python scrapyui_cli.py --token-expire-minutes 720 --check-config

# 環境変数込みで確認
ACCESS_TOKEN_EXPIRE_MINUTES=480 python scrapyui_cli.py --check-config
```

### 設定テスト

```bash
# 認証設定をテスト
python -c "
from app.auth.jwt_handler import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
print(f'アクセストークン: {ACCESS_TOKEN_EXPIRE_MINUTES}分')
print(f'リフレッシュトークン: {REFRESH_TOKEN_EXPIRE_DAYS}日')
"

# API経由で設定確認
curl http://localhost:8000/api/auth/settings | jq
```

## 📊 設定項目詳細

### 認証設定項目

| 項目 | 説明 | デフォルト値 | 推奨範囲 |
|------|------|-------------|----------|
| `access_token_expire_minutes` | アクセストークン有効期限（分） | 360 | 60-1440 |
| `refresh_token_expire_days` | リフレッシュトークン有効期限（日） | 7 | 1-30 |
| `session_timeout_minutes` | セッションタイムアウト（分） | 360 | 60-1440 |
| `auto_refresh_threshold_minutes` | 自動リフレッシュ閾値（分） | 30 | 5-60 |
| `algorithm` | JWT暗号化アルゴリズム | HS256 | HS256/RS256 |
| `bcrypt_rounds` | bcryptラウンド数 | 12 | 10-15 |

### 時間換算表

| 分 | 時間 | 用途 |
|----|------|------|
| 60 | 1時間 | 高セキュリティ |
| 180 | 3時間 | 短時間作業 |
| 360 | 6時間 | 標準（推奨） |
| 480 | 8時間 | 業務時間 |
| 720 | 12時間 | 長時間作業 |
| 1440 | 24時間 | 最大推奨 |

## 🚨 セキュリティ考慮事項

### ⚠️ 注意点

1. **SECRET_KEY**: 本番環境では必ず強力なシークレットキーを設定
2. **有効期限**: セキュリティと利便性のバランスを考慮
3. **HTTPS**: 本番環境では必ずHTTPS通信を使用
4. **ログ**: 認証ログを適切に監視

### 🔐 推奨設定

#### 開発環境
```bash
python scrapyui_cli.py --token-expire-minutes 480 --refresh-token-expire-days 7
```

#### ステージング環境
```bash
python scrapyui_cli.py --token-expire-minutes 360 --refresh-token-expire-days 7
```

#### 本番環境
```bash
SECRET_KEY="your-production-secret-key" \
python scrapyui_cli.py --token-expire-minutes 360 --refresh-token-expire-days 7
```

## 🔍 トラブルシューティング

### よくある問題

#### トークンが期限切れになる
```bash
# 有効期限を延長
python scrapyui_cli.py --token-expire-minutes 720
```

#### 設定が反映されない
```bash
# 環境変数を確認
echo $ACCESS_TOKEN_EXPIRE_MINUTES

# 設定ファイルを確認
cat backend/config/default_settings.json | jq .auth

# サーバーを再起動
./stop_servers.sh && ./start_servers.sh
```

#### 認証エラーが発生する
```bash
# 現在の設定を確認
curl http://localhost:8000/api/auth/settings

# ログを確認
tail -f logs/scrapyui.log
```

これで、ScrapyUIの認証トークンを6時間に設定し、柔軟な設定管理システムが完成しました！🔑
