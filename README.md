# ScrapyUI 🕷️

[![PyPI version](https://badge.fury.io/py/scrapyui.svg)](https://badge.fury.io/py/scrapyui)
[![Python versions](https://img.shields.io/pypi/pyversions/scrapyui.svg)](https://pypi.org/project/scrapyui/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**ScrapyUI** is a modern, web-based management interface for Scrapy projects with integrated Playwright support. It provides an intuitive UI for creating, managing, and monitoring web scraping projects.

## ✨ Features

### 🎯 **Core Features**
- **Web-based Interface**: Modern React frontend with real-time updates
- **Scrapy Integration**: Full Scrapy project management and spider execution
- **Playwright Support**: Built-in browser automation with scrapy-playwright
- **User Management**: Multi-user support with role-based access control
- **Real-time Monitoring**: Live task execution monitoring and logging

### 🛠️ **Management Tools**
- **Project Management**: Create, edit, and organize Scrapy projects
- **Spider Editor**: Monaco-based code editor with syntax highlighting
- **Task Scheduler**: Schedule and manage spider execution
- **Data Export**: Export scraped data in multiple formats (JSON, CSV, Excel, XML)
- **Performance Analytics**: Monitor scraping performance and statistics
- **Execution History**: Version-based spider result download and management

### 🔒 **Security & Authentication**
- **JWT Authentication**: Secure token-based authentication
- **Role-based Access**: Admin and user roles with appropriate permissions
- **User Isolation**: Each user can only access their own projects and data

### 🛡️ **Anti-Detection & Optimization**
- **User-Agent Rotation**: Automatic user-agent switching with scrapy-fake-useragent
- **Proxy Support**: IP rotation with scrapy-proxies for stealth scraping
- **HTTP Caching**: Development-friendly caching for faster iteration cycles
- **Japanese Support**: UTF-8 encoding and Japanese content prioritization
- **Smart Defaults**: Pre-configured settings for optimal scraping performance

## 🚀 Quick Start

### Installation

```bash
pip install scrapyui
```

### Start ScrapyUI Server

```bash
# Start with default settings
scrapyui start

# Start with custom port and auto-open browser
scrapyui start --port 8080 --open-browser

# Start in development mode with auto-reload
scrapyui start --reload
```

### Create Admin User

```bash
# Create admin user with default credentials
scrapyui create-admin

# Create admin user with custom credentials
scrapyui create-admin --email admin@example.com --password mypassword
```

### Access the Interface

Open your browser and navigate to:
- **Frontend**: http://localhost:4000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Default Admin Credentials

```
Email: admin@scrapyui.com
Password: admin123456
```

## 📖 Usage

### 1. Create a New Project

```bash
# Initialize a new Scrapy project
scrapyui init myproject

# Initialize with specific template
scrapyui init myproject --template playwright
```

### 2. Web Interface

1. **Login** with your credentials
2. **Create Project** using the web interface
3. **Add Spiders** with the built-in code editor
4. **Run Tasks** and monitor execution in real-time
5. **Export Data** in your preferred format

### 3. Command Line Interface

```bash
# Show help
scrapyui --help

# Show version
scrapyui --version

# Database management
scrapyui db init      # Initialize database
scrapyui db migrate   # Run migrations
scrapyui db reset     # Reset database
```

## 🏗️ Architecture

### Backend (FastAPI)
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM with SQLite/PostgreSQL support
- **Celery**: Distributed task queue for spider execution
- **JWT**: Secure authentication and authorization

### Frontend (React)
- **Next.js 15**: React framework with server-side rendering
- **Tailwind CSS**: Utility-first CSS framework
- **Monaco Editor**: VS Code-like code editor
- **Real-time Updates**: WebSocket integration for live monitoring

### Integration
- **Scrapy**: Web scraping framework
- **Playwright**: Browser automation for modern web apps
- **Redis**: Caching and task queue backend

## 🔧 Configuration

### Environment Variables

```bash
# Database Configuration
DATABASE_TYPE=sqlite
DATABASE_NAME=/path/to/your/backend/database/scrapy_ui.db
DATABASE_ECHO=false

# For PostgreSQL
# DATABASE_TYPE=postgresql
# DATABASE_HOST=localhost
# DATABASE_PORT=5432
# DATABASE_NAME=scrapy_ui
# DATABASE_USER=scrapy_user
# DATABASE_PASSWORD=your_password

# JWT Authentication
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application Settings
SCRAPY_UI_ENV=production
DEBUG=false
LOG_LEVEL=INFO
```

### Custom Settings

Create a `.env` file in your backend directory:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000

# Database Configuration (SQLite - Recommended for single-user)
DATABASE_TYPE=sqlite
DATABASE_NAME=/absolute/path/to/backend/database/scrapy_ui.db
DATABASE_ECHO=false

# Database Configuration (PostgreSQL - For multi-user production)
# DATABASE_TYPE=postgresql
# DATABASE_HOST=localhost
# DATABASE_PORT=5432
# DATABASE_NAME=scrapy_ui
# DATABASE_USER=scrapy_user
# DATABASE_PASSWORD=your_password

# Security
SECRET_KEY=your-super-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256

# Application Settings
SCRAPY_UI_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# File Paths
SCRAPY_PROJECTS_DIR=/path/to/scrapy_projects
UPLOADS_DIR=/path/to/uploads
EXPORTS_DIR=/path/to/exports
```

## 📚 Documentation

- **API Documentation**: Available at `/docs` when server is running
- **User Guide**: [Coming Soon]
- **Developer Guide**: [Coming Soon]

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/igtmtakan/scrapyUi.git
cd scrapyUi

# Backend setup
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Frontend setup
cd frontend
npm install
npm run dev
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Scrapy**: The amazing web scraping framework
- **Playwright**: Modern browser automation
- **FastAPI**: High-performance Python web framework
- **React**: User interface library

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/igtmtakan/scrapyUi/issues)
- **Discussions**: [GitHub Discussions](https://github.com/igtmtakan/scrapyUi/discussions)
- **Email**: admin@scrapyui.com

---

**Made with ❤️ by the ScrapyUI Team**
