"""
Node.js Puppeteer Service Client
ScrapyUIからNode.jsサービスを呼び出すためのクライアントライブラリ
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

@dataclass
class NodeJSResponse:
    """Node.jsサービスからのレスポンス"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    user_id: Optional[str] = None

class NodeJSClient:
    """
    Node.js Puppeteerサービスクライアント（改良版）
    Yahoo.co.jpスクレイピング成功要因を反映
    """

    def __init__(self, base_url: str = "http://localhost:3001", timeout: int = 60):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
        self._session_created_externally = False

        # 成功要因を反映した設定
        self.default_config = {
            "timeout": 45000,  # Yahoo.co.jp成功時の設定
            "viewport": {"width": 1920, "height": 1080},
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "waitFor": "body",  # シンプルで効果的
            "screenshot": True
        }

    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        if self.session is None:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
            self._session_created_externally = False
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        if self.session and not self._session_created_externally:
            await self.session.close()
            self.session = None

    async def _ensure_session(self):
        """セッションの存在を確保"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
            self._session_created_externally = True

    async def close(self):
        """手動でセッションをクローズ"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> NodeJSResponse:
        """HTTP リクエストを送信"""
        url = urljoin(self.base_url, endpoint)

        # セッションの存在を確保
        await self._ensure_session()

        try:
            headers = {'Content-Type': 'application/json'}

            # 個別リクエストのタイムアウトを設定
            request_timeout = aiohttp.ClientTimeout(total=self.timeout.total)

            async with self.session.request(
                method,
                url,
                json=data if data else None,
                headers=headers,
                timeout=request_timeout
            ) as response:
                # レスポンスのContent-Typeをチェック
                content_type = response.headers.get('content-type', '').lower()

                if response.status in [200, 201]:
                    if 'application/json' in content_type:
                        try:
                            response_data = await response.json()
                        except ValueError as e:
                            logger.error(f"JSON parse error: {e}")
                            return NodeJSResponse(
                                success=False,
                                message=f'Invalid JSON response: {str(e)}',
                                error=f'JSON parse error: {str(e)}'
                            )

                        return NodeJSResponse(
                            success=response_data.get('success', True),
                            message=response_data.get('message', 'Success'),
                            data=response_data.get('data') or response_data.get('nodejs_response') or response_data,
                            user_id=response_data.get('user_id')
                        )
                    else:
                        # バイナリデータ（PDF、画像など）の場合
                        try:
                            binary_data = await response.read()
                            import base64

                            return NodeJSResponse(
                                success=True,
                                message='Binary data received',
                                data={
                                    'binary_data': base64.b64encode(binary_data).decode('utf-8'),
                                    'content_type': content_type,
                                    'size': len(binary_data)
                                }
                            )
                        except Exception as e:
                            logger.error(f"Binary data read error: {e}")
                            return NodeJSResponse(
                                success=False,
                                message=f'Binary data read error: {str(e)}',
                                error=str(e)
                            )
                else:
                    # エラーレスポンスの処理
                    try:
                        response_data = await response.json()
                        error_msg = response_data.get('error', f'HTTP {response.status}')
                    except (ValueError, aiohttp.ContentTypeError):
                        # JSONでない場合はテキストを取得
                        try:
                            error_text = await response.text()
                            error_msg = f'HTTP {response.status}: {error_text[:200]}'
                        except Exception:
                            error_msg = f'HTTP {response.status}'

                    return NodeJSResponse(
                        success=False,
                        message=f'Request failed: {error_msg}',
                        error=error_msg
                    )

        except asyncio.TimeoutError as e:
            logger.error(f"Request timeout: {e}")
            return NodeJSResponse(
                success=False,
                message=f'Request timeout: {str(e)}',
                error=f'Timeout after {self.timeout.total} seconds'
            )
        except aiohttp.ClientError as e:
            logger.error(f"Node.js service request failed: {e}")
            return NodeJSResponse(
                success=False,
                message=f'Connection error: {str(e)}',
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error in Node.js request: {e}")
            return NodeJSResponse(
                success=False,
                message=f'Unexpected error: {str(e)}',
                error=str(e)
            )

    async def health_check(self) -> NodeJSResponse:
        """ヘルスチェック"""
        return await self._request('GET', '/api/health')

    async def scrape_spa(self, request_data: Dict[str, Any]) -> NodeJSResponse:
        """SPAスクレイピング"""
        return await self._request('POST', '/api/scraping/spa', request_data)

    async def scrape_dynamic(self, request_data: Dict[str, Any]) -> NodeJSResponse:
        """動的コンテンツスクレイピング"""
        return await self._request('POST', '/api/scraping/dynamic', request_data)

    async def generate_pdf(self, request_data: Dict[str, Any]) -> NodeJSResponse:
        """PDF生成"""
        return await self._request('POST', '/api/pdf/generate', request_data)

    async def capture_screenshot(self, request_data: Dict[str, Any]) -> NodeJSResponse:
        """スクリーンショット取得"""
        return await self._request('POST', '/api/screenshot/capture', request_data)

    async def execute_workflow(self, workflow_id: str, variables: Optional[Dict] = None) -> NodeJSResponse:
        """ワークフロー実行"""
        data = {'variables': variables or {}}
        return await self._request('POST', f'/api/workflows/{workflow_id}/execute', data)

    async def create_workflow(self, workflow_definition: Dict[str, Any]) -> NodeJSResponse:
        """ワークフロー作成"""
        return await self._request('POST', '/api/workflows', workflow_definition)

    async def get_workflows(self) -> NodeJSResponse:
        """ワークフロー一覧取得"""
        return await self._request('GET', '/api/workflows')

    async def get_metrics(self) -> NodeJSResponse:
        """メトリクス取得"""
        return await self._request('GET', '/api/metrics')

    async def scrape_optimized(self, url: str, selectors: Dict[str, str] = None, **kwargs) -> NodeJSResponse:
        """
        最適化されたスクレイピング（Yahoo.co.jp成功要因を反映）

        Args:
            url: スクレイピング対象URL
            selectors: 抽出するセレクター辞書
            **kwargs: 追加設定

        Returns:
            NodeJSResponse: スクレイピング結果
        """
        # デフォルト設定をベースに構築
        config = self.default_config.copy()
        config.update(kwargs)

        # デフォルトセレクター（Yahoo.co.jp成功パターン）
        default_selectors = {
            "title": "title",
            "h1": "h1",
            "h2": "h2",
            "h3": "h3",
            "all_headings": "h1, h2, h3, h4, h5, h6",
            "content": "p, div, span",
            "links": "a[href]",
            "images": "img[src]"
        }

        if selectors:
            default_selectors.update(selectors)

        request_data = {
            "url": url,
            "waitFor": config.get("waitFor", "body"),
            "timeout": config.get("timeout", 45000),
            "viewport": config.get("viewport", {"width": 1920, "height": 1080}),
            "extractData": {
                "selectors": default_selectors
            },
            "screenshot": config.get("screenshot", True),
            "userAgent": config.get("userAgent", self.default_config["userAgent"])
        }

        return await self.scrape_spa(request_data)

    async def scrape_japanese_site(self, url: str, **kwargs) -> NodeJSResponse:
        """
        日本語サイト専用最適化スクレイピング
        Yahoo.co.jp等の日本語サイトに最適化
        """
        # 日本語サイト用の特別設定
        japanese_config = {
            "timeout": 60000,  # 日本語サイトは読み込みが重い場合が多い
            "waitFor": "body",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "viewport": {"width": 1920, "height": 1080}
        }
        japanese_config.update(kwargs)

        # 日本語サイト用セレクター
        japanese_selectors = {
            "title": "title",
            "h1": "h1",
            "h2": "h2",
            "h3": "h3",
            "news_headlines": "h1, h2, h3, .news-title, .headline, .title",
            "navigation": "nav, .nav, .menu, .gnav",
            "main_content": "main, .main, .content, .contents",
            "links": "a[href]",
            "images": "img[src]"
        }

        return await self.scrape_optimized(url, japanese_selectors, **japanese_config)

    async def scrape_with_retry(self, url: str, max_retries: int = 3, **kwargs) -> NodeJSResponse:
        """
        リトライ機能付きスクレイピング
        成功要因：堅牢なエラーハンドリング
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                # 指数バックオフで待機時間を調整
                if attempt > 0:
                    wait_time = (2 ** attempt) * 5  # 5, 10, 20秒
                    await asyncio.sleep(wait_time)
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {wait_time}s wait")

                response = await self.scrape_optimized(url, **kwargs)

                if response.success:
                    return response
                else:
                    last_error = response.error
                    logger.warning(f"Attempt {attempt + 1} failed: {response.error}")

            except Exception as e:
                last_error = str(e)
                logger.error(f"Attempt {attempt + 1} exception: {e}")

        # 全てのリトライが失敗
        return NodeJSResponse(
            success=False,
            message=f'All {max_retries} retry attempts failed',
            error=f'Last error: {last_error}'
        )

    async def batch_scrape(self, urls: list, delay: float = 5.0, **kwargs) -> list:
        """
        バッチスクレイピング（レート制限対応）
        成功要因：適切な遅延とセッション管理
        """
        results = []

        for i, url in enumerate(urls):
            try:
                # レート制限回避のための遅延
                if i > 0:
                    await asyncio.sleep(delay)

                logger.info(f"Scraping {i+1}/{len(urls)}: {url}")
                response = await self.scrape_optimized(url, **kwargs)

                results.append({
                    "url": url,
                    "success": response.success,
                    "data": response.data if response.success else None,
                    "error": response.error if not response.success else None,
                    "index": i
                })

            except Exception as e:
                logger.error(f"Batch scraping error for {url}: {e}")
                results.append({
                    "url": url,
                    "success": False,
                    "data": None,
                    "error": str(e),
                    "index": i
                })

        return results

# グローバルクライアントインスタンス
_global_client = None

async def get_nodejs_client(base_url: str = "http://localhost:3001") -> NodeJSClient:
    """Node.jsクライアントを取得（改良版シングルトン）"""
    global _global_client

    if _global_client is None or (_global_client.session and _global_client.session.closed):
        if _global_client:
            await _global_client.close()
        _global_client = NodeJSClient(base_url)

    return _global_client

async def close_global_client():
    """グローバルクライアントをクローズ"""
    global _global_client
    if _global_client:
        await _global_client.close()
        _global_client = None

# 便利関数（成功要因を反映）
async def scrape_spa_simple(url: str, selectors: Dict[str, str] = None, **kwargs) -> Dict[str, Any]:
    """
    簡単なSPAスクレイピング（改良版）
    Yahoo.co.jp成功要因を反映
    """
    async with NodeJSClient() as client:
        # 成功要因を反映した最適化スクレイピングを使用
        response = await client.scrape_optimized(url, selectors, **kwargs)

        if response.success:
            return response.data
        else:
            raise Exception(f"Scraping failed: {response.error}")

async def scrape_japanese_simple(url: str, **kwargs) -> Dict[str, Any]:
    """
    日本語サイト簡単スクレイピング
    Yahoo.co.jp等の日本語サイトに最適化
    """
    async with NodeJSClient() as client:
        response = await client.scrape_japanese_site(url, **kwargs)

        if response.success:
            return response.data
        else:
            raise Exception(f"Japanese site scraping failed: {response.error}")

async def scrape_with_retry_simple(url: str, max_retries: int = 3, **kwargs) -> Dict[str, Any]:
    """
    リトライ付き簡単スクレイピング
    堅牢なエラーハンドリング
    """
    async with NodeJSClient() as client:
        response = await client.scrape_with_retry(url, max_retries, **kwargs)

        if response.success:
            return response.data
        else:
            raise Exception(f"Scraping with retry failed: {response.error}")

async def batch_scrape_simple(urls: list, delay: float = 5.0, **kwargs) -> list:
    """
    バッチスクレイピング簡単版
    レート制限対応
    """
    async with NodeJSClient() as client:
        return await client.batch_scrape(urls, delay, **kwargs)

async def generate_pdf_simple(url: str, filename: str = None, **options) -> str:
    """簡単なPDF生成"""
    async with NodeJSClient() as client:
        request_data = {
            "url": url,
            "options": options
        }
        response = await client.generate_pdf(request_data)

        if response.success:
            # バイナリデータまたはbase64データを処理
            pdf_data = None
            if response.data.get('binary_data'):
                import base64
                pdf_data = base64.b64decode(response.data['binary_data'])
            elif response.data.get('pdf'):
                import base64
                pdf_data = base64.b64decode(response.data['pdf'])

            if pdf_data:
                if not filename:
                    from datetime import datetime
                    filename = f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

                with open(filename, 'wb') as f:
                    f.write(pdf_data)

                return filename
            else:
                raise Exception("No PDF data received")
        else:
            raise Exception(f"PDF generation failed: {response.error}")

async def capture_screenshot_simple(url: str, filename: str = None, **options) -> str:
    """簡単なスクリーンショット取得"""
    async with NodeJSClient() as client:
        request_data = {
            "url": url,
            "options": options
        }
        response = await client.capture_screenshot(request_data)

        if response.success:
            # バイナリデータまたはbase64データを処理
            screenshot_data = None
            if response.data.get('binary_data'):
                import base64
                screenshot_data = base64.b64decode(response.data['binary_data'])
            elif response.data.get('screenshot'):
                import base64
                screenshot_data = base64.b64decode(response.data['screenshot'])

            if screenshot_data:
                if not filename:
                    from datetime import datetime
                    ext = options.get('type', 'png')
                    filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

                with open(filename, 'wb') as f:
                    f.write(screenshot_data)

                return filename
            else:
                raise Exception("No screenshot data received")
        else:
            raise Exception(f"Screenshot capture failed: {response.error}")

# Scrapy統合用のヘルパー
class PuppeteerRequest:
    """Puppeteerリクエストヘルパー"""

    @staticmethod
    def spa_scraping(url: str, selectors: Dict[str, str], wait_for: str = None, **kwargs):
        """SPAスクレイピングリクエストデータ生成"""
        return {
            "url": url,
            "waitFor": wait_for,
            "extractData": {"selectors": selectors},
            **kwargs
        }

    @staticmethod
    def pdf_generation(url: str, format: str = "A4", **kwargs):
        """PDF生成リクエストデータ生成"""
        return {
            "url": url,
            "options": {
                "format": format,
                **kwargs
            }
        }

    @staticmethod
    def screenshot_capture(url: str, full_page: bool = True, **kwargs):
        """スクリーンショットリクエストデータ生成"""
        return {
            "url": url,
            "options": {
                "fullPage": full_page,
                **kwargs
            }
        }

# 使用例
if __name__ == "__main__":
    async def example():
        # 基本的な使用例
        async with NodeJSClient() as client:
            # ヘルスチェック
            health = await client.health_check()
            print(f"Health: {health.success}")

            # SPAスクレイピング
            spa_data = {
                "url": "https://example.com",
                "extractData": {
                    "selectors": {
                        "title": "h1",
                        "content": ".content"
                    }
                }
            }
            result = await client.scrape_spa(spa_data)
            print(f"Scraping result: {result.data}")

    # 実行
    asyncio.run(example())
