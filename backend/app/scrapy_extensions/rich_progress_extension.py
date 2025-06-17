"""
Rich Progress Extension for ScrapyUI - GLOBALLY DISABLED

この拡張機能は完全に無効化されています。
軽量プログレスシステム（LightweightProgressExtension）を使用してください。

RichProgress関連のすべての機能は無効化され、
代わりにより軽量で安定したプログレス表示システムが使用されます。
"""

from scrapy.exceptions import NotConfigured
from scrapy.crawler import Crawler


class RichProgressExtension:
    """
    Rich Progress Extension - 完全無効化
    
    この拡張機能は無効化されています。
    LightweightProgressExtensionを使用してください。
    """
    
    def __init__(self, crawler: Crawler):
        # RichProgress拡張機能は完全に無効化
        raise NotConfigured("RichProgress extension is globally disabled. Use LightweightProgressExtension instead.")
    
    @classmethod
    def from_crawler(cls, crawler: Crawler):
        """Crawlerからインスタンスを作成 - 完全無効化"""
        # RichProgress拡張機能は完全に無効化
        return None


# 後方互換性のためのエイリアス
RichSpiderProgressExtension = RichProgressExtension
