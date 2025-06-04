# ScrapyUI Database Directory

このディレクトリには、ScrapyUIの**統一SQLiteデータベースファイル**が格納されます。

## 📁 ディレクトリ構造

```
backend/database/
├── README.md           # このファイル
├── scrapy_ui.db       # 統一メインデータベース（SQLite）
└── backups/           # バックアップファイル（オプション）
```

## 🔄 データベース統一について

**2025年6月4日より、すべてのデータベースアクセスが統一されました：**

- **統一ファイル**: `backend/database/scrapy_ui.db`
- **設定管理**: `backend/config/database.yaml`の`development`環境を使用
- **自動検出**: アプリケーション全体で統一設定から自動的にパスを取得

## 🗄️ データベースファイル

### `scrapy_ui.db`
- **用途**: ScrapyUIのメインデータベース
- **形式**: SQLite 3
- **内容**: 
  - ユーザー情報（users）
  - プロジェクト情報（projects）
  - スパイダー定義（spiders）
  - タスク実行履歴（tasks）
  - スクレイピング結果（results）
  - スケジュール設定（schedules）
  - 通知履歴（notifications）
  - その他のアプリケーションデータ

## 🔧 設定

### データベースパス設定
以下の設定ファイルでデータベースパスが定義されています：

1. **`backend/app/config/database_config.py`**
   ```python
   db_path = os.path.join(backend_dir, "database", "scrapy_ui.db")
   ```

2. **`backend/config/database.yaml`**
   ```yaml
   default:
     type: "sqlite"
     database: "/path/to/backend/database/scrapy_ui.db"
   ```

3. **`backend/.env.example`**
   ```env
   DATABASE_TYPE=sqlite
   DATABASE_NAME=/path/to/backend/database/scrapy_ui.db
   ```

## 🔒 セキュリティ

### .gitignore設定
データベースファイルはGitリポジトリから除外されています：

```gitignore
# Database files
backend/database/*.db
backend/database/*.sqlite*
```

### バックアップ推奨
本番環境では定期的なバックアップを推奨します：

```bash
# 手動バックアップ
cp scrapy_ui.db scrapy_ui_backup_$(date +%Y%m%d_%H%M%S).db

# 自動バックアップ（cron例）
0 2 * * * cp /path/to/backend/database/scrapy_ui.db /path/to/backups/scrapy_ui_$(date +\%Y\%m\%d).db
```

## 🛠️ メンテナンス

### データベース初期化
```bash
# CLIコマンドでの初期化
scrapyui db init

# 手動での初期化（開発時）
python -c "from app.database import init_db; init_db()"
```

### データベースマイグレーション
```bash
# マイグレーション実行
scrapyui db migrate

# マイグレーション状態確認
scrapyui db status
```

### データベースリセット
```bash
# 注意: 全データが削除されます
scrapyui db reset
```

## 📊 データベース情報

### 接続情報
- **エンジン**: SQLite 3
- **ファイルパス**: `/home/igtmtakan/workplace/python/scrapyUI/backend/database/scrapy_ui.db`
- **文字エンコーディング**: UTF-8
- **ジャーナルモード**: WAL（Write-Ahead Logging）

### パフォーマンス設定
- **PRAGMA synchronous**: NORMAL
- **PRAGMA journal_mode**: WAL
- **PRAGMA foreign_keys**: ON
- **PRAGMA temp_store**: MEMORY

## 🔍 トラブルシューティング

### よくある問題

1. **データベースファイルが見つからない**
   ```bash
   # ファイル存在確認
   ls -la /home/igtmtakan/workplace/python/scrapyUI/backend/database/
   
   # 設定確認
   python -c "from app.config.database_config import get_database_config; print(get_database_config().database)"
   ```

2. **権限エラー**
   ```bash
   # 権限確認・修正
   chmod 644 scrapy_ui.db
   chown $USER:$USER scrapy_ui.db
   ```

3. **データベース破損**
   ```bash
   # 整合性チェック
   sqlite3 scrapy_ui.db "PRAGMA integrity_check;"
   
   # 修復（バックアップから復元推奨）
   sqlite3 scrapy_ui.db ".recover" | sqlite3 scrapy_ui_recovered.db
   ```

## 📞 サポート

データベース関連の問題については、以下を参照してください：
- **GitHub Issues**: https://github.com/igtmtakan/scrapyUi/issues
- **ドキュメント**: プロジェクトのREADME.md
- **設定例**: backend/.env.example
