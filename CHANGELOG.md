# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-25

### Added
- Initial release of ScrapyUI
- Web-based Scrapy project management interface
- Integrated Playwright support for modern web scraping
- User authentication and authorization system
- Real-time task monitoring and logging
- Multi-format data export (JSON, CSV, Excel, XML)
- Monaco-based code editor with syntax highlighting
- Project and spider management
- Task scheduling and execution
- Performance analytics and monitoring
- Role-based access control (Admin/User)
- RESTful API with FastAPI
- Modern React frontend with Next.js 15
- Command-line interface (CLI)
- Database support (SQLite, PostgreSQL, MySQL)
- Redis integration for task queuing
- WebSocket support for real-time updates
- Comprehensive API documentation
- Docker support for easy deployment

### Features
- **Core Functionality**
  - Create and manage Scrapy projects
  - Write and edit spiders with syntax highlighting
  - Execute spiders with real-time monitoring
  - View and export scraped data
  - Schedule recurring tasks
  - Monitor performance metrics

- **User Management**
  - JWT-based authentication
  - User registration and login
  - Role-based permissions
  - Admin user management interface
  - User data isolation

- **Integration**
  - Full Scrapy framework integration
  - Scrapy-Playwright for browser automation
  - Celery for distributed task processing
  - Redis for caching and task queuing
  - Multiple database backends

- **Developer Experience**
  - Modern React frontend
  - RESTful API design
  - Comprehensive documentation
  - CLI tools for management
  - Docker containerization
  - Hot reload in development

### Technical Stack
- **Backend**: FastAPI, SQLAlchemy, Celery, Redis
- **Frontend**: React, Next.js 15, Tailwind CSS, Monaco Editor
- **Scraping**: Scrapy, Playwright, BeautifulSoup4
- **Database**: SQLite, PostgreSQL, MySQL support
- **Authentication**: JWT with bcrypt password hashing
- **Deployment**: Docker, Uvicorn, Nginx support

### Security
- Secure JWT token authentication
- Password hashing with bcrypt
- Role-based access control
- User data isolation
- CORS protection
- Input validation and sanitization

### Performance
- Asynchronous request handling
- Efficient database queries
- Real-time WebSocket updates
- Optimized frontend rendering
- Caching strategies
- Background task processing

## [Unreleased]

### Added
- **Anti-Detection Features**
  - User-Agent rotation with `scrapy-fake-useragent` library
  - Proxy support with `scrapy-proxies` library
  - Automatic browser detection evasion
  - Multiple User-Agent providers with fallback support

- **Development Efficiency**
  - HTTP caching for faster development cycles (1-day cache expiration)
  - Automatic cache directory management
  - Development-friendly default settings

- **Japanese Language Support**
  - UTF-8 encoding for all exports (FEED_EXPORT_ENCODING)
  - Japanese content prioritization (Accept-Language: ja)
  - Proper handling of Japanese characters in all output formats

- **Spider Management Enhancements**
  - Execution history tab in spider detail pages
  - Version-based result download functionality
  - Generation-based file management
  - Real-time task monitoring with progress indicators

- **Error Prevention**
  - Automatic spider inheritance validation
  - Prevention of missing `scrapy.Spider` inheritance
  - Improved spider copying with inheritance preservation
  - Enhanced error messages for failed tasks

- **UI/UX Improvements**
  - Failed task download button disabling
  - Detailed error messages for download failures
  - Improved task result pages with status-specific displays
  - Enhanced schedule monitoring with real-time updates

### Changed
- **Default Project Settings**
  - All new projects now include anti-detection middleware
  - HTTP caching enabled by default for development
  - Japanese language headers included automatically
  - UTF-8 encoding set as default for all exports

- **Spider Creation Process**
  - Enhanced validation during spider creation and copying
  - Automatic addition of missing imports and inheritance
  - Improved error handling and user feedback

### Fixed
- **Spider Inheritance Issues**
  - Fixed missing `scrapy.Spider` inheritance in copied spiders
  - Resolved class definition problems in spider templates
  - Improved spider code validation and correction

- **Download Functionality**
  - Fixed 500 errors in task result downloads
  - Improved error handling for missing result files
  - Better user feedback for download failures

- **UI Consistency**
  - Fixed React key errors in schedule listings
  - Improved error state handling across components
  - Enhanced loading states and user feedback

### Technical Details
- **Dependencies Added**
  - `scrapy-fake-useragent>=1.4.4` for User-Agent rotation
  - `scrapy-proxies>=0.4` for proxy support
  - Enhanced middleware configuration

- **Documentation**
  - Added comprehensive proxy setup guide (`docs/proxy-setup.md`)
  - Updated README with new features
  - Enhanced inline documentation and comments

### Planned Features
- Advanced scheduling with cron expressions
- Data visualization dashboards
- Plugin system for custom extensions
- Advanced analytics and reporting
- Advanced user management
- API rate limiting
- Enhanced security features
- Performance optimizations
- Mobile-responsive improvements
