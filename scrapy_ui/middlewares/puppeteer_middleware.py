"""
Puppeteer Middleware for Scrapy
ScrapyスパイダーでPuppeteerを使用するためのミドルウェア
"""

import asyncio
import logging
from typing import Union, Optional, Dict, Any
from scrapy import signals
from scrapy.http import HtmlResponse, Request
from scrapy.exceptions import NotConfigured
from scrapy.utils.python import to_bytes
from scrapy_ui.nodejs_client import NodeJSClient, PuppeteerRequest

logger = logging.getLogger(__name__)

class PuppeteerMiddleware:
    """Puppeteer統合ミドルウェア"""
    
    def __init__(self, nodejs_url: str = "http://localhost:3001", enabled: bool = True):
        if not enabled:
            raise NotConfigured("Puppeteer middleware is disabled")
        
        self.nodejs_url = nodejs_url
        self.client = None
        self.loop = None
    
    @classmethod
    def from_crawler(cls, crawler):
        """Crawlerから設定を読み込んでインスタンス作成"""
        settings = crawler.settings
        
        return cls(
            nodejs_url=settings.get('PUPPETEER_NODEJS_URL', 'http://localhost:3001'),
            enabled=settings.getbool('PUPPETEER_ENABLED', True)
        )
    
    async def _ensure_client(self):
        """Node.jsクライアントの初期化"""
        if self.client is None:
            self.client = NodeJSClient(self.nodejs_url)
    
    def _get_event_loop(self):
        """イベントループの取得"""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
    
    def process_request(self, request: Request, spider):
        """リクエスト処理"""
        # Puppeteerを使用するかチェック
        if not request.meta.get('puppeteer', False):
            return None
        
        # 非同期処理を同期的に実行
        loop = self._get_event_loop()
        return loop.run_until_complete(self._process_puppeteer_request(request, spider))
    
    async def _process_puppeteer_request(self, request: Request, spider) -> HtmlResponse:
        """Puppeteerリクエストの処理"""
        await self._ensure_client()
        
        try:
            # リクエストメタデータから設定を取得
            puppeteer_config = request.meta.get('puppeteer_config', {})
            action_type = puppeteer_config.get('action', 'scrape')
            
            if action_type == 'spa':
                response = await self._handle_spa_scraping(request, puppeteer_config)
            elif action_type == 'screenshot':
                response = await self._handle_screenshot(request, puppeteer_config)
            elif action_type == 'pdf':
                response = await self._handle_pdf_generation(request, puppeteer_config)
            else:
                response = await self._handle_basic_scraping(request, puppeteer_config)
            
            return response
            
        except Exception as e:
            logger.error(f"Puppeteer request failed: {e}")
            # フォールバック: 通常のHTTPリクエストとして処理
            return None
    
    async def _handle_spa_scraping(self, request: Request, config: Dict) -> HtmlResponse:
        """SPAスクレイピング処理"""
        request_data = {
            "url": request.url,
            "waitFor": config.get('wait_for'),
            "timeout": config.get('timeout', 30000),
            "viewport": config.get('viewport', {"width": 1920, "height": 1080}),
            "extractData": {
                "selectors": config.get('selectors', {}),
                "javascript": config.get('javascript')
            },
            "screenshot": config.get('screenshot', False)
        }
        
        response = await self.client.scrape_spa(request_data)
        
        if response.success:
            # レスポンスデータからHTMLを構築
            html_content = self._build_html_from_data(response.data)
            
            return HtmlResponse(
                url=request.url,
                body=to_bytes(html_content),
                encoding='utf-8',
                request=request,
                meta={
                    **request.meta,
                    'puppeteer_data': response.data,
                    'puppeteer_success': True
                }
            )
        else:
            raise Exception(f"SPA scraping failed: {response.error}")
    
    async def _handle_screenshot(self, request: Request, config: Dict) -> HtmlResponse:
        """スクリーンショット処理"""
        request_data = {
            "url": request.url,
            "options": {
                "fullPage": config.get('full_page', True),
                "type": config.get('type', 'png'),
                **config.get('options', {})
            },
            "viewport": config.get('viewport')
        }
        
        response = await self.client.capture_screenshot(request_data)
        
        if response.success:
            # 空のHTMLレスポンスを返し、スクリーンショットデータをメタに保存
            return HtmlResponse(
                url=request.url,
                body=b'<html><body>Screenshot captured</body></html>',
                encoding='utf-8',
                request=request,
                meta={
                    **request.meta,
                    'screenshot_data': response.data.get('screenshot'),
                    'screenshot_size': response.data.get('size'),
                    'puppeteer_success': True
                }
            )
        else:
            raise Exception(f"Screenshot capture failed: {response.error}")
    
    async def _handle_pdf_generation(self, request: Request, config: Dict) -> HtmlResponse:
        """PDF生成処理"""
        request_data = {
            "url": request.url,
            "options": {
                "format": config.get('format', 'A4'),
                "landscape": config.get('landscape', False),
                **config.get('options', {})
            }
        }
        
        response = await self.client.generate_pdf(request_data)
        
        if response.success:
            return HtmlResponse(
                url=request.url,
                body=b'<html><body>PDF generated</body></html>',
                encoding='utf-8',
                request=request,
                meta={
                    **request.meta,
                    'pdf_data': response.data.get('pdf'),
                    'pdf_size': response.data.get('size'),
                    'puppeteer_success': True
                }
            )
        else:
            raise Exception(f"PDF generation failed: {response.error}")
    
    async def _handle_basic_scraping(self, request: Request, config: Dict) -> HtmlResponse:
        """基本的なスクレイピング処理"""
        # 基本的なページ取得（JavaScript実行付き）
        request_data = {
            "url": request.url,
            "waitFor": config.get('wait_for'),
            "timeout": config.get('timeout', 30000)
        }
        
        # 簡単なスクレイピングとして処理
        response = await self.client.scrape_spa(request_data)
        
        if response.success:
            # ページのHTMLコンテンツを取得
            html_content = response.data.get('html', '<html><body></body></html>')
            
            return HtmlResponse(
                url=request.url,
                body=to_bytes(html_content),
                encoding='utf-8',
                request=request,
                meta={
                    **request.meta,
                    'puppeteer_data': response.data,
                    'puppeteer_success': True
                }
            )
        else:
            raise Exception(f"Basic scraping failed: {response.error}")
    
    def _build_html_from_data(self, data: Dict) -> str:
        """抽出データからHTMLを構築"""
        extracted_data = data.get('data', {})
        
        if not extracted_data:
            return '<html><body></body></html>'
        
        # 簡単なHTML構築
        html_parts = ['<html><head><title>Puppeteer Scraped Data</title></head><body>']
        
        for key, value in extracted_data.items():
            if isinstance(value, list):
                html_parts.append(f'<div class="{key}">')
                for item in value:
                    html_parts.append(f'<div class="{key}-item">{item}</div>')
                html_parts.append('</div>')
            else:
                html_parts.append(f'<div class="{key}">{value}</div>')
        
        html_parts.append('</body></html>')
        
        return '\n'.join(html_parts)

# Scrapy設定用のヘルパー関数
def enable_puppeteer_middleware(settings_dict: Dict[str, Any]):
    """Scrapy設定でPuppeteerミドルウェアを有効化"""
    if 'DOWNLOADER_MIDDLEWARES' not in settings_dict:
        settings_dict['DOWNLOADER_MIDDLEWARES'] = {}
    
    settings_dict['DOWNLOADER_MIDDLEWARES']['scrapy_ui.middlewares.puppeteer_middleware.PuppeteerMiddleware'] = 585
    settings_dict['PUPPETEER_ENABLED'] = True

# 使用例用のヘルパー関数
class PuppeteerRequestHelper:
    """Puppeteerリクエスト作成ヘルパー"""
    
    @staticmethod
    def spa_request(url: str, selectors: Dict[str, str], wait_for: str = None, **kwargs):
        """SPAスクレイピングリクエスト作成"""
        from scrapy import Request
        
        return Request(
            url=url,
            meta={
                'puppeteer': True,
                'puppeteer_config': {
                    'action': 'spa',
                    'selectors': selectors,
                    'wait_for': wait_for,
                    **kwargs
                }
            }
        )
    
    @staticmethod
    def screenshot_request(url: str, filename: str = None, **kwargs):
        """スクリーンショットリクエスト作成"""
        from scrapy import Request
        
        return Request(
            url=url,
            meta={
                'puppeteer': True,
                'puppeteer_config': {
                    'action': 'screenshot',
                    'filename': filename,
                    **kwargs
                }
            }
        )
    
    @staticmethod
    def pdf_request(url: str, filename: str = None, **kwargs):
        """PDFリクエスト作成"""
        from scrapy import Request
        
        return Request(
            url=url,
            meta={
                'puppeteer': True,
                'puppeteer_config': {
                    'action': 'pdf',
                    'filename': filename,
                    **kwargs
                }
            }
        )
