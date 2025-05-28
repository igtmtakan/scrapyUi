"""
Admin API endpoints for user management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db, User, UserRole
from ..models.schemas import UserListResponse, UserAdminUpdate, UserAdminCreate, UserResponse
from .auth import get_current_active_user
from ..auth.jwt_handler import PasswordHandler
import uuid

router = APIRouter(prefix="/api/admin", tags=["admin"])

def require_admin_role(current_user: User = Depends(get_current_active_user)):
    """管理者権限を要求するデコレータ"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    return current_user

@router.get("/users", response_model=List[UserListResponse])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    role: Optional[UserRole] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """
    全ユーザーの一覧を取得（管理者のみ）
    """
    query = db.query(User)

    # 検索フィルター
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (User.email.ilike(search_filter)) |
            (User.username.ilike(search_filter)) |
            (User.full_name.ilike(search_filter))
        )

    # ロールフィルター
    if role:
        query = query.filter(User.role == role)

    # アクティブ状態フィルター
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    # ページネーション
    users = query.offset(skip).limit(limit).all()

    return users

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """
    指定されたユーザーの詳細情報を取得（管理者のみ）
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )

    return user

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_create: UserAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """
    新しいユーザーを作成（管理者のみ）
    """
    # メールアドレスの重複チェック
    existing_user = db.query(User).filter(User.email == user_create.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスは既に使用されています"
        )

    # ユーザー名の重複チェック
    existing_username = db.query(User).filter(User.username == user_create.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このユーザー名は既に使用されています"
        )

    # ロールを文字列からUserRoleに変換
    role_mapping = {
        "user": UserRole.USER,
        "admin": UserRole.ADMIN,
        "moderator": UserRole.MODERATOR
    }
    user_role = role_mapping.get(user_create.role, UserRole.USER)

    # 新しいユーザーを作成
    new_user = User(
        id=str(uuid.uuid4()),
        email=user_create.email,
        username=user_create.username,
        full_name=user_create.full_name,
        hashed_password=PasswordHandler.hash_password(user_create.password),
        is_active=user_create.is_active,
        is_superuser=user_create.is_superuser,
        role=user_role,
        avatar_url=user_create.avatar_url,
        timezone=user_create.timezone,
        preferences=user_create.preferences or {}
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """
    ユーザー情報を更新（管理者のみ）
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )

    # ロール変換の準備
    role_mapping = {
        "user": UserRole.USER,
        "admin": UserRole.ADMIN,
        "moderator": UserRole.MODERATOR
    }

    # 自分自身の管理者権限を削除することを防ぐ
    if user.id == current_user.id and user_update.role and user_update.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="自分自身の管理者権限を削除することはできません"
        )

    # 更新可能なフィールドを更新
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "role" and value is not None:
            # ロールを文字列からUserRoleに変換
            setattr(user, field, role_mapping.get(value, UserRole.USER))
        else:
            setattr(user, field, value)

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """
    ユーザーを削除（管理者のみ）
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )

    # 自分自身を削除することを防ぐ
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="自分自身を削除することはできません"
        )

    db.delete(user)
    db.commit()

    return {"message": "ユーザーが正常に削除されました"}

@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """
    ユーザーをアクティブ化（管理者のみ）
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )

    user.is_active = True
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "ユーザーがアクティブ化されました"}

@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """
    ユーザーを非アクティブ化（管理者のみ）
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )

    # 自分自身を非アクティブ化することを防ぐ
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="自分自身を非アクティブ化することはできません"
        )

    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "ユーザーが非アクティブ化されました"}

@router.get("/stats/users")
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """
    ユーザー統計情報を取得（管理者のみ）
    """
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_users = db.query(User).filter(User.role == UserRole.ADMIN).count()
    moderator_users = db.query(User).filter(User.role == UserRole.MODERATOR).count()
    regular_users = db.query(User).filter(User.role == UserRole.USER).count()

    # 最近のユーザー登録（過去30日）
    from datetime import timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_registrations = db.query(User).filter(
        User.created_at >= thirty_days_ago
    ).count()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "admin_users": admin_users,
        "moderator_users": moderator_users,
        "regular_users": regular_users,
        "recent_registrations": recent_registrations
    }

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """
    ユーザーのパスワードをリセット（管理者のみ）
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )

    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="パスワードは8文字以上である必要があります"
        )

    user.hashed_password = PasswordHandler.hash_password(new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "パスワードが正常にリセットされました"}
