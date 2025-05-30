from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON, ForeignKey, Enum, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime
from typing import Optional
import os

from .config.database_config import get_database_config, DatabaseType

# データベース設定を取得
db_config = get_database_config()

# SQLAlchemyエンジンとセッション
def create_database_engine():
    """データベースエンジンを作成"""
    if db_config.type in [DatabaseType.SQLITE, DatabaseType.MYSQL, DatabaseType.POSTGRESQL]:
        connection_url = db_config.get_connection_url()

        engine_kwargs = {
            "echo": db_config.echo,
        }

        # SQLite固有設定
        if db_config.type == DatabaseType.SQLITE:
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            # MySQL/PostgreSQL用のプール設定
            engine_kwargs.update({
                "pool_size": db_config.pool_size,
                "max_overflow": db_config.max_overflow
            })

        return create_engine(connection_url, **engine_kwargs)
    else:
        raise ValueError(f"Unsupported database type for SQLAlchemy: {db_config.type}")

# エンジンとセッションを初期化
engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Enums
class TaskStatus(enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

# Models
class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    path = Column(String, unique=True, nullable=False)
    scrapy_version = Column(String, default="2.11.0")
    settings = Column(JSON)
    is_active = Column(Boolean, default=True)  # is_activeフィールドを追加
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign Keys
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User")
    spiders = relationship("Spider", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    project_files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")

    # ユーザー別のプロジェクト名一意制約
    __table_args__ = (
        UniqueConstraint('name', 'user_id', name='unique_project_name_per_user'),
    )

class Spider(Base):
    __tablename__ = "spiders"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    code = Column(Text, nullable=False)
    template = Column(String)
    framework = Column(String)
    start_urls = Column(JSON)
    settings = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign Keys
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="spiders")
    user = relationship("User")
    tasks = relationship("Task", back_populates="spider", cascade="all, delete-orphan")

class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)  # ファイル名 (settings.py, items.py, etc.)
    path = Column(String, nullable=False)  # ファイルパス (project_name/settings.py)
    content = Column(Text, nullable=False)  # ファイル内容
    file_type = Column(String, default="python")  # ファイルタイプ (python, config, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign Keys
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="project_files")
    user = relationship("User")

    # プロジェクト内でのファイルパス一意制約
    __table_args__ = (
        UniqueConstraint('path', 'project_id', name='unique_file_path_per_project'),
    )

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    items_count = Column(Integer, default=0)
    requests_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    log_level = Column(String, default="INFO")
    settings = Column(JSON)
    celery_task_id = Column(String, nullable=True)  # CeleryタスクIDとの関連付け
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign Keys
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    spider_id = Column(String, ForeignKey("spiders.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="tasks")
    spider = relationship("Spider", back_populates="tasks")
    user = relationship("User")
    results = relationship("Result", back_populates="task", cascade="all, delete-orphan")
    logs = relationship("Log", back_populates="task", cascade="all, delete-orphan")

class Result(Base):
    __tablename__ = "results"

    id = Column(String, primary_key=True, index=True)
    data = Column(JSON, nullable=False)
    url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Foreign Keys
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)

    # Relationships
    task = relationship("Task", back_populates="results")

class Log(Base):
    __tablename__ = "logs"

    id = Column(String, primary_key=True, index=True)
    level = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Foreign Keys
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)

    # Relationships
    task = relationship("Task", back_populates="logs")

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    cron_expression = Column(String, nullable=False)  # Cron式
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime(timezone=True))
    next_run = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign Keys
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    spider_id = Column(String, ForeignKey("spiders.id"), nullable=False)

    # Settings for the scheduled run
    settings = Column(JSON)

    # Relationships
    project = relationship("Project")
    spider = relationship("Spider")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, nullable=False)  # info, warning, error, success
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Optional: link to specific task or project
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)

    # Relationships
    task = relationship("Task")
    project = relationship("Project")
    user = relationship("User")

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Profile information
    avatar_url = Column(String, nullable=True)
    timezone = Column(String, default="UTC")
    preferences = Column(JSON, default={})

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    refresh_token = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Session metadata
    user_agent = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)

    # Relationships
    user = relationship("User")

class Proxy(Base):
    __tablename__ = "proxies"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    proxy_type = Column(String, default="http")  # http, https, socks4, socks5
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Performance metrics
    success_rate = Column(Integer, default=0)  # Percentage
    avg_response_time = Column(Integer, default=0)  # Milliseconds
    last_used = Column(DateTime(timezone=True), nullable=True)
    failure_count = Column(Integer, default=0)

    # User association
    user_id = Column(String, ForeignKey("users.id"), nullable=True)

    # Relationships
    user = relationship("User")
