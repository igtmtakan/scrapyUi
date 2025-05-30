"""
ScrapyRealtimeEngine - Scrapyを継承したリアルタイム進捗監視エンジン

このモジュールはScrapyの核となるクラスを継承し、メソッドをオーバーライドして
リアルタイム進捗監視機能を追加します。Scrapy自体は改変せず、継承のみで実装。

機能:
- リアルタイムダウンロード進捗監視
- リアルタイムアイテム処理監視
- WebSocket通知統合
- 詳細統計情報の収集
- エラー・例外の即座検出
"""

import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timezone
import asyncio
import threading
import json

from scrapy.crawler import CrawlerProcess, Crawler
from scrapy.core.engine import ExecutionEngine
from scrapy.core.downloader import Downloader
from scrapy.core.scraper import Scraper
from scrapy.http import Request, Response
from scrapy.item import Item
from scrapy.utils.log import configure_logging
from scrapy.statscollectors import StatsCollector
from scrapy.spiders import Spider


class RealtimeStatsCollector(StatsCollector):
    """リアルタイム統計収集クラス"""

    def __init__(self, crawler, progress_callback: Optional[Callable] = None):
        super().__init__(crawler)
        self.progress_callback = progress_callback
        self.start_time = datetime.now(timezone.utc)
        self.last_update = self.start_time

    def inc_value(self, key, count=1, start=0):
        """統計値の増加をオーバーライド"""
        super().inc_value(key, count, start)

        # リアルタイム通知
        if self.progress_callback:
            current_stats = self.get_stats()
            self._notify_progress(current_stats)

    def set_value(self, key, value):
        """統計値の設定をオーバーライド"""
        super().set_value(key, value)

        # リアルタイム通知
        if self.progress_callback:
            current_stats = self.get_stats()
            self._notify_progress(current_stats)

    def _notify_progress(self, stats: Dict[str, Any]):
        """進捗通知を送信"""
        try:
            # pending item数を計算
            pending_items = self._calculate_pending_items(stats)

            progress_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'items_count': stats.get('item_scraped_count', 0),
                'requests_count': stats.get('downloader/request_count', 0),
                'responses_count': stats.get('downloader/response_count', 0),
                'errors_count': stats.get('downloader/exception_count', 0) + stats.get('spider_exceptions', 0),
                'bytes_downloaded': stats.get('downloader/response_bytes', 0),
                'pending_items': pending_items,  # pending item数を追加
                'elapsed_time': (datetime.now(timezone.utc) - self.start_time).total_seconds(),
                'items_per_minute': self._calculate_items_per_minute(stats),
                'requests_per_minute': self._calculate_requests_per_minute(stats),
                'progress_percentage': self._calculate_progress_percentage(stats, pending_items)
            }

            # 非同期でコールバックを実行
            if hasattr(self.progress_callback, '__call__'):
                self.progress_callback(progress_data)

        except Exception as e:
            print(f"Error in progress notification: {e}")

    def _calculate_items_per_minute(self, stats: Dict[str, Any]) -> float:
        """アイテム/分を計算"""
        items = stats.get('item_scraped_count', 0)
        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds() / 60
        return items / elapsed if elapsed > 0 else 0

    def _calculate_requests_per_minute(self, stats: Dict[str, Any]) -> float:
        """リクエスト/分を計算"""
        requests = stats.get('downloader/request_count', 0)
        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds() / 60
        return requests / elapsed if elapsed > 0 else 0

    def _calculate_pending_items(self, stats: Dict[str, Any]) -> int:
        """pending item数を計算"""
        # リクエスト数からレスポンス数を引いてpending item数を推定
        requests = stats.get('downloader/request_count', 0)
        responses = stats.get('downloader/response_count', 0)
        pending = max(0, requests - responses)
        return pending

    def _calculate_progress_percentage(self, stats: Dict[str, Any], pending_items: int) -> float:
        """進捗率を計算"""
        items_scraped = stats.get('item_scraped_count', 0)
        total_estimated = items_scraped + pending_items

        if total_estimated > 0:
            return (items_scraped / total_estimated) * 100.0
        return 0.0


class RealtimeDownloader(Downloader):
    """リアルタイムダウンローダークラス"""

    def __init__(self, crawler, progress_callback: Optional[Callable] = None):
        super().__init__(crawler)
        self.progress_callback = progress_callback
        self.download_count = 0

    def download(self, request, spider):
        """ダウンロードメソッドをオーバーライド"""
        self.download_count += 1

        # ダウンロード開始通知
        if self.progress_callback:
            self._notify_download_start(request)

        # 元のダウンロード処理を実行
        deferred = super().download(request, spider)

        # ダウンロード完了時のコールバックを追加
        deferred.addCallback(self._on_download_complete, request)
        deferred.addErrback(self._on_download_error, request)

        return deferred

    def _notify_download_start(self, request: Request):
        """ダウンロード開始通知"""
        try:
            download_data = {
                'type': 'download_start',
                'url': request.url,
                'method': request.method,
                'download_count': self.download_count,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            if hasattr(self.progress_callback, '__call__'):
                self.progress_callback(download_data)

        except Exception as e:
            print(f"Error in download start notification: {e}")

    def _on_download_complete(self, response: Response, request: Request):
        """ダウンロード完了時の処理"""
        try:
            if self.progress_callback:
                download_data = {
                    'type': 'download_complete',
                    'url': response.url,
                    'status': response.status,
                    'size': len(response.body),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

                if hasattr(self.progress_callback, '__call__'):
                    self.progress_callback(download_data)

        except Exception as e:
            print(f"Error in download complete notification: {e}")

        return response

    def _on_download_error(self, failure, request: Request):
        """ダウンロードエラー時の処理"""
        try:
            if self.progress_callback:
                error_data = {
                    'type': 'download_error',
                    'url': request.url,
                    'error': str(failure.value),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

                if hasattr(self.progress_callback, '__call__'):
                    self.progress_callback(error_data)

        except Exception as e:
            print(f"Error in download error notification: {e}")

        return failure


class RealtimeScraper(Scraper):
    """リアルタイムスクレイパークラス"""

    def __init__(self, crawler, progress_callback: Optional[Callable] = None):
        super().__init__(crawler)
        self.progress_callback = progress_callback
        self.item_count = 0

    def _itemproc_finished(self, output, item, response, spider):
        """アイテム処理完了時の処理をオーバーライド"""
        self.item_count += 1

        # アイテム処理通知
        if self.progress_callback:
            self._notify_item_processed(item, response)

        # 元の処理を実行
        return super()._itemproc_finished(output, item, response, spider)

    def _notify_item_processed(self, item: Item, response: Response):
        """アイテム処理通知"""
        try:
            item_data = {
                'type': 'item_processed',
                'item_count': self.item_count,
                'url': response.url,
                'item_fields': len(dict(item)) if hasattr(item, '__iter__') else 0,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            if hasattr(self.progress_callback, '__call__'):
                self.progress_callback(item_data)

        except Exception as e:
            print(f"Error in item processed notification: {e}")


class RealtimeSpider(Spider):
    """リアルタイム監視機能付きSpiderクラス"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pending_items = []  # pending itemsのリスト
        self.processed_items = 0  # 処理済みitem数
        self.total_items_target = kwargs.get('target_items', 100)  # 目標アイテム数

    def add_pending_item(self, item_data):
        """pending itemを追加"""
        self.pending_items.append({
            'data': item_data,
            'timestamp': datetime.now(timezone.utc),
            'status': 'pending'
        })

    def process_pending_item(self, index=0):
        """pending itemを処理"""
        if index < len(self.pending_items):
            item = self.pending_items[index]
            item['status'] = 'processed'
            item['processed_timestamp'] = datetime.now(timezone.utc)
            self.processed_items += 1
            return item
        return None

    def get_pending_count(self):
        """pending item数を取得"""
        return len([item for item in self.pending_items if item['status'] == 'pending'])

    def get_progress_percentage(self):
        """進捗率を計算"""
        if self.total_items_target > 0:
            return (self.processed_items / self.total_items_target) * 100.0
        return 0.0

    def get_progress_stats(self):
        """進捗統計を取得"""
        return {
            'pending_items': self.get_pending_count(),
            'processed_items': self.processed_items,
            'total_target': self.total_items_target,
            'progress_percentage': self.get_progress_percentage(),
            'pending_ratio': self.get_pending_count() / max(1, self.total_items_target)
        }


class RealtimeExecutionEngine(ExecutionEngine):
    """リアルタイム実行エンジンクラス"""

    def __init__(self, crawler, spider_closed_callback, progress_callback: Optional[Callable] = None):
        super().__init__(crawler, spider_closed_callback)
        self.progress_callback = progress_callback
        self.pending_requests = set()  # pending requestsのセット
        self.pending_items_queue = []  # pending itemsのキュー

    def crawl(self, request, spider):
        """リクエストをクロールキューに追加（オーバーライド）"""
        # pending requestsに追加
        self.pending_requests.add(id(request))

        # 元の処理を実行
        result = super().crawl(request, spider)

        # 進捗通知
        if self.progress_callback:
            self._notify_pending_update()

        return result

    def _notify_pending_update(self):
        """pending状態の更新通知"""
        try:
            pending_data = {
                'type': 'pending_update',
                'pending_requests': len(self.pending_requests),
                'pending_items': len(self.pending_items_queue),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            if hasattr(self.progress_callback, '__call__'):
                self.progress_callback(pending_data)

        except Exception as e:
            print(f"Error in pending update notification: {e}")

    def _handle_downloader_output(self, response, request, spider):
        """ダウンローダー出力処理（オーバーライド）"""
        # pending requestsから削除
        self.pending_requests.discard(id(request))

        # 元の処理を実行
        result = super()._handle_downloader_output(response, request, spider)

        # 進捗通知
        if self.progress_callback:
            self._notify_pending_update()

        return result

    def _get_downloader(self, crawler):
        """カスタムダウンローダーを返す"""
        return RealtimeDownloader(crawler, self.progress_callback)

    def _get_scraper(self, crawler):
        """カスタムスクレイパーを返す"""
        return RealtimeScraper(crawler, self.progress_callback)


class RealtimeCrawler(Crawler):
    """リアルタイムクローラークラス"""

    def __init__(self, spidercls, settings=None, progress_callback: Optional[Callable] = None):
        super().__init__(spidercls, settings)
        self.progress_callback = progress_callback

    def _create_engine(self):
        """カスタムエンジンを作成"""
        return RealtimeExecutionEngine(self, self._spider_closed, self.progress_callback)

    def _create_stats(self):
        """カスタム統計収集器を作成"""
        return RealtimeStatsCollector(self, self.progress_callback)


class RealtimeCrawlerProcess(CrawlerProcess):
    """リアルタイムクローラープロセスクラス"""

    def __init__(self, settings=None, install_root_handler=True, progress_callback: Optional[Callable] = None):
        super().__init__(settings, install_root_handler)
        self.progress_callback = progress_callback

    def _create_crawler(self, spidercls):
        """カスタムクローラーを作成"""
        if isinstance(spidercls, str):
            spidercls = self.spider_loader.load(spidercls)
        return RealtimeCrawler(spidercls, self.settings, self.progress_callback)


class ScrapyRealtimeEngine:
    """
    Scrapyリアルタイム実行エンジン

    Scrapyを継承してリアルタイム進捗監視機能を追加したメインクラス
    """

    def __init__(self, progress_callback: Optional[Callable] = None, websocket_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.websocket_callback = websocket_callback
        self.process = None
        self.stats = {}

    def run_spider(self, spider_name: str, project_path: str, settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """スパイダーをリアルタイム監視付きで実行"""
        try:
            import os
            import sys
            import importlib.util

            # 絶対パスに変換
            project_path = os.path.abspath(project_path)

            # プロジェクト構造を確認して適切なパスを設定
            # admin_aiueo/admin_aiueo/spiders の構造に対応
            project_name = os.path.basename(project_path)
            inner_project_path = os.path.join(project_path, project_name)
            spiders_path = os.path.join(inner_project_path, 'spiders')

            # spidersディレクトリが見つからない場合は直接のspidersディレクトリを確認
            if not os.path.exists(spiders_path):
                spiders_path = os.path.join(project_path, 'spiders')

            print(f"🔍 Project path: {project_path}")
            print(f"🔍 Inner project path: {inner_project_path}")
            print(f"🔍 Spiders path: {spiders_path}")
            print(f"🔍 Spiders directory exists: {os.path.exists(spiders_path)}")

            # プロジェクトパスをPythonパスに追加
            if project_path not in sys.path:
                sys.path.insert(0, project_path)
            if inner_project_path not in sys.path:
                sys.path.insert(0, inner_project_path)
            if spiders_path not in sys.path:
                sys.path.insert(0, spiders_path)

            # 作業ディレクトリを変更（内部プロジェクトディレクトリに移動）
            original_cwd = os.getcwd()
            work_dir = inner_project_path if os.path.exists(inner_project_path) else project_path
            os.chdir(work_dir)
            print(f"🔍 Working directory: {work_dir}")

            try:
                # スパイダーファイルの存在確認
                spider_file = os.path.join(spiders_path, f'{spider_name}.py')
                print(f"🔍 Spider file: {spider_file}")
                print(f"🔍 Spider file exists: {os.path.exists(spider_file)}")

                # 設定を準備
                custom_settings = {
                    'LOG_LEVEL': 'INFO',
                    'LOGSTATS_INTERVAL': 1,  # 1秒間隔で統計出力
                    'ROBOTSTXT_OBEY': False,
                    'BOT_NAME': 'scrapybot',
                    'SPIDER_MODULES': ['spiders'],
                    'NEWSPIDER_MODULE': 'spiders',
                    'USER_AGENT': 'ScrapyUI (+http://www.scrapyui.com)',
                    # Playwright設定（有効化）
                    'DOWNLOAD_HANDLERS': {
                        "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
                        "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
                    },
                    # Reactor設定は別プロセスで処理するため削除
                    'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
                    'PLAYWRIGHT_LAUNCH_OPTIONS': {
                        'headless': True,
                        'args': ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
                    },
                    'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 30000,
                    'PLAYWRIGHT_PROCESS_REQUEST_HEADERS': None,
                    # HTTP設定
                    'DOWNLOAD_DELAY': 2,
                    'RANDOMIZE_DOWNLOAD_DELAY': True,
                    'AUTOTHROTTLE_ENABLED': True,
                    'AUTOTHROTTLE_START_DELAY': 1,
                    'AUTOTHROTTLE_MAX_DELAY': 10,
                    'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
                    # 結果出力設定
                    'FEEDS': {
                        f'results/{spider_name}_results.json': {
                            'format': 'json',
                            'encoding': 'utf8',
                            'store_empty': False,
                            'indent': 2
                        }
                    },
                    # アイテム制限設定を削除（自然な終了を待つ）
                    'DOWNLOAD_DELAY': 2,
                    'CONCURRENT_REQUESTS': 1
                }

                # カスタム設定をマージ
                if settings:
                    custom_settings.update(settings)

                # ログ設定
                configure_logging({'LOG_LEVEL': 'DEBUG'})

                # リアルタイムプロセスを作成
                self.process = RealtimeCrawlerProcess(
                    settings=custom_settings,
                    progress_callback=self._on_progress_update
                )

                # スパイダーローダーを初期化
                print(f"🔍 Available spiders: {list(self.process.spider_loader.list())}")

                # スパイダーを実行
                try:
                    self.process.crawl(spider_name)
                    print(f"✅ Spider {spider_name} added to crawler")
                    self.process.start()
                    print(f"✅ Crawler process started")
                except Exception as crawl_error:
                    print(f"❌ Error during crawl: {crawl_error}")
                    raise

                # 統計情報を取得
                final_stats = self.stats_collector.get_stats() if hasattr(self, 'stats_collector') else {}
                items_count = final_stats.get('item_scraped_count', 0)
                requests_count = final_stats.get('downloader/request_count', 0)
                errors_count = final_stats.get('spider_exceptions', 0)

                print(f"📊 Final statistics: items={items_count}, requests={requests_count}, errors={errors_count}")

                return {
                    'success': True,
                    'stats': self.stats,
                    'items_count': items_count,
                    'requests_count': requests_count,
                    'errors_count': errors_count
                }

            finally:
                # 作業ディレクトリを復元
                os.chdir(original_cwd)

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _on_progress_update(self, progress_data: Dict[str, Any]):
        """進捗更新時のコールバック"""
        try:
            # 統計を更新
            self.stats.update(progress_data)

            # 外部コールバックを呼び出し
            if self.progress_callback:
                self.progress_callback(progress_data)

            # WebSocket通知
            if self.websocket_callback:
                self.websocket_callback(progress_data)

            # デバッグ出力
            if progress_data.get('type') == 'item_processed':
                print(f"📦 Item {progress_data.get('item_count', 0)} processed from {progress_data.get('url', 'unknown')}")
            elif progress_data.get('type') == 'download_complete':
                print(f"⬇️ Downloaded {progress_data.get('url', 'unknown')} ({progress_data.get('size', 0)} bytes)")

        except Exception as e:
            print(f"Error in progress update: {e}")
