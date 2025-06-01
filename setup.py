#!/usr/bin/env python3
"""
ScrapyUI - Web-based Scrapy Management Interface
A comprehensive web interface for managing Scrapy projects with real-time monitoring,
Node.js Puppeteer integration, and advanced analytics.
"""

import os
import sys
import subprocess
import shutil
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop

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

def check_npm():
    """npmがインストールされているかチェック"""
    try:
        subprocess.run(['npm', '--version'], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_npm_dependencies():
    """npm依存関係をインストール"""
    print("🔍 npmの確認中...")

    if not check_npm():
        print("⚠️  npmが見つかりません。Node.jsをインストールしてください:")
        print("   https://nodejs.org/")
        print("   または: sudo apt install nodejs npm")
        print("   または: curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs")
        return False

    print("✅ npmが見つかりました")

    # Node.jsとnpmのバージョンを確認
    try:
        node_version = subprocess.run(['node', '--version'], capture_output=True, text=True, check=True)
        npm_version = subprocess.run(['npm', '--version'], capture_output=True, text=True, check=True)
        print(f"   Node.js: {node_version.stdout.strip()}")
        print(f"   npm: {npm_version.stdout.strip()}")
    except subprocess.CalledProcessError:
        print("⚠️  Node.jsまたはnpmのバージョン確認に失敗しました")

    success = True

    # フロントエンドの依存関係をインストール
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    if os.path.exists(frontend_dir):
        print("📦 フロントエンド依存関係をインストール中...")
        try:
            # npm ci を使用してより高速で確実なインストール
            if os.path.exists(os.path.join(frontend_dir, 'package-lock.json')):
                subprocess.run(['npm', 'ci'], cwd=frontend_dir, check=True)
            else:
                subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
            print("✅ フロントエンド依存関係のインストール完了")
        except subprocess.CalledProcessError as e:
            print(f"❌ フロントエンド依存関係のインストール失敗: {e}")
            success = False
    else:
        print("⚠️  フロントエンドディレクトリが見つかりません")

    # Node.jsサービスの依存関係をインストール
    nodejs_dir = os.path.join(os.path.dirname(__file__), 'nodejs-service')
    if os.path.exists(nodejs_dir):
        print("📦 Node.jsサービス依存関係をインストール中...")
        try:
            # npm ci を使用してより高速で確実なインストール
            if os.path.exists(os.path.join(nodejs_dir, 'package-lock.json')):
                subprocess.run(['npm', 'ci'], cwd=nodejs_dir, check=True)
            else:
                subprocess.run(['npm', 'install'], cwd=nodejs_dir, check=True)
            print("✅ Node.jsサービス依存関係のインストール完了")

            # Puppeteerのブラウザダウンロードを確認
            print("🔍 Puppeteerブラウザの確認中...")
            try:
                subprocess.run(['npx', 'puppeteer', 'browsers', 'install', 'chrome'],
                             cwd=nodejs_dir, check=True, capture_output=True)
                print("✅ Puppeteerブラウザの準備完了")
            except subprocess.CalledProcessError:
                print("⚠️  Puppeteerブラウザのダウンロードに失敗しました（後で手動実行可能）")

        except subprocess.CalledProcessError as e:
            print(f"❌ Node.jsサービス依存関係のインストール失敗: {e}")
            success = False
    else:
        print("⚠️  Node.jsサービスディレクトリが見つかりません")

    if success:
        print("🎉 すべてのnpm依存関係のインストールが完了しました！")
        print("\n📋 次のステップ:")
        print("   1. scrapyui init myproject")
        print("   2. cd myproject")
        print("   3. scrapyui start")

    return success

def run_database_migrations():
    """データベースマイグレーションを実行"""
    print("🔧 データベースマイグレーションを実行中...")

    try:
        # Alembicマイグレーションを実行
        backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
        if os.path.exists(backend_dir):
            # Alembicが利用可能かチェック
            try:
                subprocess.run(['alembic', '--version'], capture_output=True, check=True)

                # マイグレーション実行
                subprocess.run(['alembic', 'upgrade', 'head'],
                             cwd=backend_dir, check=True)
                print("✅ Alembicマイグレーション完了")

            except (subprocess.CalledProcessError, FileNotFoundError):
                # Alembicが利用できない場合は、SQLAlchemyで直接初期化
                print("⚠️ Alembicが見つかりません。SQLAlchemyで初期化します...")

                # Pythonスクリプトでデータベース初期化
                init_script = os.path.join(backend_dir, 'scripts', 'init_database.py')
                if os.path.exists(init_script):
                    subprocess.run(['python', init_script], cwd=backend_dir, check=True)
                    print("✅ データベース初期化完了")
                else:
                    print("⚠️ データベース初期化スクリプトが見つかりません")

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ データベースマイグレーション失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ データベースマイグレーション予期しないエラー: {e}")
        return False

def setup_project_directories():
    """プロジェクトディレクトリを設定"""
    print("📁 プロジェクトディレクトリを設定中...")

    try:
        # 必要なディレクトリを作成
        directories = [
            'scrapy_projects',
            'logs',
            'database',
            'user_scripts',
        ]

        for dir_name in directories:
            dir_path = os.path.join(os.getcwd(), dir_name)
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ {dir_name}/ ディレクトリを作成")

        return True

    except Exception as e:
        print(f"❌ ディレクトリ設定エラー: {e}")
        return False

class CustomInstallCommand(install):
    """カスタムインストールコマンド"""

    def run(self):
        # 通常のPythonパッケージインストール
        install.run(self)

        # プロジェクトディレクトリの設定
        setup_project_directories()

        # データベースマイグレーション
        run_database_migrations()

        # npm依存関係のインストール
        install_npm_dependencies()

class CustomDevelopCommand(develop):
    """カスタム開発モードコマンド"""

    def run(self):
        # 通常の開発モードインストール
        develop.run(self)

        # プロジェクトディレクトリの設定
        setup_project_directories()

        # データベースマイグレーション
        run_database_migrations()

        # npm依存関係のインストール
        install_npm_dependencies()

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
        '': [
            'frontend/package.json',
            'frontend/package-lock.json',
            'frontend/next.config.js',
            'frontend/next.config.ts',
            'frontend/tailwind.config.ts',
            'frontend/postcss.config.mjs',
            'frontend/tsconfig.json',
            'frontend/components.json',
            'frontend/eslint.config.mjs',
            'frontend/src/**/*',
            'frontend/public/**/*',
            'nodejs-service/package.json',
            'nodejs-service/package-lock.json',
            'nodejs-service/src/**/*',
            'nodejs-service/config/**/*',
            'nodejs-service/tests/**/*',
        ],
    },
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    entry_points=ENTRY_POINTS,
    cmdclass={
        'install': CustomInstallCommand,
        'develop': CustomDevelopCommand,
    },
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
