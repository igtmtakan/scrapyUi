import scrapy
import pprint

def debug_print(message):
    """デバッグ用のprint関数"""
    print(f"[DEBUG] {message}")

def debug_pprint(data):
    """デバッグ用のpprint関数"""
    print("[DEBUG] Data:")
    pprint.pprint(data)

class BasicHttpSpiderSpider(scrapy.Spider):
    name = 'basic_http_spider'
    start_urls = [
        'https://httpbin.org/json'  # 軽量なテスト用API
    ]

    # Playwrightを使わずに通常のHTTPリクエストを使用
    custom_settings = {
        'DOWNLOAD_HANDLERS': {},  # Playwrightハンドラーを無効化
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 1
    }

    def parse(self, response):
        debug_print(f"Parsing response from {response.url}")

        # レスポンスの基本情報を取得
        debug_print(f"Status code: {response.status}")
        debug_print(f"Content type: {response.headers.get('content-type', b'').decode()}")

        # JSONレスポンスの場合
        if 'json' in response.headers.get('content-type', b'').decode().lower():
            try:
                json_data = response.json()
                debug_print("JSON data received:")
                debug_pprint(json_data)

                yield {
                    'url': response.url,
                    'status': response.status,
                    'content_type': response.headers.get('content-type', b'').decode(),
                    'data': json_data
                }
            except Exception as e:
                debug_print(f"Error parsing JSON: {e}")
                yield {
                    'url': response.url,
                    'status': response.status,
                    'error': str(e)
                }
        else:
            # HTMLレスポンスの場合
            title = response.css('title::text').get()
            debug_print(f"Extracted title: {title}")

            # 基本的なデータを抽出
            data = {
                'url': response.url,
                'status': response.status,
                'title': title,
                'content_length': len(response.text)
            }

            debug_print("Yielding extracted data:")
            debug_pprint(data)

            yield data
