# 📚 ScrapyUI API Documentation

## 🌐 Base URL

```
http://localhost:8000/api
```

## 🔐 Authentication

ScrapyUI uses JWT (JSON Web Token) for authentication.

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "admin@scrapyui.com",
  "password": "admin123456"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user-id",
    "email": "admin@scrapyui.com",
    "role": "admin"
  }
}
```

### Using the Token
Include the token in the Authorization header:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## 📁 Projects API

### List Projects
```http
GET /projects
Authorization: Bearer {token}
```

**Response:**
```json
{
  "projects": [
    {
      "id": "project-id",
      "name": "My Project",
      "description": "Project description",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "spider_count": 5,
      "task_count": 10
    }
  ]
}
```

### Create Project
```http
POST /projects
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "New Project",
  "description": "Project description"
}
```

### Get Project
```http
GET /projects/{project_id}
Authorization: Bearer {token}
```

### Update Project
```http
PUT /projects/{project_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Updated Project",
  "description": "Updated description"
}
```

### Delete Project
```http
DELETE /projects/{project_id}
Authorization: Bearer {token}
```

## 🕷️ Spiders API

### List Spiders
```http
GET /spiders?project_id={project_id}
Authorization: Bearer {token}
```

### Create Spider
```http
POST /spiders
Authorization: Bearer {token}
Content-Type: application/json

{
  "project_id": "project-id",
  "name": "my_spider",
  "code": "import scrapy\n\nclass MySpider(scrapy.Spider):\n    name = 'my_spider'\n    start_urls = ['https://example.com']\n    \n    def parse(self, response):\n        yield {'title': response.css('title::text').get()}"
}
```

### Get Spider
```http
GET /spiders/{spider_id}
Authorization: Bearer {token}
```

### Update Spider
```http
PUT /spiders/{spider_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "updated_spider",
  "code": "# Updated spider code"
}
```

### Delete Spider
```http
DELETE /spiders/{spider_id}
Authorization: Bearer {token}
```

## 🚀 Tasks API

### List Tasks
```http
GET /tasks?project_id={project_id}
Authorization: Bearer {token}
```

### Create Task (Run Spider)
```http
POST /tasks
Authorization: Bearer {token}
Content-Type: application/json

{
  "project_id": "project-id",
  "spider_id": "spider-id",
  "settings": {
    "DOWNLOAD_DELAY": 1,
    "CONCURRENT_REQUESTS": 16
  }
}
```

### Get Task
```http
GET /tasks/{task_id}
Authorization: Bearer {token}
```

### Stop Task
```http
POST /tasks/{task_id}/stop
Authorization: Bearer {token}
```

## 📊 Results API

### Get Task Results
```http
GET /tasks/{task_id}/results
Authorization: Bearer {token}
```

### Export Results
```http
GET /tasks/{task_id}/export?format={json|csv|excel|xml}
Authorization: Bearer {token}
```

## 🔧 Templates API

### List Templates
```http
GET /templates
Authorization: Bearer {token}
```

### Get Template
```http
GET /templates/{template_id}
Authorization: Bearer {token}
```

## 📈 Analytics API

### Get Dashboard Stats
```http
GET /analytics/dashboard
Authorization: Bearer {token}
```

### Get Performance Metrics
```http
GET /analytics/performance?project_id={project_id}&days={days}
Authorization: Bearer {token}
```

## 🌐 WebSocket API

### Task Monitoring
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/monitor_{user_id}');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Task update:', data);
};
```

**Message Format:**
```json
{
  "type": "task_update",
  "task_id": "task-id",
  "status": "running",
  "progress": 45,
  "items_count": 100,
  "requests_count": 150
}
```

## 🚨 Error Handling

All API endpoints return standard HTTP status codes:

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

**Error Response Format:**
```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 📝 Rate Limiting

API requests are rate limited:
- **Authenticated users**: 1000 requests per hour
- **Anonymous users**: 100 requests per hour

Rate limit headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## 🔍 Pagination

List endpoints support pagination:

```http
GET /projects?page=1&size=20
```

**Response:**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

## 📋 OpenAPI Specification

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
