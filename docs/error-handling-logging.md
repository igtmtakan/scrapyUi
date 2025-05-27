# エラーハンドリングとロギングシステム

ScrapyUIには、包括的なエラーハンドリングとロギングシステムが実装されています。

## 🎯 概要

### 実装された機能

#### 📊 **統一ロギングシステム**
- **構造化ログ**: JSON形式とテキスト形式の両方をサポート
- **コンテキスト情報**: ユーザーID、プロジェクトID、スパイダーID、タスクIDを自動追加
- **ローテーション**: ファイルサイズ制限とバックアップ機能
- **複数出力**: コンソール、ファイル、エラー専用ファイルへの同時出力

#### 🛡️ **カスタム例外システム**
- **階層化例外**: 機能別の例外クラス（Project、Spider、Task、Database等）
- **エラーコード**: 体系的なエラーコード管理
- **詳細情報**: エラーの詳細情報とコンテキストを保持
- **自動ログ**: 例外発生時の自動ログ記録

#### 🔧 **FastAPIミドルウェア**
- **エラーハンドリング**: 全ての例外を統一的に処理
- **リクエストログ**: 全APIリクエストの詳細ログ
- **パフォーマンス監視**: 処理時間の測定と遅いリクエストの検出
- **リクエストID**: 各リクエストに一意IDを付与

## 📁 ログファイル構成

### ファイル一覧

```
backend/logs/
├── scrapyui.log     # 一般ログ（INFO以上）
├── error.log        # エラー専用ログ（ERROR以上）
└── access.log       # APIアクセスログ
```

### ローテーション設定

- **最大ファイルサイズ**: 10MB
- **バックアップ数**: 5ファイル
- **エンコーディング**: UTF-8
- **自動圧縮**: 古いファイルは自動的にローテーション

## 🔍 ログ形式

### 標準ログ形式

```
2025-05-27 20:28:21,412 - logger_name - LEVEL - message
```

### JSON形式（オプション）

```json
{
  "timestamp": "2025-05-27T20:28:21.412000",
  "level": "INFO",
  "logger": "app.api.projects",
  "message": "Project created successfully",
  "module": "projects",
  "function": "create_project",
  "line": 142,
  "user_id": "user-123",
  "project_id": "project-456",
  "request_id": "req-789"
}
```

## 🚨 エラーコード体系

### 一般的なエラー

| コード | 説明 |
|--------|------|
| `INTERNAL_SERVER_ERROR` | 内部サーバーエラー |
| `VALIDATION_ERROR` | バリデーションエラー |
| `NOT_FOUND` | リソースが見つからない |
| `UNAUTHORIZED` | 認証エラー |
| `FORBIDDEN` | 認可エラー |

### プロジェクト関連

| コード | 説明 |
|--------|------|
| `PROJECT_NOT_FOUND` | プロジェクトが見つからない |
| `PROJECT_CREATION_FAILED` | プロジェクト作成失敗 |
| `PROJECT_DELETION_FAILED` | プロジェクト削除失敗 |
| `PROJECT_ACCESS_DENIED` | プロジェクトアクセス拒否 |

### スパイダー関連

| コード | 説明 |
|--------|------|
| `SPIDER_NOT_FOUND` | スパイダーが見つからない |
| `SPIDER_CREATION_FAILED` | スパイダー作成失敗 |
| `SPIDER_EXECUTION_FAILED` | スパイダー実行失敗 |
| `SPIDER_CODE_INVALID` | スパイダーコードが無効 |

### タスク関連

| コード | 説明 |
|--------|------|
| `TASK_NOT_FOUND` | タスクが見つからない |
| `TASK_CREATION_FAILED` | タスク作成失敗 |
| `TASK_EXECUTION_FAILED` | タスク実行失敗 |
| `TASK_CANCELLATION_FAILED` | タスクキャンセル失敗 |

## 💻 使用方法

### 基本的なログ出力

```python
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# 基本ログ
logger.info("処理が開始されました")
logger.warning("警告メッセージ")
logger.error("エラーが発生しました")
```

### コンテキスト付きログ

```python
from app.utils.logging_config import log_with_context

log_with_context(
    logger, "INFO",
    "プロジェクトが作成されました",
    user_id="user-123",
    project_id="project-456",
    extra_data={"project_name": "my_project"}
)
```

### 例外ログ

```python
from app.utils.logging_config import log_exception

try:
    # 何らかの処理
    pass
except Exception:
    log_exception(
        logger,
        "プロジェクト作成中にエラーが発生しました",
        user_id="user-123",
        project_id="project-456"
    )
```

### カスタム例外の使用

```python
from app.utils.error_handler import ProjectException, ErrorCode

# 例外を発生
raise ProjectException(
    message="プロジェクトの作成に失敗しました",
    error_code=ErrorCode.PROJECT_CREATION_FAILED,
    project_id="project-123",
    details={"reason": "ディスク容量不足"}
)
```

## 🔧 設定

### ロギング設定

```python
from app.utils.logging_config import setup_logging

# 基本設定
setup_logging(
    level="INFO",           # ログレベル
    log_to_file=True,       # ファイル出力
    log_to_console=True,    # コンソール出力
    json_format=False       # JSON形式
)
```

### ミドルウェア設定

```python
from app.middleware.error_middleware import (
    ErrorHandlingMiddleware,
    RequestLoggingMiddleware,
    PerformanceLoggingMiddleware
)

# FastAPIアプリケーションに追加
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(PerformanceLoggingMiddleware, slow_request_threshold=2.0)
```

## 📊 監視とデバッグ

### ログファイルの監視

```bash
# リアルタイムでログを監視
tail -f backend/logs/scrapyui.log

# エラーログのみ監視
tail -f backend/logs/error.log

# アクセスログの監視
tail -f backend/logs/access.log
```

### パフォーマンス監視

- **遅いリクエスト**: 2秒以上のリクエストを自動検出
- **処理時間**: レスポンスヘッダーに処理時間を追加
- **リクエストID**: 各リクエストに一意IDを付与してトラッキング

### エラー分析

```bash
# エラーの頻度を確認
grep "ERROR" backend/logs/scrapyui.log | wc -l

# 特定のエラーコードを検索
grep "PROJECT_CREATION_FAILED" backend/logs/error.log

# 特定のユーザーのエラーを検索
grep "user-123" backend/logs/error.log
```

## 🎯 運用のベストプラクティス

### ログレベルの使い分け

- **DEBUG**: 開発時の詳細情報
- **INFO**: 一般的な処理の記録
- **WARNING**: 注意が必要な状況
- **ERROR**: エラーが発生した場合
- **CRITICAL**: システムに重大な影響がある場合

### エラーハンドリングの指針

1. **適切な例外クラスを使用**: 機能に応じた例外クラスを選択
2. **詳細情報を含める**: エラーの原因と対処法を明確に
3. **ログを残す**: 全ての例外をログに記録
4. **ユーザーフレンドリー**: エラーメッセージは分かりやすく

### セキュリティ考慮事項

- **機密情報の除外**: パスワードやトークンをログに含めない
- **ログファイルの権限**: 適切なファイル権限を設定
- **ログローテーション**: 古いログファイルの自動削除
- **監査ログ**: 重要な操作は必ずログに記録

## 🚀 効果

### 開発効率の向上

- **デバッグ時間短縮**: 詳細なログで問題の特定が容易
- **エラー追跡**: リクエストIDによる完全なトレーサビリティ
- **パフォーマンス最適化**: 遅いリクエストの自動検出

### 運用品質の向上

- **障害対応**: 迅速な問題の特定と対処
- **監視**: システムの健全性を継続的に監視
- **分析**: ログデータによる利用パターンの分析

### ユーザー体験の向上

- **エラーメッセージ**: 分かりやすいエラー情報
- **安定性**: 堅牢なエラーハンドリングによる安定動作
- **レスポンス**: 適切なHTTPステータスコードとエラー情報

このシステムにより、ScrapyUIはより堅牢で監視しやすく、デバッグしやすいアプリケーションになりました。
