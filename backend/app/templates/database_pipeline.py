"""
ScrapyUI データベースパイプライン
スパイダーが抽出したデータを自動的にデータベースに保存
"""
import os
import sys
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# ScrapyUIのバックエンドパスを追加
scrapy_ui_backend = Path(__file__).parent.parent.parent
sys.path.insert(0, str(scrapy_ui_backend))

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database import Result as DBResult
    from app.database import Base
except ImportError as e:
    print(f"⚠️ ScrapyUIモジュールのインポートに失敗: {e}")
    # フォールバック: 基本的なログ出力のみ
    DBResult = None
    Base = None


class ScrapyUIDatabasePipeline:
    """
    ScrapyUI データベースパイプライン
    
    スパイダーが抽出したアイテムを自動的にScrapyUIのデータベースに保存します。
    """
    
    def __init__(self, database_url: str = None, task_id: str = None):
        """
        パイプラインの初期化
        
        Args:
            database_url: データベースURL
            task_id: タスクID
        """
        self.database_url = database_url
        self.task_id = task_id
        self.engine = None
        self.session_factory = None
        self.session = None
        self.items_saved = 0
        self.crawl_start_datetime = None
        
    @classmethod
    def from_crawler(cls, crawler):
        """
        クローラーからパイプラインを作成
        
        Args:
            crawler: Scrapyクローラーインスタンス
            
        Returns:
            ScrapyUIDatabasePipeline: パイプラインインスタンス
        """
        # 設定からデータベースURLとタスクIDを取得
        database_url = crawler.settings.get('SCRAPYUI_DATABASE_URL')
        task_id = crawler.settings.get('SCRAPYUI_TASK_ID')
        
        # 環境変数からも取得を試行
        if not database_url:
            database_url = os.getenv('SCRAPYUI_DATABASE_URL')
        if not task_id:
            task_id = os.getenv('SCRAPYUI_TASK_ID')
        
        # デフォルトのデータベースURL
        if not database_url:
            db_path = scrapy_ui_backend / "database" / "scrapy_ui.db"
            database_url = f"sqlite:///{db_path}"
        
        return cls(database_url=database_url, task_id=task_id)
    
    def open_spider(self, spider):
        """
        スパイダー開始時の処理
        
        Args:
            spider: Scrapyスパイダーインスタンス
        """
        try:
            # クロールスタート日時を記録
            self.crawl_start_datetime = datetime.now().isoformat()
            
            # スパイダーにクロールスタート日時を設定
            if hasattr(spider, 'crawl_start_datetime'):
                spider.crawl_start_datetime = self.crawl_start_datetime
            
            # データベース接続を初期化
            if DBResult and Base:
                self.engine = create_engine(self.database_url)
                Base.metadata.create_all(self.engine)
                self.session_factory = sessionmaker(bind=self.engine)
                self.session = self.session_factory()
                
                spider.logger.info(f"✅ ScrapyUI データベースパイプライン開始")
                spider.logger.info(f"   データベースURL: {self.database_url}")
                spider.logger.info(f"   タスクID: {self.task_id}")
                spider.logger.info(f"   クロールスタート: {self.crawl_start_datetime}")
            else:
                spider.logger.warning("⚠️ ScrapyUIデータベースモジュールが利用できません")
                
        except Exception as e:
            spider.logger.error(f"❌ データベースパイプライン初期化エラー: {e}")
    
    def close_spider(self, spider):
        """
        スパイダー終了時の処理
        
        Args:
            spider: Scrapyスパイダーインスタンス
        """
        try:
            if self.session:
                self.session.close()
                
            spider.logger.info(f"✅ ScrapyUI データベースパイプライン終了")
            spider.logger.info(f"   保存されたアイテム数: {self.items_saved}件")
            
        except Exception as e:
            spider.logger.error(f"❌ データベースパイプライン終了エラー: {e}")
    
    def process_item(self, item, spider):
        """
        アイテム処理
        
        Args:
            item: 抽出されたアイテム
            spider: Scrapyスパイダーインスタンス
            
        Returns:
            item: 処理されたアイテム
        """
        try:
            if not self.session or not DBResult:
                # データベースが利用できない場合はアイテムをそのまま返す
                return item
            
            # アイテムを辞書に変換
            if hasattr(item, '_values'):
                # Scrapy Itemの場合
                item_dict = dict(item)
            elif isinstance(item, dict):
                # 辞書の場合
                item_dict = item.copy()
            else:
                # その他の場合は文字列化
                item_dict = {"data": str(item)}
            
            # 日時フィールドを追加
            current_time = datetime.now().isoformat()
            item_dict['crawl_start_datetime'] = self.crawl_start_datetime
            item_dict['item_acquired_datetime'] = current_time
            
            # データベースレコードを作成
            db_result = DBResult(
                id=str(uuid.uuid4()),
                task_id=self.task_id,
                data=item_dict,
                url=item_dict.get('url', ''),
                created_at=datetime.now(),
                crawl_start_datetime=datetime.fromisoformat(self.crawl_start_datetime) if self.crawl_start_datetime else None,
                item_acquired_datetime=datetime.fromisoformat(current_time)
            )
            
            # データベースに保存
            self.session.add(db_result)
            self.session.commit()
            
            self.items_saved += 1
            
            # 定期的にログ出力
            if self.items_saved % 10 == 0:
                spider.logger.info(f"📊 データベースに保存済み: {self.items_saved}件")
            
            return item
            
        except Exception as e:
            spider.logger.error(f"❌ アイテム保存エラー: {e}")
            spider.logger.error(f"   アイテム: {item}")
            
            # エラーが発生してもアイテムは返す
            return item


class ScrapyUIJSONPipeline:
    """
    ScrapyUI JSON出力パイプライン
    
    データベース保存と並行してJSONL形式でファイル出力も行います。
    """
    
    def __init__(self, file_path: str = None):
        """
        パイプラインの初期化
        
        Args:
            file_path: 出力ファイルパス
        """
        self.file_path = file_path
        self.file = None
        self.items_exported = 0
    
    @classmethod
    def from_crawler(cls, crawler):
        """
        クローラーからパイプラインを作成
        
        Args:
            crawler: Scrapyクローラーインスタンス
            
        Returns:
            ScrapyUIJSONPipeline: パイプラインインスタンス
        """
        # 設定からファイルパスを取得
        file_path = crawler.settings.get('SCRAPYUI_JSON_FILE')
        
        # 環境変数からも取得を試行
        if not file_path:
            file_path = os.getenv('SCRAPYUI_JSON_FILE')
        
        # デフォルトのファイルパス
        if not file_path:
            task_id = crawler.settings.get('SCRAPYUI_TASK_ID', 'unknown')
            file_path = f"results_{task_id}.jsonl"
        
        return cls(file_path=file_path)
    
    def open_spider(self, spider):
        """
        スパイダー開始時の処理
        
        Args:
            spider: Scrapyスパイダーインスタンス
        """
        try:
            self.file = open(self.file_path, 'w', encoding='utf-8')
            spider.logger.info(f"✅ JSON出力パイプライン開始: {self.file_path}")
        except Exception as e:
            spider.logger.error(f"❌ JSON出力ファイル開始エラー: {e}")
    
    def close_spider(self, spider):
        """
        スパイダー終了時の処理
        
        Args:
            spider: Scrapyスパイダーインスタンス
        """
        try:
            if self.file:
                self.file.close()
            spider.logger.info(f"✅ JSON出力パイプライン終了: {self.items_exported}件出力")
        except Exception as e:
            spider.logger.error(f"❌ JSON出力ファイル終了エラー: {e}")
    
    def process_item(self, item, spider):
        """
        アイテム処理
        
        Args:
            item: 抽出されたアイテム
            spider: Scrapyスパイダーインスタンス
            
        Returns:
            item: 処理されたアイテム
        """
        try:
            if self.file:
                # アイテムを辞書に変換
                if hasattr(item, '_values'):
                    item_dict = dict(item)
                elif isinstance(item, dict):
                    item_dict = item
                else:
                    item_dict = {"data": str(item)}
                
                # JSONL形式で出力
                line = json.dumps(item_dict, ensure_ascii=False) + '\n'
                self.file.write(line)
                self.file.flush()
                
                self.items_exported += 1
            
            return item
            
        except Exception as e:
            spider.logger.error(f"❌ JSON出力エラー: {e}")
            return item
