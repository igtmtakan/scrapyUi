"""
Uvicorn configuration for ScrapyUI backend
"""

import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Uvicorn configuration
config = {
    "app": "app.main:app",
    "host": "0.0.0.0",
    "port": 8000,
    "reload": True,
    "reload_dirs": [str(Path(__file__).parent)],  # Only watch backend directory
    "reload_excludes": [
        "../scrapy_projects/*",
        "../scrapy_projects/**/*",
    ],
    "log_level": "info",
}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(**config)
