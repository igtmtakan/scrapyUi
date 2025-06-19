#!/usr/bin/env python3
"""
Playwright専用サービス
ScrapyUIのPlaywright実行を専門的に処理する独立サービス
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Playwright imports
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# グローバル変数
browser_pool: Dict[str, Browser] = {}
context_pool: Dict[str, BrowserContext] = {}
page_pool: Dict[str, Page] = {}
playwright_instance = None

class PlaywrightRequest(BaseModel):
    """Playwright実行リクエスト"""
    url: str
    browser_type: str = "chromium"
    headless: bool = True
    wait_for: str = "domcontentloaded"
    timeout: int = 30000
    viewport: Optional[Dict[str, int]] = None
    user_agent: Optional[str] = None
    extra_headers: Optional[Dict[str, str]] = None
    javascript_code: Optional[str] = None
    screenshot: bool = False
    pdf: bool = False
    session_id: Optional[str] = None

class PlaywrightResponse(BaseModel):
    """Playwright実行レスポンス"""
    success: bool
    session_id: str
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    screenshot_base64: Optional[str] = None
    pdf_base64: Optional[str] = None
    error: Optional[str] = None
    execution_time: float
    timestamp: str

class BrowserPoolManager:
    """ブラウザプール管理クラス"""
    
    def __init__(self):
        self.browsers: Dict[str, Browser] = {}
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}
        self.playwright = None
        
    async def initialize(self):
        """Playwrightを初期化"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright is not available")
            
        self.playwright = await async_playwright().start()
        logger.info("✅ Playwright initialized successfully")
        
    async def get_browser(self, browser_type: str = "chromium", headless: bool = True) -> Browser:
        """ブラウザインスタンスを取得"""
        browser_key = f"{browser_type}_{headless}"
        
        if browser_key not in self.browsers:
            browser_launcher = getattr(self.playwright, browser_type)
            
            launch_options = {
                "headless": headless,
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--disable-field-trial-config",
                    "--disable-ipc-flooding-protection"
                ]
            }
            
            browser = await browser_launcher.launch(**launch_options)
            self.browsers[browser_key] = browser
            logger.info(f"✅ Browser {browser_type} (headless={headless}) launched")
            
        return self.browsers[browser_key]
    
    async def create_session(self, request: PlaywrightRequest) -> str:
        """新しいセッションを作成"""
        session_id = str(uuid.uuid4())
        
        browser = await self.get_browser(request.browser_type, request.headless)
        
        context_options = {}
        if request.viewport:
            context_options["viewport"] = request.viewport
        if request.user_agent:
            context_options["user_agent"] = request.user_agent
        if request.extra_headers:
            context_options["extra_http_headers"] = request.extra_headers
            
        context = await browser.new_context(**context_options)
        page = await context.new_page()
        
        self.contexts[session_id] = context
        self.pages[session_id] = page
        
        logger.info(f"✅ Session {session_id} created")
        return session_id
    
    async def execute_request(self, request: PlaywrightRequest) -> PlaywrightResponse:
        """Playwrightリクエストを実行"""
        start_time = datetime.now()
        session_id = request.session_id or await self.create_session(request)
        
        try:
            page = self.pages[session_id]
            
            # ページに移動
            await page.goto(request.url, wait_until=request.wait_for, timeout=request.timeout)
            
            # JavaScriptコードを実行（オプション）
            if request.javascript_code:
                await page.evaluate(request.javascript_code)
            
            # ページ情報を取得
            title = await page.title()
            content = await page.content()
            
            # スクリーンショット（オプション）
            screenshot_base64 = None
            if request.screenshot:
                screenshot_bytes = await page.screenshot()
                import base64
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode()
            
            # PDF生成（オプション）
            pdf_base64 = None
            if request.pdf:
                pdf_bytes = await page.pdf()
                import base64
                pdf_base64 = base64.b64encode(pdf_bytes).decode()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return PlaywrightResponse(
                success=True,
                session_id=session_id,
                url=request.url,
                title=title,
                content=content,
                screenshot_base64=screenshot_base64,
                pdf_base64=pdf_base64,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Playwright execution error: {e}")
            
            return PlaywrightResponse(
                success=False,
                session_id=session_id,
                url=request.url,
                error=str(e),
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )
    
    async def close_session(self, session_id: str):
        """セッションを閉じる"""
        if session_id in self.pages:
            await self.pages[session_id].close()
            del self.pages[session_id]
            
        if session_id in self.contexts:
            await self.contexts[session_id].close()
            del self.contexts[session_id]
            
        logger.info(f"✅ Session {session_id} closed")
    
    async def cleanup(self):
        """リソースをクリーンアップ"""
        # 全セッションを閉じる
        for session_id in list(self.pages.keys()):
            await self.close_session(session_id)
        
        # 全ブラウザを閉じる
        for browser in self.browsers.values():
            await browser.close()
        
        if self.playwright:
            await self.playwright.stop()
            
        logger.info("✅ Playwright cleanup completed")

# グローバルブラウザプールマネージャー
pool_manager = BrowserPoolManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    # 起動時
    await pool_manager.initialize()
    yield
    # 終了時
    await pool_manager.cleanup()

# FastAPIアプリケーション
app = FastAPI(
    title="ScrapyUI Playwright Service",
    description="専用Playwright実行サービス",
    version="1.0.0",
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "playwright_available": PLAYWRIGHT_AVAILABLE,
        "active_sessions": len(pool_manager.pages),
        "active_browsers": len(pool_manager.browsers),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/execute", response_model=PlaywrightResponse)
async def execute_playwright(request: PlaywrightRequest):
    """Playwrightリクエストを実行"""
    if not PLAYWRIGHT_AVAILABLE:
        raise HTTPException(status_code=500, detail="Playwright is not available")
    
    return await pool_manager.execute_request(request)

@app.post("/session/create")
async def create_session(request: PlaywrightRequest):
    """新しいセッションを作成"""
    session_id = await pool_manager.create_session(request)
    return {"session_id": session_id}

@app.delete("/session/{session_id}")
async def close_session(session_id: str):
    """セッションを閉じる"""
    await pool_manager.close_session(session_id)
    return {"message": f"Session {session_id} closed"}

@app.get("/sessions")
async def list_sessions():
    """アクティブセッション一覧"""
    return {
        "active_sessions": list(pool_manager.pages.keys()),
        "count": len(pool_manager.pages)
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
