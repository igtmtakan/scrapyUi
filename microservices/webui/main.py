#!/usr/bin/env python3
"""
ScrapyUI WebUI Service
Simple web interface for microservices
"""

import logging
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ScrapyUI WebUI", version="1.0.0")

# Templates
templates = Jinja2Templates(directory="templates")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "ScrapyUI Dashboard",
        "timestamp": datetime.now().isoformat()
    })

@app.get("/schedules", response_class=HTMLResponse)
async def schedules(request: Request):
    """Schedules page"""
    return templates.TemplateResponse("schedules.html", {
        "request": request,
        "title": "Schedules"
    })

@app.get("/processes", response_class=HTMLResponse)
async def processes(request: Request):
    """Processes page"""
    return templates.TemplateResponse("processes.html", {
        "request": request,
        "title": "Spider Processes"
    })

@app.get("/results", response_class=HTMLResponse)
async def results(request: Request):
    """Results page"""
    return templates.TemplateResponse("results.html", {
        "request": request,
        "title": "Results"
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "webui",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
        log_level="info"
    )
