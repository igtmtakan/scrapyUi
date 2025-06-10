#!/usr/bin/env python3
"""
ScrapyUI Spider Manager Service
Handles spider execution and process management
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Callable

import aioredis
import psutil
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Watchdog service import
from watchdog_service import WatchdogSpiderService, WatchdogTask

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ScrapyUI Spider Manager", version="1.0.0")

class TaskMessage(BaseModel):
    task_id: str
    schedule_id: str
    project_id: str
    spider_id: str
    settings: Dict
    priority: int = 5
    created_at: datetime

class SpiderProcess(BaseModel):
    task_id: str
    pid: int
    project_path: str
    spider_name: str
    output_file: str
    started_at: datetime
    status: str = "RUNNING"

class SpiderManager:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.running = False
        self.processes: Dict[str, SpiderProcess] = {}
        self.max_concurrent = 3  # Maximum concurrent spiders
        self.base_projects_path = Path("/app/scrapy_projects")
        self.watchdog_service: Optional[WatchdogSpiderService] = None
        
    async def initialize(self):
        """Initialize connections"""
        try:
            self.redis = aioredis.from_url(
                "redis://localhost:6379",
                encoding="utf-8",
                decode_responses=True
            )
            
            # Ensure projects directory exists
            self.base_projects_path.mkdir(parents=True, exist_ok=True)
            
            logger.info("🔗 Spider Manager initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize: {e}")
            raise
    
    async def get_project_info(self, project_id: str, spider_id: str) -> Dict:
        """Get project and spider information"""
        try:
            # In real implementation, this would query the database
            # For now, return mock data
            return {
                "project_name": f"project_{project_id[:8]}",
                "spider_name": f"spider_{spider_id[:8]}",
                "project_path": self.base_projects_path / f"project_{project_id[:8]}"
            }
        except Exception as e:
            logger.error(f"❌ Failed to get project info: {e}")
            raise
    
    async def execute_spider(self, task: TaskMessage) -> str:
        """Execute a spider process"""
        try:
            # Check concurrent limit
            running_count = len([p for p in self.processes.values() if p.status == "RUNNING"])
            if running_count >= self.max_concurrent:
                logger.warning(f"⚠️ Max concurrent limit reached ({self.max_concurrent})")
                # Re-queue the task
                await self.redis.lpush("queue:spider_tasks", task.json())
                return None
            
            # Get project information
            project_info = await self.get_project_info(task.project_id, task.spider_id)
            project_path = project_info["project_path"]
            spider_name = project_info["spider_name"]
            
            # Prepare output file
            output_file = project_path / f"results_{task.task_id}.jsonl"
            
            # Build command
            cmd = [
                "python3", "-m", "scrapy", "crawl", spider_name,
                "-o", str(output_file),
                "-s", "FEED_FORMAT=jsonlines",
                "-s", "LOG_LEVEL=INFO"
            ]
            
            # Add custom settings
            for key, value in task.settings.items():
                cmd.extend(["-s", f"{key}={value}"])
            
            # Start process
            process = subprocess.Popen(
                cmd,
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Store process info
            spider_process = SpiderProcess(
                task_id=task.task_id,
                pid=process.pid,
                project_path=str(project_path),
                spider_name=spider_name,
                output_file=str(output_file),
                started_at=datetime.now()
            )
            
            self.processes[task.task_id] = spider_process
            
            # Update task status in Redis
            await self.redis.hset(f"task:{task.task_id}", mapping={
                "status": "RUNNING",
                "pid": process.pid,
                "started_at": datetime.now().isoformat()
            })
            
            # Start monitoring in background
            asyncio.create_task(self.monitor_process(task.task_id, process))
            
            logger.info(f"🚀 Started spider {spider_name} (PID: {process.pid}, Task: {task.task_id})")
            
            # Publish start event
            await self.redis.publish("events:spider_started", json.dumps({
                "task_id": task.task_id,
                "pid": process.pid,
                "spider_name": spider_name,
                "timestamp": datetime.now().isoformat()
            }))
            
            return task.task_id
            
        except Exception as e:
            logger.error(f"❌ Failed to execute spider: {e}")
            # Update task status to failed
            await self.redis.hset(f"task:{task.task_id}", mapping={
                "status": "FAILED",
                "error": str(e),
                "finished_at": datetime.now().isoformat()
            })
            raise
    
    async def monitor_process(self, task_id: str, process: subprocess.Popen):
        """Monitor spider process execution"""
        try:
            spider_process = self.processes[task_id]
            
            # Wait for process completion
            stdout, stderr = await asyncio.get_event_loop().run_in_executor(
                None, process.communicate
            )
            
            return_code = process.returncode
            finished_at = datetime.now()
            
            # Update process status
            spider_process.status = "FINISHED" if return_code == 0 else "FAILED"
            
            # Get output file size and line count
            output_file = Path(spider_process.output_file)
            items_count = 0
            file_size = 0
            
            if output_file.exists():
                file_size = output_file.stat().st_size
                with open(output_file, 'r') as f:
                    items_count = sum(1 for line in f if line.strip())
            
            # Update task status in Redis
            await self.redis.hset(f"task:{task_id}", mapping={
                "status": spider_process.status,
                "return_code": return_code,
                "items_count": items_count,
                "file_size": file_size,
                "finished_at": finished_at.isoformat(),
                "stdout": stdout.decode('utf-8', errors='ignore')[:1000],  # Limit size
                "stderr": stderr.decode('utf-8', errors='ignore')[:1000]
            })
            
            # Publish completion event
            await self.redis.publish("events:spider_finished", json.dumps({
                "task_id": task_id,
                "status": spider_process.status,
                "return_code": return_code,
                "items_count": items_count,
                "duration": (finished_at - spider_process.started_at).total_seconds(),
                "timestamp": finished_at.isoformat()
            }))
            
            # Queue for result processing
            await self.redis.lpush("queue:result_processing", json.dumps({
                "task_id": task_id,
                "output_file": spider_process.output_file,
                "items_count": items_count
            }))
            
            logger.info(f"✅ Spider completed: {task_id} ({spider_process.status}, {items_count} items)")
            
        except Exception as e:
            logger.error(f"❌ Error monitoring process {task_id}: {e}")
            
        finally:
            # Clean up process record
            if task_id in self.processes:
                del self.processes[task_id]
    
    async def kill_spider(self, task_id: str) -> bool:
        """Kill a running spider process"""
        try:
            if task_id not in self.processes:
                return False
            
            spider_process = self.processes[task_id]
            
            # Kill process group
            try:
                os.killpg(spider_process.pid, signal.SIGTERM)
                logger.info(f"🛑 Killed spider process: {task_id} (PID: {spider_process.pid})")
                
                # Update status
                spider_process.status = "KILLED"
                await self.redis.hset(f"task:{task_id}", mapping={
                    "status": "KILLED",
                    "finished_at": datetime.now().isoformat()
                })
                
                return True
                
            except ProcessLookupError:
                logger.warning(f"⚠️ Process {spider_process.pid} already terminated")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to kill spider {task_id}: {e}")
            return False
    
    async def task_consumer(self):
        """Consume tasks from queue - pyspider inspired"""
        logger.info("🔄 Task consumer started")
        
        while self.running:
            try:
                # Block and wait for tasks
                task_data = await self.redis.brpop("queue:spider_tasks", timeout=10)
                
                if task_data:
                    _, task_json = task_data
                    task = TaskMessage.parse_raw(task_json)
                    
                    logger.info(f"📥 Received task: {task.task_id}")
                    
                    # Execute spider
                    await self.execute_spider(task)
                
            except Exception as e:
                logger.error(f"❌ Task consumer error: {e}")
                await asyncio.sleep(5)
    
    async def cleanup_orphaned_processes(self):
        """Clean up orphaned spider processes"""
        try:
            for task_id, spider_process in list(self.processes.items()):
                try:
                    # Check if process still exists
                    process = psutil.Process(spider_process.pid)
                    if not process.is_running():
                        logger.info(f"🧹 Cleaning up orphaned process: {task_id}")
                        del self.processes[task_id]
                        
                except psutil.NoSuchProcess:
                    logger.info(f"🧹 Cleaning up non-existent process: {task_id}")
                    del self.processes[task_id]
                    
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")
    
    async def start(self):
        """Start spider manager service"""
        self.running = True
        await self.initialize()

        # Initialize watchdog service
        self.watchdog_service = WatchdogSpiderService()
        await self.watchdog_service.initialize()

        # Start task consumer
        asyncio.create_task(self.task_consumer())

        # Start periodic cleanup
        async def cleanup_loop():
            while self.running:
                await self.cleanup_orphaned_processes()
                await asyncio.sleep(60)  # Every minute

        asyncio.create_task(cleanup_loop())

        logger.info("🚀 Spider Manager started")
    
    async def stop(self):
        """Stop spider manager service"""
        self.running = False
        
        # Kill all running processes
        for task_id in list(self.processes.keys()):
            await self.kill_spider(task_id)
        
        if self.redis:
            await self.redis.close()
            
        logger.info("🛑 Spider Manager stopped")

# Global manager instance
manager = SpiderManager()

# API Endpoints
@app.on_event("startup")
async def startup_event():
    await manager.start()

@app.on_event("shutdown")
async def shutdown_event():
    await manager.stop()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "spider-manager",
        "timestamp": datetime.now().isoformat(),
        "running_processes": len(manager.processes)
    }

@app.get("/processes")
async def get_processes():
    """Get all running processes"""
    return {
        "processes": [process.dict() for process in manager.processes.values()],
        "count": len(manager.processes)
    }

@app.post("/processes/{task_id}/kill")
async def kill_process(task_id: str):
    """Kill a specific process"""
    success = await manager.kill_spider(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Process not found")
    
    return {"message": "Process killed", "task_id": task_id}

@app.post("/execute-watchdog")
async def execute_spider_with_watchdog(request: dict):
    """Execute spider with watchdog monitoring (Celery replacement)"""
    try:
        # Create watchdog task
        task = WatchdogTask(
            task_id=request["task_id"],
            project_id=request["project_id"],
            spider_id=request["spider_id"],
            project_path=request["project_path"],
            spider_name=request["spider_name"],
            output_file=request["output_file"],
            settings=request.get("settings", {}),
            created_at=datetime.now().isoformat()
        )

        # Execute with watchdog
        result = await manager.watchdog_service.execute_spider_with_watchdog(task)

        return {
            "message": "Spider executed with watchdog",
            "task_id": task.task_id,
            "result": result
        }

    except Exception as e:
        logger.error(f"❌ Watchdog execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/watchdog/active")
async def get_active_watchdog_tasks():
    """Get active watchdog tasks"""
    try:
        if manager.watchdog_service:
            active_tasks = await manager.watchdog_service.get_active_tasks()
            return {
                "active_tasks": active_tasks,
                "count": len(active_tasks)
            }
        else:
            return {"active_tasks": [], "count": 0}

    except Exception as e:
        logger.error(f"❌ Failed to get active watchdog tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/watchdog/{task_id}/stop")
async def stop_watchdog_task(task_id: str):
    """Stop watchdog task"""
    try:
        if manager.watchdog_service:
            success = await manager.watchdog_service.stop_task(task_id)
            if success:
                return {"message": "Watchdog task stopped", "task_id": task_id}
            else:
                raise HTTPException(status_code=404, detail="Task not found")
        else:
            raise HTTPException(status_code=503, detail="Watchdog service not available")

    except Exception as e:
        logger.error(f"❌ Failed to stop watchdog task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Get spider manager metrics"""
    try:
        queue_size = await manager.redis.llen("queue:spider_tasks")

        # Watchdog metrics
        watchdog_active = 0
        if manager.watchdog_service:
            active_tasks = await manager.watchdog_service.get_active_tasks()
            watchdog_active = len(active_tasks)

        return {
            "running_processes": len(manager.processes),
            "max_concurrent": manager.max_concurrent,
            "queue_size": queue_size,
            "watchdog_active": watchdog_active,
            "service_status": "running" if manager.running else "stopped"
        }

    except Exception as e:
        logger.error(f"❌ Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
