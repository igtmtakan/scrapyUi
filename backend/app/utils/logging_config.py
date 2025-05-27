"""
統一されたロギング設定とエラーハンドリング
"""
import logging
import logging.handlers
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import json

# ログディレクトリの設定
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

class JSONFormatter(logging.Formatter):
    """JSON形式でログを出力するフォーマッター"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 例外情報がある場合は追加
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # 追加のコンテキスト情報
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'project_id'):
            log_entry["project_id"] = record.project_id
        if hasattr(record, 'spider_id'):
            log_entry["spider_id"] = record.spider_id
        if hasattr(record, 'task_id'):
            log_entry["task_id"] = record.task_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        return json.dumps(log_entry, ensure_ascii=False)

class ContextFilter(logging.Filter):
    """ログにコンテキスト情報を追加するフィルター"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # デフォルト値を設定
        if not hasattr(record, 'user_id'):
            record.user_id = None
        if not hasattr(record, 'project_id'):
            record.project_id = None
        if not hasattr(record, 'spider_id'):
            record.spider_id = None
        if not hasattr(record, 'task_id'):
            record.task_id = None
        if not hasattr(record, 'request_id'):
            record.request_id = None
        
        return True

def setup_logging(
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    json_format: bool = False
) -> None:
    """
    ロギングシステムのセットアップ
    
    Args:
        level: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: ファイルへのログ出力を有効にするか
        log_to_console: コンソールへのログ出力を有効にするか
        json_format: JSON形式でログを出力するか
    """
    
    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # 既存のハンドラーをクリア
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # コンテキストフィルターを追加
    context_filter = ContextFilter()
    
    # フォーマッターの設定
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # コンソールハンドラー
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(context_filter)
        root_logger.addHandler(console_handler)
    
    # ファイルハンドラー
    if log_to_file:
        # 一般ログファイル（ローテーション）
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_DIR / "scrapyui.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(context_filter)
        root_logger.addHandler(file_handler)
        
        # エラー専用ログファイル
        error_handler = logging.handlers.RotatingFileHandler(
            LOG_DIR / "error.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        error_handler.addFilter(context_filter)
        root_logger.addHandler(error_handler)
        
        # アクセスログファイル（API用）
        access_handler = logging.handlers.RotatingFileHandler(
            LOG_DIR / "access.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        access_handler.setFormatter(formatter)
        access_handler.addFilter(context_filter)
        
        # アクセスログ専用ロガー
        access_logger = logging.getLogger("access")
        access_logger.addHandler(access_handler)
        access_logger.setLevel(logging.INFO)

def get_logger(name: str) -> logging.Logger:
    """
    名前付きロガーを取得
    
    Args:
        name: ロガー名
        
    Returns:
        設定済みのロガー
    """
    return logging.getLogger(name)

def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    spider_id: Optional[str] = None,
    task_id: Optional[str] = None,
    request_id: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    コンテキスト情報付きでログを出力
    
    Args:
        logger: ロガー
        level: ログレベル
        message: ログメッセージ
        user_id: ユーザーID
        project_id: プロジェクトID
        spider_id: スパイダーID
        task_id: タスクID
        request_id: リクエストID
        extra_data: 追加データ
    """
    
    # エクストラ情報を準備
    extra = {}
    if user_id:
        extra['user_id'] = user_id
    if project_id:
        extra['project_id'] = project_id
    if spider_id:
        extra['spider_id'] = spider_id
    if task_id:
        extra['task_id'] = task_id
    if request_id:
        extra['request_id'] = request_id
    
    # 追加データがある場合はメッセージに含める
    if extra_data:
        message = f"{message} | Extra: {json.dumps(extra_data, ensure_ascii=False)}"
    
    # ログレベルに応じて出力
    log_method = getattr(logger, level.lower())
    log_method(message, extra=extra)

def log_exception(
    logger: logging.Logger,
    message: str,
    exc_info: bool = True,
    **context
) -> None:
    """
    例外情報付きでエラーログを出力
    
    Args:
        logger: ロガー
        message: ログメッセージ
        exc_info: 例外情報を含めるか
        **context: コンテキスト情報
    """
    log_with_context(
        logger=logger,
        level="ERROR",
        message=message,
        **context
    )
    
    if exc_info:
        logger.error(message, exc_info=True, extra=context)

# デフォルトのロギング設定を初期化
setup_logging()
