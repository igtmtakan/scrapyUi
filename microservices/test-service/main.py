#!/usr/bin/env python3
"""
Simple Test Service for ScrapyUI Microservices
Basic functionality test without complex dependencies
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ScrapyUI Test Service", version="1.0.0")

# Simple in-memory storage for testing
schedules_db = {}
tasks_db = {}
results_db = {}

# Models
class Schedule(BaseModel):
    id: str
    name: str
    cron_expression: str
    project_id: str
    spider_id: str
    is_active: bool = True
    created_at: str

class Task(BaseModel):
    id: str
    schedule_id: str
    status: str = "PENDING"
    created_at: str
    started_at: str = None
    finished_at: str = None

class Result(BaseModel):
    id: str
    task_id: str
    data: Dict
    created_at: str

# Test Service Class
class TestService:
    def __init__(self):
        self.running = False
        self.stats = {
            "schedules": 0,
            "tasks": 0,
            "results": 0,
            "uptime": 0
        }
        self.start_time = time.time()
    
    def get_uptime(self) -> float:
        return time.time() - self.start_time
    
    def update_stats(self):
        self.stats.update({
            "schedules": len(schedules_db),
            "tasks": len(tasks_db),
            "results": len(results_db),
            "uptime": self.get_uptime()
        })

# Global service instance
service = TestService()

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    service.update_stats()
    return {
        "status": "healthy",
        "service": "test-service",
        "timestamp": datetime.now().isoformat(),
        "uptime": service.get_uptime(),
        "stats": service.stats
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ScrapyUI Test Service",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/health",
            "/schedules",
            "/tasks", 
            "/results",
            "/metrics"
        ]
    }

# Schedule endpoints
@app.get("/schedules")
async def get_schedules():
    """Get all schedules"""
    return {
        "schedules": list(schedules_db.values()),
        "count": len(schedules_db)
    }

@app.post("/schedules")
async def create_schedule(schedule: Schedule):
    """Create a new schedule"""
    schedules_db[schedule.id] = schedule.model_dump()
    logger.info(f"Created schedule: {schedule.name}")
    return {"message": "Schedule created", "id": schedule.id}

@app.get("/schedules/{schedule_id}")
async def get_schedule(schedule_id: str):
    """Get specific schedule"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedules_db[schedule_id]

@app.post("/schedules/{schedule_id}/execute")
async def execute_schedule(schedule_id: str):
    """Execute a schedule (create task)"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Create task
    task_id = f"task_{int(time.time())}"
    task = Task(
        id=task_id,
        schedule_id=schedule_id,
        status="RUNNING",
        created_at=datetime.now().isoformat(),
        started_at=datetime.now().isoformat()
    )
    
    tasks_db[task_id] = task.model_dump()
    logger.info(f"Executed schedule {schedule_id}, created task {task_id}")
    
    return {
        "message": "Schedule executed",
        "task_id": task_id,
        "schedule_id": schedule_id
    }

# Task endpoints
@app.get("/tasks")
async def get_tasks():
    """Get all tasks"""
    return {
        "tasks": list(tasks_db.values()),
        "count": len(tasks_db)
    }

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get specific task"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_db[task_id]

@app.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str):
    """Mark task as completed"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    tasks_db[task_id]["status"] = "COMPLETED"
    tasks_db[task_id]["finished_at"] = datetime.now().isoformat()
    
    # Create sample result
    result_id = f"result_{int(time.time())}"
    result = Result(
        id=result_id,
        task_id=task_id,
        data={"items": 10, "pages": 5, "duration": 30.5},
        created_at=datetime.now().isoformat()
    )
    
    results_db[result_id] = result.model_dump()
    logger.info(f"Completed task {task_id}, created result {result_id}")
    
    return {
        "message": "Task completed",
        "task_id": task_id,
        "result_id": result_id
    }

# Result endpoints
@app.get("/results")
async def get_results():
    """Get all results"""
    return {
        "results": list(results_db.values()),
        "count": len(results_db)
    }

@app.get("/results/{result_id}")
async def get_result(result_id: str):
    """Get specific result"""
    if result_id not in results_db:
        raise HTTPException(status_code=404, detail="Result not found")
    return results_db[result_id]

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    service.update_stats()
    
    # Calculate status distribution
    task_statuses = {}
    for task in tasks_db.values():
        status = task["status"]
        task_statuses[status] = task_statuses.get(status, 0) + 1
    
    return {
        "service": "test-service",
        "uptime": service.get_uptime(),
        "stats": service.stats,
        "task_statuses": task_statuses,
        "memory_usage": {
            "schedules": len(schedules_db),
            "tasks": len(tasks_db),
            "results": len(results_db)
        },
        "timestamp": datetime.now().isoformat()
    }

# Test endpoints
@app.post("/test/populate")
async def populate_test_data():
    """Populate with test data"""
    # Create test schedules
    test_schedules = [
        {
            "id": "schedule_1",
            "name": "Amazon Ranking Spider",
            "cron_expression": "*/10 * * * *",
            "project_id": "project_1",
            "spider_id": "amazon_spider",
            "is_active": True,
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "schedule_2", 
            "name": "News Crawler",
            "cron_expression": "*/5 * * * *",
            "project_id": "project_2",
            "spider_id": "news_spider",
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
    ]
    
    for schedule_data in test_schedules:
        schedules_db[schedule_data["id"]] = schedule_data
    
    logger.info(f"Populated {len(test_schedules)} test schedules")
    
    return {
        "message": "Test data populated",
        "schedules_created": len(test_schedules)
    }

@app.delete("/test/clear")
async def clear_test_data():
    """Clear all test data"""
    schedules_db.clear()
    tasks_db.clear()
    results_db.clear()
    
    logger.info("Cleared all test data")
    
    return {
        "message": "Test data cleared",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    logger.info("🚀 Starting ScrapyUI Test Service...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info"
    )
