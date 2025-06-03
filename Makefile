# ScrapyUI Maintenance Commands

.PHONY: check-large-files cleanup install-hooks help

# 大きなファイルをチェック
check-large-files:
	@echo "🔍 大きなファイルをチェック中..."
	@python3 scripts/check_large_files.py

# 自動クリーンアップを実行
cleanup:
	@echo "🧹 自動クリーンアップを実行中..."
	@python3 scripts/cleanup_large_files.py

# Git hooksをインストール
install-hooks:
	@echo "🔧 Git hooksをインストール中..."
	@chmod +x .git/hooks/pre-commit
	@chmod +x scripts/check_large_files.py
	@chmod +x scripts/cleanup_large_files.py
	@echo "✅ Git hooks インストール完了"

# 完全なメンテナンス（クリーンアップ + チェック）
maintenance: cleanup check-large-files
	@echo "✅ メンテナンス完了"

# ヘルプ
help:
	@echo "ScrapyUI メンテナンスコマンド:"
	@echo ""
	@echo "  make check-large-files  - 大きなファイルをチェック"
	@echo "  make cleanup           - 不要なファイルをクリーンアップ"
	@echo "  make install-hooks     - Git hooksをインストール"
	@echo "  make maintenance       - 完全なメンテナンス実行"
	@echo "  make help             - このヘルプを表示"
	@echo ""
	@echo "推奨使用方法:"
	@echo "  1. 初回セットアップ: make install-hooks"
	@echo "  2. 定期メンテナンス: make maintenance"
	@echo "  3. コミット前チェック: make check-large-files"
