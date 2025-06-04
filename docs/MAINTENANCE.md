# ScrapyUI メンテナンスガイド

## 🛡️ 大きなファイル監視とクリーンアップ

GitHubの100MBファイルサイズ制限を超えるファイルを防ぐための自動化システムです。

## 📋 利用可能なコマンド

### Make コマンド（推奨）

```bash
# 初回セットアップ
make install-hooks

# 大きなファイルをチェック
make check-large-files

# 自動クリーンアップを実行
make cleanup

# 完全なメンテナンス（クリーンアップ + チェック）
make maintenance

# ヘルプを表示
make help
```

### 直接実行

```bash
# 大きなファイルをチェック
python3 scripts/check_large_files.py

# 自動クリーンアップを実行
python3 scripts/cleanup_large_files.py
```

## 🔧 自動化機能

### 1. Git Pre-commitフック

コミット前に自動的に大きなファイルをチェックします。

- **場所**: `.git/hooks/pre-commit`
- **動作**: 100MB以上のファイルが検出されるとコミットを中止
- **インストール**: `make install-hooks`

### 2. 大きなファイル検出

以下のファイルを監視します：

- **GitHub制限**: 100MB以上（エラー）
- **警告サイズ**: 50MB以上（警告）
- **対象**: Gitで追跡されているファイルのみ

### 3. 自動クリーンアップ

以下のファイルを自動削除します：

#### データベースバックアップファイル
- `*.db.backup*`
- `*.db.bak*`
- `*.sql.backup*`
- `*.sql.bak*`

#### 古いログファイル（7日以上前）
- `*.log`
- `logs/*.log`
- `scrapy_projects/*/logs/*.log`

#### 一時ファイル・キャッシュ
- `*.tmp`, `*.temp`
- `**/__pycache__/`
- `**/.pytest_cache/`
- `**/node_modules/.cache/`

#### 大きな結果ファイル（7日以上前、50MB以上）
- `*.jsonl`
- `*.json`
- `*.csv`
- `ranking_results.*`
- `stats_task_*.json`

## 📁 .gitignore 強化

以下のパターンが自動的に除外されます：

```gitignore
# Database files
*.db
*.sqlite
*.sqlite3
*.db.backup*
*.db.bak*
*.sql.backup*
*.sql.bak*

# Large result files (over 50MB)
**/ranking_results.jsonl
**/stats_task_*.json
**/*.jsonl.large
**/*.csv.large

# Temporary and cache files
*.tmp
*.temp
**/__pycache__/
**/.pytest_cache/
**/node_modules/.cache/
```

## 🚀 推奨ワークフロー

### 初回セットアップ

```bash
# Git hooksをインストール
make install-hooks
```

### 日常的な使用

```bash
# 定期メンテナンス（週1回推奨）
make maintenance

# コミット前の手動チェック（必要に応じて）
make check-large-files
```

### 問題が発生した場合

```bash
# 大きなファイルが検出された場合
make cleanup

# 手動でファイルを削除
rm <large_file_path>

# .gitignoreに追加
echo "<pattern>" >> .gitignore
```

## ⚠️ 注意事項

1. **自動削除**: クリーンアップスクリプトは自動的にファイルを削除します
2. **バックアップ**: 重要なファイルは事前にバックアップしてください
3. **Git LFS**: 100MB以上のファイルが必要な場合はGit LFSを使用してください

## 🔍 トラブルシューティング

### Pre-commitフックが動作しない

```bash
# 実行権限を確認
ls -la .git/hooks/pre-commit

# 権限を付与
chmod +x .git/hooks/pre-commit
```

### スクリプトが見つからない

```bash
# スクリプトの存在確認
ls -la scripts/

# 権限を付与
chmod +x scripts/*.py
```

### 大きなファイルを強制的にコミットしたい場合

```bash
# Pre-commitフックを一時的に無効化
git commit --no-verify -m "message"
```

## 📊 統計情報

クリーンアップ実行時に以下の情報が表示されます：

- 削除ファイル数
- 解放された容量
- 削除されたファイルの詳細

## 🔄 定期実行の設定

### Cron（Linux/Mac）

```bash
# 毎日午前2時に実行
0 2 * * * cd /path/to/scrapyui && make cleanup
```

### タスクスケジューラ（Windows）

1. タスクスケジューラを開く
2. 基本タスクを作成
3. `make cleanup` を実行するように設定
