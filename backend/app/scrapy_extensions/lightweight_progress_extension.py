"""
軽量プログレス表示エクステンション

Rich Progress Extensionの代替として、シンプルで安定した統計収集を提供
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from scrapy import signals
from scrapy.http import Request, Response
from scrapy.spiders import Spider
from scrapy.exceptions import NotConfigured


class LightweightProgressExtension:
    """軽量プログレス表示エクステンション"""
    
    def __init__(self, crawler):
        """初期化"""
        self.crawler = crawler
        self.settings = crawler.settings
        
        # 統計データ
        self.stats = {
            'requests_count': 0,
            'responses_count': 0,
            'items_count': 0,
            'errors_count': 0,
            'start_time': None,
            'last_update': None,
            'spider_name': '',
            'task_id': '',
            'status': 'STARTING'
        }
        
        # 設定
        self.task_id = (
            self.settings.get('TASK_ID', '') or
            os.environ.get('SCRAPY_TASK_ID', '') or
            f"task_{int(time.time())}"
        )
        self.update_interval = 2.0  # 2秒間隔で更新
        self.stats_file = None

        # WebSocket無効化チェック
        self.websocket_enabled = self.settings.getbool('LIGHTWEIGHT_PROGRESS_WEBSOCKET', True)

        # バルクインサート用のアイテムバッファ
        self.item_buffer = []
        self.bulk_insert_size = 100  # 100件ごとにバルクインサート
        self.bulk_insert_enabled = self.settings.getbool('LIGHTWEIGHT_BULK_INSERT', True)

        # 自動ファイル管理設定
        self.auto_file_management = self.settings.getbool('AUTO_FILE_MANAGEMENT', True)
        self.max_file_lines = self.settings.getint('MAX_JSONL_LINES', 500)
        self.keep_sessions = self.settings.getint('KEEP_SESSIONS', 1)
        self.auto_cleanup_interval = self.settings.getint('AUTO_CLEANUP_INTERVAL_HOURS', 1)

        print(f"🔧 Lightweight Progress Extension initialized for task: {self.task_id}")
        if self.auto_file_management:
            print(f"🗂️ Auto file management enabled: max_lines={self.max_file_lines}, keep_sessions={self.keep_sessions}")

    @classmethod
    def from_crawler(cls, crawler):
        """Crawlerからインスタンスを作成"""
        # WebSocket無効化チェック
        if not crawler.settings.getbool('LIGHTWEIGHT_PROGRESS_WEBSOCKET', True):
            print("🔧 Lightweight Progress Extension disabled by settings")
            return None
            
        extension = cls(crawler)
        
        # シグナルを接続（シンプルな接続）
        try:
            crawler.signals.connect(extension.spider_opened, signal=signals.spider_opened)
            crawler.signals.connect(extension.spider_closed, signal=signals.spider_closed)
            crawler.signals.connect(extension.request_scheduled, signal=signals.request_scheduled)
            crawler.signals.connect(extension.response_received, signal=signals.response_received)
            crawler.signals.connect(extension.item_scraped, signal=signals.item_scraped)
            crawler.signals.connect(extension.spider_error, signal=signals.spider_error)
            
            print("🔧 Lightweight Progress Extension signals connected")
        except Exception as e:
            print(f"❌ Failed to connect Lightweight Progress Extension signals: {e}")
        
        return extension

    def spider_opened(self, spider: Spider):
        """スパイダー開始時の処理"""
        try:
            self.stats['spider_name'] = spider.name
            self.stats['start_time'] = time.time()
            self.stats['last_update'] = time.time()
            self.stats['status'] = 'RUNNING'
            
            # 統計ファイルパスを設定
            if self.task_id:
                stats_dir = os.path.join(os.getcwd(), 'stats')
                os.makedirs(stats_dir, exist_ok=True)
                self.stats_file = os.path.join(stats_dir, f"{self.task_id}_stats.json")
            
            self._save_stats()
            print(f"🕷️ Lightweight Progress started for spider: {spider.name}")
            
        except Exception as e:
            print(f"❌ Error in spider_opened: {e}")

    def spider_closed(self, spider: Spider, reason: str):
        """スパイダー終了時の処理"""
        try:
            # 残りのアイテムをバルクインサート
            if self.bulk_insert_enabled and self.item_buffer:
                print(f"🔄 Final bulk insert: {len(self.item_buffer)} items")
                self._perform_bulk_insert()

            self.stats['status'] = 'COMPLETED' if reason == 'finished' else 'FAILED'
            self.stats['last_update'] = time.time()

            # 最終統計を保存
            self._save_stats()

            # 自動ファイル管理を実行
            if self.auto_file_management:
                self._perform_auto_file_management()

            # 統計サマリーを表示
            elapsed = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
            print(f"🏁 Lightweight Progress completed:")
            print(f"   📤 Requests: {self.stats['requests_count']}")
            print(f"   📥 Responses: {self.stats['responses_count']}")
            print(f"   📦 Items: {self.stats['items_count']}")
            print(f"   ❌ Errors: {self.stats['errors_count']}")
            print(f"   ⏱️ Duration: {elapsed:.1f}s")
            print(f"   🎯 Status: {self.stats['status']}")
            
        except Exception as e:
            print(f"❌ Error in spider_closed: {e}")

    def request_scheduled(self, request: Request, spider: Spider):
        """リクエスト送信時の処理"""
        try:
            self.stats['requests_count'] += 1
            self._update_if_needed()
        except Exception as e:
            print(f"❌ Error in request_scheduled: {e}")

    def response_received(self, response: Response, request: Request, spider: Spider):
        """レスポンス受信時の処理"""
        try:
            self.stats['responses_count'] += 1
            self._update_if_needed()
        except Exception as e:
            print(f"❌ Error in response_received: {e}")

    def item_scraped(self, item: Dict[str, Any], response: Response, spider: Spider):
        """アイテム取得時の処理（バルクインサート対応）"""
        try:
            self.stats['items_count'] += 1

            # バルクインサート機能
            if self.bulk_insert_enabled:
                # アイテムをバッファに追加
                item_data = dict(item)
                item_data['scraped_at'] = datetime.now().isoformat()
                item_data['task_id'] = self.task_id
                item_data['spider_name'] = spider.name
                self.item_buffer.append(item_data)

                # バッファが満杯になったらバルクインサート実行
                if len(self.item_buffer) >= self.bulk_insert_size:
                    self._perform_bulk_insert()

            self._update_if_needed()
        except Exception as e:
            print(f"❌ Error in item_scraped: {e}")

    def spider_error(self, failure, response: Response, spider: Spider):
        """エラー発生時の処理"""
        try:
            self.stats['errors_count'] += 1
            self._update_if_needed()
        except Exception as e:
            print(f"❌ Error in spider_error: {e}")

    def _update_if_needed(self):
        """必要に応じて統計を更新"""
        try:
            current_time = time.time()
            if (current_time - self.stats['last_update']) >= self.update_interval:
                self.stats['last_update'] = current_time
                self._save_stats()
                
                # 簡単な進捗表示
                elapsed = current_time - self.stats['start_time'] if self.stats['start_time'] else 0
                rate = self.stats['items_count'] / elapsed if elapsed > 0 else 0
                print(f"📊 Progress: R:{self.stats['requests_count']} | "
                      f"Res:{self.stats['responses_count']} | "
                      f"I:{self.stats['items_count']} | "
                      f"E:{self.stats['errors_count']} | "
                      f"Rate:{rate:.2f}/s")
                
        except Exception as e:
            print(f"❌ Error in _update_if_needed: {e}")

    def _save_stats(self):
        """統計をファイルに保存"""
        try:
            if self.stats_file:
                # タイムスタンプを追加
                stats_with_timestamp = self.stats.copy()
                stats_with_timestamp['timestamp'] = datetime.now().isoformat()
                
                # JSONファイルに保存
                with open(self.stats_file, 'w', encoding='utf-8') as f:
                    json.dump(stats_with_timestamp, f, ensure_ascii=False, indent=2)
                
                # WebSocket送信（有効な場合）
                if self.websocket_enabled:
                    self._send_websocket_update(stats_with_timestamp)
                    
        except Exception as e:
            print(f"❌ Error saving stats: {e}")

    def _send_websocket_update(self, stats: Dict[str, Any]):
        """WebSocket経由で統計を送信"""
        try:
            # WebSocket送信の実装（必要に応じて）
            # 現在はファイルベースの統計のみ
            pass
        except Exception as e:
            print(f"❌ Error sending WebSocket update: {e}")

    def _perform_bulk_insert(self):
        """バルクインサートを実行"""
        try:
            if not self.item_buffer:
                return

            print(f"📦 Performing bulk insert: {len(self.item_buffer)} items")

            # データベース接続の取得
            try:
                import sys
                import uuid
                import hashlib
                sys.path.append('/home/igtmtakan/workplace/python/scrapyUI/backend')
                from app.database import SessionLocal, Result as DBResult

                # データベースセッションを取得
                db = SessionLocal()

                # バルクインサート用のデータを準備（重複チェック付き）
                bulk_data = []
                skipped_duplicates = 0

                for item_data in self.item_buffer:
                    # 改良されたデータハッシュを生成
                    data_hash = self._generate_improved_data_hash(item_data)

                    # 重複チェック（同一タスク内）
                    existing = db.query(DBResult).filter(
                        DBResult.task_id == self.task_id,
                        DBResult.data_hash == data_hash
                    ).first()

                    if existing:
                        skipped_duplicates += 1
                        print(f"⚠️ 重複データをスキップ: {data_hash[:8]}...")
                        continue

                    result_data = DBResult(
                        id=str(uuid.uuid4()),
                        task_id=self.task_id,
                        data=item_data,
                        data_hash=data_hash,
                        item_acquired_datetime=datetime.now(),
                        created_at=datetime.now()
                    )
                    bulk_data.append(result_data)

                # バルクインサート実行
                if bulk_data:
                    db.bulk_save_objects(bulk_data)
                    db.commit()
                    print(f"✅ Bulk insert completed: {len(bulk_data)} items")
                    if skipped_duplicates > 0:
                        print(f"⚠️ Skipped {skipped_duplicates} duplicate items")
                else:
                    print("⚠️ No new items to insert (all duplicates)")

                db.close()

                # バッファをクリア
                self.item_buffer.clear()

            except Exception as db_error:
                print(f"❌ Database bulk insert error: {db_error}")
                # データベースエラーの場合、ファイルに保存
                self._save_items_to_file()

        except Exception as e:
            print(f"❌ Error in bulk insert: {e}")

    def _save_items_to_file(self):
        """アイテムをファイルに保存（データベース障害時のフォールバック）"""
        try:
            if not self.item_buffer:
                return

            backup_file = f"backup_items_{self.task_id}_{int(time.time())}.jsonl"
            with open(backup_file, 'w', encoding='utf-8') as f:
                for item in self.item_buffer:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')

            print(f"💾 Items saved to backup file: {backup_file}")
            self.item_buffer.clear()

        except Exception as e:
            print(f"❌ Error saving items to file: {e}")

    def _generate_improved_data_hash(self, item_data: Dict[str, Any]) -> str:
        """改良されたデータハッシュを生成（重複防止強化）"""
        try:
            import hashlib

            # 重要なフィールドのみを使用してハッシュを生成
            key_fields = ['title', 'product_url', 'ranking_position', 'price', 'rating']
            hash_data = {}

            for field in key_fields:
                if field in item_data and item_data[field] is not None:
                    hash_data[field] = str(item_data[field]).strip()

            # URLからASINを抽出してハッシュに含める
            product_url = item_data.get('product_url', '')
            if '/dp/' in product_url:
                asin = product_url.split('/dp/')[1].split('/')[0]
                hash_data['asin'] = asin

            # ソートされた辞書から文字列を生成
            data_str = str(sorted(hash_data.items()))
            return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

        except Exception as e:
            print(f"❌ Error generating data hash: {e}")
            # フォールバック：全データのハッシュ
            import hashlib
            data_str = str(sorted(item_data.items()))
            return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

    def _perform_auto_file_management(self):
        """自動ファイル管理を実行"""
        try:
            print("🗂️ Starting auto file management...")

            # 現在のディレクトリでJSONLファイルを検索
            import glob
            jsonl_files = glob.glob("*.jsonl")

            for jsonl_file in jsonl_files:
                self._manage_jsonl_file(jsonl_file)

        except Exception as e:
            print(f"❌ Error in auto file management: {e}")

    def _manage_jsonl_file(self, jsonl_file):
        """個別のJSONLファイルを管理"""
        try:
            import os
            from pathlib import Path

            # ファイルサイズと行数をチェック
            if not os.path.exists(jsonl_file):
                return

            line_count = self._count_file_lines(jsonl_file)
            file_size = os.path.getsize(jsonl_file)

            print(f"📄 Checking {jsonl_file}: {line_count:,} lines, {file_size:,} bytes")

            # 行数が上限を超えている場合、または常にクリーンアップ
            if line_count > self.max_file_lines:
                print(f"🧹 File {jsonl_file} exceeds max lines ({line_count:,} > {self.max_file_lines:,})")
                self._cleanup_jsonl_file(jsonl_file)
            elif line_count > 100:  # 100行を超えたら常にクリーンアップ
                print(f"🧹 File {jsonl_file} cleanup triggered ({line_count:,} lines)")
                self._cleanup_jsonl_file(jsonl_file)
            else:
                print(f"✅ File {jsonl_file} is within limits")

        except Exception as e:
            print(f"❌ Error managing file {jsonl_file}: {e}")

    def _count_file_lines(self, file_path):
        """ファイルの行数を効率的にカウント"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def _cleanup_jsonl_file(self, jsonl_file):
        """JSONLファイルをクリーンアップ"""
        try:
            import subprocess
            import sys

            # JSONLファイル管理ツールを使用してクリーンアップ
            backend_path = '/home/igtmtakan/workplace/python/scrapyUI/backend'
            tool_path = os.path.join(backend_path, 'jsonl_file_manager.py')

            if os.path.exists(tool_path):
                cmd = [
                    sys.executable, tool_path, jsonl_file,
                    '--clean', '--keep-sessions', str(self.keep_sessions)
                ]

                print(f"🔧 Running cleanup: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

                if result.returncode == 0:
                    print(f"✅ Successfully cleaned up {jsonl_file}")
                    print(result.stdout)
                else:
                    print(f"❌ Cleanup failed for {jsonl_file}: {result.stderr}")
            else:
                print(f"⚠️ Cleanup tool not found: {tool_path}")

        except Exception as e:
            print(f"❌ Error cleaning up {jsonl_file}: {e}")
