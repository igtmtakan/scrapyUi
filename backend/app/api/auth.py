from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import uuid

from ..database import get_db, User as DBUser, UserSession as DBUserSession
from ..models.schemas import UserCreate, UserLogin, UserResponse, Token
from ..auth.jwt_handler import JWTHandler, PasswordHandler, create_tokens

router = APIRouter(
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not found"},
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"}
    }
)

security = HTTPBearer()

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ユーザー登録",
    description="新しいユーザーアカウントを作成します。"
)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    ## ユーザー登録

    新しいユーザーアカウントを作成します。

    ### リクエストボディ
    - **email**: メールアドレス（一意）
    - **username**: ユーザー名（一意）
    - **password**: パスワード（8文字以上）
    - **full_name** (optional): フルネーム

    ### レスポンス
    - **201**: ユーザーが正常に作成された場合
    - **400**: リクエストデータが不正、またはユーザーが既に存在する場合
    - **500**: サーバーエラー
    """

    # メールアドレスの重複チェック
    existing_user = db.query(DBUser).filter(DBUser.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # ユーザー名の重複チェック
    existing_username = db.query(DBUser).filter(DBUser.username == user.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # パスワードのハッシュ化
    hashed_password = PasswordHandler.hash_password(user.password)

    # ユーザー作成
    db_user = DBUser(
        id=str(uuid.uuid4()),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_superuser=False  # 最初のユーザーのみスーパーユーザーにする場合は別途処理
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@router.post(
    "/login",
    response_model=Token,
    summary="ログイン",
    description="ユーザーログインを行い、アクセストークンを取得します。"
)
async def login(
    user_login: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    ## ログイン

    ユーザーログインを行い、アクセストークンとリフレッシュトークンを取得します。

    ### リクエストボディ
    - **email**: メールアドレス
    - **password**: パスワード

    ### レスポンス
    - **200**: ログイン成功時にトークンを返します
    - **401**: 認証情報が不正な場合
    - **500**: サーバーエラー
    """

    # ユーザー検索
    user = db.query(DBUser).filter(DBUser.email == user_login.email).first()
    if not user or not PasswordHandler.verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )

    # トークン生成
    tokens = create_tokens({"id": user.id, "email": user.email})

    # セッション作成
    session = DBUserSession(
        id=str(uuid.uuid4()),
        user_id=user.id,
        refresh_token=tokens["refresh_token"],
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None
    )

    db.add(session)

    # 最終ログイン時刻を更新
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    return tokens

@router.post(
    "/refresh",
    response_model=Token,
    summary="トークンリフレッシュ",
    description="リフレッシュトークンを使用して新しいアクセストークンを取得します。"
)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    ## トークンリフレッシュ

    リフレッシュトークンを使用して新しいアクセストークンを取得します。

    ### ヘッダー
    - **Authorization**: Bearer {refresh_token}

    ### レスポンス
    - **200**: 新しいトークンを返します
    - **401**: リフレッシュトークンが無効な場合
    - **500**: サーバーエラー
    """

    refresh_token = credentials.credentials

    # トークン検証
    payload = JWTHandler.verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # セッション確認
    session = db.query(DBUserSession).filter(
        DBUserSession.refresh_token == refresh_token,
        DBUserSession.is_active == True
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or expired"
        )

    # ユーザー取得
    user = db.query(DBUser).filter(DBUser.id == session.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled"
        )

    # 新しいトークン生成
    tokens = create_tokens({"id": user.id, "email": user.email})

    # セッション更新
    session.refresh_token = tokens["refresh_token"]
    session.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    db.commit()

    return tokens

@router.post(
    "/logout",
    summary="ログアウト",
    description="現在のセッションを無効化します。"
)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    ## ログアウト

    現在のセッションを無効化します。

    ### ヘッダー
    - **Authorization**: Bearer {access_token}

    ### レスポンス
    - **200**: ログアウト成功
    - **401**: トークンが無効な場合
    - **500**: サーバーエラー
    """

    try:
        token = credentials.credentials

        # トークン検証
        payload = JWTHandler.verify_token(token)
        if not payload:
            # トークンが無効でもログアウト成功として扱う
            return {"message": "Successfully logged out"}

        # アクセストークンかどうか確認
        if payload.get("type") != "access":
            # 無効なトークンタイプでもログアウト成功として扱う
            return {"message": "Successfully logged out"}

        user_id = payload.get("user_id")
        if user_id:
            # アクティブなセッションを無効化
            db.query(DBUserSession).filter(
                DBUserSession.user_id == user_id,
                DBUserSession.is_active == True
            ).update({"is_active": False})

            db.commit()

        return {"message": "Successfully logged out"}

    except Exception as e:
        # ログアウト処理でエラーが発生してもログアウト成功として扱う
        print(f"Logout error (ignored): {e}")
        return {"message": "Successfully logged out"}

@router.get(
    "/me",
    response_model=UserResponse,
    summary="現在のユーザー情報取得",
    description="認証されたユーザーの情報を取得します。"
)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    ## 現在のユーザー情報取得

    認証されたユーザーの情報を取得します。

    ### ヘッダー
    - **Authorization**: Bearer {access_token}

    ### レスポンス
    - **200**: ユーザー情報を返します
    - **401**: トークンが無効な場合
    - **500**: サーバーエラー
    """

    token = credentials.credentials

    # トークン検証
    payload = JWTHandler.verify_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token"
        )

    user_id = payload.get("user_id")

    # ユーザー取得
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled"
        )

    return user

# 認証依存関数
async def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> DBUser:
    """現在のアクティブユーザーを取得する依存関数"""

    token = credentials.credentials

    # トークン検証
    payload = JWTHandler.verify_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")

    # ユーザー取得
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
