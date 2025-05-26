import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import tempfile
import uuid
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

class PlaywrightCrawlerService:
    """Playwrightベースのクローラーサービス"""
    
    def __init__(self, base_projects_dir: str = "./crawler_projects"):
        self.base_projects_dir = Path(base_projects_dir)
        self.base_projects_dir.mkdir(exist_ok=True)
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    async def initialize(self):
        """Playwrightを初期化"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
    
    async def cleanup(self):
        """リソースをクリーンアップ"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    def create_project(self, project_name: str, project_path: str) -> bool:
        """新しいクローラープロジェクトを作成"""
        try:
            full_path = self.base_projects_dir / project_path
            full_path.mkdir(parents=True, exist_ok=True)
            
            # プロジェクト設定ファイルを作成
            config = {
                "name": project_name,
                "version": "1.0.0",
                "description": f"Playwright crawler project: {project_name}",
                "browser_settings": {
                    "browser_type": "chromium",
                    "headless": True,
                    "viewport": {"width": 1280, "height": 720},
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                "crawl_settings": {
                    "delay": 1000,
                    "timeout": 30000,
                    "retry_count": 3
                }
            }
            
            config_file = full_path / "crawler_config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # crawlersディレクトリを作成
            crawlers_dir = full_path / "crawlers"
            crawlers_dir.mkdir(exist_ok=True)
            
            # __init__.pyファイルを作成
            init_file = crawlers_dir / "__init__.py"
            init_file.write_text("# Crawlers module")
            
            return True
            
        except Exception as e:
            raise Exception(f"Error creating project: {str(e)}")
    
    def delete_project(self, project_path: str) -> bool:
        """クローラープロジェクトを削除"""
        try:
            full_path = self.base_projects_dir / project_path
            if full_path.exists():
                import shutil
                shutil.rmtree(full_path)
            return True
        except Exception as e:
            raise Exception(f"Error deleting project: {str(e)}")
    
    def get_project_crawlers(self, project_path: str) -> List[str]:
        """プロジェクト内のクローラー一覧を取得"""
        try:
            full_path = self.base_projects_dir / project_path
            crawlers_dir = full_path / "crawlers"
            
            if not crawlers_dir.exists():
                return []
            
            crawler_files = []
            for file in crawlers_dir.glob("*.py"):
                if file.name != "__init__.py":
                    crawler_files.append(file.stem)
            
            return crawler_files
            
        except Exception as e:
            raise Exception(f"Error getting crawlers: {str(e)}")
    
    def create_crawler(self, project_path: str, crawler_name: str, template: str = "basic") -> bool:
        """新しいクローラーを作成"""
        try:
            full_path = self.base_projects_dir / project_path
            crawlers_dir = full_path / "crawlers"
            crawler_file = crawlers_dir / f"{crawler_name}.py"
            
            # テンプレートに基づいてクローラーコードを生成
            template_code = self._get_crawler_template(crawler_name, template)
            
            with open(crawler_file, 'w', encoding='utf-8') as f:
                f.write(template_code)
            
            return True
            
        except Exception as e:
            raise Exception(f"Error creating crawler: {str(e)}")
    
    def _get_crawler_template(self, crawler_name: str, template: str) -> str:
        """クローラーテンプレートを取得"""
        if template == "basic":
            return f'''import asyncio
from playwright.async_api import async_playwright, Page
from typing import Dict, List, Any, Optional

class {crawler_name.capitalize()}Crawler:
    """
    {crawler_name} crawler using Playwright
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {{}}
        self.results = []
    
    async def crawl(self, urls: List[str]) -> List[Dict[str, Any]]:
        """メインのクローリング関数"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.config.get('headless', True)
            )
            
            try:
                for url in urls:
                    page = await browser.new_page()
                    await page.goto(url)
                    
                    # ここにスクレイピングロジックを追加
                    data = await self.extract_data(page, url)
                    if data:
                        self.results.append(data)
                    
                    await page.close()
                    
                    # 遅延
                    delay = self.config.get('delay', 1000)
                    await asyncio.sleep(delay / 1000)
                
                return self.results
                
            finally:
                await browser.close()
    
    async def extract_data(self, page: Page, url: str) -> Optional[Dict[str, Any]]:
        """データ抽出ロジック（カスタマイズ必要）"""
        try:
            title = await page.title()
            
            return {{
                'url': url,
                'title': title,
                'timestamp': '{datetime.now().isoformat()}'
            }}
            
        except Exception as e:
            print(f"Error extracting data from {{url}}: {{e}}")
            return None

# 使用例
if __name__ == "__main__":
    crawler = {crawler_name.capitalize()}Crawler()
    urls = ["https://example.com"]
    
    async def main():
        results = await crawler.crawl(urls)
        for result in results:
            print(result)
    
    asyncio.run(main())
'''
        
        elif template == "ecommerce":
            return f'''import asyncio
from playwright.async_api import async_playwright, Page
from typing import Dict, List, Any, Optional

class {crawler_name.capitalize()}Crawler:
    """
    E-commerce crawler using Playwright
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {{}}
        self.results = []
    
    async def crawl(self, urls: List[str]) -> List[Dict[str, Any]]:
        """メインのクローリング関数"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.config.get('headless', True)
            )
            
            try:
                for url in urls:
                    page = await browser.new_page()
                    await page.goto(url, wait_until='networkidle')
                    
                    # 商品データを抽出
                    products = await self.extract_products(page, url)
                    self.results.extend(products)
                    
                    await page.close()
                    
                    # 遅延
                    delay = self.config.get('delay', 1000)
                    await asyncio.sleep(delay / 1000)
                
                return self.results
                
            finally:
                await browser.close()
    
    async def extract_products(self, page: Page, url: str) -> List[Dict[str, Any]]:
        """商品データ抽出"""
        try:
            products = []
            
            # 商品要素を取得（セレクターは実際のサイトに合わせて調整）
            product_elements = await page.query_selector_all('.product-item')
            
            for element in product_elements:
                try:
                    name = await element.query_selector('.product-name')
                    price = await element.query_selector('.product-price')
                    image = await element.query_selector('.product-image')
                    
                    product_data = {{
                        'name': await name.inner_text() if name else '',
                        'price': await price.inner_text() if price else '',
                        'image_url': await image.get_attribute('src') if image else '',
                        'source_url': url,
                        'timestamp': '{datetime.now().isoformat()}'
                    }}
                    
                    products.append(product_data)
                    
                except Exception as e:
                    print(f"Error extracting product: {{e}}")
                    continue
            
            return products
            
        except Exception as e:
            print(f"Error extracting products from {{url}}: {{e}}")
            return []

# 使用例
if __name__ == "__main__":
    crawler = {crawler_name.capitalize()}Crawler()
    urls = ["https://example-shop.com/products"]
    
    async def main():
        results = await crawler.crawl(urls)
        for result in results:
            print(result)
    
    asyncio.run(main())
'''
        
        else:
            # デフォルトはbasicテンプレート
            return self._get_crawler_template(crawler_name, "basic")
    
    def get_crawler_code(self, project_path: str, crawler_name: str) -> str:
        """クローラーのコードを取得"""
        try:
            full_path = self.base_projects_dir / project_path
            crawler_file = full_path / "crawlers" / f"{crawler_name}.py"
            
            if not crawler_file.exists():
                raise Exception(f"Crawler file not found: {crawler_file}")
            
            with open(crawler_file, 'r', encoding='utf-8') as f:
                return f.read()
                
        except Exception as e:
            raise Exception(f"Error reading crawler code: {str(e)}")
    
    def save_crawler_code(self, project_path: str, crawler_name: str, code: str) -> bool:
        """クローラーのコードを保存"""
        try:
            full_path = self.base_projects_dir / project_path
            crawler_file = full_path / "crawlers" / f"{crawler_name}.py"
            
            # ディレクトリが存在しない場合は作成
            crawler_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(crawler_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            return True
            
        except Exception as e:
            raise Exception(f"Error saving crawler code: {str(e)}")
    
    def validate_crawler_code(self, code: str) -> Dict[str, Any]:
        """クローラーコードの構文チェック"""
        try:
            # 一時ファイルに書き込んで構文チェック
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Pythonの構文チェック
                with open(temp_file, 'r') as f:
                    compile(f.read(), temp_file, 'exec')
                
                return {"valid": True, "errors": []}
                
            except SyntaxError as e:
                return {
                    "valid": False,
                    "errors": [f"Syntax error at line {e.lineno}: {e.msg}"]
                }
            finally:
                os.unlink(temp_file)
                
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"]
            }
