#!/usr/bin/env python3
"""
ScrapyUI Scheduler Service
pyspider inspired microservice architecture
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import redis.asyncio as aioredis
import asyncpg
from croniter import croniter
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ScrapyUI Scheduler Service", version="1.0.0")

# Models
class ScheduleModel(BaseModel):
    id: str
    name: str
    cron_expression: str
    project_id: str
    spider_id: str
    is_active: bool
    settings: Dict = {}
    created_at: datetime
    updated_at: datetime

class TaskMessage(BaseModel):
    task_id: str
    schedule_id: str
    project_id: str
    spider_id: str
    settings: Dict
    priority: int = 5
    created_at: datetime

class SchedulerService:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.db_pool: Optional[asyncpg.Pool] = None
        self.running = False
        self.schedules: Dict[str, ScheduleModel] = {}
        
    async def initialize(self):
        """Initialize connections"""
        try:
            # Redis connection
            self.redis = aioredis.from_url(
                "redis://localhost:6379",
                encoding="utf-8",
                decode_responses=True
            )
            
            # Database connection
            self.db_pool = await asyncpg.create_pool(
                "postgresql://user:password@localhost:5432/scrapyui",
                min_size=2,
                max_size=10
            )
            
            logger.info("🔗 Scheduler service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize: {e}")
            raise
    
    async def load_schedules(self) -> List[ScheduleModel]:
        """Load active schedules from database"""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, name, cron_expression, project_id, spider_id, 
                           is_active, settings, created_at, updated_at
                    FROM schedules 
                    WHERE is_active = true
                """)
                
                schedules = []
                for row in rows:
                    schedule = ScheduleModel(
                        id=row['id'],
                        name=row['name'],
                        cron_expression=row['cron_expression'],
                        project_id=row['project_id'],
                        spider_id=row['spider_id'],
                        is_active=row['is_active'],
                        settings=row['settings'] or {},
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    schedules.append(schedule)
                    self.schedules[schedule.id] = schedule
                
                logger.info(f"📋 Loaded {len(schedules)} active schedules")
                return schedules
                
        except Exception as e:
            logger.error(f"❌ Failed to load schedules: {e}")
            return []
    
    async def should_execute(self, schedule: ScheduleModel) -> bool:
        """Check if schedule should execute now"""
        try:
            now = datetime.now()
            cron = croniter(schedule.cron_expression, now)
            
            # Get last execution time
            last_run_key = f"schedule:last_run:{schedule.id}"
            last_run_str = await self.redis.get(last_run_key)
            
            if last_run_str:
                last_run = datetime.fromisoformat(last_run_str)
                next_run = cron.get_next(datetime)
                
                # Check if it's time to run
                if now >= next_run and (now - last_run).total_seconds() >= 60:
                    return True
            else:
                # First time execution
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking execution time for {schedule.id}: {e}")
            return False
    
    async def create_task(self, schedule: ScheduleModel) -> str:
        """Create and queue a new task"""
        try:
            task_id = str(uuid.uuid4())
            
            # Create task message
            task_message = TaskMessage(
                task_id=task_id,
                schedule_id=schedule.id,
                project_id=schedule.project_id,
                spider_id=schedule.spider_id,
                settings=schedule.settings,
                created_at=datetime.now()
            )
            
            # Queue task to spider manager
            await self.redis.lpush(
                "queue:spider_tasks",
                task_message.json()
            )
            
            # Update last run time
            last_run_key = f"schedule:last_run:{schedule.id}"
            await self.redis.set(last_run_key, datetime.now().isoformat())
            
            # Store task info
            task_key = f"task:{task_id}"
            await self.redis.hset(task_key, mapping={
                "id": task_id,
                "schedule_id": schedule.id,
                "status": "QUEUED",
                "created_at": datetime.now().isoformat()
            })
            
            logger.info(f"📤 Task {task_id} queued for schedule {schedule.name}")
            return task_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create task for {schedule.id}: {e}")
            raise
    
    async def scheduler_loop(self):
        """Main scheduler loop - pyspider inspired"""
        logger.info("🔄 Scheduler loop started")
        
        while self.running:
            try:
                # Reload schedules periodically
                await self.load_schedules()
                
                executed_count = 0
                for schedule in self.schedules.values():
                    if await self.should_execute(schedule):
                        try:
                            task_id = await self.create_task(schedule)
                            executed_count += 1
                            
                            # Publish execution event
                            await self.redis.publish(
                                "events:schedule_executed",
                                json.dumps({
                                    "schedule_id": schedule.id,
                                    "task_id": task_id,
                                    "timestamp": datetime.now().isoformat()
                                })
                            )
                            
                        except Exception as e:
                            logger.error(f"❌ Failed to execute schedule {schedule.id}: {e}")
                
                if executed_count > 0:
                    logger.info(f"🚀 Executed {executed_count} schedules")
                
                # Sleep for next iteration
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"❌ Scheduler loop error: {e}")
                await asyncio.sleep(30)  # Longer sleep on error
    
    async def start(self):
        """Start scheduler service"""
        self.running = True
        await self.initialize()
        await self.load_schedules()
        
        # Start scheduler loop in background
        asyncio.create_task(self.scheduler_loop())
        logger.info("🚀 Scheduler service started")
    
    async def stop(self):
        """Stop scheduler service"""
        self.running = False
        if self.redis:
            await self.redis.close()
        if self.db_pool:
            await self.db_pool.close()
        logger.info("🛑 Scheduler service stopped")

# Global scheduler instance
scheduler = SchedulerService()

# API Endpoints
@app.on_event("startup")
async def startup_event():
    await scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    await scheduler.stop()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "scheduler",
        "timestamp": datetime.now().isoformat(),
        "schedules_loaded": len(scheduler.schedules)
    }

@app.get("/schedules")
async def get_schedules():
    """Get all loaded schedules"""
    return {
        "schedules": [schedule.dict() for schedule in scheduler.schedules.values()],
        "count": len(scheduler.schedules)
    }

@app.post("/schedules/{schedule_id}/execute")
async def execute_schedule(schedule_id: str):
    """Manually execute a schedule"""
    if schedule_id not in scheduler.schedules:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = scheduler.schedules[schedule_id]
    task_id = await scheduler.create_task(schedule)
    
    return {
        "message": "Schedule executed",
        "task_id": task_id,
        "schedule_id": schedule_id
    }

@app.get("/metrics")
async def get_metrics():
    """Get scheduler metrics"""
    try:
        # Get queue sizes
        queue_size = await scheduler.redis.llen("queue:spider_tasks")
        
        # Get recent executions
        recent_executions = 0
        for schedule_id in scheduler.schedules.keys():
            last_run_key = f"schedule:last_run:{schedule_id}"
            last_run_str = await scheduler.redis.get(last_run_key)
            if last_run_str:
                last_run = datetime.fromisoformat(last_run_str)
                if (datetime.now() - last_run).total_seconds() < 3600:  # Last hour
                    recent_executions += 1
        
        return {
            "active_schedules": len(scheduler.schedules),
            "queue_size": queue_size,
            "recent_executions": recent_executions,
            "service_status": "running" if scheduler.running else "stopped"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
