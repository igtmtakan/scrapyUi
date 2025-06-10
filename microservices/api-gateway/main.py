#!/usr/bin/env python3
"""
ScrapyUI API Gateway
Central entry point for all API requests
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

import aiohttp
import aioredis
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ScrapyUI API Gateway", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

class APIGateway:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.services = {
            "scheduler": "http://localhost:8001",
            "spider-manager": "http://localhost:8002", 
            "result-collector": "http://localhost:8003",
            "webui": "http://localhost:8004"
        }
        self.rate_limits = {
            "default": {"requests": 100, "window": 60},  # 100 req/min
            "execute": {"requests": 10, "window": 60},   # 10 executions/min
        }
        
    async def initialize(self):
        """Initialize connections"""
        try:
            self.redis = aioredis.from_url(
                "redis://localhost:6379",
                encoding="utf-8", 
                decode_responses=True
            )
            logger.info("🔗 API Gateway initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize: {e}")
            raise
    
    async def check_rate_limit(self, client_ip: str, endpoint_type: str = "default") -> bool:
        """Check rate limiting"""
        try:
            limit_config = self.rate_limits.get(endpoint_type, self.rate_limits["default"])
            key = f"rate_limit:{client_ip}:{endpoint_type}"
            
            current = await self.redis.get(key)
            if current is None:
                await self.redis.setex(key, limit_config["window"], 1)
                return True
            
            if int(current) >= limit_config["requests"]:
                return False
            
            await self.redis.incr(key)
            return True
            
        except Exception as e:
            logger.error(f"❌ Rate limit check failed: {e}")
            return True  # Allow on error
    
    async def authenticate_request(self, credentials: HTTPAuthorizationCredentials) -> Dict:
        """Authenticate API request"""
        try:
            token = credentials.credentials
            
            # Check token in Redis (in real implementation, validate JWT)
            user_data = await self.redis.get(f"token:{token}")
            if not user_data:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            return json.loads(user_data)
            
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    async def proxy_request(self, service: str, path: str, method: str, 
                          headers: Dict, params: Dict = None, json_data: Dict = None) -> Dict:
        """Proxy request to microservice"""
        try:
            service_url = self.services.get(service)
            if not service_url:
                raise HTTPException(status_code=404, detail=f"Service {service} not found")
            
            url = f"{service_url}{path}"
            
            # Remove authorization header for internal requests
            internal_headers = {k: v for k, v in headers.items() 
                              if k.lower() != "authorization"}
            
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=internal_headers,
                    params=params,
                    json=json_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.content_type == "application/json":
                        result = await response.json()
                    else:
                        result = {"data": await response.text()}
                    
                    if response.status >= 400:
                        raise HTTPException(status_code=response.status, detail=result)
                    
                    return result
                    
        except aiohttp.ClientError as e:
            logger.error(f"❌ Service {service} unavailable: {e}")
            raise HTTPException(status_code=503, detail=f"Service {service} unavailable")
        except Exception as e:
            logger.error(f"❌ Proxy request failed: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def log_request(self, request: Request, response_time: float, status_code: int):
        """Log API request"""
        try:
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "method": request.method,
                "path": str(request.url.path),
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent", ""),
                "response_time": response_time,
                "status_code": status_code
            }
            
            # Store in Redis for analytics
            await self.redis.lpush("logs:api_requests", json.dumps(log_data))
            await self.redis.ltrim("logs:api_requests", 0, 9999)  # Keep last 10k logs
            
        except Exception as e:
            logger.error(f"❌ Failed to log request: {e}")

# Global gateway instance
gateway = APIGateway()

# Middleware for request logging and timing
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Check rate limiting
    client_ip = request.client.host
    endpoint_type = "execute" if "execute" in str(request.url.path) else "default"
    
    if not await gateway.check_rate_limit(client_ip, endpoint_type):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    response = await call_next(request)
    
    # Log request
    response_time = time.time() - start_time
    await gateway.log_request(request, response_time, response.status_code)
    
    return response

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await gateway.authenticate_request(credentials)

# Health check
@app.get("/health")
async def health_check():
    """Gateway health check"""
    service_health = {}
    
    for service, url in gateway.services.items():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    service_health[service] = {
                        "status": "healthy" if response.status == 200 else "unhealthy",
                        "response_time": response.headers.get("X-Response-Time", "unknown")
                    }
        except Exception:
            service_health[service] = {"status": "unavailable", "response_time": "timeout"}
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": service_health
    }

# Scheduler endpoints
@app.get("/api/schedules")
async def get_schedules(request: Request, user: Dict = Depends(get_current_user)):
    return await gateway.proxy_request(
        "scheduler", "/schedules", "GET", 
        dict(request.headers), dict(request.query_params)
    )

@app.post("/api/schedules/{schedule_id}/execute")
async def execute_schedule(schedule_id: str, request: Request, user: Dict = Depends(get_current_user)):
    return await gateway.proxy_request(
        "scheduler", f"/schedules/{schedule_id}/execute", "POST",
        dict(request.headers)
    )

# Spider Manager endpoints
@app.get("/api/processes")
async def get_processes(request: Request, user: Dict = Depends(get_current_user)):
    return await gateway.proxy_request(
        "spider-manager", "/processes", "GET",
        dict(request.headers), dict(request.query_params)
    )

@app.post("/api/processes/{task_id}/kill")
async def kill_process(task_id: str, request: Request, user: Dict = Depends(get_current_user)):
    return await gateway.proxy_request(
        "spider-manager", f"/processes/{task_id}/kill", "POST",
        dict(request.headers)
    )

# Result Collector endpoints
@app.get("/api/results/{task_id}")
async def get_results(task_id: str, request: Request, user: Dict = Depends(get_current_user)):
    return await gateway.proxy_request(
        "result-collector", f"/results/{task_id}", "GET",
        dict(request.headers), dict(request.query_params)
    )

@app.post("/api/results/{task_id}/process")
async def process_results(task_id: str, request: Request, user: Dict = Depends(get_current_user)):
    body = await request.json()
    return await gateway.proxy_request(
        "result-collector", f"/process/{task_id}", "POST",
        dict(request.headers), json_data=body
    )

# Metrics aggregation
@app.get("/api/metrics")
async def get_metrics(user: Dict = Depends(get_current_user)):
    """Aggregate metrics from all services"""
    metrics = {"timestamp": datetime.now().isoformat()}
    
    for service in gateway.services.keys():
        try:
            service_metrics = await gateway.proxy_request(
                service, "/metrics", "GET", {}
            )
            metrics[service] = service_metrics
        except Exception as e:
            logger.warning(f"⚠️ Failed to get metrics from {service}: {e}")
            metrics[service] = {"error": str(e)}
    
    return metrics

# Analytics endpoints
@app.get("/api/analytics/requests")
async def get_request_analytics(user: Dict = Depends(get_current_user)):
    """Get API request analytics"""
    try:
        # Get recent logs
        logs = await gateway.redis.lrange("logs:api_requests", 0, 999)
        
        # Parse and analyze
        request_data = []
        for log_str in logs:
            try:
                log_data = json.loads(log_str)
                request_data.append(log_data)
            except json.JSONDecodeError:
                continue
        
        # Calculate statistics
        total_requests = len(request_data)
        avg_response_time = sum(r["response_time"] for r in request_data) / max(total_requests, 1)
        
        status_codes = {}
        for req in request_data:
            code = req["status_code"]
            status_codes[code] = status_codes.get(code, 0) + 1
        
        return {
            "total_requests": total_requests,
            "average_response_time": avg_response_time,
            "status_codes": status_codes,
            "recent_requests": request_data[:50]  # Last 50 requests
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

# WebSocket proxy for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket proxy for real-time updates"""
    await websocket.accept()
    
    # Subscribe to Redis events
    pubsub = gateway.redis.pubsub()
    await pubsub.subscribe("events:*")
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        await pubsub.unsubscribe("events:*")
        await pubsub.close()

@app.on_event("startup")
async def startup_event():
    await gateway.initialize()

@app.on_event("shutdown") 
async def shutdown_event():
    if gateway.redis:
        await gateway.redis.close()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
