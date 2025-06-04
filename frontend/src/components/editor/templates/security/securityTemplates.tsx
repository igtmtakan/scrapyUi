import React from 'react'
import { Shield, Lock, Eye } from 'lucide-react'
import { Template } from '../types'

export const securityTemplates: Template[] = [
  {
    id: 'security-headers-spider',
    name: 'Security Headers Spider',
    description: 'Webサイトのセキュリティヘッダーをチェックするスパイダー',
    icon: <Shield className="w-5 h-5" />,
    category: 'security',
    code: `import scrapy
from urllib.parse import urljoin
import re
from datetime import datetime
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class SecurityHeadersSpider(scrapy.Spider):
    name = 'security_headers_spider'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com']
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'ScrapyUI Security Scanner 1.0 (Educational Purpose)',
    }
    
    def parse(self, response):
        debug_print(f"Analyzing security headers for: {response.url}")
        
        # セキュリティヘッダーの分析
        security_headers = self.analyze_security_headers(response)
        
        # HTTPSの使用状況
        https_analysis = self.analyze_https_usage(response)
        
        # Cookieのセキュリティ設定
        cookie_analysis = self.analyze_cookie_security(response)
        
        # CSPの分析
        csp_analysis = self.analyze_csp(response)
        
        # フォームのセキュリティ
        form_security = self.analyze_form_security(response)
        
        security_report = {
            'url': response.url,
            'timestamp': datetime.now().isoformat(),
            'security_headers': security_headers,
            'https_analysis': https_analysis,
            'cookie_analysis': cookie_analysis,
            'csp_analysis': csp_analysis,
            'form_security': form_security,
            'overall_score': self.calculate_security_score(security_headers, https_analysis, cookie_analysis),
            'item_type': 'security_report'
        }
        
        debug_print("Security analysis complete:")
        debug_pprint(security_report)
        
        yield security_report
        
        # 内部リンクも分析（最初の3個のみ）
        links = response.css('a::attr(href)').getall()
        internal_links = [link for link in links if link.startswith('/') or response.url in link]
        
        for link in internal_links[:3]:
            yield response.follow(link, self.parse)
    
    def analyze_security_headers(self, response):
        """セキュリティヘッダーを分析"""
        headers = response.headers
        
        security_headers = {
            'strict_transport_security': {
                'present': b'Strict-Transport-Security' in headers,
                'value': headers.get('Strict-Transport-Security', b'').decode('utf-8', errors='ignore')
            },
            'content_security_policy': {
                'present': b'Content-Security-Policy' in headers,
                'value': headers.get('Content-Security-Policy', b'').decode('utf-8', errors='ignore')
            },
            'x_frame_options': {
                'present': b'X-Frame-Options' in headers,
                'value': headers.get('X-Frame-Options', b'').decode('utf-8', errors='ignore')
            },
            'x_content_type_options': {
                'present': b'X-Content-Type-Options' in headers,
                'value': headers.get('X-Content-Type-Options', b'').decode('utf-8', errors='ignore')
            },
            'x_xss_protection': {
                'present': b'X-XSS-Protection' in headers,
                'value': headers.get('X-XSS-Protection', b'').decode('utf-8', errors='ignore')
            },
            'referrer_policy': {
                'present': b'Referrer-Policy' in headers,
                'value': headers.get('Referrer-Policy', b'').decode('utf-8', errors='ignore')
            },
            'permissions_policy': {
                'present': b'Permissions-Policy' in headers,
                'value': headers.get('Permissions-Policy', b'').decode('utf-8', errors='ignore')
            }
        }
        
        return security_headers
    
    def analyze_https_usage(self, response):
        """HTTPS使用状況を分析"""
        is_https = response.url.startswith('https://')
        
        # 混在コンテンツのチェック
        mixed_content = []
        
        # 画像の混在コンテンツ
        images = response.css('img::attr(src)').getall()
        for img in images:
            if img.startswith('http://'):
                mixed_content.append({'type': 'image', 'url': img})
        
        # スクリプトの混在コンテンツ
        scripts = response.css('script::attr(src)').getall()
        for script in scripts:
            if script.startswith('http://'):
                mixed_content.append({'type': 'script', 'url': script})
        
        # CSSの混在コンテンツ
        stylesheets = response.css('link[rel="stylesheet"]::attr(href)').getall()
        for css in stylesheets:
            if css.startswith('http://'):
                mixed_content.append({'type': 'stylesheet', 'url': css})
        
        return {
            'is_https': is_https,
            'mixed_content_count': len(mixed_content),
            'mixed_content_items': mixed_content[:5],  # 最初の5個のみ
            'has_mixed_content': len(mixed_content) > 0
        }
    
    def analyze_cookie_security(self, response):
        """Cookieのセキュリティ設定を分析"""
        cookies = []
        
        for cookie in response.headers.getlist('Set-Cookie'):
            cookie_str = cookie.decode('utf-8', errors='ignore')
            
            cookie_analysis = {
                'cookie_string': cookie_str,
                'has_secure': 'Secure' in cookie_str,
                'has_httponly': 'HttpOnly' in cookie_str,
                'has_samesite': 'SameSite' in cookie_str,
                'samesite_value': None
            }
            
            # SameSite属性の値を抽出
            samesite_match = re.search(r'SameSite=([^;]+)', cookie_str)
            if samesite_match:
                cookie_analysis['samesite_value'] = samesite_match.group(1).strip()
            
            cookies.append(cookie_analysis)
        
        return {
            'total_cookies': len(cookies),
            'cookies': cookies,
            'secure_cookies': len([c for c in cookies if c['has_secure']]),
            'httponly_cookies': len([c for c in cookies if c['has_httponly']]),
            'samesite_cookies': len([c for c in cookies if c['has_samesite']])
        }
    
    def analyze_csp(self, response):
        """Content Security Policyを分析"""
        csp_header = response.headers.get('Content-Security-Policy', b'').decode('utf-8', errors='ignore')
        
        if not csp_header:
            return {'present': False, 'analysis': None}
        
        # CSPディレクティブを解析
        directives = {}
        for directive in csp_header.split(';'):
            directive = directive.strip()
            if directive:
                parts = directive.split(' ', 1)
                if len(parts) == 2:
                    directives[parts[0]] = parts[1]
                else:
                    directives[parts[0]] = ''
        
        # 危険な設定をチェック
        unsafe_settings = []
        
        for directive, value in directives.items():
            if "'unsafe-inline'" in value:
                unsafe_settings.append(f"{directive} allows unsafe-inline")
            if "'unsafe-eval'" in value:
                unsafe_settings.append(f"{directive} allows unsafe-eval")
            if "*" in value and directive != 'report-uri':
                unsafe_settings.append(f"{directive} uses wildcard")
        
        return {
            'present': True,
            'directives': directives,
            'directive_count': len(directives),
            'unsafe_settings': unsafe_settings,
            'has_unsafe_settings': len(unsafe_settings) > 0
        }
    
    def analyze_form_security(self, response):
        """フォームのセキュリティを分析"""
        forms = response.css('form')
        
        form_analysis = []
        
        for i, form in enumerate(forms):
            method = form.css('::attr(method)').get() or 'GET'
            action = form.css('::attr(action)').get() or ''
            
            # CSRF保護の確認
            csrf_tokens = form.css('input[name*="csrf"], input[name*="token"], input[type="hidden"]')
            has_csrf_protection = len(csrf_tokens) > 0
            
            # HTTPSでの送信確認
            is_secure_action = action.startswith('https://') or not action.startswith('http://')
            
            form_data = {
                'form_index': i,
                'method': method.upper(),
                'action': action,
                'has_csrf_protection': has_csrf_protection,
                'is_secure_action': is_secure_action,
                'input_count': len(form.css('input')),
                'has_password_field': len(form.css('input[type="password"]')) > 0
            }
            
            form_analysis.append(form_data)
        
        return {
            'total_forms': len(forms),
            'forms': form_analysis,
            'secure_forms': len([f for f in form_analysis if f['is_secure_action']]),
            'csrf_protected_forms': len([f for f in form_analysis if f['has_csrf_protection']])
        }
    
    def calculate_security_score(self, security_headers, https_analysis, cookie_analysis):
        """セキュリティスコアを計算"""
        score = 0
        max_score = 100
        
        # HTTPS使用 (20点)
        if https_analysis['is_https']:
            score += 20
        
        # 混在コンテンツなし (10点)
        if not https_analysis['has_mixed_content']:
            score += 10
        
        # セキュリティヘッダー (各10点、最大70点)
        header_scores = {
            'strict_transport_security': 10,
            'content_security_policy': 15,
            'x_frame_options': 10,
            'x_content_type_options': 10,
            'x_xss_protection': 5,
            'referrer_policy': 10,
            'permissions_policy': 10
        }
        
        for header, points in header_scores.items():
            if security_headers[header]['present']:
                score += points
        
        return {
            'score': score,
            'max_score': max_score,
            'percentage': round((score / max_score) * 100, 2),
            'grade': self.get_security_grade(score, max_score)
        }
    
    def get_security_grade(self, score, max_score):
        """セキュリティグレードを取得"""
        percentage = (score / max_score) * 100
        
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B'
        elif percentage >= 60:
            return 'C'
        elif percentage >= 50:
            return 'D'
        else:
            return 'F'
`
  },
  {
    id: 'vulnerability-scanner-spider',
    name: 'Vulnerability Scanner Spider',
    description: '基本的な脆弱性をチェックするスパイダー（教育用）',
    icon: <Eye className="w-5 h-5" />,
    category: 'security',
    code: `import scrapy
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class VulnerabilityScannerSpider(scrapy.Spider):
    name = 'vulnerability_scanner_spider'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com']
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,  # 丁寧にスキャン
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'ScrapyUI Vulnerability Scanner 1.0 (Educational Purpose)',
    }
    
    def parse(self, response):
        debug_print(f"Scanning for vulnerabilities: {response.url}")
        
        # 情報漏洩のチェック
        info_disclosure = self.check_information_disclosure(response)
        
        # SQLインジェクションの可能性
        sql_injection_risks = self.check_sql_injection_risks(response)
        
        # XSSの可能性
        xss_risks = self.check_xss_risks(response)
        
        # ディレクトリトラバーサルの可能性
        directory_traversal = self.check_directory_traversal(response)
        
        # 機密ファイルの存在確認
        sensitive_files = self.check_sensitive_files(response)
        
        # サーバー情報の漏洩
        server_info = self.check_server_information(response)
        
        vulnerability_report = {
            'url': response.url,
            'timestamp': datetime.now().isoformat(),
            'info_disclosure': info_disclosure,
            'sql_injection_risks': sql_injection_risks,
            'xss_risks': xss_risks,
            'directory_traversal': directory_traversal,
            'sensitive_files': sensitive_files,
            'server_info': server_info,
            'risk_level': self.calculate_risk_level(info_disclosure, sql_injection_risks, xss_risks),
            'item_type': 'vulnerability_report'
        }
        
        debug_print("Vulnerability scan complete:")
        debug_pprint(vulnerability_report)
        
        yield vulnerability_report
        
        # 追加のページもスキャン
        links = response.css('a::attr(href)').getall()
        internal_links = [link for link in links if link.startswith('/')]
        
        for link in internal_links[:5]:  # 最初の5個のみ
            yield response.follow(link, self.parse)
    
    def check_information_disclosure(self, response):
        """情報漏洩をチェック"""
        issues = []
        
        # HTMLコメント内の機密情報
        comments = response.css('*').re(r'<!--.*?-->')
        for comment in comments:
            if any(keyword in comment.lower() for keyword in ['password', 'secret', 'key', 'token', 'admin']):
                issues.append({
                    'type': 'sensitive_comment',
                    'content': comment[:100],  # 最初の100文字のみ
                    'risk': 'medium'
                })
        
        # エラーメッセージの確認
        error_patterns = [
            r'mysql.*error',
            r'postgresql.*error',
            r'oracle.*error',
            r'sql.*syntax.*error',
            r'warning.*mysql',
            r'fatal.*error'
        ]
        
        page_text = response.text.lower()
        for pattern in error_patterns:
            if re.search(pattern, page_text):
                issues.append({
                    'type': 'database_error',
                    'pattern': pattern,
                    'risk': 'high'
                })
        
        # バージョン情報の漏洩
        version_patterns = [
            r'apache/[\d.]+',
            r'nginx/[\d.]+',
            r'php/[\d.]+',
            r'mysql/[\d.]+',
            r'wordpress [\d.]+'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, page_text)
            if match:
                issues.append({
                    'type': 'version_disclosure',
                    'version': match.group(0),
                    'risk': 'low'
                })
        
        return {
            'total_issues': len(issues),
            'issues': issues,
            'high_risk_count': len([i for i in issues if i['risk'] == 'high']),
            'medium_risk_count': len([i for i in issues if i['risk'] == 'medium']),
            'low_risk_count': len([i for i in issues if i['risk'] == 'low'])
        }
    
    def check_sql_injection_risks(self, response):
        """SQLインジェクションのリスクをチェック"""
        risks = []
        
        # URLパラメータの確認
        if '?' in response.url:
            query_params = response.url.split('?')[1]
            if any(param in query_params.lower() for param in ['id=', 'user=', 'page=', 'category=']):
                risks.append({
                    'type': 'url_parameters',
                    'description': 'URL parameters that might be vulnerable to SQL injection',
                    'url': response.url,
                    'risk': 'medium'
                })
        
        # フォーム入力フィールドの確認
        forms = response.css('form')
        for i, form in enumerate(forms):
            inputs = form.css('input[type="text"], input[type="search"], textarea')
            if inputs:
                risks.append({
                    'type': 'form_inputs',
                    'description': f'Form {i+1} has text inputs that might be vulnerable',
                    'input_count': len(inputs),
                    'risk': 'medium'
                })
        
        return {
            'total_risks': len(risks),
            'risks': risks
        }
    
    def check_xss_risks(self, response):
        """XSSのリスクをチェック"""
        risks = []
        
        # ユーザー入力を反映する可能性のある要素
        search_forms = response.css('form input[type="search"], form input[name*="search"], form input[name*="query"]')
        if search_forms:
            risks.append({
                'type': 'search_forms',
                'description': 'Search forms that might reflect user input',
                'count': len(search_forms),
                'risk': 'medium'
            })
        
        # JavaScriptでのDOM操作
        scripts = response.css('script::text').getall()
        for script in scripts:
            if any(method in script for method in ['innerHTML', 'document.write', 'eval(']):
                risks.append({
                    'type': 'dangerous_js',
                    'description': 'JavaScript code using potentially dangerous methods',
                    'risk': 'high'
                })
                break
        
        # URLパラメータの反映
        if '?' in response.url:
            query_string = response.url.split('?')[1]
            if any(param.split('=')[1] in response.text for param in query_string.split('&') if '=' in param):
                risks.append({
                    'type': 'reflected_parameters',
                    'description': 'URL parameters reflected in page content',
                    'risk': 'high'
                })
        
        return {
            'total_risks': len(risks),
            'risks': risks
        }
    
    def check_directory_traversal(self, response):
        """ディレクトリトラバーサルの可能性をチェック"""
        risks = []
        
        # ファイルパスを含むパラメータ
        if '?' in response.url:
            query_params = response.url.split('?')[1]
            if any(param in query_params.lower() for param in ['file=', 'path=', 'page=', 'include=']):
                risks.append({
                    'type': 'file_parameters',
                    'description': 'URL parameters that might allow directory traversal',
                    'url': response.url,
                    'risk': 'high'
                })
        
        return {
            'total_risks': len(risks),
            'risks': risks
        }
    
    def check_sensitive_files(self, response):
        """機密ファイルの存在をチェック"""
        # 注意: 実際のペネトレーションテストでは許可が必要
        sensitive_files = [
            '/robots.txt',
            '/sitemap.xml',
            '/.htaccess',
            '/wp-config.php',
            '/config.php',
            '/admin/',
            '/backup/',
            '/.git/',
            '/.env'
        ]
        
        found_files = []
        
        # この例では実際にリクエストを送信せず、
        # 既存のレスポンスから推測可能な情報のみチェック
        
        # robots.txtへのリンクがあるかチェック
        if response.css('a[href*="robots.txt"]'):
            found_files.append({
                'file': '/robots.txt',
                'method': 'link_found',
                'risk': 'low'
            })
        
        # 管理者ページへのリンク
        admin_links = response.css('a[href*="admin"], a[href*="login"], a[href*="dashboard"]')
        if admin_links:
            found_files.append({
                'file': 'admin_pages',
                'count': len(admin_links),
                'method': 'link_found',
                'risk': 'medium'
            })
        
        return {
            'total_files': len(found_files),
            'files': found_files
        }
    
    def check_server_information(self, response):
        """サーバー情報の漏洩をチェック"""
        server_info = {}
        
        # HTTPヘッダーからサーバー情報を取得
        headers = response.headers
        
        server_header = headers.get('Server', b'').decode('utf-8', errors='ignore')
        if server_header:
            server_info['server'] = server_header
        
        powered_by = headers.get('X-Powered-By', b'').decode('utf-8', errors='ignore')
        if powered_by:
            server_info['powered_by'] = powered_by
        
        # HTMLからサーバー情報を推測
        html_lower = response.text.lower()
        
        if 'apache' in html_lower:
            server_info['detected_apache'] = True
        if 'nginx' in html_lower:
            server_info['detected_nginx'] = True
        if 'php' in html_lower:
            server_info['detected_php'] = True
        
        return server_info
    
    def calculate_risk_level(self, info_disclosure, sql_injection_risks, xss_risks):
        """総合的なリスクレベルを計算"""
        high_risk_count = (
            info_disclosure['high_risk_count'] +
            len([r for r in sql_injection_risks['risks'] if r['risk'] == 'high']) +
            len([r for r in xss_risks['risks'] if r['risk'] == 'high'])
        )
        
        medium_risk_count = (
            info_disclosure['medium_risk_count'] +
            len([r for r in sql_injection_risks['risks'] if r['risk'] == 'medium']) +
            len([r for r in xss_risks['risks'] if r['risk'] == 'medium'])
        )
        
        if high_risk_count > 0:
            return 'HIGH'
        elif medium_risk_count > 2:
            return 'MEDIUM'
        elif medium_risk_count > 0:
            return 'LOW'
        else:
            return 'MINIMAL'
`
  }
]
