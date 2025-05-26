import React from 'react'
import { Search, Code, Filter, FileText } from 'lucide-react'
import { Template } from '../types'

export const parsingTemplates: Template[] = [
  {
    id: 'bs4-advanced-spider',
    name: 'BeautifulSoup4 Advanced Parser',
    description: 'BeautifulSoup4を使った高度なHTMLパーシング',
    icon: <Search className="w-5 h-5" />,
    category: 'parsing',
    code: `import scrapy
from bs4 import BeautifulSoup, Comment
import re
import json
from urllib.parse import urljoin, urlparse
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class BS4AdvancedSpider(scrapy.Spider):
    name = 'bs4_advanced_spider'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'ScrapyUI BS4 Advanced Spider 1.0',
    }

    def parse(self, response):
        debug_print(f"Processing: {response.url}")

        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. 基本的な要素抽出
        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else None

        # 2. 複数要素の抽出
        headings = []
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            elements = soup.find_all(tag)
            for elem in elements:
                headings.append({
                    'tag': tag,
                    'text': elem.get_text(strip=True),
                    'id': elem.get('id'),
                    'class': elem.get('class')
                })

        # 3. 属性による検索
        images = []
        for img in soup.find_all('img', src=True):
            images.append({
                'src': urljoin(response.url, img['src']),
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'width': img.get('width'),
                'height': img.get('height')
            })

        # 4. CSSセレクタを使った抽出
        navigation_links = []
        nav_elements = soup.select('nav a, .navigation a, .menu a')
        for link in nav_elements:
            href = link.get('href')
            if href:
                navigation_links.append({
                    'text': link.get_text(strip=True),
                    'href': urljoin(response.url, href),
                    'class': link.get('class')
                })

        # 5. 親子関係を利用した抽出
        articles = []
        for article in soup.find_all(['article', 'div'], class_=re.compile(r'(post|article|content)')):
            article_data = {
                'title': None,
                'content': None,
                'author': None,
                'date': None,
                'tags': []
            }

            # タイトル検索
            title_elem = article.find(['h1', 'h2', 'h3'], class_=re.compile(r'(title|heading)'))
            if title_elem:
                article_data['title'] = title_elem.get_text(strip=True)

            # コンテンツ検索
            content_elem = article.find(['div', 'p'], class_=re.compile(r'(content|body|text)'))
            if content_elem:
                article_data['content'] = content_elem.get_text(strip=True)[:200]

            # メタ情報検索
            meta_elem = article.find(['div', 'span'], class_=re.compile(r'(meta|info|author|date)'))
            if meta_elem:
                article_data['author'] = meta_elem.get_text(strip=True)

            # タグ検索
            tag_elements = article.find_all(['span', 'a'], class_=re.compile(r'(tag|category|label)'))
            for tag_elem in tag_elements:
                article_data['tags'].append(tag_elem.get_text(strip=True))

            if article_data['title'] or article_data['content']:
                articles.append(article_data)

        # 6. コメントの抽出
        comments = []
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment_text = comment.strip()
            if comment_text and len(comment_text) > 10:
                comments.append(comment_text)

        # 7. テーブルデータの抽出
        tables = []
        for table in soup.find_all('table'):
            table_data = {
                'headers': [],
                'rows': []
            }

            # ヘッダー抽出
            header_row = table.find('tr')
            if header_row:
                headers = header_row.find_all(['th', 'td'])
                table_data['headers'] = [h.get_text(strip=True) for h in headers]

            # データ行抽出
            rows = table.find_all('tr')[1:]  # ヘッダー行をスキップ
            for row in rows[:5]:  # 最初の5行のみ
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text(strip=True) for cell in cells]
                if row_data:
                    table_data['rows'].append(row_data)

            if table_data['headers'] or table_data['rows']:
                tables.append(table_data)

        # 8. フォームの抽出
        forms = []
        for form in soup.find_all('form'):
            form_data = {
                'action': form.get('action'),
                'method': form.get('method', 'get'),
                'fields': []
            }

            # 入力フィールド抽出
            inputs = form.find_all(['input', 'select', 'textarea'])
            for input_elem in inputs:
                field_data = {
                    'type': input_elem.get('type', input_elem.name),
                    'name': input_elem.get('name'),
                    'id': input_elem.get('id'),
                    'placeholder': input_elem.get('placeholder'),
                    'required': input_elem.has_attr('required')
                }
                form_data['fields'].append(field_data)

            if form_data['fields']:
                forms.append(form_data)

        # データを構造化
        parsed_data = {
            'url': response.url,
            'title': title_text,
            'headings': headings[:10],  # 最初の10個
            'images': images[:10],      # 最初の10個
            'navigation_links': navigation_links[:10],
            'articles': articles[:5],   # 最初の5個
            'comments': comments[:5],   # 最初の5個
            'tables': tables[:3],       # 最初の3個
            'forms': forms[:3],         # 最初の3個
            'stats': {
                'total_headings': len(headings),
                'total_images': len(images),
                'total_links': len(navigation_links),
                'total_articles': len(articles),
                'total_comments': len(comments),
                'total_tables': len(tables),
                'total_forms': len(forms)
            }
        }

        debug_print(f"Extracted data from: {response.url}")
        debug_pprint(parsed_data['stats'])

        yield parsed_data

        # 内部リンクをフォロー
        for link in navigation_links[:3]:
            if link['href'] and urlparse(link['href']).netloc in self.allowed_domains:
                yield response.follow(link['href'], self.parse)
`
  },
  {
    id: 'css-selector-spider',
    name: 'CSS3/4 Selector Master',
    description: 'CSS3/4セレクタを活用した高度な要素抽出',
    icon: <Code className="w-5 h-5" />,
    category: 'parsing',
    code: `import scrapy
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urljoin
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class CSSAdvancedSpider(scrapy.Spider):
    name = 'css_advanced_spider'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'ScrapyUI CSS Advanced Spider 1.0',
    }

    def parse(self, response):
        debug_print(f"Processing: {response.url}")

        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. 基本的なCSSセレクタ
        basic_selectors = {
            'title': soup.select_one('title'),
            'main_heading': soup.select_one('h1'),
            'all_paragraphs': soup.select('p'),
            'all_links': soup.select('a[href]')
        }

        # 2. 属性セレクタ
        attribute_selectors = {
            'external_links': soup.select('a[href^="http"]'),
            'email_links': soup.select('a[href^="mailto:"]'),
            'images_with_alt': soup.select('img[alt]'),
            'required_inputs': soup.select('input[required]'),
            'placeholder_inputs': soup.select('input[placeholder]')
        }

        # 3. 疑似クラスセレクタ
        pseudo_selectors = {
            'first_paragraph': soup.select('p:first-child'),
            'last_list_item': soup.select('li:last-child'),
            'even_table_rows': soup.select('tr:nth-child(even)'),
            'odd_table_rows': soup.select('tr:nth-child(odd)'),
            'third_elements': soup.select('*:nth-child(3)')
        }

        # 4. 組み合わせセレクタ
        combination_selectors = {
            'nav_links': soup.select('nav a, .navigation a, .menu a'),
            'article_headings': soup.select('article h1, article h2, article h3'),
            'form_inputs': soup.select('form input, form select, form textarea'),
            'content_images': soup.select('.content img, .post img, article img')
        }

        # 5. 高度なセレクタ
        advanced_selectors = {
            'data_attributes': soup.select('[data-id], [data-value], [data-type]'),
            'class_contains': soup.select('[class*="btn"], [class*="button"]'),
            'id_starts_with': soup.select('[id^="menu"], [id^="nav"]'),
            'href_ends_with': soup.select('a[href$=".pdf"], a[href$=".doc"]'),
            'not_selector': soup.select('a:not([href^="http"])')
        }

        # 6. 構造的セレクタ
        structural_selectors = {
            'direct_children': soup.select('ul > li'),
            'descendants': soup.select('div p'),
            'adjacent_siblings': soup.select('h1 + p'),
            'general_siblings': soup.select('h1 ~ p')
        }

        # 7. フォーム関連セレクタ
        form_selectors = {
            'text_inputs': soup.select('input[type="text"]'),
            'checkboxes': soup.select('input[type="checkbox"]'),
            'radio_buttons': soup.select('input[type="radio"]'),
            'submit_buttons': soup.select('input[type="submit"], button[type="submit"]'),
            'disabled_elements': soup.select(':disabled'),
            'enabled_elements': soup.select('input:not(:disabled)')
        }

        # データ抽出関数
        def extract_element_data(elements, limit=10):
            data = []
            for elem in elements[:limit]:
                elem_data = {
                    'tag': elem.name,
                    'text': elem.get_text(strip=True)[:100],
                    'attributes': dict(elem.attrs) if elem.attrs else {},
                    'classes': elem.get('class', []),
                    'id': elem.get('id')
                }
                data.append(elem_data)
            return data

        # 結果をまとめる
        css_extraction_results = {
            'url': response.url,
            'basic_selectors': {
                'title': basic_selectors['title'].get_text(strip=True) if basic_selectors['title'] else None,
                'main_heading': basic_selectors['main_heading'].get_text(strip=True) if basic_selectors['main_heading'] else None,
                'paragraph_count': len(basic_selectors['all_paragraphs']),
                'link_count': len(basic_selectors['all_links'])
            },
            'attribute_selectors': {
                'external_links': extract_element_data(attribute_selectors['external_links'], 5),
                'email_links': extract_element_data(attribute_selectors['email_links'], 5),
                'images_with_alt': extract_element_data(attribute_selectors['images_with_alt'], 5),
                'required_inputs': extract_element_data(attribute_selectors['required_inputs'], 5)
            },
            'pseudo_selectors': {
                'first_paragraphs': extract_element_data(pseudo_selectors['first_paragraph'], 3),
                'last_list_items': extract_element_data(pseudo_selectors['last_list_item'], 3),
                'even_rows': extract_element_data(pseudo_selectors['even_table_rows'], 3)
            },
            'combination_selectors': {
                'navigation_links': extract_element_data(combination_selectors['nav_links'], 5),
                'article_headings': extract_element_data(combination_selectors['article_headings'], 5),
                'form_inputs': extract_element_data(combination_selectors['form_inputs'], 5)
            },
            'advanced_selectors': {
                'data_elements': extract_element_data(advanced_selectors['data_attributes'], 5),
                'button_elements': extract_element_data(advanced_selectors['class_contains'], 5),
                'menu_elements': extract_element_data(advanced_selectors['id_starts_with'], 5)
            },
            'structural_selectors': {
                'direct_children': extract_element_data(structural_selectors['direct_children'], 5),
                'adjacent_siblings': extract_element_data(structural_selectors['adjacent_siblings'], 3)
            },
            'form_selectors': {
                'text_inputs': extract_element_data(form_selectors['text_inputs'], 5),
                'checkboxes': extract_element_data(form_selectors['checkboxes'], 5),
                'submit_buttons': extract_element_data(form_selectors['submit_buttons'], 3)
            }
        }

        debug_print(f"CSS selector extraction completed for: {response.url}")
        debug_pprint({
            'total_elements_found': sum([
                len(basic_selectors['all_paragraphs']),
                len(basic_selectors['all_links']),
                len(attribute_selectors['external_links']),
                len(combination_selectors['nav_links'])
            ])
        })

        yield css_extraction_results

        # 次のページへのリンクをフォロー
        next_links = soup.select('a[href*="next"], a[href*="page"], .pagination a')
        for link in next_links[:2]:
            href = link.get('href')
            if href:
                yield response.follow(urljoin(response.url, href), self.parse)
`
  },
  {
    id: 'regex-pattern-spider',
    name: 'Regex Pattern Extractor',
    description: '正規表現を使った高度なパターンマッチング',
    icon: <Filter className="w-5 h-5" />,
    category: 'parsing',
    code: `import scrapy
import re
import json
from urllib.parse import urljoin, urlparse
from datetime import datetime
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class RegexPatternSpider(scrapy.Spider):
    name = 'regex_pattern_spider'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'ScrapyUI Regex Pattern Spider 1.0',
    }

    def __init__(self):
        # 正規表現パターンを定義
        self.patterns = {
            # 基本的なパターン
            'email': re.compile(r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'),
            'phone': re.compile(r'\\b(?:\\+?1[-.]?)?\\(?([0-9]{3})\\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\\b'),
            'url': re.compile(r'https?://(?:[-\\w.])+(?:[:\\d]+)?(?:/(?:[\\w/_.])*(?:\\?(?:[\\w&=%.])*)?(?:#(?:[\\w.])*)?)?'),
            'ip_address': re.compile(r'\\b(?:[0-9]{1,3}\\.){3}[0-9]{1,3}\\b'),

            # 日付パターン
            'date_iso': re.compile(r'\\b\\d{4}-\\d{2}-\\d{2}\\b'),
            'date_us': re.compile(r'\\b\\d{1,2}/\\d{1,2}/\\d{4}\\b'),
            'date_eu': re.compile(r'\\b\\d{1,2}\\.\\d{1,2}\\.\\d{4}\\b'),
            'time': re.compile(r'\\b\\d{1,2}:\\d{2}(?::\\d{2})?(?:\\s?[AP]M)?\\b'),

            # 価格パターン
            'price_dollar': re.compile(r'\\$\\d{1,3}(?:,\\d{3})*(?:\\.\\d{2})?'),
            'price_yen': re.compile(r'¥\\d{1,3}(?:,\\d{3})*'),
            'price_euro': re.compile(r'€\\d{1,3}(?:,\\d{3})*(?:\\.\\d{2})?'),

            # IDパターン
            'credit_card': re.compile(r'\\b\\d{4}[-\\s]?\\d{4}[-\\s]?\\d{4}[-\\s]?\\d{4}\\b'),
            'ssn': re.compile(r'\\b\\d{3}-\\d{2}-\\d{4}\\b'),
            'zip_code': re.compile(r'\\b\\d{5}(?:-\\d{4})?\\b'),

            # HTMLタグパターン
            'html_tags': re.compile(r'<[^>]+>'),
            'script_content': re.compile(r'<script[^>]*>(.*?)</script>', re.DOTALL | re.IGNORECASE),
            'style_content': re.compile(r'<style[^>]*>(.*?)</style>', re.DOTALL | re.IGNORECASE),

            # ソーシャルメディア
            'twitter_handle': re.compile(r'@[A-Za-z0-9_]+'),
            'hashtag': re.compile(r'#[A-Za-z0-9_]+'),

            # ファイル拡張子
            'image_files': re.compile(r'\\b\\w+\\.(jpg|jpeg|png|gif|bmp|svg)\\b', re.IGNORECASE),
            'document_files': re.compile(r'\\b\\w+\\.(pdf|doc|docx|xls|xlsx|ppt|pptx)\\b', re.IGNORECASE),

            # 数値パターン
            'integers': re.compile(r'\\b\\d+\\b'),
            'decimals': re.compile(r'\\b\\d+\\.\\d+\\b'),
            'percentages': re.compile(r'\\b\\d+(?:\\.\\d+)?%\\b'),

            # カスタムパターン（サイト固有）
            'product_id': re.compile(r'\\b[A-Z]{2,3}\\d{4,8}\\b'),
            'order_number': re.compile(r'\\b(?:ORDER|ORD)[-_]?\\d{6,10}\\b', re.IGNORECASE),
        }

    def extract_patterns(self, text):
        """テキストから各パターンを抽出"""
        results = {}

        for pattern_name, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                # 重複を除去し、最初の10個まで
                unique_matches = list(set(matches))[:10]
                results[pattern_name] = {
                    'matches': unique_matches,
                    'count': len(matches),
                    'unique_count': len(unique_matches)
                }

        return results

    def parse(self, response):
        debug_print(f"Processing: {response.url}")

        # ページのテキストコンテンツを取得
        page_text = response.text
        body_text = ' '.join(response.css('body *::text').getall())

        # 基本パターンの抽出
        pattern_results = self.extract_patterns(page_text)
        body_pattern_results = self.extract_patterns(body_text)

        # 結果をまとめる
        regex_results = {
            'url': response.url,
            'timestamp': datetime.now().isoformat(),
            'html_patterns': pattern_results,
            'text_patterns': body_pattern_results,
            'statistics': {
                'total_pattern_types': len(pattern_results) + len(body_pattern_results),
                'total_matches': sum(result['count'] for result in pattern_results.values()),
                'text_length': len(body_text),
                'html_length': len(page_text)
            }
        }

        debug_print(f"Regex extraction completed for: {response.url}")
        debug_pprint(regex_results['statistics'])

        yield regex_results
`
  },
  {
    id: 'xpath-advanced-spider',
    name: 'XPath Advanced Extractor',
    description: 'XPathを使った高度な要素抽出とナビゲーション',
    icon: <FileText className="w-5 h-5" />,
    category: 'parsing',
    code: `import scrapy
from lxml import etree, html
import re
import json
from urllib.parse import urljoin
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class XPathAdvancedSpider(scrapy.Spider):
    name = 'xpath_advanced_spider'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'ScrapyUI XPath Advanced Spider 1.0',
    }

    def parse(self, response):
        debug_print(f"Processing: {response.url}")

        # 1. 基本的なXPath抽出
        basic_xpath = {
            'title': response.xpath('//title/text()').get(),
            'all_headings': response.xpath('//h1 | //h2 | //h3 | //h4 | //h5 | //h6').getall(),
            'all_links': response.xpath('//a/@href').getall(),
            'all_images': response.xpath('//img/@src').getall(),
            'meta_description': response.xpath('//meta[@name="description"]/@content').get(),
            'meta_keywords': response.xpath('//meta[@name="keywords"]/@content').get()
        }

        # 2. 属性による選択
        attribute_xpath = {
            'external_links': response.xpath('//a[starts-with(@href, "http")]/@href').getall(),
            'email_links': response.xpath('//a[starts-with(@href, "mailto:")]/@href').getall(),
            'images_with_alt': response.xpath('//img[@alt]').getall(),
            'required_inputs': response.xpath('//input[@required]').getall(),
            'elements_with_id': response.xpath('//*[@id]').getall()
        }

        # 3. テキスト内容による選択
        text_xpath = {
            'links_containing_home': response.xpath('//a[contains(text(), "Home") or contains(text(), "ホーム")]').getall(),
            'headings_with_news': response.xpath('//h1[contains(text(), "News")] | //h2[contains(text(), "ニュース")]').getall(),
            'buttons_with_submit': response.xpath('//button[contains(text(), "Submit") or contains(text(), "送信")]').getall(),
            'divs_with_content': response.xpath('//div[contains(@class, "content") or contains(@class, "main")]').getall()
        }

        # 4. 位置による選択
        position_xpath = {
            'first_paragraph': response.xpath('//p[1]').get(),
            'last_list_item': response.xpath('//li[last()]').get(),
            'second_table_row': response.xpath('//tr[2]').get(),
            'first_three_links': response.xpath('//a[position() <= 3]').getall(),
            'even_table_rows': response.xpath('//tr[position() mod 2 = 0]').getall()
        }

        # 5. 親子関係による選択
        relationship_xpath = {
            'nav_children': response.xpath('//nav/child::*').getall(),
            'article_descendants': response.xpath('//article//p').getall(),
            'form_following_siblings': response.xpath('//form/following-sibling::*').getall(),
            'heading_preceding_siblings': response.xpath('//h1/preceding-sibling::*').getall(),
            'div_parent_of_p': response.xpath('//p/parent::div').getall()
        }

        # 6. 複雑な条件による選択
        complex_xpath = {
            'links_not_external': response.xpath('//a[not(starts-with(@href, "http"))]/@href').getall(),
            'inputs_text_or_email': response.xpath('//input[@type="text" or @type="email"]').getall(),
            'divs_with_multiple_classes': response.xpath('//div[contains(@class, "content") and contains(@class, "main")]').getall(),
            'images_without_alt': response.xpath('//img[not(@alt)]').getall(),
            'links_with_title_and_href': response.xpath('//a[@title and @href]').getall()
        }

        # 結果をまとめる
        xpath_results = {
            'url': response.url,
            'basic_xpath': {
                'title': basic_xpath['title'],
                'headings_count': len(basic_xpath['all_headings']),
                'links_count': len(basic_xpath['all_links']),
                'images_count': len(basic_xpath['all_images']),
                'meta_description': basic_xpath['meta_description'],
                'meta_keywords': basic_xpath['meta_keywords']
            },
            'attribute_selections': {
                'external_links': attribute_xpath['external_links'][:5],
                'email_links': attribute_xpath['email_links'][:5],
                'images_with_alt_count': len(attribute_xpath['images_with_alt']),
                'required_inputs_count': len(attribute_xpath['required_inputs'])
            },
            'text_selections': {
                'home_links_count': len(text_xpath['links_containing_home']),
                'news_headings_count': len(text_xpath['headings_with_news']),
                'submit_buttons_count': len(text_xpath['buttons_with_submit'])
            },
            'position_selections': {
                'first_paragraph': position_xpath['first_paragraph'],
                'last_list_item': position_xpath['last_list_item'],
                'first_three_links': position_xpath['first_three_links'],
                'even_rows_count': len(position_xpath['even_table_rows'])
            },
            'relationship_selections': {
                'nav_children_count': len(relationship_xpath['nav_children']),
                'article_paragraphs_count': len(relationship_xpath['article_descendants']),
                'form_siblings_count': len(relationship_xpath['form_following_siblings'])
            },
            'complex_selections': {
                'internal_links': complex_xpath['links_not_external'][:5],
                'text_email_inputs_count': len(complex_xpath['inputs_text_or_email']),
                'images_without_alt_count': len(complex_xpath['images_without_alt'])
            },
            'statistics': {
                'total_xpath_queries': 6,
                'total_elements_found': sum([
                    len(basic_xpath['all_headings']),
                    len(basic_xpath['all_links']),
                    len(basic_xpath['all_images'])
                ])
            }
        }

        debug_print(f"XPath extraction completed for: {response.url}")
        debug_pprint(xpath_results['statistics'])

        yield xpath_results

        # 内部リンクをフォロー
        for link in complex_xpath['links_not_external'][:3]:
            if link and not link.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                yield response.follow(link, self.parse)
`
  },
  {
    id: 'comprehensive-parser-spider',
    name: 'Comprehensive Parser Master',
    description: 'BS4、CSS、正規表現、XPathを統合した包括的パーサー',
    icon: <Search className="w-5 h-5" />,
    category: 'parsing',
    code: `import scrapy
from bs4 import BeautifulSoup, Comment
import re
import json
from urllib.parse import urljoin, urlparse
from datetime import datetime
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class ComprehensiveParserSpider(scrapy.Spider):
    name = 'comprehensive_parser_spider'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'ScrapyUI Comprehensive Parser Spider 1.0',
    }

    def __init__(self):
        # 正規表現パターンを定義
        self.patterns = {
            'email': re.compile(r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'),
            'phone': re.compile(r'\\b(?:\\+?1[-.]?)?\\(?([0-9]{3})\\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\\b'),
            'price_dollar': re.compile(r'\\$\\d{1,3}(?:,\\d{3})*(?:\\.\\d{2})?'),
            'price_yen': re.compile(r'¥\\d{1,3}(?:,\\d{3})*'),
            'date_iso': re.compile(r'\\b\\d{4}-\\d{2}-\\d{2}\\b'),
            'url': re.compile(r'https?://(?:[-\\w.])+(?:[:\\d]+)?(?:/(?:[\\w/_.])*(?:\\?(?:[\\w&=%.])*)?(?:#(?:[\\w.])*)?)?'),
        }

    def extract_with_bs4(self, response):
        """BeautifulSoup4を使った抽出"""
        soup = BeautifulSoup(response.text, 'html.parser')

        bs4_data = {
            'title': soup.find('title').get_text(strip=True) if soup.find('title') else None,
            'meta_description': None,
            'headings': [],
            'links': [],
            'images': [],
            'tables': [],
            'forms': []
        }

        # メタ情報
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            bs4_data['meta_description'] = meta_desc.get('content')

        # 見出し
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            elements = soup.find_all(tag)
            for elem in elements[:5]:
                bs4_data['headings'].append({
                    'tag': tag,
                    'text': elem.get_text(strip=True),
                    'id': elem.get('id'),
                    'class': elem.get('class')
                })

        # リンク
        for link in soup.find_all('a', href=True)[:10]:
            bs4_data['links'].append({
                'text': link.get_text(strip=True),
                'href': urljoin(response.url, link['href']),
                'title': link.get('title')
            })

        # 画像
        for img in soup.find_all('img', src=True)[:10]:
            bs4_data['images'].append({
                'src': urljoin(response.url, img['src']),
                'alt': img.get('alt', ''),
                'title': img.get('title', '')
            })

        # テーブル
        for table in soup.find_all('table')[:3]:
            table_data = {'headers': [], 'rows': []}
            header_row = table.find('tr')
            if header_row:
                headers = header_row.find_all(['th', 'td'])
                table_data['headers'] = [h.get_text(strip=True) for h in headers]

            rows = table.find_all('tr')[1:]
            for row in rows[:3]:
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text(strip=True) for cell in cells]
                if row_data:
                    table_data['rows'].append(row_data)

            if table_data['headers'] or table_data['rows']:
                bs4_data['tables'].append(table_data)

        return bs4_data

    def extract_with_css(self, response):
        """CSS3/4セレクタを使った抽出"""
        soup = BeautifulSoup(response.text, 'html.parser')

        css_data = {
            'navigation': [],
            'articles': [],
            'forms': [],
            'media': []
        }

        # ナビゲーション
        nav_elements = soup.select('nav a, .navigation a, .menu a, header a')
        for nav in nav_elements[:10]:
            href = nav.get('href')
            if href:
                css_data['navigation'].append({
                    'text': nav.get_text(strip=True),
                    'href': urljoin(response.url, href)
                })

        # 記事
        article_elements = soup.select('article, .post, .content, .entry')
        for article in article_elements[:5]:
            article_data = {
                'title': None,
                'content': None,
                'author': None
            }

            title_elem = article.select_one('h1, h2, h3, .title, .heading')
            if title_elem:
                article_data['title'] = title_elem.get_text(strip=True)

            content_elem = article.select_one('p, .content, .body, .text')
            if content_elem:
                article_data['content'] = content_elem.get_text(strip=True)[:200]

            author_elem = article.select_one('.author, .by, .writer')
            if author_elem:
                article_data['author'] = author_elem.get_text(strip=True)

            if any(article_data.values()):
                css_data['articles'].append(article_data)

        # フォーム
        form_elements = soup.select('form')
        for form in form_elements[:3]:
            form_data = {
                'action': form.get('action'),
                'method': form.get('method', 'get'),
                'inputs': []
            }

            inputs = form.select('input, select, textarea')
            for input_elem in inputs:
                form_data['inputs'].append({
                    'type': input_elem.get('type', input_elem.name),
                    'name': input_elem.get('name'),
                    'placeholder': input_elem.get('placeholder')
                })

            if form_data['inputs']:
                css_data['forms'].append(form_data)

        return css_data

    def extract_with_regex(self, text):
        """正規表現を使った抽出"""
        regex_data = {}

        for pattern_name, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                unique_matches = list(set(matches))[:10]
                regex_data[pattern_name] = {
                    'matches': unique_matches,
                    'count': len(matches)
                }

        return regex_data

    def extract_with_xpath(self, response):
        """XPathを使った抽出"""
        xpath_data = {
            'title': response.xpath('//title/text()').get(),
            'meta_keywords': response.xpath('//meta[@name="keywords"]/@content').get(),
            'external_links': response.xpath('//a[starts-with(@href, "http")]/@href').getall()[:10],
            'images_with_alt': len(response.xpath('//img[@alt]')),
            'required_inputs': len(response.xpath('//input[@required]')),
            'first_paragraph': response.xpath('//p[1]/text()').get(),
            'last_list_item': response.xpath('//li[last()]/text()').get(),
            'nav_children': len(response.xpath('//nav/child::*')),
            'article_paragraphs': len(response.xpath('//article//p')),
            'internal_links': response.xpath('//a[not(starts-with(@href, "http"))]/@href').getall()[:10]
        }

        return xpath_data

    def parse(self, response):
        debug_print(f"Processing: {response.url}")

        # 各手法でデータを抽出
        bs4_results = self.extract_with_bs4(response)
        css_results = self.extract_with_css(response)
        regex_results = self.extract_with_regex(response.text)
        xpath_results = self.extract_with_xpath(response)

        # 統合結果
        comprehensive_data = {
            'url': response.url,
            'timestamp': datetime.now().isoformat(),
            'extraction_methods': {
                'beautifulsoup4': bs4_results,
                'css_selectors': css_results,
                'regex_patterns': regex_results,
                'xpath_queries': xpath_results
            },
            'cross_validation': {
                'title_bs4': bs4_results.get('title'),
                'title_xpath': xpath_results.get('title'),
                'links_bs4': len(bs4_results.get('links', [])),
                'links_xpath_external': len(xpath_results.get('external_links', [])),
                'images_bs4': len(bs4_results.get('images', [])),
                'images_xpath_with_alt': xpath_results.get('images_with_alt', 0)
            },
            'statistics': {
                'bs4_elements': {
                    'headings': len(bs4_results.get('headings', [])),
                    'links': len(bs4_results.get('links', [])),
                    'images': len(bs4_results.get('images', [])),
                    'tables': len(bs4_results.get('tables', []))
                },
                'css_elements': {
                    'navigation': len(css_results.get('navigation', [])),
                    'articles': len(css_results.get('articles', [])),
                    'forms': len(css_results.get('forms', []))
                },
                'regex_patterns': len(regex_results),
                'xpath_queries': len([v for v in xpath_results.values() if v is not None])
            }
        }

        debug_print(f"Comprehensive extraction completed for: {response.url}")
        debug_pprint(comprehensive_data['statistics'])

        yield comprehensive_data

        # 抽出したリンクをフォロー（複数の手法で見つかったリンクを優先）
        all_links = set()

        # BS4のリンク
        for link in bs4_results.get('links', [])[:3]:
            href = link.get('href')
            if href and not href.startswith(('http', 'mailto:', 'tel:', '#')):
                all_links.add(href)

        # XPathの内部リンク
        for link in xpath_results.get('internal_links', [])[:3]:
            if link and not link.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                all_links.add(link)

        # リンクをフォロー
        for link in list(all_links)[:3]:
            yield response.follow(link, self.parse)
`
  }
]
