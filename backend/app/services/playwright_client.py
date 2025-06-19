#!/usr/bin/env python3
"""
Playwright専用サービスクライアント
ScrapyからPlaywright専用サービスを利用するためのクライアント
"""

import asyncio
import json
import logging
from typing import Dict, Optional, Any
import httpx
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class PlaywrightServiceClient:
    """Playwright専用サービスクライアント"""
    
    def __init__(self, service_url: str = "http://localhost:8004"):
        self.service_url = service_url.rstrip('/')
        self.session_id: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=60.0)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def close(self):
        """クライアントを閉じる"""
        if self.session_id:
            await self.close_session()
        await self.client.aclose()
        
    async def health_check(self) -> Dict[str, Any]:
        """サービスのヘルスチェック"""
        try:
            response = await self.client.get(f"{self.service_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def create_session(self, browser_type: str = "chromium", headless: bool = True, 
                           viewport: Optional[Dict[str, int]] = None,
                           user_agent: Optional[str] = None) -> str:
        """新しいセッションを作成"""
        request_data = {
            "url": "about:blank",  # ダミーURL
            "browser_type": browser_type,
            "headless": headless
        }
        
        if viewport:
            request_data["viewport"] = viewport
        if user_agent:
            request_data["user_agent"] = user_agent
            
        try:
            response = await self.client.post(
                f"{self.service_url}/session/create",
                json=request_data
            )
            response.raise_for_status()
            result = response.json()
            self.session_id = result["session_id"]
            logger.info(f"✅ Session created: {self.session_id}")
            return self.session_id
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    async def close_session(self):
        """現在のセッションを閉じる"""
        if not self.session_id:
            return
            
        try:
            response = await self.client.delete(
                f"{self.service_url}/session/{self.session_id}"
            )
            response.raise_for_status()
            logger.info(f"✅ Session closed: {self.session_id}")
            self.session_id = None
        except Exception as e:
            logger.error(f"Failed to close session: {e}")
    
    async def execute_request(self, url: str, **kwargs) -> Dict[str, Any]:
        """Playwrightリクエストを実行"""
        request_data = {
            "url": url,
            "browser_type": kwargs.get("browser_type", "chromium"),
            "headless": kwargs.get("headless", True),
            "wait_for": kwargs.get("wait_for", "domcontentloaded"),
            "timeout": kwargs.get("timeout", 30000),
            "javascript_code": kwargs.get("javascript_code"),
            "screenshot": kwargs.get("screenshot", False),
            "pdf": kwargs.get("pdf", False),
            "session_id": self.session_id
        }
        
        # オプション設定
        if "viewport" in kwargs:
            request_data["viewport"] = kwargs["viewport"]
        if "user_agent" in kwargs:
            request_data["user_agent"] = kwargs["user_agent"]
        if "extra_headers" in kwargs:
            request_data["extra_headers"] = kwargs["extra_headers"]
        
        try:
            response = await self.client.post(
                f"{self.service_url}/execute",
                json=request_data
            )
            response.raise_for_status()
            result = response.json()
            
            if not result["success"]:
                logger.error(f"Playwright execution failed: {result.get('error')}")
                
            return result
        except Exception as e:
            logger.error(f"Failed to execute Playwright request: {e}")
            raise

class ScrapyPlaywrightIntegration:
    """Scrapy-Playwright統合クラス"""
    
    def __init__(self, service_url: str = "http://localhost:8004"):
        self.service_url = service_url
        self.client: Optional[PlaywrightServiceClient] = None
        
    async def process_request(self, request, spider):
        """Scrapyリクエストを処理"""
        # Playwrightメタデータを確認
        if not request.meta.get('playwright'):
            return None
            
        if not self.client:
            self.client = PlaywrightServiceClient(self.service_url)
            
        # セッションが存在しない場合は作成
        if not self.client.session_id:
            await self.client.create_session(
                browser_type=request.meta.get('playwright_browser_type', 'chromium'),
                headless=request.meta.get('playwright_headless', True),
                viewport=request.meta.get('playwright_viewport'),
                user_agent=request.meta.get('playwright_user_agent')
            )
        
        # Playwrightリクエストを実行
        playwright_kwargs = {
            "wait_for": request.meta.get('playwright_wait_for', 'domcontentloaded'),
            "timeout": request.meta.get('playwright_timeout', 30000),
            "javascript_code": request.meta.get('playwright_javascript'),
            "screenshot": request.meta.get('playwright_screenshot', False),
            "pdf": request.meta.get('playwright_pdf', False)
        }
        
        result = await self.client.execute_request(request.url, **playwright_kwargs)
        
        if result["success"]:
            # Scrapyレスポンスを作成
            from scrapy.http import HtmlResponse
            
            response = HtmlResponse(
                url=result["url"],
                body=result["content"].encode('utf-8'),
                encoding='utf-8',
                request=request
            )
            
            # 追加メタデータを設定
            response.meta.update({
                'playwright_session_id': result["session_id"],
                'playwright_title': result["title"],
                'playwright_execution_time': result["execution_time"],
                'playwright_screenshot': result.get("screenshot_base64"),
                'playwright_pdf': result.get("pdf_base64")
            })
            
            return response
        else:
            logger.error(f"Playwright request failed: {result.get('error')}")
            return None
    
    async def close(self):
        """リソースを閉じる"""
        if self.client:
            await self.client.close()
            self.client = None

# Scrapy Middleware として使用するためのクラス
class PlaywrightMiddleware:
    """Scrapy Playwright Middleware"""
    
    def __init__(self, service_url: str = "http://localhost:8004"):
        self.integration = ScrapyPlaywrightIntegration(service_url)
        
    @classmethod
    def from_crawler(cls, crawler):
        service_url = crawler.settings.get('PLAYWRIGHT_SERVICE_URL', 'http://localhost:8004')
        return cls(service_url)
    
    async def process_request(self, request, spider):
        """リクエストを処理"""
        return await self.integration.process_request(request, spider)
    
    async def spider_closed(self, spider):
        """スパイダー終了時の処理"""
        await self.integration.close()
