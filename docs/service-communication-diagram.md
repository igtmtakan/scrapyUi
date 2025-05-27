# ScrapyUI サービス間通信・ポート構成図

## 🔌 ポート構成とサービス通信

```mermaid
graph TB
    subgraph "🌐 External Access"
        USER[👤 User Browser]
        ADMIN[👨‍💼 Admin Browser]
        API_CLIENT[🔧 API Client]
    end

    subgraph "🎨 Frontend Layer (Port 4000)"
        NEXTJS[📱 Next.js Server<br/>Port: 4000<br/>Protocol: HTTP/HTTPS]
        STATIC[📁 Static Assets<br/>Served by Next.js]
    end

    subgraph "⚡ Backend API Layer (Port 8000)"
        FASTAPI[⚡ FastAPI Server<br/>Port: 8000<br/>Protocol: HTTP/HTTPS]
        WEBSOCKET[🔌 WebSocket Server<br/>Port: 8000<br/>Protocol: WS/WSS]
        API_DOCS[📚 API Documentation<br/>Port: 8000/docs]
    end

    subgraph "🟢 Node.js Service Layer (Port 3001)"
        NODEJS[🟢 Express.js Server<br/>Port: 3001<br/>Protocol: HTTP]
        PUPPETEER[🎭 Puppeteer Service<br/>Internal Communication]
        PDF_SVC[📄 PDF Service<br/>Internal Communication]
    end

    subgraph "🗄️ Database Layer"
        SQLITE[📦 SQLite<br/>File: scrapy_ui.db<br/>Protocol: File I/O]
        POSTGRES[🐘 PostgreSQL<br/>Port: 5432<br/>Protocol: TCP]
        REDIS[🔴 Redis<br/>Port: 6379<br/>Protocol: TCP]
    end

    subgraph "📁 File System"
        PROJECTS[📂 Scrapy Projects<br/>Path: /scrapy_projects]
        RESULTS[📊 Results<br/>Path: /results]
        LOGS[📝 Logs<br/>Path: /logs]
        UPLOADS[📤 Uploads<br/>Path: /uploads]
    end

    subgraph "👷 Worker Processes"
        SCRAPY_WORKER[🕷️ Scrapy Workers<br/>Dynamic Processes<br/>Protocol: Subprocess]
        TASK_MONITOR[👁️ Task Monitor<br/>Background Thread]
        SCHEDULER[⏰ Scheduler<br/>Background Service]
    end

    %% External to Frontend
    USER -->|HTTP/HTTPS:4000| NEXTJS
    ADMIN -->|HTTP/HTTPS:4000| NEXTJS
    API_CLIENT -->|HTTP/HTTPS:8000| FASTAPI

    %% Frontend to Backend
    NEXTJS -->|HTTP API:8000| FASTAPI
    NEXTJS -->|WebSocket:8000| WEBSOCKET

    %% Backend to Node.js
    FASTAPI -->|HTTP API:3001| NODEJS

    %% Backend to Database
    FASTAPI -->|SQLAlchemy| SQLITE
    FASTAPI -->|SQLAlchemy| POSTGRES
    FASTAPI -->|Redis Client| REDIS

    %% Backend to File System
    FASTAPI -->|File I/O| PROJECTS
    FASTAPI -->|File I/O| RESULTS
    FASTAPI -->|File I/O| LOGS
    FASTAPI -->|File I/O| UPLOADS

    %% Backend to Workers
    FASTAPI -->|Subprocess| SCRAPY_WORKER
    FASTAPI -->|Thread| TASK_MONITOR
    FASTAPI -->|Service| SCHEDULER

    %% Workers to File System
    SCRAPY_WORKER -->|File I/O| PROJECTS
    SCRAPY_WORKER -->|File I/O| RESULTS
    TASK_MONITOR -->|File I/O| LOGS

    %% Node.js Internal
    NODEJS -->|Internal| PUPPETEER
    NODEJS -->|Internal| PDF_SVC
```

## 📡 通信プロトコル詳細

### HTTP/REST API 通信

```mermaid
sequenceDiagram
    participant F as 🎨 Frontend (4000)
    participant A as ⚡ API Server (8000)
    participant N as 🟢 Node.js (3001)
    participant D as 💾 Database
    participant W as 👷 Worker

    Note over F,W: 標準的なAPI通信フロー

    F->>A: GET /api/projects
    A->>D: SELECT * FROM projects
    D-->>A: Project data
    A-->>F: JSON response

    F->>A: POST /api/tasks
    A->>W: Start scrapy process
    W-->>A: Process started
    A-->>F: Task created

    F->>A: POST /api/nodejs/pdf
    A->>N: HTTP POST :3001/api/pdf
    N-->>A: PDF generated
    A-->>F: PDF URL
```

### WebSocket リアルタイム通信

```mermaid
sequenceDiagram
    participant F as 🎨 Frontend
    participant W as 🔌 WebSocket (8000)
    participant M as 👁️ Task Monitor
    participant T as 📋 Task

    Note over F,T: リアルタイム更新フロー

    F->>W: WebSocket Connect
    W-->>F: Connection established

    T->>M: Task status change
    M->>W: Broadcast update
    W-->>F: Real-time notification

    T->>M: Progress update
    M->>W: Progress data
    W-->>F: Live progress
```

## 🔧 サービス設定詳細

### Frontend Service (Port 4000)
```yaml
Service: Next.js Development Server
Port: 4000
Protocol: HTTP (dev) / HTTPS (prod)
Environment Variables:
  - NEXT_PUBLIC_API_URL=http://localhost:8000
  - NEXT_PUBLIC_WS_URL=ws://localhost:8000
Proxy Configuration:
  - /api/* → http://localhost:8000/api/*
Static Assets: Served by Next.js
Hot Reload: Enabled in development
```

### Backend API Service (Port 8000)
```yaml
Service: FastAPI + Uvicorn
Port: 8000
Protocol: HTTP/HTTPS + WebSocket
Workers: 1 (dev) / 4+ (prod)
Environment Variables:
  - DATABASE_URL=sqlite:///./database/scrapy_ui.db
  - NODEJS_SERVICE_URL=http://localhost:3001
  - JWT_SECRET_KEY=your-secret-key
Endpoints:
  - REST API: /api/*
  - WebSocket: /ws/*
  - Documentation: /docs
  - Health Check: /health
```

### Node.js Service (Port 3001)
```yaml
Service: Express.js + Puppeteer
Port: 3001
Protocol: HTTP
Process Manager: PM2 (prod)
Environment Variables:
  - PORT=3001
  - PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
  - MAX_BROWSER_INSTANCES=5
Services:
  - PDF Generation: /api/pdf
  - Screenshot: /api/screenshot
  - Web Scraping: /api/scraping
  - Health Check: /api/health
```

## 🗄️ データベース接続

### SQLite (Development)
```yaml
Type: File-based Database
Location: backend/database/scrapy_ui.db
Connection: SQLAlchemy File URI
Backup: File copy
Migration: Alembic
```

### PostgreSQL (Production)
```yaml
Type: Network Database
Port: 5432
Connection Pool: 20 connections
SSL: Required in production
Backup: pg_dump automated
Migration: Alembic
```

### Redis (Cache/Queue)
```yaml
Type: In-memory Database
Port: 6379
Use Cases:
  - Session storage
  - Task queue
  - Cache layer
  - Real-time data
```

## 📁 ファイルシステム構成

```mermaid
graph TB
    subgraph "📁 File System Layout"
        ROOT[🏠 Project Root]
        
        subgraph "🎨 Frontend Files"
            FE_ROOT[📁 frontend/]
            FE_BUILD[📦 .next/]
            FE_PUBLIC[📁 public/]
            FE_STATIC[📁 static/]
        end
        
        subgraph "⚡ Backend Files"
            BE_ROOT[📁 backend/]
            BE_APP[📁 app/]
            BE_DB[📁 database/]
            BE_LOGS[📁 logs/]
        end
        
        subgraph "🟢 Node.js Files"
            NODE_ROOT[📁 nodejs-service/]
            NODE_TEMP[📁 temp/]
            NODE_UPLOADS[📁 uploads/]
        end
        
        subgraph "🕷️ Scrapy Files"
            SCRAPY_ROOT[📁 scrapy_projects/]
            PROJECT1[📁 project1/]
            PROJECT2[📁 project2/]
            RESULTS_DIR[📁 results/]
        end
    end
    
    ROOT --> FE_ROOT
    ROOT --> BE_ROOT
    ROOT --> NODE_ROOT
    ROOT --> SCRAPY_ROOT
    
    FE_ROOT --> FE_BUILD
    FE_ROOT --> FE_PUBLIC
    FE_ROOT --> FE_STATIC
    
    BE_ROOT --> BE_APP
    BE_ROOT --> BE_DB
    BE_ROOT --> BE_LOGS
    
    NODE_ROOT --> NODE_TEMP
    NODE_ROOT --> NODE_UPLOADS
    
    SCRAPY_ROOT --> PROJECT1
    SCRAPY_ROOT --> PROJECT2
    SCRAPY_ROOT --> RESULTS_DIR
```

## 🔄 プロセス管理

### Development Environment
```yaml
Frontend: npm run dev (Port 4000)
Backend: uvicorn main:app --reload (Port 8000)
Node.js: npm run dev (Port 3001)
Database: SQLite file
Monitoring: Console logs
```

### Production Environment
```yaml
Frontend: 
  - Build: npm run build
  - Serve: npm start or static hosting
Backend:
  - Server: uvicorn main:app --workers 4
  - Process Manager: systemd or Docker
Node.js:
  - Process Manager: PM2
  - Clustering: PM2 cluster mode
Database:
  - PostgreSQL with connection pooling
  - Redis for caching
Monitoring:
  - Prometheus metrics
  - Grafana dashboards
  - Log aggregation
```

## 🚨 ヘルスチェック・監視

```mermaid
graph TB
    subgraph "🏥 Health Check System"
        subgraph "🎨 Frontend Health"
            FE_HEALTH[📊 Next.js Health]
            FE_BUILD[🔨 Build Status]
            FE_ASSETS[📁 Asset Loading]
        end
        
        subgraph "⚡ Backend Health"
            API_HEALTH[📊 API Health]
            DB_HEALTH[💾 Database Health]
            WS_HEALTH[🔌 WebSocket Health]
        end
        
        subgraph "🟢 Node.js Health"
            NODE_HEALTH[📊 Service Health]
            BROWSER_HEALTH[🎭 Browser Pool Health]
            MEMORY_HEALTH[💾 Memory Usage]
        end
        
        subgraph "👷 Worker Health"
            WORKER_HEALTH[📊 Worker Status]
            TASK_HEALTH[📋 Task Queue Health]
            PROCESS_HEALTH[⚙️ Process Health]
        end
    end
```

### Health Check Endpoints
```yaml
Frontend: http://localhost:4000/_next/static/health
Backend: http://localhost:8000/health
Node.js: http://localhost:3001/api/health
Database: Connection test in API health check
Workers: Process status in API health check
```

このサービス間通信図により、ScrapyUIの各コンポーネントがどのように連携し、どのポートで通信しているかが明確になります。
