#!/usr/bin/env python3
"""
ScrapyUI データベース初期化スクリプト
"""

import sys
import os
import asyncio
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import engine, Base
from app.config.database_config import get_database_config, DatabaseType
from app.services.database_service import get_database_service, DatabaseServiceFactory
from app.auth.jwt_handler import PasswordHandler
from app.database import User, SessionLocal
import uuid

async def init_relational_database():
    """リレーショナルデータベースを初期化"""
    print("🔧 Initializing relational database...")
    
    try:
        # テーブル作成
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # デモユーザー作成
        await create_demo_user()
        
    except Exception as e:
        print(f"❌ Failed to initialize relational database: {str(e)}")
        raise

async def create_demo_user():
    """デモユーザーを作成"""
    print("👤 Creating demo user...")
    
    db = SessionLocal()
    try:
        # 既存ユーザーをチェック
        existing_user = db.query(User).filter(User.email == 'demo@example.com').first()
        if existing_user:
            print("ℹ️  Demo user already exists")
            return
        
        # デモユーザー作成
        demo_user = User(
            id=str(uuid.uuid4()),
            email='demo@example.com',
            username='demo',
            full_name='Demo User',
            hashed_password=PasswordHandler.hash_password('demo12345'),
            is_active=True,
            is_superuser=False
        )
        
        db.add(demo_user)
        db.commit()
        
        print(f"✅ Demo user created: {demo_user.email}")
        print(f"   Username: {demo_user.username}")
        print(f"   Password: demo12345")
        
    except Exception as e:
        print(f"❌ Failed to create demo user: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

async def init_mongodb():
    """MongoDBを初期化"""
    print("🍃 Initializing MongoDB...")
    
    try:
        mongodb_service = await get_database_service(DatabaseType.MONGODB)
        if not mongodb_service:
            print("ℹ️  MongoDB not configured, skipping...")
            return
        
        # 接続テスト
        if await mongodb_service.health_check():
            print("✅ MongoDB connection successful")
            
            # インデックス作成
            await create_mongodb_indexes(mongodb_service)
        else:
            print("❌ MongoDB connection failed")
            
    except Exception as e:
        print(f"❌ Failed to initialize MongoDB: {str(e)}")

async def create_mongodb_indexes(mongodb_service):
    """MongoDBインデックスを作成"""
    print("📊 Creating MongoDB indexes...")
    
    try:
        # スクレイピング結果用インデックス
        await mongodb_service.database.scrapy_results.create_index([
            ("task_id", 1),
            ("created_at", -1)
        ])
        
        # ログ用インデックス
        await mongodb_service.database.scrapy_logs.create_index([
            ("task_id", 1),
            ("level", 1),
            ("timestamp", -1)
        ])
        
        print("✅ MongoDB indexes created")
        
    except Exception as e:
        print(f"❌ Failed to create MongoDB indexes: {str(e)}")

async def init_elasticsearch():
    """Elasticsearchを初期化"""
    print("🔍 Initializing Elasticsearch...")
    
    try:
        es_service = await get_database_service(DatabaseType.ELASTICSEARCH)
        if not es_service:
            print("ℹ️  Elasticsearch not configured, skipping...")
            return
        
        # 接続テスト
        if await es_service.health_check():
            print("✅ Elasticsearch connection successful")
            
            # インデックステンプレート作成
            await create_elasticsearch_templates(es_service)
        else:
            print("❌ Elasticsearch connection failed")
            
    except Exception as e:
        print(f"❌ Failed to initialize Elasticsearch: {str(e)}")

async def create_elasticsearch_templates(es_service):
    """Elasticsearchインデックステンプレートを作成"""
    print("📋 Creating Elasticsearch templates...")
    
    try:
        # ログ用テンプレート
        log_template = {
            "index_patterns": [f"{es_service.config.index_prefix}_logs_*"],
            "mappings": {
                "properties": {
                    "task_id": {"type": "keyword"},
                    "level": {"type": "keyword"},
                    "message": {"type": "text"},
                    "timestamp": {"type": "date"},
                    "spider_name": {"type": "keyword"},
                    "project_name": {"type": "keyword"}
                }
            }
        }
        
        await es_service.client.indices.put_template(
            name=f"{es_service.config.index_prefix}_logs",
            body=log_template
        )
        
        # 結果用テンプレート
        results_template = {
            "index_patterns": [f"{es_service.config.index_prefix}_results_*"],
            "mappings": {
                "properties": {
                    "task_id": {"type": "keyword"},
                    "url": {"type": "keyword"},
                    "data": {"type": "object"},
                    "created_at": {"type": "date"},
                    "spider_name": {"type": "keyword"},
                    "project_name": {"type": "keyword"}
                }
            }
        }
        
        await es_service.client.indices.put_template(
            name=f"{es_service.config.index_prefix}_results",
            body=results_template
        )
        
        print("✅ Elasticsearch templates created")
        
    except Exception as e:
        print(f"❌ Failed to create Elasticsearch templates: {str(e)}")

async def init_redis():
    """Redisを初期化"""
    print("🔴 Initializing Redis...")
    
    try:
        redis_service = await get_database_service(DatabaseType.REDIS)
        if not redis_service:
            print("ℹ️  Redis not configured, skipping...")
            return
        
        # 接続テスト
        if await redis_service.health_check():
            print("✅ Redis connection successful")
            
            # 初期キー設定
            await redis_service.set_value("scrapy_ui:initialized", True)
            print("✅ Redis initialized")
        else:
            print("❌ Redis connection failed")
            
    except Exception as e:
        print(f"❌ Failed to initialize Redis: {str(e)}")

async def check_database_config():
    """データベース設定をチェック"""
    print("🔍 Checking database configuration...")
    
    try:
        config = get_database_config()
        print(f"📊 Database type: {config.type.value}")
        
        if config.type == DatabaseType.SQLITE:
            print(f"📁 Database file: {config.database}")
        elif config.type in [DatabaseType.MYSQL, DatabaseType.POSTGRESQL]:
            print(f"🌐 Host: {config.host}:{config.port}")
            print(f"🗄️  Database: {config.database}")
            print(f"👤 User: {config.username}")
        
        print("✅ Database configuration valid")
        
    except Exception as e:
        print(f"❌ Invalid database configuration: {str(e)}")
        raise

async def main():
    """メイン処理"""
    print("🚀 ScrapyUI Database Initialization")
    print("=" * 50)
    
    try:
        # 設定チェック
        await check_database_config()
        
        # リレーショナルデータベース初期化
        await init_relational_database()
        
        # NoSQLデータベース初期化
        await init_mongodb()
        await init_elasticsearch()
        await init_redis()
        
        print("\n" + "=" * 50)
        print("🎉 Database initialization completed successfully!")
        print("\n📋 Next steps:")
        print("1. Start the ScrapyUI server: uvicorn app.main:app --reload")
        print("2. Access the web interface: http://localhost:8000")
        print("3. Login with demo credentials: demo@example.com / demo12345")
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
