#!/usr/bin/env python3
"""
ScrapyUI - Web-based Scrapy Management Interface
A comprehensive web interface for managing Scrapy projects with real-time monitoring,
Node.js Puppeteer integration, and advanced analytics.
"""

import os
import sys
from setuptools import setup, find_packages

# Read version from VERSION file
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'VERSION')
    with open(version_file, 'r', encoding='utf-8') as f:
        return f.read().strip()

# Read long description from README
def get_long_description():
    readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_file):
        with open(readme_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "ScrapyUI - Web-based Scrapy Management Interface"

# Read requirements from requirements.txt
def get_requirements():
    requirements_file = os.path.join(os.path.dirname(__file__), 'backend', 'requirements.txt')
    requirements = []
    
    if os.path.exists(requirements_file):
        with open(requirements_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    # Handle commented out packages
                    if line.startswith('# '):
                        continue
                    requirements.append(line)
    
    return requirements

# Additional requirements for the package
INSTALL_REQUIRES = [
    'fastapi>=0.104.0',
    'uvicorn[standard]>=0.24.0',
    'sqlalchemy>=2.0.0',
    'alembic>=1.12.0',
    'pydantic>=2.5.0',
    'python-multipart>=0.0.6',
    'websockets>=12.0',
    'python-jose[cryptography]>=3.3.0',
    'passlib[bcrypt,argon2]>=1.7.4',
    'argon2-cffi>=23.1.0',
    'bcrypt>=4.0.0,<4.1.0',
    'python-dotenv>=1.0.0',
    'aiofiles>=23.2.0',
    'celery>=5.3.0',
    'redis>=5.0.0',
    'PyYAML>=6.0.0',
    'pymysql>=1.1.0',
    'motor>=3.3.0',
    'elasticsearch>=8.11.0',
    'aioredis>=2.0.0',
    'psutil>=5.9.0',
    'scrapy>=2.12.0',
    'scrapy-playwright>=0.0.40',
    'playwright>=1.51.0',
    'croniter>=3.0.0',
    'pandas>=2.2.0',
    'openpyxl>=3.1.0',
    'beautifulsoup4>=4.12.0',
    'pyquery>=2.0.0',
    'openai>=1.54.0',
    'aiohttp>=3.11.0',
    'httpx>=0.28.0',
]

EXTRAS_REQUIRE = {
    'dev': [
        'pytest>=8.3.0',
        'pytest-asyncio>=0.24.0',
        'pytest-mock>=3.14.0',
    ],
    'postgresql': [
        'psycopg2-binary>=2.9.9',
    ],
    'xml': [
        'lxml>=4.9.0',
    ],
}

# Entry points for command line tools
ENTRY_POINTS = {
    'console_scripts': [
        'scrapyui=backend.app.cli:main',
        'scrapyui-server=backend.app.main:start_server',
        'scrapyui-admin=backend.create_admin:main',
    ],
}

setup(
    name='ScrapyUI',
    version=get_version(),
    description='Web-based Scrapy Management Interface with Node.js Puppeteer Integration',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    author='motoaki',
    author_email='igtmtakan@gmail.com',
    url='https://github.com/igtmtakan/scrapyUi',
    project_urls={
        'Bug Reports': 'https://github.com/igtmtakan/scrapyUi/issues',
        'Source': 'https://github.com/igtmtakan/scrapyUi',
        'Documentation': 'https://github.com/igtmtakan/scrapyUi/blob/main/docs/',
    },
    packages=find_packages(include=['backend*']),
    include_package_data=True,
    package_data={
        'backend': [
            'app/templates/*.json',
            'config/*.yaml',
            'scripts/*.py',
            'templates/*.json',
        ],
    },
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    entry_points=ENTRY_POINTS,
    python_requires='>=3.9',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Monitoring',
        'Topic :: Text Processing :: Markup :: HTML',
        'Framework :: FastAPI',
        'Framework :: Scrapy',
    ],
    keywords='scrapy web-scraping ui interface monitoring puppeteer automation',
    zip_safe=False,
)
