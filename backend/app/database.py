from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON, ForeignKey, Enum, Boolean, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime
from typing import Optional
import os
import pytz

from .config.database_config import get_database_config, DatabaseType

# タイムゾーン設定
TIMEZONE = pytz.timezone('Asia/Tokyo')

# SQLAlchemyエンジンとセッション
def create_database_engine():
    """データベースエンジンを作成"""
    # データベース設定を動的に取得
    db_config = get_database_config()

    if db_config.type in [DatabaseType.SQLITE, DatabaseType.MYSQL, DatabaseType.POSTGRESQL]:
        connection_url = db_config.get_connection_url()

        engine_kwargs = {
            "echo": db_config.echo,
        }

        # SQLite固有設定（高負荷対応）
        if db_config.type == DatabaseType.SQLITE:
            engine_kwargs["connect_args"] = {
                "check_same_thread": False,
                "timeout": 30,  # 30秒のタイムアウト
                "isolation_level": None,  # autocommitモード
            }
            # SQLite用のプール設定
            engine_kwargs.update({
                "pool_size": 20,  # 接続プールサイズを増加
                "max_overflow": 30,  # オーバーフロー接続数を増加
                "pool_timeout": 30,  # プールタイムアウト
                "pool_recycle": 3600,  # 1時間で接続をリサイクル
                "pool_pre_ping": True,  # 接続の事前チェック
            })
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
    USER = "USER"
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"

# Models
class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text)
    path = Column(String(500), unique=True, nullable=False)
    scrapy_version = Column(String(50), default="2.11.0")
    settings = Column(JSON)
    is_active = Column(Boolean, default=True)  # is_activeフィールドを追加
    db_save_enabled = Column(Boolean, default=True, nullable=False)  # 結果をDBに保存するかどうか
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign Keys
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

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

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    code = Column(Text, nullable=False)
    template = Column(String(100))
    framework = Column(String(50))
    start_urls = Column(JSON)
    settings = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign Keys
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="spiders")
    user = relationship("User")
    tasks = relationship("Task", back_populates="spider", cascade="all, delete-orphan")

class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # ファイル名 (settings.py, items.py, etc.)
    path = Column(String(500), nullable=False)  # ファイルパス (project_name/settings.py)
    content = Column(Text, nullable=False)  # ファイル内容
    file_type = Column(String(50), default="python")  # ファイルタイプ (python, config, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign Keys
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="project_files")
    user = relationship("User")

    # プロジェクト内でのファイルパス一意制約
    __table_args__ = (
        UniqueConstraint('path', 'project_id', name='unique_file_path_per_project'),
    )

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, index=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    items_count = Column(Integer, default=0)
    requests_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    log_level = Column(String(20), default="INFO")
    settings = Column(JSON)
    celery_task_id = Column(String(255), nullable=True)  # CeleryタスクIDとの関連付け
    error_message = Column(String(2000), nullable=True)  # エラーメッセージフィールドを追加
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign Keys
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    spider_id = Column(String(36), ForeignKey("spiders.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    schedule_id = Column(String(36), ForeignKey("schedules.id"), nullable=True)  # スケジュール実行の場合のみ

    # Relationships
    project = relationship("Project", back_populates="tasks")
    spider = relationship("Spider", back_populates="tasks")
    user = relationship("User")
    schedule = relationship("Schedule")
    results = relationship("Result", back_populates="task", cascade="all, delete-orphan")
    logs = relationship("Log", back_populates="task", cascade="all, delete-orphan")

class Result(Base):
    __tablename__ = "results"

    id = Column(String(36), primary_key=True, index=True)
    data = Column(JSON, nullable=False)
    url = Column(String(2000))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    crawl_start_datetime = Column(DateTime(timezone=True), nullable=True)  # クロールスタート日時
    item_acquired_datetime = Column(DateTime(timezone=True), nullable=True)  # アイテム取得日時

    # データの重複を防ぐためのハッシュ値
    data_hash = Column(String(64), nullable=True, index=True)

    # Foreign Keys
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)

    # Relationships
    task = relationship("Task", back_populates="results")

    # インデックス（パフォーマンス向上のため）
    __table_args__ = (
        Index('idx_task_data_hash', 'task_id', 'data_hash'),
    )

class Log(Base):
    __tablename__ = "logs"

    id = Column(String(36), primary_key=True, index=True)
    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Foreign Keys
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)

    # Relationships
    task = relationship("Task", back_populates="logs")

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    cron_expression = Column(String(100), nullable=False)  # Cron式
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime(timezone=True))
    next_run = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign Keys
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    spider_id = Column(String(36), ForeignKey("spiders.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)  # user_idを追加

    # Settings for the scheduled run
    settings = Column(JSON)

    # Relationships
    project = relationship("Project")
    spider = relationship("Spider")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(20), nullable=False)  # info, warning, error, success
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Optional: link to specific task or project
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    task = relationship("Task")
    project = relationship("Project")
    user = relationship("User")

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Profile information
    avatar_url = Column(String(500), nullable=True)
    timezone = Column(String(50), default="UTC")
    preferences = Column(JSON, default={})

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    refresh_token = Column(String(500), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Session metadata
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Relationships
    user = relationship("User")

class Proxy(Base):
    __tablename__ = "proxies"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(100), nullable=True)
    password = Column(String(255), nullable=True)
    proxy_type = Column(String(20), default="http")  # http, https, socks4, socks5
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Performance metrics
    success_rate = Column(Integer, default=0)  # Percentage
    avg_response_time = Column(Integer, default=0)  # Milliseconds
    last_used = Column(DateTime(timezone=True), nullable=True)
    failure_count = Column(Integer, default=0)

    # User association
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    user = relationship("User")
