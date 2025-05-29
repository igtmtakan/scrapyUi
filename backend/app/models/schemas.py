from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import re

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

# Project schemas
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    scrapy_version: Optional[str] = "2.11.0"
    settings: Optional[Dict[str, Any]] = None

class ProjectCreate(ProjectBase):
    path: Optional[str] = None  # パスはオプション、自動生成される

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    scrapy_version: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class Project(ProjectBase):
    id: str
    path: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProjectWithUser(ProjectBase):
    id: str
    path: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: str
    username: Optional[str] = None  # ユーザー名を追加
    is_active: bool = True  # is_activeフィールドを追加

    class Config:
        from_attributes = True

# Spider schemas
class SpiderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    code: str = Field(..., min_length=1)
    template: Optional[str] = None
    framework: Optional[str] = None
    start_urls: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None

    @field_validator('name')
    @classmethod
    def validate_spider_name(cls, v):
        """スパイダー名のバリデーション"""
        # 英数字、アンダースコア、ハイフンのみ許可
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Spider name can only contain letters, numbers, underscores, and hyphens')

        # 先頭は英字またはアンダースコア
        if not re.match(r'^[a-zA-Z_]', v):
            raise ValueError('Spider name must start with a letter or underscore')

        # 予約語チェック
        reserved_words = ['scrapy', 'spider', 'item', 'pipeline', 'middleware', 'settings']
        if v.lower() in reserved_words:
            raise ValueError(f'Spider name cannot be a reserved word: {", ".join(reserved_words)}')

        return v

class SpiderCreate(SpiderBase):
    project_id: str

class SpiderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    code: Optional[str] = Field(None, min_length=1)
    template: Optional[str] = None
    framework: Optional[str] = None
    start_urls: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None

class Spider(SpiderBase):
    id: str
    project_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Task schemas
class TaskBase(BaseModel):
    log_level: str = "INFO"
    settings: Optional[Dict[str, Any]] = None

class TaskCreate(TaskBase):
    project_id: str
    spider_id: str

class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    items_count: Optional[int] = None
    requests_count: Optional[int] = None
    error_count: Optional[int] = None

class Task(TaskBase):
    id: str
    status: TaskStatus
    project_id: str
    spider_id: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    items_count: int = 0
    requests_count: int = 0
    error_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Result schemas
class ResultBase(BaseModel):
    data: Dict[str, Any]
    url: Optional[str] = None

class ResultCreate(ResultBase):
    task_id: str

class Result(ResultBase):
    id: str
    task_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Log schemas
class LogBase(BaseModel):
    level: str
    message: str

class LogCreate(LogBase):
    task_id: str

class Log(LogBase):
    id: str
    task_id: str
    timestamp: datetime

    class Config:
        from_attributes = True

# Schedule schemas
class ScheduleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    cron_expression: str = Field(..., min_length=1)
    is_active: bool = True
    settings: Optional[Dict[str, Any]] = None

class ScheduleCreate(ScheduleBase):
    project_id: str
    spider_id: str

class ScheduleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    cron_expression: Optional[str] = Field(None, min_length=1)
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None

class Schedule(ScheduleBase):
    id: str
    project_id: str
    spider_id: str
    project_name: Optional[str] = None
    spider_name: Optional[str] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Notification schemas
class NotificationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    type: str = Field(..., pattern="^(info|warning|error|success)$")

class NotificationCreate(NotificationBase):
    task_id: Optional[str] = None
    project_id: Optional[str] = None

class Notification(NotificationBase):
    id: str
    is_read: bool = False
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Response schemas
class ProjectWithSpiders(Project):
    spiders: List[Spider] = []

class TaskWithDetails(Task):
    project: Project
    spider: Spider
    results_count: int = 0
    logs_count: int = 0

class ScheduleWithDetails(Schedule):
    project: Project
    spider: Spider

# User authentication schemas
class UserBase(BaseModel):
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9]+$')
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=1)

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class UserResponse(UserBase):
    id: str
    is_active: bool
    is_superuser: bool
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None
    timezone: str = "UTC"
    preferences: Dict[str, Any] = {}

    class Config:
        from_attributes = True

# Admin user management schemas
class UserAdminCreate(BaseModel):
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9]+$')
    full_name: Optional[str] = None
    password: str = Field(..., min_length=8)
    role: Optional[str] = "user"  # 文字列として受け取り、後でUserRoleに変換
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    avatar_url: Optional[str] = None
    timezone: Optional[str] = "UTC"
    preferences: Optional[Dict[str, Any]] = {}

class UserAdminUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role: Optional[str] = None  # 文字列として受け取り、後でUserRoleに変換
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class UserListResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True



class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Proxy schemas
class ProxyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    host: str = Field(..., min_length=1)
    port: int = Field(..., ge=1, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: str = Field(default="http", pattern="^(http|https|socks4|socks5)$")

class ProxyCreate(ProxyBase):
    pass

class ProxyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    host: Optional[str] = Field(None, min_length=1)
    port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: Optional[str] = Field(None, pattern="^(http|https|socks4|socks5)$")
    is_active: Optional[bool] = None

class Proxy(ProxyBase):
    id: str
    is_active: bool
    success_rate: int = 0
    avg_response_time: int = 0
    last_used: Optional[datetime] = None
    failure_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Project Files
class ProjectFileBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    path: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=0)
    file_type: Optional[str] = "python"

class ProjectFileCreate(ProjectFileBase):
    pass

class ProjectFileUpdate(BaseModel):
    content: str = Field(..., min_length=0)

class ProjectFileResponse(ProjectFileBase):
    id: str
    project_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    size: Optional[int] = None
    modified_at: Optional[float] = None

    class Config:
        from_attributes = True

class ProjectFile(ProjectFileBase):
    id: str
    project_id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# 拡張機能用スキーマ
# =============================================================================

class GitCommitRequest(BaseModel):
    message: str
    author: Optional[str] = "ScrapyUI"


class GitBranchRequest(BaseModel):
    name: str


class TemplateCreateRequest(BaseModel):
    name: str
    description: str
    type: str  # spider, middleware, pipeline, item
    content: str
    tags: Optional[List[str]] = []
    category: Optional[str] = "custom"


class TemplateUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class TemplateRenderRequest(BaseModel):
    variables: Dict[str, str]


class ConfigValidationRequest(BaseModel):
    content: str


class ValidationResult(BaseModel):
    level: str  # error, warning, info, success
    message: str
    line_number: Optional[int] = None
    setting_name: Optional[str] = None
    suggestion: Optional[str] = None


class OptimizationReport(BaseModel):
    performance_score: int
    security_score: int
    compatibility_score: int
    recommendations: List[str]
    summary: Dict[str, Any]