import scrapy
import json

class UserAgentTestSpider(scrapy.Spider):
name = "user_agent_test"
    start_urls = [
        'https://httpbin.org/user-agent',
        'https://httpbin.org/headers',
    ]
    
    def parse(self, response):
        try:
            data = json.loads(response.text)
            
            if 'user-agent' in data:
                yield {
                    'url': response.url,
                    'user_agent': data['user-agent'],
                    'type': 'user-agent-endpoint'
                }
            elif 'headers' in data:
                headers = data['headers']
                yield {
                    'url': response.url,
                    'user_agent': headers.get('User-Agent', 'Unknown'),
                    'accept_language': headers.get('Accept-Language', 'Unknown'),
                    'type': 'headers-endpoint'
                }
        except Exception as e:
            yield {
                'url': response.url,
                'error': str(e),
                'type': 'error'
            }
