from typing import Dict, Any, List, Optional, Union
import json
from datetime import datetime
from abc import ABC, abstractmethod

from ..config.database_config import get_database_config, DatabaseType, DatabaseConfig

class DatabaseService(ABC):
    """データベースサービスの抽象基底クラス"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
    
    @abstractmethod
    async def connect(self):
        """データベースに接続"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """データベース接続を切断"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        pass

class MongoDBService(DatabaseService):
    """MongoDB サービスクラス"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.client = None
        self.database = None
    
    async def connect(self):
        """MongoDBに接続"""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            
            connection_url = self.config.get_mongodb_url()
            self.client = AsyncIOMotorClient(connection_url)
            self.database = self.client[self.config.database]
            
            # 接続テスト
            await self.client.admin.command('ping')
            return True
        except ImportError:
            raise ImportError("motor package is required for MongoDB support. Install with: pip install motor")
        except Exception as e:
            raise Exception(f"Failed to connect to MongoDB: {str(e)}")
    
    async def disconnect(self):
        """MongoDB接続を切断"""
        if self.client:
            self.client.close()
    
    async def health_check(self) -> bool:
        """MongoDBヘルスチェック"""
        try:
            if self.client:
                await self.client.admin.command('ping')
                return True
            return False
        except Exception:
            return False
    
    async def insert_document(self, collection: str, document: Dict[str, Any]) -> str:
        """ドキュメントを挿入"""
        try:
            result = await self.database[collection].insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            raise Exception(f"Failed to insert document: {str(e)}")
    
    async def find_documents(self, collection: str, filter_dict: Dict[str, Any] = None, limit: int = None) -> List[Dict[str, Any]]:
        """ドキュメントを検索"""
        try:
            cursor = self.database[collection].find(filter_dict or {})
            if limit:
                cursor = cursor.limit(limit)
            
            documents = []
            async for doc in cursor:
                # ObjectIdを文字列に変換
                doc['_id'] = str(doc['_id'])
                documents.append(doc)
            
            return documents
        except Exception as e:
            raise Exception(f"Failed to find documents: {str(e)}")
    
    async def update_document(self, collection: str, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> bool:
        """ドキュメントを更新"""
        try:
            result = await self.database[collection].update_one(filter_dict, {"$set": update_dict})
            return result.modified_count > 0
        except Exception as e:
            raise Exception(f"Failed to update document: {str(e)}")
    
    async def delete_document(self, collection: str, filter_dict: Dict[str, Any]) -> bool:
        """ドキュメントを削除"""
        try:
            result = await self.database[collection].delete_one(filter_dict)
            return result.deleted_count > 0
        except Exception as e:
            raise Exception(f"Failed to delete document: {str(e)}")

class ElasticsearchService(DatabaseService):
    """Elasticsearch サービスクラス"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.client = None
    
    async def connect(self):
        """Elasticsearchに接続"""
        try:
            from elasticsearch import AsyncElasticsearch
            
            es_config = self.config.get_elasticsearch_config()
            self.client = AsyncElasticsearch(**es_config)
            
            # 接続テスト
            await self.client.ping()
            return True
        except ImportError:
            raise ImportError("elasticsearch package is required for Elasticsearch support. Install with: pip install elasticsearch")
        except Exception as e:
            raise Exception(f"Failed to connect to Elasticsearch: {str(e)}")
    
    async def disconnect(self):
        """Elasticsearch接続を切断"""
        if self.client:
            await self.client.close()
    
    async def health_check(self) -> bool:
        """Elasticsearchヘルスチェック"""
        try:
            if self.client:
                return await self.client.ping()
            return False
        except Exception:
            return False
    
    async def index_document(self, index: str, document: Dict[str, Any], doc_id: str = None) -> str:
        """ドキュメントをインデックス"""
        try:
            full_index = f"{self.config.index_prefix}_{index}"
            result = await self.client.index(
                index=full_index,
                body=document,
                id=doc_id
            )
            return result['_id']
        except Exception as e:
            raise Exception(f"Failed to index document: {str(e)}")
    
    async def search_documents(self, index: str, query: Dict[str, Any], size: int = 10) -> List[Dict[str, Any]]:
        """ドキュメントを検索"""
        try:
            full_index = f"{self.config.index_prefix}_{index}"
            result = await self.client.search(
                index=full_index,
                body={"query": query, "size": size}
            )
            
            documents = []
            for hit in result['hits']['hits']:
                doc = hit['_source']
                doc['_id'] = hit['_id']
                doc['_score'] = hit['_score']
                documents.append(doc)
            
            return documents
        except Exception as e:
            raise Exception(f"Failed to search documents: {str(e)}")
    
    async def delete_document(self, index: str, doc_id: str) -> bool:
        """ドキュメントを削除"""
        try:
            full_index = f"{self.config.index_prefix}_{index}"
            result = await self.client.delete(index=full_index, id=doc_id)
            return result['result'] == 'deleted'
        except Exception as e:
            raise Exception(f"Failed to delete document: {str(e)}")

class RedisService(DatabaseService):
    """Redis サービスクラス"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.client = None
    
    async def connect(self):
        """Redisに接続"""
        try:
            import aioredis
            
            redis_config = self.config.get_redis_config()
            self.client = aioredis.from_url(
                f"redis://{redis_config['host']}:{redis_config['port']}/{redis_config['db']}",
                password=redis_config.get('password'),
                **{k: v for k, v in redis_config.items() if k not in ['host', 'port', 'db', 'password']}
            )
            
            # 接続テスト
            await self.client.ping()
            return True
        except ImportError:
            raise ImportError("aioredis package is required for Redis support. Install with: pip install aioredis")
        except Exception as e:
            raise Exception(f"Failed to connect to Redis: {str(e)}")
    
    async def disconnect(self):
        """Redis接続を切断"""
        if self.client:
            await self.client.close()
    
    async def health_check(self) -> bool:
        """Redisヘルスチェック"""
        try:
            if self.client:
                await self.client.ping()
                return True
            return False
        except Exception:
            return False
    
    async def set_value(self, key: str, value: Union[str, Dict, List], expire: int = None) -> bool:
        """値を設定"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            await self.client.set(key, value, ex=expire)
            return True
        except Exception as e:
            raise Exception(f"Failed to set value: {str(e)}")
    
    async def get_value(self, key: str) -> Optional[Union[str, Dict, List]]:
        """値を取得"""
        try:
            value = await self.client.get(key)
            if value is None:
                return None
            
            # JSON形式の場合はパース
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value.decode('utf-8') if isinstance(value, bytes) else value
        except Exception as e:
            raise Exception(f"Failed to get value: {str(e)}")
    
    async def delete_key(self, key: str) -> bool:
        """キーを削除"""
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            raise Exception(f"Failed to delete key: {str(e)}")
    
    async def exists(self, key: str) -> bool:
        """キーの存在確認"""
        try:
            result = await self.client.exists(key)
            return result > 0
        except Exception as e:
            return False

class DatabaseServiceFactory:
    """データベースサービスファクトリー"""
    
    @staticmethod
    def create_service(config: DatabaseConfig) -> DatabaseService:
        """設定に基づいてサービスを作成"""
        if config.type == DatabaseType.MONGODB:
            return MongoDBService(config)
        elif config.type == DatabaseType.ELASTICSEARCH:
            return ElasticsearchService(config)
        elif config.type == DatabaseType.REDIS:
            return RedisService(config)
        else:
            raise ValueError(f"Unsupported database type: {config.type}")
    
    @staticmethod
    def create_all_services() -> Dict[str, DatabaseService]:
        """全設定からサービスを作成"""
        from ..config.database_config import db_config_manager
        
        services = {}
        for env_name, config in db_config_manager.get_all_configs().items():
            if config.type in [DatabaseType.MONGODB, DatabaseType.ELASTICSEARCH, DatabaseType.REDIS]:
                services[env_name] = DatabaseServiceFactory.create_service(config)
        
        return services

# グローバルサービスインスタンス
_services: Dict[str, DatabaseService] = {}

async def get_database_service(service_type: DatabaseType, environment: str = None) -> Optional[DatabaseService]:
    """データベースサービスを取得"""
    global _services
    
    service_key = f"{service_type.value}_{environment or 'default'}"
    
    if service_key not in _services:
        try:
            config = get_database_config(environment)
            if config.type == service_type:
                service = DatabaseServiceFactory.create_service(config)
                await service.connect()
                _services[service_key] = service
            else:
                return None
        except Exception as e:
            print(f"Failed to create {service_type.value} service: {str(e)}")
            return None
    
    return _services.get(service_key)

async def close_all_services():
    """全サービス接続を閉じる"""
    global _services
    
    for service in _services.values():
        try:
            await service.disconnect()
        except Exception as e:
            print(f"Error closing service: {str(e)}")
    
    _services.clear()
