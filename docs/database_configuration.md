# ScrapyUI データベース設定ガイド

ScrapyUIでは、SQLite、MySQL、PostgreSQLなど複数のデータベースをサポートしており、柔軟な設定方法を提供しています。

## 📊 設定の優先順位

データベース設定は以下の優先順位で決定されます：

1. **コマンドライン引数** `--database` (最優先)
2. **環境変数** `SCRAPY_UI_DATABASE`
3. **database.yamlの`usedatabase`設定**
4. **デフォルト** (`default`)

## 🔧 設定方法

### 1. database.yamlでの設定

`backend/config/database.yaml`ファイルで使用するデータベース環境を指定：

```yaml
# 使用するデータベース環境を指定
usedatabase: development

# デフォルト設定: SQLite
default:
  type: "sqlite"
  database: "backend/database/scrapy_ui.db"
  echo: false

# 開発環境設定
development:
  type: "sqlite"
  database: "backend/database/scrapy_ui_dev.db"
  echo: true

# 本番環境設定: MySQL
production:
  type: "mysql"
  host: "localhost"
  port: 3306
  database: "scrapy_ui_prod"
  username: "scrapy_user"
  password: "secure_password"
  charset: "utf8mb4"
  pool_size: 15
  max_overflow: 30
```

### 2. コマンドライン引数での指定

```bash
# development環境を使用
python scrapyui_cli.py --database development

# MySQL本番環境を使用
python scrapyui_cli.py --database production --port 8080

# カスタム設定ファイルを使用
python scrapyui_cli.py -c custom_database.yaml --database mysql_prod
```

### 3. 環境変数での指定

```bash
# 環境変数で指定
export SCRAPY_UI_DATABASE=production
python scrapyui_cli.py

# 一時的に指定
SCRAPY_UI_DATABASE=testing python scrapyui_cli.py
```

## 🎯 使用例

### SQLiteからMySQLに切り替え

#### ステップ1: MySQLサーバーの準備
```bash
# MySQLにログイン
mysql -u root -p

# データベースとユーザーを作成
CREATE DATABASE scrapy_ui CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'scrapy_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON scrapy_ui.* TO 'scrapy_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### ステップ2: ScrapyUIの設定変更
```bash
# 自動切り替えスクリプトを使用（推奨）
python scripts/switch_database.py --db mysql --user scrapy_user --password your_secure_password

# または手動でdatabase.yamlを編集
# usedatabase: mysql_production
```

#### ステップ3: 設定確認
```bash
# 設定を確認
python scrapyui_cli.py --check-config

# MySQLで起動
python scrapyui_cli.py --database mysql_production
```

### 複数環境での運用

```bash
# 開発環境（SQLite）
python scrapyui_cli.py --database development --debug --reload

# ステージング環境（MySQL）
python scrapyui_cli.py --database staging --host 0.0.0.0 --port 8080

# 本番環境（PostgreSQL）
SCRAPY_UI_DATABASE=production python scrapyui_cli.py --host 0.0.0.0 --port 80
```

## 🛠️ 便利なコマンド

### 設定確認
```bash
# 現在の設定を確認
python scrapyui_cli.py --check-config

# 特定の環境設定を確認
python scrapyui_cli.py --database production --check-config

# データベース接続テスト
python scripts/check_database.py
```

### データベース切り替え
```bash
# SQLiteに切り替え
python scripts/switch_database.py --db sqlite

# MySQLに切り替え
python scripts/switch_database.py --db mysql --host localhost --user scrapy_user --password your_password

# PostgreSQLに切り替え
python scripts/switch_database.py --db postgresql --host localhost --user scrapy_user --password your_password
```

### ヘルプ表示
```bash
# コマンドライン引数のヘルプ
python scrapyui_cli.py --help

# データベース切り替えスクリプトのヘルプ
python scripts/switch_database.py --help
```

## 📋 サポートするデータベース

| データベース | タイプ | 用途 | 設定例 |
|-------------|--------|------|--------|
| SQLite | `sqlite` | 開発・小規模 | `database: "backend/database/scrapy_ui.db"` |
| MySQL | `mysql` | 本番・大規模 | `host: localhost, port: 3306` |
| PostgreSQL | `postgresql` | 本番・高性能 | `host: localhost, port: 5432` |
| MongoDB | `mongodb` | NoSQL | `host: localhost, port: 27017` |
| Elasticsearch | `elasticsearch` | 検索・分析 | `hosts: ["localhost:9200"]` |
| Redis | `redis` | キャッシュ | `host: localhost, port: 6379` |

## 🚨 注意事項

### データベース切り替え時
- **既存データは自動移行されません**
- 切り替え前にデータのバックアップを取ってください
- テーブル構造は自動で作成されます

### 必要な依存関係
```bash
# MySQL
pip install pymysql

# PostgreSQL
pip install psycopg2-binary

# MongoDB
pip install pymongo

# Elasticsearch
pip install elasticsearch

# Redis
pip install redis
```

### パフォーマンス考慮
- **SQLite**: 小〜中規模、開発環境に最適
- **MySQL/PostgreSQL**: 大規模、本番環境に推奨
- **接続プール設定**: `pool_size`, `max_overflow`で調整

## 🔍 トラブルシューティング

### 接続エラーの場合
```bash
# 設定確認
python scrapyui_cli.py --check-config

# データベース接続テスト
python scripts/check_database.py

# ログレベルを上げて詳細確認
python scrapyui_cli.py --database production --log-level DEBUG
```

### 設定ファイルエラーの場合
```bash
# 設定ファイルの構文確認
python -c "import yaml; print(yaml.safe_load(open('backend/config/database.yaml')))"

# デフォルト設定で起動
python scrapyui_cli.py --database default
```

これで、ScrapyUIのデータベース設定を柔軟に管理できます！
