"""
エラーハンドリングとロギングのミドルウェア
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils.error_handler import handle_exception, log_api_access
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """エラーハンドリングミドルウェア"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # リクエストIDを生成
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 開始時間を記録
        start_time = time.time()
        
        # ユーザーIDを取得（認証情報から）
        user_id = getattr(request.state, 'user_id', None)
        
        try:
            # リクエスト処理
            response = await call_next(request)
            
            # 処理時間を計算
            processing_time = time.time() - start_time
            
            # アクセスログを記録
            log_api_access(
                request=request,
                response_status=response.status_code,
                user_id=user_id,
                processing_time=processing_time
            )
            
            # レスポンスヘッダーにリクエストIDを追加
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as exc:
            # 処理時間を計算
            processing_time = time.time() - start_time
            
            # エラーレスポンスを生成
            error_response = handle_exception(
                exc=exc,
                request=request,
                user_id=user_id
            )
            
            # アクセスログを記録
            log_api_access(
                request=request,
                response_status=error_response.status_code,
                user_id=user_id,
                processing_time=processing_time
            )
            
            # レスポンスヘッダーにリクエストIDを追加
            error_response.headers["X-Request-ID"] = request_id
            
            return error_response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """リクエストロギングミドルウェア"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # リクエスト開始ログ
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": getattr(request.state, 'request_id', None),
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        # リクエスト処理
        response = await call_next(request)
        
        # レスポンス完了ログ
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": getattr(request.state, 'request_id', None),
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
            }
        )
        
        return response

class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """パフォーマンスロギングミドルウェア"""
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        processing_time = time.time() - start_time
        
        # 遅いリクエストをログに記録
        if processing_time > self.slow_request_threshold:
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} took {processing_time:.2f}s",
                extra={
                    "request_id": getattr(request.state, 'request_id', None),
                    "method": request.method,
                    "url": str(request.url),
                    "processing_time": processing_time,
                    "threshold": self.slow_request_threshold,
                }
            )
        
        # パフォーマンスメトリクスをヘッダーに追加
        response.headers["X-Processing-Time"] = f"{processing_time:.3f}"
        
        return response
