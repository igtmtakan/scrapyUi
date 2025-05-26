"""
テンプレート管理サービス
カスタムスパイダーテンプレートとプロジェクトテンプレートを管理
"""
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum


class TemplateType(Enum):
    SPIDER = "spider"
    PROJECT = "project"
    MIDDLEWARE = "middleware"
    PIPELINE = "pipeline"
    ITEM = "item"


@dataclass
class Template:
    id: str
    name: str
    description: str
    type: TemplateType
    content: str
    variables: List[str]  # テンプレート変数のリスト
    tags: List[str]
    author: str
    created_at: str
    updated_at: str
    usage_count: int = 0
    is_public: bool = True
    category: str = "general"


class TemplateService:
    """テンプレート管理サービス"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        self.templates_file = self.templates_dir / "templates.json"
        self.templates: Dict[str, Template] = {}
        self.load_templates()
        self._initialize_default_templates()
    
    def load_templates(self):
        """テンプレートを読み込み"""
        if self.templates_file.exists():
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for template_data in data:
                        template = Template(**template_data)
                        template.type = TemplateType(template.type)
                        self.templates[template.id] = template
            except Exception as e:
                print(f"Error loading templates: {e}")
    
    def save_templates(self):
        """テンプレートを保存"""
        try:
            data = []
            for template in self.templates.values():
                template_dict = asdict(template)
                template_dict['type'] = template.type.value
                data.append(template_dict)
            
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving templates: {e}")
    
    def create_template(
        self,
        name: str,
        description: str,
        template_type: TemplateType,
        content: str,
        variables: List[str] = None,
        tags: List[str] = None,
        author: str = "ScrapyUI",
        category: str = "custom"
    ) -> str:
        """新しいテンプレートを作成"""
        template_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        template = Template(
            id=template_id,
            name=name,
            description=description,
            type=template_type,
            content=content,
            variables=variables or [],
            tags=tags or [],
            author=author,
            created_at=now,
            updated_at=now,
            category=category
        )
        
        self.templates[template_id] = template
        self.save_templates()
        return template_id
    
    def update_template(
        self,
        template_id: str,
        name: str = None,
        description: str = None,
        content: str = None,
        variables: List[str] = None,
        tags: List[str] = None,
        category: str = None
    ) -> bool:
        """テンプレートを更新"""
        if template_id not in self.templates:
            return False
        
        template = self.templates[template_id]
        
        if name is not None:
            template.name = name
        if description is not None:
            template.description = description
        if content is not None:
            template.content = content
        if variables is not None:
            template.variables = variables
        if tags is not None:
            template.tags = tags
        if category is not None:
            template.category = category
        
        template.updated_at = datetime.now().isoformat()
        self.save_templates()
        return True
    
    def delete_template(self, template_id: str) -> bool:
        """テンプレートを削除"""
        if template_id in self.templates:
            del self.templates[template_id]
            self.save_templates()
            return True
        return False
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """テンプレートを取得"""
        return self.templates.get(template_id)
    
    def list_templates(
        self,
        template_type: TemplateType = None,
        category: str = None,
        tags: List[str] = None,
        author: str = None
    ) -> List[Template]:
        """テンプレート一覧を取得"""
        templates = list(self.templates.values())
        
        if template_type:
            templates = [t for t in templates if t.type == template_type]
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]
        
        if author:
            templates = [t for t in templates if t.author == author]
        
        # 使用回数順でソート
        templates.sort(key=lambda t: t.usage_count, reverse=True)
        return templates
    
    def render_template(self, template_id: str, variables: Dict[str, str]) -> Tuple[bool, str]:
        """テンプレートを変数で置換してレンダリング"""
        template = self.get_template(template_id)
        if not template:
            return False, "Template not found"
        
        try:
            content = template.content
            for var_name, var_value in variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                content = content.replace(placeholder, var_value)
            
            # 使用回数を増加
            template.usage_count += 1
            self.save_templates()
            
            return True, content
        except Exception as e:
            return False, f"Error rendering template: {str(e)}"
    
    def extract_variables(self, content: str) -> List[str]:
        """テンプレート内の変数を抽出"""
        import re
        pattern = r'\{\{(\w+)\}\}'
        variables = re.findall(pattern, content)
        return list(set(variables))
    
    def _initialize_default_templates(self):
        """デフォルトテンプレートを初期化"""
        if not self.templates:
            self._create_default_spider_templates()
            self._create_default_middleware_templates()
            self._create_default_pipeline_templates()
            self._create_default_item_templates()
    
    def _create_default_spider_templates(self):
        """デフォルトスパイダーテンプレートを作成"""
        # 基本スパイダーテンプレート
        basic_spider = '''import scrapy
from scrapy_playwright.page import PageCoroutine
from {{project_name}}.items import {{item_class}}


class {{spider_class}}(scrapy.Spider):
    name = '{{spider_name}}'
    allowed_domains = [{{allowed_domains}}]
    start_urls = [{{start_urls}}]

    custom_settings = {
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_page_coroutines": [
                        PageCoroutine("wait_for_selector", "body"),
                        PageCoroutine("wait_for_timeout", 1000),
                    ],
                },
                callback=self.parse
            )

    async def parse(self, response):
        # データの抽出
        items = response.css('{{item_selector}}')
        for item in items:
            scrapy_item = {{item_class}}()
            scrapy_item['{{field_name}}'] = item.css('{{field_selector}}').get()
            yield scrapy_item

        # 次のページ
        next_page = response.css('{{next_page_selector}}').get()
        if next_page:
            yield response.follow(
                next_page,
                meta={"playwright": True},
                callback=self.parse
            )
'''
        
        self.create_template(
            name="Basic Playwright Spider",
            description="基本的なPlaywright対応スパイダー",
            template_type=TemplateType.SPIDER,
            content=basic_spider,
            variables=["project_name", "item_class", "spider_class", "spider_name", 
                      "allowed_domains", "start_urls", "item_selector", "field_name", 
                      "field_selector", "next_page_selector"],
            tags=["playwright", "basic", "spider"],
            author="ScrapyUI",
            category="default"
        )
        
        # E-commerceスパイダーテンプレート
        ecommerce_spider = '''import scrapy
from scrapy_playwright.page import PageCoroutine
from {{project_name}}.items import ProductItem


class {{spider_class}}(scrapy.Spider):
    name = '{{spider_name}}'
    allowed_domains = [{{allowed_domains}}]
    start_urls = [{{start_urls}}]

    custom_settings = {
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_CONTEXTS": {
            "default": {
                "viewport": {"width": 1280, "height": 800},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
        },
    }

    async def parse(self, response):
        # 商品リストページの解析
        products = response.css('{{product_selector}}')
        for product in products:
            product_url = product.css('{{product_url_selector}}').get()
            if product_url:
                yield response.follow(
                    product_url,
                    meta={"playwright": True},
                    callback=self.parse_product
                )

        # 次のページ
        next_page = response.css('{{next_page_selector}}').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    async def parse_product(self, response):
        # 商品詳細ページの解析
        item = ProductItem()
        item['name'] = response.css('{{product_name_selector}}').get()
        item['price'] = response.css('{{price_selector}}').re_first(r'[\\d,]+')
        item['description'] = response.css('{{description_selector}}').get()
        item['images'] = response.css('{{images_selector}}').getall()
        item['url'] = response.url
        
        yield item
'''
        
        self.create_template(
            name="E-commerce Product Spider",
            description="E-commerce商品スクレイピング用スパイダー",
            template_type=TemplateType.SPIDER,
            content=ecommerce_spider,
            variables=["project_name", "spider_class", "spider_name", "allowed_domains", 
                      "start_urls", "product_selector", "product_url_selector", 
                      "next_page_selector", "product_name_selector", "price_selector",
                      "description_selector", "images_selector"],
            tags=["playwright", "ecommerce", "product"],
            author="ScrapyUI",
            category="default"
        )
    
    def _create_default_middleware_templates(self):
        """デフォルトミドルウェアテンプレートを作成"""
        user_agent_middleware = '''import random
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware


class {{middleware_class}}(UserAgentMiddleware):
    """ランダムユーザーエージェントミドルウェア"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]

    def process_request(self, request, spider):
        ua = random.choice(self.user_agents)
        request.headers['User-Agent'] = ua
        return None
'''
        
        self.create_template(
            name="Random User Agent Middleware",
            description="ランダムユーザーエージェントミドルウェア",
            template_type=TemplateType.MIDDLEWARE,
            content=user_agent_middleware,
            variables=["middleware_class"],
            tags=["middleware", "user-agent", "random"],
            author="ScrapyUI",
            category="default"
        )
    
    def _create_default_pipeline_templates(self):
        """デフォルトパイプラインテンプレートを作成"""
        json_pipeline = '''import json
from pathlib import Path
from datetime import datetime
from itemadapter import ItemAdapter


class {{pipeline_class}}:
    """JSON出力パイプライン"""
    
    def open_spider(self, spider):
        self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{spider.name}_{timestamp}.json"
        self.file = open(self.output_dir / filename, 'w', encoding='utf-8')
        self.file.write('[\\n')
        self.first_item = True

    def close_spider(self, spider):
        self.file.write('\\n]')
        self.file.close()

    def process_item(self, item, spider):
        if not self.first_item:
            self.file.write(',\\n')
        else:
            self.first_item = False
        
        line = json.dumps(ItemAdapter(item).asdict(), ensure_ascii=False, indent=2)
        self.file.write(line)
        return item
'''
        
        self.create_template(
            name="JSON Export Pipeline",
            description="JSON形式でデータを出力するパイプライン",
            template_type=TemplateType.PIPELINE,
            content=json_pipeline,
            variables=["pipeline_class"],
            tags=["pipeline", "json", "export"],
            author="ScrapyUI",
            category="default"
        )
    
    def _create_default_item_templates(self):
        """デフォルトアイテムテンプレートを作成"""
        basic_item = '''import scrapy
from itemloaders.processors import TakeFirst, MapCompose
from w3lib.html import remove_tags


def clean_text(value):
    """テキストをクリーニング"""
    if value:
        return value.strip().replace('\\n', ' ').replace('\\r', ' ')
    return value


class {{item_class}}(scrapy.Item):
    """{{item_description}}"""
    
    {{fields}}
'''
        
        self.create_template(
            name="Basic Item",
            description="基本的なアイテムクラス",
            template_type=TemplateType.ITEM,
            content=basic_item,
            variables=["item_class", "item_description", "fields"],
            tags=["item", "basic"],
            author="ScrapyUI",
            category="default"
        )
