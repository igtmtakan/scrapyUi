#!/usr/bin/env python3
"""
ScrapyUI - Web-based Scrapy Management Interface
A modern, user-friendly web interface for managing Scrapy projects and spiders.
"""

from setuptools import setup, find_packages
import os

# パッケージのルートディレクトリ
here = os.path.abspath(os.path.dirname(__file__))

# README.mdの内容を読み込み
def read_readme():
    readme_path = os.path.join(here, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "ScrapyUI - Web-based Scrapy Management Interface"

# requirements.txtから依存関係を読み込み
def read_requirements():
    requirements_path = os.path.join(here, "backend", "requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

# バージョン情報
VERSION = "1.0.0"

setup(
    name="scrapyui",
    version=VERSION,
    author="ScrapyUI Team",
    author_email="admin@scrapyui.com",
    description="Web-based Scrapy Management Interface with Playwright Integration",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/scrapyui/scrapyui",
    project_urls={
        "Bug Reports": "https://github.com/scrapyui/scrapyui/issues",
        "Source": "https://github.com/scrapyui/scrapyui",
        "Documentation": "https://scrapyui.readthedocs.io/",
    },
    packages=find_packages(where="backend"),
    package_dir={"": "backend"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Framework :: FastAPI",
        "Framework :: Scrapy",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "scrapyui=app.cli:main",
            "scrapyui-server=app.main:start_server",
            "scrapyui-admin=app.cli:create_admin",
        ],
    },
    include_package_data=True,
    package_data={
        "app": [
            "templates/*.py",
            "static/*",
            "config/*.py",
        ],
    },
    zip_safe=False,
    keywords=[
        "scrapy",
        "web-scraping",
        "playwright",
        "fastapi",
        "react",
        "ui",
        "management",
        "spider",
        "crawler",
        "automation",
    ],
)
