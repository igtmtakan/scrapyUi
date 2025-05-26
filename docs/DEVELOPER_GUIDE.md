# 🛠️ ScrapyUI Developer Guide

## 🏗️ Architecture Overview

ScrapyUI follows a modern microservices architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │  Node.js Service│
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Puppeteer)   │
│   Port: 4000    │    │   Port: 8000    │    │   Port: 3001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Static Files  │    │    Database     │    │   Browser Pool  │
│   (CDN/Nginx)   │    │   (SQLite/PG)   │    │   (Chromium)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Development Setup

### Prerequisites

- **Python 3.8+** with pip and virtualenv
- **Node.js 18+** with npm
- **Git** for version control
- **Docker** (optional)

### Local Development

#### 1. Clone Repository
```bash
git clone https://github.com/igtmtakan/scrapyUi.git
cd scrapyUi
```

#### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Set up environment
cp .env.example .env

# Initialize database
python scripts/init_database.py

# Run migrations
alembic upgrade head

# Create admin user
python create_admin.py

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env.local

# Start development server
npm run dev
```

#### 4. Node.js Service Setup
```bash
cd nodejs-service

# Install dependencies
npm install

# Set up environment
cp .env.example .env

# Start development server
npm run dev
```

## 🏗️ Backend Development

### Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   ├── auth/             # Authentication
│   ├── models/           # Database models
│   ├── services/         # Business logic
│   ├── utils/            # Utilities
│   ├── websocket/        # WebSocket handlers
│   └── main.py           # FastAPI app
├── tests/                # Test suite
├── scripts/              # Utility scripts
└── requirements.txt      # Dependencies
```

### Adding New API Endpoints

1. **Create endpoint file**:
```python
# app/api/new_feature.py
from fastapi import APIRouter, Depends
from app.auth.jwt_handler import get_current_user

router = APIRouter(prefix="/new-feature", tags=["new-feature"])

@router.get("/")
async def get_items(current_user = Depends(get_current_user)):
    return {"items": []}

@router.post("/")
async def create_item(item_data: dict, current_user = Depends(get_current_user)):
    return {"id": "new-item-id"}
```

2. **Register router**:
```python
# app/main.py
from app.api.new_feature import router as new_feature_router

app.include_router(new_feature_router, prefix="/api")
```

### Database Models

Using SQLAlchemy ORM:

```python
# app/models/new_model.py
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class NewModel(Base):
    __tablename__ = "new_models"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_id = Column(String, ForeignKey("users.id"))
    user = relationship("User", back_populates="new_models")
```

### Services Layer

Business logic separation:

```python
# app/services/new_service.py
from typing import List, Optional
from app.models.new_model import NewModel
from app.database import get_db

class NewService:
    def __init__(self, db_session):
        self.db = db_session
    
    async def create_item(self, data: dict) -> NewModel:
        item = NewModel(**data)
        self.db.add(item)
        self.db.commit()
        return item
    
    async def get_items(self, user_id: str) -> List[NewModel]:
        return self.db.query(NewModel).filter(
            NewModel.user_id == user_id
        ).all()
```

### Testing

```python
# tests/test_new_feature.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_item():
    response = client.post(
        "/api/new-feature/",
        json={"name": "Test Item"},
        headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code == 200
    assert response.json()["id"] is not None
```

## 🎨 Frontend Development

### Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js app router
│   ├── components/       # React components
│   ├── hooks/            # Custom hooks
│   ├── services/         # API services
│   ├── stores/           # State management
│   └── utils/            # Utilities
├── public/               # Static assets
└── package.json          # Dependencies
```

### Creating Components

```tsx
// src/components/NewComponent.tsx
import React from 'react';
import { Button } from '@/components/ui/button';

interface NewComponentProps {
  title: string;
  onAction: () => void;
}

export const NewComponent: React.FC<NewComponentProps> = ({
  title,
  onAction
}) => {
  return (
    <div className="p-4 border rounded-lg">
      <h3 className="text-lg font-semibold">{title}</h3>
      <Button onClick={onAction} className="mt-2">
        Action
      </Button>
    </div>
  );
};
```

### API Integration

```tsx
// src/services/newService.ts
import { api } from './api';

export interface NewItem {
  id: string;
  name: string;
  created_at: string;
}

export const newService = {
  async getItems(): Promise<NewItem[]> {
    const response = await api.get('/new-feature/');
    return response.data.items;
  },

  async createItem(data: { name: string }): Promise<NewItem> {
    const response = await api.post('/new-feature/', data);
    return response.data;
  }
};
```

### State Management

Using Zustand:

```tsx
// src/stores/newStore.ts
import { create } from 'zustand';
import { NewItem, newService } from '@/services/newService';

interface NewStore {
  items: NewItem[];
  loading: boolean;
  fetchItems: () => Promise<void>;
  createItem: (data: { name: string }) => Promise<void>;
}

export const useNewStore = create<NewStore>((set, get) => ({
  items: [],
  loading: false,

  fetchItems: async () => {
    set({ loading: true });
    try {
      const items = await newService.getItems();
      set({ items, loading: false });
    } catch (error) {
      set({ loading: false });
      throw error;
    }
  },

  createItem: async (data) => {
    const newItem = await newService.createItem(data);
    set(state => ({
      items: [...state.items, newItem]
    }));
  }
}));
```

## 🌐 Node.js Service Development

### Project Structure

```
nodejs-service/
├── src/
│   ├── routes/           # Express routes
│   ├── services/         # Business logic
│   ├── middleware/       # Express middleware
│   └── utils/            # Utilities
├── tests/                # Test suite
└── package.json          # Dependencies
```

### Adding New Routes

```javascript
// src/routes/newFeature.js
const express = require('express');
const { NewFeatureService } = require('../services/NewFeatureService');

const router = express.Router();
const newFeatureService = new NewFeatureService();

router.post('/process', async (req, res) => {
  try {
    const result = await newFeatureService.processData(req.body);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
```

### Puppeteer Integration

```javascript
// src/services/NewFeatureService.js
const puppeteer = require('puppeteer');

class NewFeatureService {
  constructor() {
    this.browser = null;
  }

  async initBrowser() {
    if (!this.browser) {
      this.browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      });
    }
    return this.browser;
  }

  async processData(data) {
    const browser = await this.initBrowser();
    const page = await browser.newPage();
    
    try {
      await page.goto(data.url);
      await page.waitForSelector(data.selector);
      
      const result = await page.evaluate((sel) => {
        return document.querySelector(sel).textContent;
      }, data.selector);
      
      return result;
    } finally {
      await page.close();
    }
  }
}

module.exports = { NewFeatureService };
```

## 🧪 Testing Strategy

### Backend Testing

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

### Frontend Testing

```tsx
// src/__tests__/components/NewComponent.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { NewComponent } from '@/components/NewComponent';

describe('NewComponent', () => {
  it('renders title correctly', () => {
    const mockAction = jest.fn();
    render(<NewComponent title="Test Title" onAction={mockAction} />);
    
    expect(screen.getByText('Test Title')).toBeInTheDocument();
  });

  it('calls onAction when button is clicked', () => {
    const mockAction = jest.fn();
    render(<NewComponent title="Test" onAction={mockAction} />);
    
    fireEvent.click(screen.getByText('Action'));
    expect(mockAction).toHaveBeenCalledTimes(1);
  });
});
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Configuration

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/scrapyui
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=https://api.scrapyui.com

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=scrapyui
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass

  redis:
    image: redis:7-alpine
```

## 📊 Monitoring & Logging

### Application Monitoring

```python
# app/middleware/monitoring.py
import time
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"{response.status_code} - {process_time:.3f}s"
    )
    
    return response
```

### Performance Metrics

```python
# app/utils/metrics.py
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')

def track_request(method: str, endpoint: str, duration: float):
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    REQUEST_DURATION.observe(duration)
```

## 🔧 Contributing Guidelines

### Code Style

- **Python**: Follow PEP 8, use Black formatter
- **TypeScript**: Follow ESLint rules, use Prettier
- **JavaScript**: Follow ESLint rules, use Prettier

### Commit Messages

Follow conventional commits:
```
feat: add new spider template
fix: resolve authentication issue
docs: update API documentation
test: add unit tests for spider service
```

### Pull Request Process

1. Fork the repository
2. Create feature branch
3. Write tests
4. Update documentation
5. Submit pull request
6. Address review feedback

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push to fork
git push origin feature/new-feature

# Create pull request on GitHub
```
