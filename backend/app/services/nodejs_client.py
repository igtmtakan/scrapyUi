import httpx
import asyncio
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class NodeJSServiceConfig(BaseModel):
    base_url: str = "http://localhost:3001"
    timeout: int = 30
    api_key: Optional[str] = None
    max_retries: int = 3

class NodeJSServiceResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: int

class NodeJSClient:
    def __init__(self, config: Optional[NodeJSServiceConfig] = None):
        self.config = config or NodeJSServiceConfig()
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "ScrapyUI-Backend/1.0"
        }
        if self.config.api_key:
            headers["x-api-key"] = self.config.api_key
        return headers

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> NodeJSServiceResponse:
        """Make HTTP request to Node.js service with retry logic"""

        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"Making request to Node.js service: {method} {endpoint}")
                logger.info(f"Request data: {data}")

                response = await self.client.request(
                    method=method,
                    url=endpoint,
                    json=data,
                    headers=self._get_headers()
                )

                if 200 <= response.status_code < 300:
                    return NodeJSServiceResponse(
                        success=True,
                        data=response.json(),
                        status_code=response.status_code
                    )
                else:
                    error_data = response.json() if response.content else {}
                    logger.error(f"Node.js service error: {response.status_code} - {error_data}")
                    error_message = error_data.get("error", f"HTTP {response.status_code}")
                    if "details" in error_data:
                        error_message += f" - Details: {error_data['details']}"
                    return NodeJSServiceResponse(
                        success=False,
                        error=error_message,
                        status_code=response.status_code,
                        data=error_data
                    )

            except httpx.TimeoutException:
                logger.warning(f"Timeout on attempt {attempt + 1} for {endpoint}")
                if attempt == self.config.max_retries - 1:
                    return NodeJSServiceResponse(
                        success=False,
                        error="Request timeout",
                        status_code=408
                    )
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff

            except httpx.ConnectError:
                logger.error(f"Connection error on attempt {attempt + 1} for {endpoint}")
                if attempt == self.config.max_retries - 1:
                    return NodeJSServiceResponse(
                        success=False,
                        error="Service unavailable",
                        status_code=503
                    )
                await asyncio.sleep(2 * (attempt + 1))

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                if attempt == self.config.max_retries - 1:
                    return NodeJSServiceResponse(
                        success=False,
                        error=f"Unexpected error: {str(e)}",
                        status_code=500
                    )
                await asyncio.sleep(1)

    async def health_check(self) -> NodeJSServiceResponse:
        """Check if Node.js service is healthy"""
        return await self._make_request("GET", "/api/health")

    async def test_connection(self, test_data: Optional[Dict[str, Any]] = None) -> NodeJSServiceResponse:
        """Test connection to Node.js service"""
        data = test_data or {"test": "connection", "timestamp": "2024-01-01T00:00:00Z"}
        return await self._make_request("POST", "/api/test", data)

    # Future Puppeteer methods (will be implemented when Puppeteer is added)
    async def scrape_spa(
        self,
        url: str,
        options: Optional[Dict[str, Any]] = None
    ) -> NodeJSServiceResponse:
        """Scrape Single Page Application (Future implementation)"""
        data = {
            "url": url,
            **(options or {})
        }
        return await self._make_request("POST", "/api/scraping/spa", data)

    async def scrape_dynamic_content(
        self,
        url: str,
        actions: Optional[list] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> NodeJSServiceResponse:
        """Scrape dynamic content with actions (Future implementation)"""
        data = {
            "url": url,
            "actions": actions or [],
            **(options or {})
        }
        return await self._make_request("POST", "/api/scraping/dynamic", data)

    async def generate_pdf(
        self,
        url: Optional[str] = None,
        html: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> NodeJSServiceResponse:
        """Generate PDF from URL or HTML (Future implementation)"""
        if not url and not html:
            return NodeJSServiceResponse(
                success=False,
                error="Either url or html must be provided",
                status_code=400
            )

        data = {
            "options": options or {}
        }
        if url:
            data["url"] = url
        if html:
            data["html"] = html

        return await self._make_request("POST", "/api/pdf/generate-base64", data)

    async def capture_screenshot(
        self,
        url: str,
        options: Optional[Dict[str, Any]] = None
    ) -> NodeJSServiceResponse:
        """Capture screenshot (Future implementation)"""
        data = {
            "url": url,
            "options": options or {}
        }
        return await self._make_request("POST", "/api/screenshot/capture-base64", data)

    # Workflow methods
    async def get_workflows(self) -> NodeJSServiceResponse:
        """Get all workflows"""
        return await self._make_request("GET", "/api/workflows")

    async def create_workflow(self, workflow_definition: Dict[str, Any]) -> NodeJSServiceResponse:
        """Create a new workflow"""
        return await self._make_request("POST", "/api/workflows", workflow_definition)

    async def execute_workflow(self, workflow_id: str, variables: Optional[Dict] = None) -> NodeJSServiceResponse:
        """Execute a workflow"""
        data = {'variables': variables or {}}
        return await self._make_request("POST", f"/api/workflows/{workflow_id}/execute", data)

    async def get_workflow(self, workflow_id: str) -> NodeJSServiceResponse:
        """Get a specific workflow by ID"""
        return await self._make_request("GET", f"/api/workflows/{workflow_id}")

    async def delete_workflow(self, workflow_id: str) -> NodeJSServiceResponse:
        """Delete a workflow"""
        return await self._make_request("DELETE", f"/api/workflows/{workflow_id}")

    async def get_workflow_executions(self, workflow_id: str) -> NodeJSServiceResponse:
        """Get workflow execution history"""
        return await self._make_request("GET", f"/api/workflows/{workflow_id}/executions")

    async def get_workflow_templates(self) -> NodeJSServiceResponse:
        """Get workflow templates"""
        return await self._make_request("GET", "/api/workflows/templates/list")

# Singleton instance
_nodejs_client = None

async def get_nodejs_client() -> NodeJSClient:
    """Get singleton NodeJS client instance"""
    global _nodejs_client
    if _nodejs_client is None:
        _nodejs_client = NodeJSClient()
    return _nodejs_client

async def close_nodejs_client():
    """Close NodeJS client connection"""
    global _nodejs_client
    if _nodejs_client:
        await _nodejs_client.client.aclose()
        _nodejs_client = None
