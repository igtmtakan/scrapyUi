# ScrapyUI タイムゾーン設定ガイド

ScrapyUIでは、アプリケーション全体のタイムゾーンを統一管理し、日時の表示や処理を一貫して行うことができます。

## 🌍 タイムゾーン設定の概要

### 設定の優先順位

タイムゾーン設定は以下の優先順位で決定されます：

1. **コマンドライン引数** `--timezone` (最優先)
2. **環境変数** `SCRAPY_UI_TIMEZONE`
3. **default_settings.jsonの設定**
4. **デフォルト** (`Asia/Tokyo`)

### サポートするタイムゾーン

- **日本標準時**: `Asia/Tokyo`
- **協定世界時**: `UTC`
- **東部標準時**: `America/New_York`
- **太平洋標準時**: `America/Los_Angeles`
- **グリニッジ標準時**: `Europe/London`
- **中央ヨーロッパ時間**: `Europe/Paris`
- **中国標準時**: `Asia/Shanghai`
- **韓国標準時**: `Asia/Seoul`
- その他、pytzでサポートされる全タイムゾーン

## 🔧 設定方法

### 1. 設定ファイルでの設定

`backend/config/default_settings.json`でデフォルトタイムゾーンを設定：

```json
{
  "timezone": {
    "default": "Asia/Tokyo",
    "display_format": "%Y-%m-%d %H:%M:%S %Z",
    "available_timezones": [
      "Asia/Tokyo",
      "UTC",
      "America/New_York",
      "America/Los_Angeles",
      "Europe/London",
      "Europe/Paris",
      "Asia/Shanghai",
      "Asia/Seoul"
    ],
    "auto_detect": false
  }
}
```

### 2. コマンドライン引数での指定

```bash
# 日本標準時で起動
python scrapyui_cli.py --timezone Asia/Tokyo

# UTC時間で起動
python scrapyui_cli.py --timezone UTC

# 東部標準時で起動
python scrapyui_cli.py --timezone America/New_York

# 短縮形も使用可能
python scrapyui_cli.py --tz UTC
```

### 3. 環境変数での指定

```bash
# 環境変数で指定
export SCRAPY_UI_TIMEZONE=UTC
python scrapyui_cli.py

# 一時的に指定
SCRAPY_UI_TIMEZONE=Europe/London python scrapyui_cli.py
```

## 🎯 使用例

### 基本的な使用方法

```bash
# 設定確認
python scrapyui_cli.py --timezone Asia/Tokyo --check-config

# デバッグモードで起動
python scrapyui_cli.py --timezone UTC --debug --reload

# 本番環境で起動
SCRAPY_UI_TIMEZONE=Asia/Tokyo python scrapyui_cli.py --host 0.0.0.0 --port 80
```

### API経由での設定

```bash
# 現在のタイムゾーン情報を取得
curl http://localhost:8000/api/timezone/current

# 利用可能なタイムゾーン一覧を取得
curl http://localhost:8000/api/timezone/available

# タイムゾーンを設定（管理者のみ）
curl -X POST http://localhost:8000/api/timezone/set \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"timezone": "UTC"}'
```

## 📋 API エンドポイント

### タイムゾーン情報取得

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/timezone/current` | GET | 現在のタイムゾーン情報 |
| `/api/timezone/available` | GET | 利用可能なタイムゾーン一覧 |
| `/api/timezone/common` | GET | よく使用されるタイムゾーン |
| `/api/timezone/now` | GET | 現在時刻 |

### タイムゾーン設定（管理者のみ）

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/timezone/set` | POST | タイムゾーンを設定 |
| `/api/timezone/settings` | GET | タイムゾーン設定を取得 |
| `/api/timezone/settings` | PUT | タイムゾーン設定を更新 |

### ユーティリティ

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/timezone/convert` | POST | 日時変換 |
| `/api/timezone/validate/{timezone}` | GET | タイムゾーン検証 |
| `/api/timezone/search/{query}` | GET | タイムゾーン検索 |

## 🛠️ 便利なコマンド

### 設定確認

```bash
# 現在のタイムゾーン設定を確認
python scrapyui_cli.py --check-config

# 特定のタイムゾーンで確認
python scrapyui_cli.py --timezone UTC --check-config

# タイムゾーン情報をテスト
python -c "
from app.services.timezone_service import timezone_service
info = timezone_service.get_timezone_info()
print(f'タイムゾーン: {info[\"timezone\"]}')
print(f'現在時刻: {info[\"current_time\"]}')
"
```

### タイムゾーン変更

```bash
# 設定ファイルを直接編集
vim backend/config/default_settings.json

# 環境変数で一時的に変更
SCRAPY_UI_TIMEZONE=UTC python scrapyui_cli.py

# コマンドライン引数で変更
python scrapyui_cli.py --timezone Europe/London
```

## 📊 タイムゾーン設定の詳細

### 設定項目

| 項目 | 説明 | デフォルト値 |
|------|------|-------------|
| `default` | デフォルトタイムゾーン | `Asia/Tokyo` |
| `display_format` | 日時表示フォーマット | `%Y-%m-%d %H:%M:%S %Z` |
| `available_timezones` | 利用可能なタイムゾーン一覧 | 8つの主要タイムゾーン |
| `auto_detect` | 自動検出の有効/無効 | `false` |

### 表示フォーマット

```python
# デフォルト: 2024-12-07 15:30:45 JST
"%Y-%m-%d %H:%M:%S %Z"

# ISO形式: 2024-12-07T15:30:45+09:00
"%Y-%m-%dT%H:%M:%S%z"

# 日本語形式: 2024年12月07日 15時30分45秒
"%Y年%m月%d日 %H時%M分%S秒"
```

## 🚨 注意事項

### タイムゾーン変更時

- **既存データの時刻表示が変更されます**
- データベース内の時刻はUTCで保存されるため、データ自体は影響を受けません
- フロントエンドの表示が新しいタイムゾーンに更新されます

### サマータイム（夏時間）

- 自動的にサマータイムが適用されます
- `America/New_York`、`Europe/London`などで有効
- APIで現在のサマータイム状態を確認可能

### パフォーマンス

- タイムゾーン変換は軽量な処理です
- 大量のデータ処理時も性能に影響しません
- キャッシュ機能により高速な変換を実現

## 🔍 トラブルシューティング

### 無効なタイムゾーンエラー

```bash
# 利用可能なタイムゾーンを確認
python -c "import pytz; print(sorted(pytz.all_timezones)[:20])"

# タイムゾーンを検証
curl http://localhost:8000/api/timezone/validate/Asia/Tokyo
```

### 時刻表示の問題

```bash
# 現在の設定を確認
curl http://localhost:8000/api/timezone/current

# 時刻変換をテスト
curl -X POST http://localhost:8000/api/timezone/convert \
  -H "Content-Type: application/json" \
  -d '{"datetime_str": "2024-12-07 15:30:45", "to_timezone": "UTC"}'
```

### 設定が反映されない場合

```bash
# 環境変数を確認
echo $SCRAPY_UI_TIMEZONE

# 設定ファイルの構文確認
python -c "import json; print(json.load(open('backend/config/default_settings.json'))['timezone'])"

# ScrapyUIを再起動
./stop_servers.sh && ./start_servers.sh
```

これで、ScrapyUIのタイムゾーン設定を柔軟に管理できます！
