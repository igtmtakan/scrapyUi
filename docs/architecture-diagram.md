# ScrapyUI システムアーキテクチャ図

## 🏗️ 全体アーキテクチャ概要

```mermaid
graph TB
    %% ユーザー層
    subgraph "👥 User Layer"
        USER[👤 User Browser]
        ADMIN[👨‍💼 Admin Dashboard]
    end

    %% フロントエンド層
    subgraph "🎨 Frontend Layer (Port 4000)"
        NEXTJS[📱 Next.js 15 + React 19]
        MONACO[📝 Monaco Editor]
        CHARTS[📊 Chart.js]
        WEBSOCKET_CLIENT[🔌 WebSocket Client]
    end

    %% API Gateway層
    subgraph "🌐 API Gateway Layer (Port 8000)"
        FASTAPI[⚡ FastAPI Server]
        AUTH[🔐 JWT Authentication]
        MIDDLEWARE[🛡️ Error Handling Middleware]
        CORS[🌍 CORS Handler]
    end

    %% Node.js サービス層
    subgraph "🟢 Node.js Service Layer (Port 3001)"
        NODEJS[🟢 Express.js Server]
        PUPPETEER[🎭 Puppeteer Pool]
        BROWSER_POOL[🌐 Browser Pool Manager]
        PDF_SERVICE[📄 PDF Generator]
        SCREENSHOT[📸 Screenshot Service]
    end

    %% コア処理層
    subgraph "⚙️ Core Processing Layer"
        SCRAPY_SERVICE[🕷️ Scrapy Service]
        TASK_MANAGER[📋 Task Manager]
        SCHEDULER[⏰ APScheduler]
        MONITOR[👁️ Task Monitor]
        WORKER_POOL[👷 Worker Pool]
    end

    %% Python 3.13 最適化層
    subgraph "🚀 Python 3.13 Optimization Layer"
        FREE_THREAD[🔥 Free-threaded Executor]
        JIT_OPTIMIZER[⚡ JIT Optimizer]
        ASYNC_OPT[🔄 Async Optimizer]
        MEMORY_OPT[💾 Memory Optimizer]
        PERF_MONITOR[📊 Performance Monitor]
    end

    %% データ層
    subgraph "💾 Data Layer"
        subgraph "🗄️ Primary Database"
            SQLITE[📦 SQLite (Default)]
            POSTGRES[🐘 PostgreSQL (Optional)]
            MYSQL[🐬 MySQL (Optional)]
        end

        subgraph "📊 Analytics Database"
            MONGODB[🍃 MongoDB (Optional)]
            ELASTICSEARCH[🔍 Elasticsearch (Optional)]
        end

        subgraph "⚡ Cache Layer"
            REDIS[🔴 Redis (Optional)]
            MEMORY_CACHE[💾 In-Memory Cache]
        end
    end

    %% ファイルシステム層
    subgraph "📁 File System Layer"
        PROJECT_FILES[📂 Scrapy Projects]
        RESULTS[📊 Scraping Results]
        LOGS[📝 Log Files]
        TEMPLATES[📋 Spider Templates]
        UPLOADS[📤 Upload Storage]
    end

    %% 外部サービス層
    subgraph "🌐 External Services"
        PROXY_SERVICES[🔀 Proxy Services]
        AI_SERVICES[🤖 AI Analysis APIs]
        NOTIFICATION[📧 Notification Services]
        MONITORING[📈 External Monitoring]
    end

    %% 接続関係
    USER --> NEXTJS
    ADMIN --> NEXTJS

    NEXTJS --> FASTAPI
    NEXTJS --> WEBSOCKET_CLIENT
    MONACO --> FASTAPI
    CHARTS --> FASTAPI

    FASTAPI --> AUTH
    FASTAPI --> MIDDLEWARE
    FASTAPI --> SCRAPY_SERVICE
    FASTAPI --> NODEJS

    SCRAPY_SERVICE --> TASK_MANAGER
    SCRAPY_SERVICE --> FREE_THREAD
    TASK_MANAGER --> SCHEDULER
    TASK_MANAGER --> MONITOR
    TASK_MANAGER --> WORKER_POOL

    FREE_THREAD --> JIT_OPTIMIZER
    FREE_THREAD --> ASYNC_OPT
    ASYNC_OPT --> MEMORY_OPT
    MEMORY_OPT --> PERF_MONITOR

    NODEJS --> PUPPETEER
    NODEJS --> BROWSER_POOL
    NODEJS --> PDF_SERVICE
    NODEJS --> SCREENSHOT

    SCRAPY_SERVICE --> SQLITE
    SCRAPY_SERVICE --> PROJECT_FILES
    TASK_MANAGER --> RESULTS
    MONITOR --> LOGS

    SCRAPY_SERVICE --> PROXY_SERVICES
    FASTAPI --> AI_SERVICES
    MONITOR --> NOTIFICATION
    PERF_MONITOR --> MONITORING
```

## 🔧 詳細コンポーネント構成

### 1. **フロントエンド層 (Port 4000)**

```mermaid
graph LR
    subgraph "🎨 Frontend Architecture"
        subgraph "📱 Next.js 15 Application"
            APP_ROUTER[🗂️ App Router]
            PAGES[📄 Pages]
            COMPONENTS[🧩 Components]
            HOOKS[🪝 Custom Hooks]
            STORES[🏪 Zustand Stores]
        end

        subgraph "🎨 UI Components"
            DASHBOARD[📊 Dashboard]
            PROJECT_UI[📁 Project Management]
            SPIDER_UI[🕷️ Spider Editor]
            TASK_UI[📋 Task Monitor]
            RESULTS_UI[📊 Results Viewer]
        end

        subgraph "🔧 Utilities"
            API_CLIENT[🌐 API Client]
            WEBSOCKET_CLIENT[🔌 WebSocket Client]
            MONACO[📝 Monaco Editor]
            CHARTS[📊 Chart.js]
        end
    end
```

### 2. **バックエンド API層 (Port 8000)**

```mermaid
graph TB
    subgraph "⚡ FastAPI Backend"
        subgraph "🛡️ Middleware Stack"
            ERROR_MW[🚨 Error Handling]
            REQUEST_MW[📝 Request Logging]
            PERF_MW[⏱️ Performance Logging]
            CORS_MW[🌍 CORS Middleware]
        end

        subgraph "🔐 Authentication"
            JWT_AUTH[🎫 JWT Authentication]
            ROLE_AUTH[👥 Role-based Authorization]
            API_KEY[🔑 API Key Authentication]
        end

        subgraph "📡 API Endpoints"
            PROJECT_API[📁 Projects API]
            SPIDER_API[🕷️ Spiders API]
            TASK_API[📋 Tasks API]
            RESULTS_API[📊 Results API]
            SCHEDULE_API[⏰ Schedules API]
            PERF_API[🚀 Performance API]
            ADMIN_API[👨‍💼 Admin API]
        end

        subgraph "🔌 Real-time Communication"
            WEBSOCKET[🔌 WebSocket Endpoints]
            SSE[📡 Server-Sent Events]
        end
    end
```

### 3. **Node.js サービス層 (Port 3001)**

```mermaid
graph TB
    subgraph "🟢 Node.js Microservice"
        subgraph "🎭 Browser Automation"
            PUPPETEER_POOL[🎭 Puppeteer Pool]
            BROWSER_MGR[🌐 Browser Manager]
            PAGE_POOL[📄 Page Pool]
        end

        subgraph "📄 Document Services"
            PDF_GEN[📄 PDF Generator]
            SCREENSHOT_SVC[📸 Screenshot Service]
            HTML_PARSER[📝 HTML Parser]
        end

        subgraph "🔄 Workflow Engine"
            WORKFLOW_MGR[🔄 Workflow Manager]
            BATCH_PROCESSOR[📦 Batch Processor]
            SCHEDULER_SVC[⏰ Scheduler Service]
        end

        subgraph "📊 Monitoring"
            METRICS_COLLECTOR[📊 Metrics Collector]
            HEALTH_CHECK[🏥 Health Check]
            PERFORMANCE_TRACKER[📈 Performance Tracker]
        end
    end
```

### 4. **コア処理層**

```mermaid
graph TB
    subgraph "⚙️ Core Processing Engine"
        subgraph "🕷️ Scrapy Integration"
            SCRAPY_SERVICE[🕷️ Scrapy Service]
            PROJECT_MGR[📁 Project Manager]
            SPIDER_RUNNER[🏃 Spider Runner]
            SETTINGS_MGR[⚙️ Settings Manager]
        end

        subgraph "📋 Task Management"
            TASK_QUEUE[📋 Task Queue]
            TASK_EXECUTOR[⚡ Task Executor]
            TASK_MONITOR[👁️ Task Monitor]
            PROGRESS_TRACKER[📊 Progress Tracker]
        end

        subgraph "⏰ Scheduling System"
            CRON_SCHEDULER[⏰ Cron Scheduler]
            JOB_QUEUE[📋 Job Queue]
            RETRY_HANDLER[🔄 Retry Handler]
        end

        subgraph "👷 Worker Management"
            WORKER_POOL[👷 Worker Pool]
            PROCESS_MGR[🔧 Process Manager]
            RESOURCE_MGR[💾 Resource Manager]
        end
    end
```

### 5. **Python 3.13 最適化層**

```mermaid
graph TB
    subgraph "🚀 Python 3.13 Optimization"
        subgraph "🔥 Parallel Processing"
            FREE_THREAD[🔥 Free-threaded Executor]
            THREAD_POOL[🧵 Thread Pool]
            PROCESS_POOL[⚙️ Process Pool]
        end

        subgraph "⚡ Performance Optimization"
            JIT_COMPILER[⚡ JIT Compiler]
            HOT_FUNCTIONS[🔥 Hot Functions]
            PERF_MONITOR[📊 Performance Monitor]
        end

        subgraph "🔄 Async Optimization"
            ASYNC_OPT[🔄 Async Optimizer]
            TASK_GROUP[👥 Task Groups]
            SEMAPHORE[🚦 Semaphore Control]
        end

        subgraph "💾 Memory Management"
            MEMORY_OPT[💾 Memory Optimizer]
            WEAK_CACHE[🔗 Weak Reference Cache]
            LRU_CACHE[📦 LRU Cache]
        end
    end
```

## 📊 データフロー図

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant F as 🎨 Frontend
    participant A as ⚡ API Gateway
    participant S as 🕷️ Scrapy Service
    participant N as 🟢 Node.js Service
    participant D as 💾 Database
    participant FS as 📁 File System
    participant W as 👷 Worker

    U->>F: Create Spider
    F->>A: POST /api/spiders
    A->>S: Create Spider
    S->>FS: Save Spider File
    S->>D: Save Metadata
    D-->>S: Confirm Save
    S-->>A: Spider Created
    A-->>F: Success Response
    F-->>U: Show Success

    U->>F: Run Spider
    F->>A: POST /api/tasks
    A->>S: Execute Spider
    S->>W: Start Worker Process
    W->>FS: Read Spider Code
    W->>N: Request Browser (if needed)
    N-->>W: Provide Browser
    W->>W: Execute Scraping
    W->>FS: Save Results
    W->>D: Update Task Status
    W-->>S: Task Complete
    S-->>A: Task Status
    A-->>F: Real-time Update (WebSocket)
    F-->>U: Show Progress
```

## 🔌 通信プロトコル

### HTTP/REST API
- **Frontend ↔ Backend**: REST API (JSON)
- **Backend ↔ Node.js**: HTTP API calls
- **External Services**: HTTP/HTTPS

### WebSocket
- **Real-time Updates**: Task progress, logs
- **Live Monitoring**: System metrics
- **Notifications**: Task completion, errors

### Inter-Process Communication
- **Worker Processes**: Subprocess communication
- **Scrapy Integration**: Command-line interface
- **Browser Automation**: Puppeteer API

## 🛡️ セキュリティ層

```mermaid
graph TB
    subgraph "🛡️ Security Architecture"
        subgraph "🔐 Authentication"
            JWT[🎫 JWT Tokens]
            REFRESH[🔄 Refresh Tokens]
            SESSION[📝 Session Management]
        end

        subgraph "👥 Authorization"
            RBAC[👥 Role-based Access Control]
            PERMISSIONS[🔑 Permission System]
            API_KEYS[🔑 API Key Management]
        end

        subgraph "🛡️ Protection"
            RATE_LIMIT[⏱️ Rate Limiting]
            CORS_POLICY[🌍 CORS Policy]
            INPUT_VALIDATION[✅ Input Validation]
            XSS_PROTECTION[🛡️ XSS Protection]
        end
    end
```

## 🚀 デプロイメント構成

```mermaid
graph TB
    subgraph "☁️ Production Environment"
        subgraph "🌐 Load Balancer"
            LB[⚖️ Nginx/HAProxy]
            SSL[🔒 SSL Termination]
        end

        subgraph "🖥️ Application Servers"
            APP1[🎨 Frontend Server 1]
            APP2[🎨 Frontend Server 2]
            API1[⚡ API Server 1]
            API2[⚡ API Server 2]
            NODE1[🟢 Node.js Service 1]
            NODE2[🟢 Node.js Service 2]
        end

        subgraph "👷 Worker Cluster"
            WORKER1[👷 Scrapy Worker 1]
            WORKER2[👷 Scrapy Worker 2]
            WORKER3[👷 Scrapy Worker 3]
            WORKER4[👷 Scrapy Worker 4]
        end

        subgraph "💾 Data Tier"
            DB_PRIMARY[🗄️ Primary Database]
            DB_REPLICA[🗄️ Read Replica]
            REDIS_CLUSTER[🔴 Redis Cluster]
            FILE_STORAGE[📁 Distributed Storage]
        end

        subgraph "📊 Monitoring"
            PROMETHEUS[📊 Prometheus]
            GRAFANA[📈 Grafana]
            ALERTMANAGER[🚨 Alert Manager]
            LOG_AGGREGATOR[📝 Log Aggregator]
        end
    end

    LB --> APP1
    LB --> APP2
    LB --> API1
    LB --> API2

    API1 --> NODE1
    API2 --> NODE2

    API1 --> WORKER1
    API1 --> WORKER2
    API2 --> WORKER3
    API2 --> WORKER4

    API1 --> DB_PRIMARY
    API2 --> DB_REPLICA
    API1 --> REDIS_CLUSTER
    API2 --> REDIS_CLUSTER

    WORKER1 --> FILE_STORAGE
    WORKER2 --> FILE_STORAGE
    WORKER3 --> FILE_STORAGE
    WORKER4 --> FILE_STORAGE
```

## 🔧 技術スタック詳細

### Frontend Stack
```yaml
Framework: Next.js 15
Runtime: React 19
Language: TypeScript
Styling: Tailwind CSS
State Management: Zustand
Data Fetching: React Query
Code Editor: Monaco Editor
Charts: Chart.js
Build Tool: Webpack 5
Package Manager: npm/yarn/pnpm
```

### Backend Stack
```yaml
Framework: FastAPI
Language: Python 3.13
ORM: SQLAlchemy
Migration: Alembic
Authentication: JWT
Validation: Pydantic
ASGI Server: Uvicorn
Task Queue: APScheduler
WebSocket: FastAPI WebSocket
Testing: pytest
```

### Node.js Service Stack
```yaml
Framework: Express.js
Language: Node.js 18+
Browser Automation: Puppeteer
PDF Generation: Puppeteer PDF
Process Management: PM2
Testing: Jest
Documentation: Swagger/OpenAPI
Monitoring: Winston Logger
```

### Database Stack
```yaml
Primary: SQLite (Development)
Production Options:
  - PostgreSQL 15+
  - MySQL 8.0+
  - MongoDB 6.0+
  - Elasticsearch 8.0+
Cache: Redis 7.0+
Search: Elasticsearch (Optional)
```

### Infrastructure Stack
```yaml
Containerization: Docker
Orchestration: Docker Compose / Kubernetes
Reverse Proxy: Nginx
Load Balancer: HAProxy / Nginx
SSL/TLS: Let's Encrypt / Custom Certificates
Monitoring: Prometheus + Grafana
Logging: ELK Stack / Fluentd
CI/CD: GitHub Actions
```

## 📈 スケーラビリティ設計

```mermaid
graph TB
    subgraph "📈 Horizontal Scaling"
        subgraph "🎨 Frontend Scaling"
            FE_LB[⚖️ Frontend Load Balancer]
            FE1[🎨 Frontend Instance 1]
            FE2[🎨 Frontend Instance 2]
            FE3[🎨 Frontend Instance N]
        end

        subgraph "⚡ API Scaling"
            API_LB[⚖️ API Load Balancer]
            API1[⚡ API Instance 1]
            API2[⚡ API Instance 2]
            API3[⚡ API Instance N]
        end

        subgraph "🟢 Node.js Scaling"
            NODE_LB[⚖️ Node.js Load Balancer]
            NODE1[🟢 Node.js Instance 1]
            NODE2[🟢 Node.js Instance 2]
            NODE3[🟢 Node.js Instance N]
        end

        subgraph "👷 Worker Scaling"
            WORKER_QUEUE[📋 Worker Queue]
            WORKER1[👷 Worker Pod 1]
            WORKER2[👷 Worker Pod 2]
            WORKER3[👷 Worker Pod N]
        end
    end

    FE_LB --> FE1
    FE_LB --> FE2
    FE_LB --> FE3

    API_LB --> API1
    API_LB --> API2
    API_LB --> API3

    NODE_LB --> NODE1
    NODE_LB --> NODE2
    NODE_LB --> NODE3

    WORKER_QUEUE --> WORKER1
    WORKER_QUEUE --> WORKER2
    WORKER_QUEUE --> WORKER3
```

## 🔄 CI/CD パイプライン

```mermaid
graph LR
    subgraph "🔄 CI/CD Pipeline"
        CODE[📝 Code Commit]
        BUILD[🔨 Build]
        TEST[🧪 Test]
        SECURITY[🛡️ Security Scan]
        DEPLOY_STAGING[🚀 Deploy to Staging]
        E2E_TEST[🔍 E2E Tests]
        DEPLOY_PROD[🌟 Deploy to Production]
        MONITOR[📊 Monitor]
    end

    CODE --> BUILD
    BUILD --> TEST
    TEST --> SECURITY
    SECURITY --> DEPLOY_STAGING
    DEPLOY_STAGING --> E2E_TEST
    E2E_TEST --> DEPLOY_PROD
    DEPLOY_PROD --> MONITOR
```

## 📊 監視・ログ・メトリクス

```mermaid
graph TB
    subgraph "📊 Observability Stack"
        subgraph "📈 Metrics Collection"
            PROMETHEUS[📊 Prometheus]
            GRAFANA[📈 Grafana Dashboards]
            ALERTMANAGER[🚨 Alert Manager]
        end

        subgraph "📝 Log Management"
            FLUENTD[📝 Fluentd/Fluent Bit]
            ELASTICSEARCH_LOG[🔍 Elasticsearch]
            KIBANA[📊 Kibana]
        end

        subgraph "🔍 Tracing"
            JAEGER[🔍 Jaeger]
            OPENTELEMETRY[📡 OpenTelemetry]
        end

        subgraph "🚨 Alerting"
            SLACK[💬 Slack Notifications]
            EMAIL[📧 Email Alerts]
            PAGERDUTY[📞 PagerDuty]
        end
    end
```

## 🛡️ セキュリティ・コンプライアンス

```mermaid
graph TB
    subgraph "🛡️ Security Layers"
        subgraph "🌐 Network Security"
            WAF[🛡️ Web Application Firewall]
            DDoS[🛡️ DDoS Protection]
            VPN[🔒 VPN Access]
        end

        subgraph "🔐 Application Security"
            AUTH[🔐 Authentication]
            AUTHZ[👥 Authorization]
            ENCRYPTION[🔒 Data Encryption]
            SECRETS[🔑 Secret Management]
        end

        subgraph "📊 Security Monitoring"
            SIEM[🔍 SIEM]
            VULNERABILITY[🔍 Vulnerability Scanning]
            COMPLIANCE[📋 Compliance Monitoring]
        end
    end
```

## 💾 データ管理戦略

```mermaid
graph TB
    subgraph "💾 Data Management"
        subgraph "🗄️ Database Strategy"
            PRIMARY[🗄️ Primary Database]
            REPLICA[🗄️ Read Replicas]
            BACKUP[💾 Automated Backups]
            ARCHIVE[📦 Data Archiving]
        end

        subgraph "📁 File Storage"
            LOCAL[📁 Local Storage]
            S3[☁️ Object Storage]
            CDN[🌐 CDN]
        end

        subgraph "🔄 Data Pipeline"
            ETL[🔄 ETL Processes]
            ANALYTICS[📊 Analytics]
            REPORTING[📋 Reporting]
        end
    end
```

このアーキテクチャにより、ScrapyUIは高度にスケーラブルで保守性の高いWebスクレイピングプラットフォームを実現しています。各コンポーネントは独立してスケールでき、障害時の影響を最小限に抑える設計となっています。
