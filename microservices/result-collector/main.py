#!/usr/bin/env python3
"""
ScrapyUI Result Collector Service
Handles result file processing and data storage
"""

import asyncio
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles
import aioredis
import asyncpg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ScrapyUI Result Collector", version="1.0.0")

class ResultMessage(BaseModel):
    task_id: str
    output_file: str
    items_count: int

class ResultItem(BaseModel):
    id: str
    task_id: str
    data: Dict
    hash: str
    created_at: datetime

class ResultCollector:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.db_pool: Optional[asyncpg.Pool] = None
        self.running = False
        self.batch_size = 100  # Batch insert size
        
    async def initialize(self):
        """Initialize connections"""
        try:
            self.redis = aioredis.from_url(
                "redis://localhost:6379",
                encoding="utf-8",
                decode_responses=True
            )
            
            self.db_pool = await asyncpg.create_pool(
                "postgresql://user:password@localhost:5432/scrapyui",
                min_size=2,
                max_size=10
            )
            
            logger.info("🔗 Result Collector initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize: {e}")
            raise
    
    def calculate_hash(self, data: Dict) -> str:
        """Calculate hash for duplicate detection"""
        # Create a consistent string representation
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()
    
    async def process_jsonl_file(self, file_path: str, task_id: str) -> Dict:
        """Process JSONL file and extract items"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.warning(f"⚠️ File not found: {file_path}")
                return {"processed": 0, "duplicates": 0, "errors": 0}
            
            items = []
            duplicates = 0
            errors = 0
            seen_hashes = set()
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                async for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        
                        # Calculate hash for duplicate detection
                        item_hash = self.calculate_hash(data)
                        
                        if item_hash in seen_hashes:
                            duplicates += 1
                            continue
                        
                        seen_hashes.add(item_hash)
                        
                        # Create result item
                        item = ResultItem(
                            id=f"{task_id}_{len(items)}",
                            task_id=task_id,
                            data=data,
                            hash=item_hash,
                            created_at=datetime.now()
                        )
                        
                        items.append(item)
                        
                        # Batch insert when reaching batch size
                        if len(items) >= self.batch_size:
                            await self.bulk_insert_items(items)
                            items = []
                        
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ Invalid JSON line in {file_path}: {e}")
                        errors += 1
                    except Exception as e:
                        logger.error(f"❌ Error processing line: {e}")
                        errors += 1
            
            # Insert remaining items
            if items:
                await self.bulk_insert_items(items)
            
            total_processed = len(seen_hashes)
            
            logger.info(f"✅ Processed {file_path}: {total_processed} items, {duplicates} duplicates, {errors} errors")
            
            return {
                "processed": total_processed,
                "duplicates": duplicates,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to process file {file_path}: {e}")
            raise
    
    async def bulk_insert_items(self, items: List[ResultItem]):
        """Bulk insert items into database"""
        try:
            if not items:
                return
            
            async with self.db_pool.acquire() as conn:
                # Prepare data for bulk insert
                values = [
                    (item.id, item.task_id, json.dumps(item.data), 
                     item.hash, item.created_at)
                    for item in items
                ]
                
                # Use COPY for high performance bulk insert
                await conn.copy_records_to_table(
                    'results',
                    records=values,
                    columns=['id', 'task_id', 'data', 'hash', 'created_at']
                )
                
                logger.debug(f"📦 Bulk inserted {len(items)} items")
                
        except Exception as e:
            logger.error(f"❌ Bulk insert failed: {e}")
            # Fallback to individual inserts
            await self.fallback_insert_items(items)
    
    async def fallback_insert_items(self, items: List[ResultItem]):
        """Fallback individual insert for items"""
        try:
            async with self.db_pool.acquire() as conn:
                for item in items:
                    try:
                        await conn.execute("""
                            INSERT INTO results (id, task_id, data, hash, created_at)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (hash) DO NOTHING
                        """, item.id, item.task_id, json.dumps(item.data), 
                            item.hash, item.created_at)
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to insert item {item.id}: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Fallback insert failed: {e}")
    
    async def cleanup_duplicates(self, task_id: str) -> int:
        """Remove duplicate items for a task"""
        try:
            async with self.db_pool.acquire() as conn:
                # Find and remove duplicates, keeping the first occurrence
                result = await conn.execute("""
                    DELETE FROM results 
                    WHERE id IN (
                        SELECT id FROM (
                            SELECT id, ROW_NUMBER() OVER (
                                PARTITION BY hash ORDER BY created_at
                            ) as rn
                            FROM results 
                            WHERE task_id = $1
                        ) t 
                        WHERE t.rn > 1
                    )
                """, task_id)
                
                deleted_count = int(result.split()[-1])
                logger.info(f"🧹 Removed {deleted_count} duplicates for task {task_id}")
                return deleted_count
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup duplicates: {e}")
            return 0
    
    async def update_task_statistics(self, task_id: str, stats: Dict):
        """Update task statistics in Redis"""
        try:
            await self.redis.hset(f"task:{task_id}", mapping={
                "items_processed": stats["processed"],
                "duplicates_found": stats["duplicates"],
                "processing_errors": stats["errors"],
                "processed_at": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to update task statistics: {e}")
    
    async def result_processor(self):
        """Process result files from queue"""
        logger.info("🔄 Result processor started")
        
        while self.running:
            try:
                # Block and wait for result processing tasks
                result_data = await self.redis.brpop("queue:result_processing", timeout=10)
                
                if result_data:
                    _, result_json = result_data
                    result_msg = ResultMessage.parse_raw(result_json)
                    
                    logger.info(f"📥 Processing results for task: {result_msg.task_id}")
                    
                    # Process the file
                    stats = await self.process_jsonl_file(
                        result_msg.output_file, 
                        result_msg.task_id
                    )
                    
                    # Cleanup duplicates
                    duplicates_removed = await self.cleanup_duplicates(result_msg.task_id)
                    stats["duplicates_removed"] = duplicates_removed
                    
                    # Update task statistics
                    await self.update_task_statistics(result_msg.task_id, stats)
                    
                    # Publish completion event
                    await self.redis.publish("events:results_processed", json.dumps({
                        "task_id": result_msg.task_id,
                        "statistics": stats,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    logger.info(f"✅ Results processed for task: {result_msg.task_id}")
                
            except Exception as e:
                logger.error(f"❌ Result processor error: {e}")
                await asyncio.sleep(5)
    
    async def start(self):
        """Start result collector service"""
        self.running = True
        await self.initialize()
        
        # Start result processor
        asyncio.create_task(self.result_processor())
        
        logger.info("🚀 Result Collector started")
    
    async def stop(self):
        """Stop result collector service"""
        self.running = False
        
        if self.redis:
            await self.redis.close()
        if self.db_pool:
            await self.db_pool.close()
            
        logger.info("🛑 Result Collector stopped")

# Global collector instance
collector = ResultCollector()

# API Endpoints
@app.on_event("startup")
async def startup_event():
    await collector.start()

@app.on_event("shutdown")
async def shutdown_event():
    await collector.stop()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "result-collector",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/process/{task_id}")
async def process_task_results(task_id: str, file_path: str):
    """Manually trigger result processing for a task"""
    try:
        stats = await collector.process_jsonl_file(file_path, task_id)
        duplicates_removed = await collector.cleanup_duplicates(task_id)
        stats["duplicates_removed"] = duplicates_removed
        
        await collector.update_task_statistics(task_id, stats)
        
        return {
            "message": "Results processed",
            "task_id": task_id,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to process results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results/{task_id}")
async def get_task_results(task_id: str, limit: int = 100, offset: int = 0):
    """Get results for a specific task"""
    try:
        async with collector.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, data, hash, created_at
                FROM results 
                WHERE task_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """, task_id, limit, offset)
            
            results = []
            for row in rows:
                results.append({
                    "id": row["id"],
                    "data": json.loads(row["data"]),
                    "hash": row["hash"],
                    "created_at": row["created_at"].isoformat()
                })
            
            # Get total count
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM results WHERE task_id = $1", 
                task_id
            )
            
            return {
                "results": results,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
    except Exception as e:
        logger.error(f"❌ Failed to get results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Get result collector metrics"""
    try:
        queue_size = await collector.redis.llen("queue:result_processing")
        
        # Get total results count
        async with collector.db_pool.acquire() as conn:
            total_results = await conn.fetchval("SELECT COUNT(*) FROM results")
        
        return {
            "queue_size": queue_size,
            "total_results": total_results,
            "batch_size": collector.batch_size,
            "service_status": "running" if collector.running else "stopped"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
