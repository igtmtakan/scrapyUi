"""
包括的なエラーハンドリングシステム
"""
import traceback
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import logging

from .logging_config import get_logger, log_exception

logger = get_logger(__name__)

class ErrorCode(Enum):
    """エラーコードの定義"""
    
    # 一般的なエラー
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    
    # 認証関連
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    
    # プロジェクト関連
    PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
    PROJECT_CREATION_FAILED = "PROJECT_CREATION_FAILED"
    PROJECT_DELETION_FAILED = "PROJECT_DELETION_FAILED"
    PROJECT_ACCESS_DENIED = "PROJECT_ACCESS_DENIED"
    
    # スパイダー関連
    SPIDER_NOT_FOUND = "SPIDER_NOT_FOUND"
    SPIDER_CREATION_FAILED = "SPIDER_CREATION_FAILED"
    SPIDER_EXECUTION_FAILED = "SPIDER_EXECUTION_FAILED"
    SPIDER_CODE_INVALID = "SPIDER_CODE_INVALID"
    SPIDER_INHERITANCE_ERROR = "SPIDER_INHERITANCE_ERROR"
    
    # タスク関連
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_CREATION_FAILED = "TASK_CREATION_FAILED"
    TASK_EXECUTION_FAILED = "TASK_EXECUTION_FAILED"
    TASK_CANCELLATION_FAILED = "TASK_CANCELLATION_FAILED"
    
    # ファイル関連
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_CREATION_FAILED = "FILE_CREATION_FAILED"
    FILE_DELETION_FAILED = "FILE_DELETION_FAILED"
    FILE_PERMISSION_DENIED = "FILE_PERMISSION_DENIED"
    
    # データベース関連
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_QUERY_ERROR = "DATABASE_QUERY_ERROR"
    DATABASE_CONSTRAINT_ERROR = "DATABASE_CONSTRAINT_ERROR"
    
    # 外部サービス関連
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"

class ScrapyUIException(Exception):
    """ScrapyUI用のベース例外クラス"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        spider_id: Optional[str] = None,
        task_id: Optional[str] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.user_id = user_id
        self.project_id = project_id
        self.spider_id = spider_id
        self.task_id = task_id
        self.timestamp = datetime.utcnow()
        
        super().__init__(self.message)

class ValidationException(ScrapyUIException):
    """バリデーションエラー"""
    
    def __init__(self, message: str, field_errors: Optional[Dict[str, List[str]]] = None, **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field_errors": field_errors or {}},
            **kwargs
        )

class AuthenticationException(ScrapyUIException):
    """認証エラー"""
    
    def __init__(self, message: str = "認証に失敗しました", **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=status.HTTP_401_UNAUTHORIZED,
            **kwargs
        )

class AuthorizationException(ScrapyUIException):
    """認可エラー"""
    
    def __init__(self, message: str = "アクセス権限がありません", **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.FORBIDDEN,
            status_code=status.HTTP_403_FORBIDDEN,
            **kwargs
        )

class ResourceNotFoundException(ScrapyUIException):
    """リソースが見つからないエラー"""
    
    def __init__(self, resource_type: str, resource_id: str, **kwargs):
        message = f"{resource_type} (ID: {resource_id}) が見つかりません"
        super().__init__(
            message=message,
            error_code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id},
            **kwargs
        )

class ProjectException(ScrapyUIException):
    """プロジェクト関連エラー"""
    pass

class SpiderException(ScrapyUIException):
    """スパイダー関連エラー"""
    pass

class TaskException(ScrapyUIException):
    """タスク関連エラー"""
    pass

class DatabaseException(ScrapyUIException):
    """データベース関連エラー"""
    pass

def handle_exception(
    exc: Exception,
    request: Optional[Request] = None,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    spider_id: Optional[str] = None,
    task_id: Optional[str] = None
) -> JSONResponse:
    """
    例外を適切にハンドリングしてJSONレスポンスを返す
    
    Args:
        exc: 発生した例外
        request: FastAPIリクエストオブジェクト
        user_id: ユーザーID
        project_id: プロジェクトID
        spider_id: スパイダーID
        task_id: タスクID
        
    Returns:
        JSONレスポンス
    """
    
    # リクエスト情報を取得
    request_info = {}
    if request:
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
    
    # ScrapyUI例外の場合
    if isinstance(exc, ScrapyUIException):
        log_exception(
            logger,
            f"ScrapyUI Exception: {exc.message}",
            user_id=exc.user_id or user_id,
            project_id=exc.project_id or project_id,
            spider_id=exc.spider_id or spider_id,
            task_id=exc.task_id or task_id,
            extra_data={
                "error_code": exc.error_code.value,
                "details": exc.details,
                "request": request_info
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code.value,
                    "message": exc.message,
                    "details": exc.details,
                    "timestamp": exc.timestamp.isoformat()
                }
            }
        )
    
    # HTTPException の場合
    elif isinstance(exc, HTTPException):
        log_exception(
            logger,
            f"HTTP Exception: {exc.detail}",
            user_id=user_id,
            project_id=project_id,
            spider_id=spider_id,
            task_id=task_id,
            extra_data={
                "status_code": exc.status_code,
                "request": request_info
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )
    
    # その他の例外
    else:
        log_exception(
            logger,
            f"Unhandled Exception: {str(exc)}",
            user_id=user_id,
            project_id=project_id,
            spider_id=spider_id,
            task_id=task_id,
            extra_data={
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc(),
                "request": request_info
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                    "message": "内部サーバーエラーが発生しました",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )

def create_error_response(
    error_code: ErrorCode,
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    エラーレスポンスを作成
    
    Args:
        error_code: エラーコード
        message: エラーメッセージ
        status_code: HTTPステータスコード
        details: 詳細情報
        
    Returns:
        JSONレスポンス
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": error_code.value,
                "message": message,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

def log_api_access(
    request: Request,
    response_status: int,
    user_id: Optional[str] = None,
    processing_time: Optional[float] = None
) -> None:
    """
    APIアクセスログを記録
    
    Args:
        request: FastAPIリクエストオブジェクト
        response_status: レスポンスステータスコード
        user_id: ユーザーID
        processing_time: 処理時間（秒）
    """
    access_logger = get_logger("access")
    
    log_data = {
        "method": request.method,
        "url": str(request.url),
        "status_code": response_status,
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "user_id": user_id,
        "processing_time": processing_time
    }
    
    access_logger.info(
        f"{request.method} {request.url.path} - {response_status}",
        extra=log_data
    )
