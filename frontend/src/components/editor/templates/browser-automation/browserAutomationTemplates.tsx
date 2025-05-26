import React from 'react'
import { MousePointer, Edit, Upload, Lock, FileText, ShoppingCart, User, Search } from 'lucide-react'
import { Template } from '../types'

export const browserAutomationTemplates: Template[] = [
  {
    id: 'form-automation-spider',
    name: 'Form Automation Master',
    description: 'フォーム入力、送信、ファイルアップロードの自動化',
    icon: <Edit className="w-5 h-5" />,
    category: 'browser-automation',
    code: `import scrapy
import aiohttp
import asyncio
import json
import base64
from datetime import datetime
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class FormAutomationSpider(scrapy.Spider):
    name = 'form_automation_spider'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com/contact']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'ScrapyUI Form Automation Spider 1.0',
    }

    def __init__(self):
        self.nodejs_url = "http://localhost:3001"

    async def fill_and_submit_form(self, url, form_data):
        """フォームの入力と送信を自動化"""
        request_data = {
            "url": url,
            "actions": [
                # ページロード待機
                {"type": "wait", "delay": 2000},

                # フォームフィールドの入力
                {"type": "type", "selector": "input[name='name']", "value": form_data.get('name', 'テストユーザー')},
                {"type": "type", "selector": "input[name='email']", "value": form_data.get('email', 'test@example.com')},
                {"type": "type", "selector": "input[name='phone']", "value": form_data.get('phone', '090-1234-5678')},
                {"type": "type", "selector": "textarea[name='message']", "value": form_data.get('message', 'これはテストメッセージです。')},

                # セレクトボックスの選択
                {"type": "click", "selector": "select[name='category']"},
                {"type": "click", "selector": "select[name='category'] option[value='inquiry']"},

                # チェックボックスの選択
                {"type": "click", "selector": "input[type='checkbox'][name='agree']"},

                # ラジオボタンの選択
                {"type": "click", "selector": "input[type='radio'][name='contact_method'][value='email']"},

                # フォーム送信前のスクリーンショット
                {"type": "wait", "delay": 1000},

                # フォーム送信
                {"type": "click", "selector": "button[type='submit'], input[type='submit']"},

                # 送信後の待機
                {"type": "wait", "delay": 3000}
            ],
            "extractAfter": {
                "selectors": {
                    "success_message": ".success, .confirmation, .thank-you",
                    "error_message": ".error, .alert-danger, .validation-error",
                    "form_status": ".status, .result",
                    "confirmation_number": ".confirmation-number, .reference-id"
                },
                "javascript": '''
                    return {
                        formSubmitted: document.querySelector('form') ? false : true,
                        currentUrl: window.location.href,
                        pageTitle: document.title,
                        hasSuccessMessage: !!document.querySelector('.success, .confirmation, .thank-you'),
                        hasErrorMessage: !!document.querySelector('.error, .alert-danger, .validation-error'),
                        timestamp: new Date().toISOString()
                    };
                '''
            },
            "timeout": 60000
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.nodejs_url}/api/scraping/dynamic", json=request_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Request failed: {response.status}")

    async def upload_file_to_form(self, url, file_path, form_data):
        """ファイルアップロード付きフォーム送信"""
        request_data = {
            "url": url,
            "actions": [
                # 基本情報入力
                {"type": "type", "selector": "input[name='name']", "value": form_data.get('name', 'テストユーザー')},
                {"type": "type", "selector": "input[name='email']", "value": form_data.get('email', 'test@example.com')},

                # ファイルアップロード（注意: 実際のファイルパスが必要）
                {"type": "upload", "selector": "input[type='file']", "value": file_path},

                # アップロード完了待機
                {"type": "wait", "delay": 5000},

                # 送信
                {"type": "click", "selector": "button[type='submit']"},
                {"type": "wait", "delay": 3000}
            ],
            "extractAfter": {
                "selectors": {
                    "upload_status": ".upload-status, .file-status",
                    "uploaded_files": ".uploaded-file, .file-list li",
                    "success_message": ".success, .confirmation"
                }
            },
            "timeout": 90000  # ファイルアップロードのため長めのタイムアウト
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.nodejs_url}/api/scraping/dynamic", json=request_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"File upload failed: {response.status}")

    def parse(self, response):
        debug_print(f"Processing form page: {response.url}")

        # フォームデータの準備
        form_data = {
            'name': '山田太郎',
            'email': 'yamada@example.com',
            'phone': '03-1234-5678',
            'message': 'お問い合わせテストです。自動化されたフォーム送信のテストを行っています。',
            'company': 'テスト株式会社',
            'department': '開発部'
        }

        # 非同期でフォーム送信を実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # 通常のフォーム送信
            result = loop.run_until_complete(self.fill_and_submit_form(response.url, form_data))

            form_result = {
                'url': response.url,
                'timestamp': datetime.now().isoformat(),
                'form_data_sent': form_data,
                'automation_result': result,
                'success': result.get('success', False),
                'actions_executed': result.get('actionsExecuted', 0)
            }

            debug_print("Form automation completed:")
            debug_pprint(form_result)

            yield form_result

            # ファイルアップロードテスト（オプション）
            # 注意: 実際のファイルパスを指定してください
            file_upload_url = response.urljoin('/upload')
            try:
                upload_result = loop.run_until_complete(
                    self.upload_file_to_form(file_upload_url, '/path/to/test/file.pdf', form_data)
                )

                upload_result_data = {
                    'url': file_upload_url,
                    'timestamp': datetime.now().isoformat(),
                    'upload_result': upload_result,
                    'file_uploaded': upload_result.get('success', False)
                }

                yield upload_result_data

            except Exception as e:
                debug_print(f"File upload test skipped: {e}")

        except Exception as e:
            debug_print(f"Form automation failed: {e}")
            yield {
                'url': response.url,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'success': False
            }

        finally:
            loop.close()
`
  },
  {
    id: 'authentication-spider',
    name: 'Authentication & Login Master',
    description: 'ログイン認証、セッション管理、保護されたページのスクレイピング',
    icon: <Lock className="w-5 h-5" />,
    category: 'browser-automation',
    code: `import scrapy
import aiohttp
import asyncio
import json
import base64
from datetime import datetime
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class AuthenticationSpider(scrapy.Spider):
    name = 'authentication_spider'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com/login']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'ScrapyUI Authentication Spider 1.0',
    }

    def __init__(self):
        self.nodejs_url = "http://localhost:3001"
        # 認証情報（実際の使用時は環境変数から取得することを推奨）
        self.credentials = {
            'username': 'your_username',  # ← 実際のユーザー名に変更
            'password': 'your_password',  # ← 実際のパスワードに変更
            'email': 'your_email@example.com'  # ← 実際のメールアドレスに変更
        }

    async def perform_login(self, login_url, username, password):
        """ログイン処理を実行"""
        request_data = {
            "url": login_url,
            "actions": [
                # ページロード待機
                {"type": "wait", "delay": 2000},

                # ログインフォームの入力
                {"type": "type", "selector": "input[name='username'], input[name='email'], input[type='email']", "value": username},
                {"type": "type", "selector": "input[name='password'], input[type='password']", "value": password},

                # CAPTCHAやreCAPTCHAがある場合の待機
                {"type": "wait", "delay": 1000},

                # ログインボタンクリック
                {"type": "click", "selector": "button[type='submit'], input[type='submit'], .login-button, #login-btn"},

                # ログイン処理完了待機
                {"type": "wait", "delay": 5000}
            ],
            "extractAfter": {
                "selectors": {
                    "user_info": ".user-name, .username, .profile-name",
                    "dashboard_title": "h1, .dashboard-title, .welcome-message",
                    "navigation_menu": ".nav, .menu, .sidebar",
                    "logout_button": ".logout, .sign-out, [href*='logout']",
                    "error_message": ".error, .alert-danger, .login-error"
                },
                "javascript": '''
                    return {
                        isLoggedIn: !window.location.href.includes('login') &&
                                   (!!document.querySelector('.user-name, .username, .profile') ||
                                    !!document.querySelector('.logout, .sign-out') ||
                                    !!document.querySelector('.dashboard, .profile')),
                        currentUrl: window.location.href,
                        pageTitle: document.title,
                        hasLoginForm: !!document.querySelector('form[action*="login"], .login-form'),
                        hasErrorMessage: !!document.querySelector('.error, .alert-danger, .login-error'),
                        cookies: document.cookie,
                        localStorage: JSON.stringify(localStorage),
                        sessionStorage: JSON.stringify(sessionStorage),
                        timestamp: new Date().toISOString()
                    };
                '''
            },
            "timeout": 60000
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.nodejs_url}/api/scraping/dynamic", json=request_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Login failed: {response.status}")

    async def scrape_protected_page(self, protected_url):
        """認証後の保護されたページをスクレイピング"""
        request_data = {
            "url": protected_url,
            "waitFor": "body",
            "timeout": 30000,
            "extractData": {
                "selectors": {
                    "page_title": "h1, .page-title, .title",
                    "content": ".content, .main, article, .post",
                    "user_specific_data": ".user-data, .profile-info, .account-info",
                    "private_content": ".private, .protected, .member-only",
                    "navigation": ".nav a, .menu a",
                    "breadcrumbs": ".breadcrumb, .breadcrumbs"
                },
                "javascript": '''
                    return {
                        pageType: 'protected',
                        isAuthenticated: !window.location.href.includes('login'),
                        userAgent: navigator.userAgent,
                        referrer: document.referrer,
                        loadTime: performance.timing.loadEventEnd - performance.timing.navigationStart,
                        elementCounts: {
                            links: document.querySelectorAll('a').length,
                            images: document.querySelectorAll('img').length,
                            forms: document.querySelectorAll('form').length
                        },
                        timestamp: new Date().toISOString()
                    };
                '''
            },
            "screenshot": True
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.nodejs_url}/api/scraping/spa", json=request_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Protected page scraping failed: {response.status}")

    async def perform_logout(self, logout_url):
        """ログアウト処理"""
        request_data = {
            "url": logout_url,
            "actions": [
                {"type": "click", "selector": ".logout, .sign-out, [href*='logout']"},
                {"type": "wait", "delay": 3000}
            ],
            "extractAfter": {
                "selectors": {
                    "login_form": "form[action*='login'], .login-form",
                    "logout_message": ".logout-message, .goodbye-message"
                },
                "javascript": '''
                    return {
                        isLoggedOut: window.location.href.includes('login') ||
                                    !!document.querySelector('form[action*="login"], .login-form'),
                        currentUrl: window.location.href,
                        timestamp: new Date().toISOString()
                    };
                '''
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.nodejs_url}/api/scraping/dynamic", json=request_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Logout failed: {response.status}")

    def parse(self, response):
        debug_print(f"Starting authentication process: {response.url}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # 1. ログイン実行
            login_result = loop.run_until_complete(
                self.perform_login(response.url, self.credentials['username'], self.credentials['password'])
            )

            auth_data = {
                'url': response.url,
                'timestamp': datetime.now().isoformat(),
                'login_attempt': {
                    'username': self.credentials['username'],
                    'success': login_result.get('success', False),
                    'result': login_result
                }
            }

            debug_print("Login attempt completed:")
            debug_pprint(auth_data)

            yield auth_data

            # 2. ログイン成功時は保護されたページをスクレイピング
            if login_result.get('success') and login_result.get('data', {}).get('customData', {}).get('isLoggedIn'):
                protected_pages = [
                    '/dashboard',
                    '/profile',
                    '/account',
                    '/settings',
                    '/private'
                ]

                for page_path in protected_pages:
                    try:
                        protected_url = response.urljoin(page_path)
                        protected_result = loop.run_until_complete(
                            self.scrape_protected_page(protected_url)
                        )

                        protected_data = {
                            'url': protected_url,
                            'timestamp': datetime.now().isoformat(),
                            'page_type': 'protected',
                            'scraping_result': protected_result,
                            'authenticated': True
                        }

                        yield protected_data

                    except Exception as e:
                        debug_print(f"Failed to scrape protected page {page_path}: {e}")

                # 3. ログアウト実行
                try:
                    logout_url = response.urljoin('/logout')
                    logout_result = loop.run_until_complete(self.perform_logout(logout_url))

                    logout_data = {
                        'url': logout_url,
                        'timestamp': datetime.now().isoformat(),
                        'logout_result': logout_result,
                        'session_ended': logout_result.get('data', {}).get('customData', {}).get('isLoggedOut', False)
                    }

                    yield logout_data

                except Exception as e:
                    debug_print(f"Logout failed: {e}")

            else:
                debug_print("Login failed - skipping protected page scraping")

        except Exception as e:
            debug_print(f"Authentication process failed: {e}")
            yield {
                'url': response.url,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'success': False
            }

        finally:
            loop.close()
`
  },
  {
    id: 'user-interaction-spider',
    name: 'User Interaction Master',
    description: 'クリック、スクロール、ホバー、キーボード操作の高度な自動化',
    icon: <MousePointer className="w-5 h-5" />,
    category: 'browser-automation',
    code: `import scrapy
import aiohttp
import asyncio
import json
import base64
from datetime import datetime
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class UserInteractionSpider(scrapy.Spider):
    name = 'user_interaction_spider'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {},
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'ScrapyUI User Interaction Spider 1.0',
    }

    def __init__(self):
        self.nodejs_url = "http://localhost:3001"

    async def perform_complex_interactions(self, url):
        """複雑なユーザー操作の自動化"""
        request_data = {
            "url": url,
            "actions": [
                # 1. ページロード待機
                {"type": "wait", "delay": 2000},

                # 2. スクロール操作
                {"type": "scroll", "direction": "down", "amount": 500},
                {"type": "wait", "delay": 1000},

                # 3. 要素へのホバー
                {"type": "hover", "selector": ".menu-item, .nav-item"},
                {"type": "wait", "delay": 1000},

                # 4. ドロップダウンメニューの操作
                {"type": "click", "selector": ".dropdown-toggle, .menu-toggle"},
                {"type": "wait", "delay": 500},
                {"type": "click", "selector": ".dropdown-item:first-child"},
                {"type": "wait", "delay": 1000},

                # 5. タブ操作
                {"type": "click", "selector": ".tab:nth-child(2), .tab-item:nth-child(2)"},
                {"type": "wait", "delay": 1000},

                # 6. アコーディオン操作
                {"type": "click", "selector": ".accordion-header, .collapsible-header"},
                {"type": "wait", "delay": 1000},

                # 7. モーダル操作
                {"type": "click", "selector": ".modal-trigger, .popup-trigger"},
                {"type": "wait", "delay": 2000},
                {"type": "click", "selector": ".modal-close, .popup-close, .close"},
                {"type": "wait", "delay": 1000},

                # 8. フォーム要素の操作
                {"type": "click", "selector": "input[type='checkbox']:first-of-type"},
                {"type": "click", "selector": "input[type='radio']:first-of-type"},
                {"type": "click", "selector": "select"},
                {"type": "click", "selector": "select option:nth-child(2)"},

                # 9. 範囲スライダー操作
                {"type": "click", "selector": "input[type='range']"},

                # 10. 最終スクロール（ページ下部へ）
                {"type": "scroll", "direction": "bottom"},
                {"type": "wait", "delay": 2000}
            ],
            "extractAfter": {
                "selectors": {
                    "interactive_elements": "button, a, input, select, textarea",
                    "dropdown_menus": ".dropdown, .menu",
                    "tabs": ".tab, .tab-item",
                    "accordions": ".accordion, .collapsible",
                    "modals": ".modal, .popup",
                    "forms": "form",
                    "navigation": "nav, .navigation",
                    "dynamic_content": "[data-dynamic], .dynamic, .ajax-content"
                },
                "javascript": '''
                    return {
                        pageInteractions: {
                            totalButtons: document.querySelectorAll('button').length,
                            totalLinks: document.querySelectorAll('a').length,
                            totalInputs: document.querySelectorAll('input').length,
                            totalSelects: document.querySelectorAll('select').length,
                            hasDropdowns: !!document.querySelector('.dropdown, .menu'),
                            hasTabs: !!document.querySelector('.tab, .tab-item'),
                            hasAccordions: !!document.querySelector('.accordion, .collapsible'),
                            hasModals: !!document.querySelector('.modal, .popup'),
                            hasForms: !!document.querySelector('form')
                        },
                        scrollPosition: {
                            x: window.pageXOffset,
                            y: window.pageYOffset,
                            maxY: document.body.scrollHeight - window.innerHeight
                        },
                        viewportInfo: {
                            width: window.innerWidth,
                            height: window.innerHeight,
                            devicePixelRatio: window.devicePixelRatio
                        },
                        userAgent: navigator.userAgent,
                        timestamp: new Date().toISOString()
                    };
                '''
            },
            "screenshot": True,
            "timeout": 60000
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.nodejs_url}/api/scraping/dynamic", json=request_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"User interaction failed: {response.status}")

    async def test_keyboard_interactions(self, url):
        """キーボード操作のテスト"""
        request_data = {
            "url": url,
            "actions": [
                # 検索フィールドでのキーボード操作
                {"type": "click", "selector": "input[type='search'], input[name='search']"},
                {"type": "type", "selector": "input[type='search'], input[name='search']", "value": "test search"},

                # キーボードショートカット（Ctrl+A で全選択）
                {"type": "key", "key": "Control+a"},
                {"type": "wait", "delay": 500},

                # 新しいテキストで置換
                {"type": "type", "selector": "input[type='search'], input[name='search']", "value": "new search term"},

                # Enterキーで検索実行
                {"type": "key", "key": "Enter"},
                {"type": "wait", "delay": 3000},

                # Escキーでモーダルを閉じる（もしあれば）
                {"type": "key", "key": "Escape"},
                {"type": "wait", "delay": 1000},

                # Tab キーでフォーカス移動
                {"type": "key", "key": "Tab"},
                {"type": "wait", "delay": 500},
                {"type": "key", "key": "Tab"},
                {"type": "wait", "delay": 500},

                # スペースキーでボタンクリック
                {"type": "key", "key": "Space"},
                {"type": "wait", "delay": 1000}
            ],
            "extractAfter": {
                "selectors": {
                    "focused_element": ":focus",
                    "search_results": ".search-result, .result-item",
                    "active_elements": ".active, .current, .selected"
                },
                "javascript": '''
                    return {
                        keyboardNavigation: {
                            focusedElement: document.activeElement?.tagName || 'none',
                            focusedElementId: document.activeElement?.id || '',
                            focusedElementClass: document.activeElement?.className || '',
                            tabIndex: document.activeElement?.tabIndex || -1
                        },
                        searchPerformed: window.location.href.includes('search') ||
                                        !!document.querySelector('.search-result, .result-item'),
                        currentUrl: window.location.href,
                        timestamp: new Date().toISOString()
                    };
                '''
            },
            "timeout": 45000
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.nodejs_url}/api/scraping/dynamic", json=request_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Keyboard interaction failed: {response.status}")

    async def test_drag_and_drop(self, url):
        """ドラッグ&ドロップ操作のテスト"""
        request_data = {
            "url": url,
            "actions": [
                # ドラッグ可能な要素を探す
                {"type": "wait", "delay": 2000},

                # ドラッグ&ドロップ操作（要素が存在する場合）
                {"type": "drag", "from": ".draggable, [draggable='true']", "to": ".drop-zone, .droppable"},
                {"type": "wait", "delay": 2000},

                # ソート可能なリストの操作
                {"type": "drag", "from": ".sortable-item:first-child", "to": ".sortable-item:last-child"},
                {"type": "wait", "delay": 2000}
            ],
            "extractAfter": {
                "selectors": {
                    "draggable_elements": "[draggable='true'], .draggable",
                    "drop_zones": ".drop-zone, .droppable",
                    "sortable_lists": ".sortable, .sort-list"
                },
                "javascript": '''
                    return {
                        dragDropSupport: {
                            hasDraggableElements: !!document.querySelector('[draggable="true"], .draggable'),
                            hasDropZones: !!document.querySelector('.drop-zone, .droppable'),
                            hasSortableLists: !!document.querySelector('.sortable, .sort-list'),
                            dragDropEvents: typeof window.ondragstart !== 'undefined'
                        },
                        timestamp: new Date().toISOString()
                    };
                '''
            },
            "timeout": 30000
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.nodejs_url}/api/scraping/dynamic", json=request_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Drag and drop test failed: {response.status}")

    def parse(self, response):
        debug_print(f"Starting user interaction tests: {response.url}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # 1. 複雑なユーザー操作テスト
            interaction_result = loop.run_until_complete(
                self.perform_complex_interactions(response.url)
            )

            interaction_data = {
                'url': response.url,
                'test_type': 'complex_interactions',
                'timestamp': datetime.now().isoformat(),
                'result': interaction_result,
                'interactions_completed': interaction_result.get('actionsExecuted', 0)
            }

            debug_print("Complex interactions completed:")
            debug_pprint(interaction_data)

            yield interaction_data

            # 2. キーボード操作テスト
            keyboard_result = loop.run_until_complete(
                self.test_keyboard_interactions(response.url)
            )

            keyboard_data = {
                'url': response.url,
                'test_type': 'keyboard_interactions',
                'timestamp': datetime.now().isoformat(),
                'result': keyboard_result,
                'keyboard_navigation_tested': True
            }

            yield keyboard_data

            # 3. ドラッグ&ドロップテスト
            drag_drop_result = loop.run_until_complete(
                self.test_drag_and_drop(response.url)
            )

            drag_drop_data = {
                'url': response.url,
                'test_type': 'drag_and_drop',
                'timestamp': datetime.now().isoformat(),
                'result': drag_drop_result,
                'drag_drop_tested': True
            }

            yield drag_drop_data

        except Exception as e:
            debug_print(f"User interaction tests failed: {e}")
            yield {
                'url': response.url,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'success': False
            }

        finally:
            loop.close()
`
  }
]
