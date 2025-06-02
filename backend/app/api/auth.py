from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import uuid

from ..database import get_db, User as DBUser, UserSession as DBUserSession
from ..models.schemas import UserCreate, UserLogin, UserResponse, Token
from ..auth.jwt_handler import JWTHandler, PasswordHandler, create_tokens
from ..services.default_settings_service import default_settings_service

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

@router.get(
    "/health",
    summary="認証システムヘルスチェック",
    description="認証システムの状態を確認します。"
)
async def health_check(db: Session = Depends(get_db)):
    """
    ## 認証システムヘルスチェック

    認証システムとデータベース接続の状態を確認します。

    ### レスポンス
    - **200**: システムが正常に動作している場合
    - **500**: システムに問題がある場合
    """
    try:
        # データベース接続テスト
        db.execute("SELECT 1")

        # 認証設定の確認
        auth_settings = default_settings_service.get_auth_settings()

        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": "connected",
            "auth_settings": {
                "algorithm": auth_settings.get("algorithm", "HS256"),
                "access_token_expire_minutes": auth_settings.get("access_token_expire_minutes", 360),
                "refresh_token_expire_days": auth_settings.get("refresh_token_expire_days", 7)
            }
        }
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System health check failed: {str(e)}"
        )

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

    try:
        # リクエスト情報をログに記録
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        print(f"🔐 Login attempt: email={user_login.email}, ip={client_ip}")

        # ユーザー検索
        user = db.query(DBUser).filter(DBUser.email == user_login.email).first()
        if not user:
            print(f"❌ Login failed: User not found for email={user_login.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        # パスワード検証
        if not PasswordHandler.verify_password(user_login.password, user.hashed_password):
            print(f"❌ Login failed: Invalid password for email={user_login.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        # アカウント状態確認
        if not user.is_active:
            print(f"❌ Login failed: Inactive account for email={user_login.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )

        print(f"✅ User authenticated: id={user.id}, email={user.email}")

        # トークン生成
        try:
            tokens = create_tokens({"id": user.id, "email": user.email})
            print(f"✅ Tokens generated for user: {user.id}")
        except Exception as token_error:
            print(f"❌ Token generation failed: {token_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate authentication tokens"
            )

        # セッション作成
        try:
            session = DBUserSession(
                id=str(uuid.uuid4()),
                user_id=user.id,
                refresh_token=tokens["refresh_token"],
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                user_agent=user_agent,
                ip_address=client_ip
            )

            db.add(session)

            # 最終ログイン時刻を更新
            user.last_login = datetime.now(timezone.utc)
            db.commit()

            print(f"✅ Session created for user: {user.id}")
        except Exception as session_error:
            print(f"❌ Session creation failed: {session_error}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user session"
            )

        print(f"✅ Login successful: user={user.id}, email={user.email}")
        return tokens

    except HTTPException:
        # HTTPExceptionは再発生
        raise
    except Exception as e:
        print(f"❌ Unexpected login error: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")

        # データベースロールバック
        try:
            db.rollback()
        except:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

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

@router.put(
    "/profile",
    response_model=UserResponse,
    summary="プロフィール更新",
    description="認証されたユーザーのプロフィール情報を更新します。"
)
async def update_profile(
    profile_data: dict,
    current_user: DBUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    ## プロフィール更新

    認証されたユーザーのプロフィール情報を更新します。

    ### リクエストボディ
    - **full_name** (optional): フルネーム
    - **timezone** (optional): タイムゾーン
    - **preferences** (optional): ユーザー設定

    ### レスポンス
    - **200**: 更新されたユーザー情報を返します
    - **401**: 認証が必要
    - **422**: バリデーションエラー
    - **500**: サーバーエラー
    """

    # 許可されたフィールドのみ更新
    allowed_fields = {'full_name', 'timezone', 'preferences'}

    for field, value in profile_data.items():
        if field in allowed_fields and hasattr(current_user, field):
            setattr(current_user, field, value)

    # 更新日時を設定
    current_user.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(current_user)

    return current_user

@router.put(
    "/change-password",
    summary="パスワード変更",
    description="認証されたユーザーのパスワードを変更します。"
)
async def change_password(
    password_data: dict,
    current_user: DBUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    ## パスワード変更

    認証されたユーザーのパスワードを変更します。

    ### リクエストボディ
    - **current_password**: 現在のパスワード
    - **new_password**: 新しいパスワード（6文字以上）

    ### レスポンス
    - **200**: パスワードが正常に変更された場合
    - **400**: リクエストデータが不正な場合
    - **401**: 認証が必要、または現在のパスワードが間違っている場合
    - **422**: バリデーションエラー
    - **500**: サーバーエラー
    """

    # 必須フィールドの確認
    if 'current_password' not in password_data or 'new_password' not in password_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="現在のパスワードと新しいパスワードの両方が必要です"
        )

    current_password = password_data['current_password']
    new_password = password_data['new_password']

    # 現在のパスワードを確認
    if not PasswordHandler.verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="現在のパスワードが正しくありません"
        )

    # 新しいパスワードのバリデーション
    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新しいパスワードは6文字以上である必要があります"
        )

    # 新しいパスワードをハッシュ化
    hashed_new_password = PasswordHandler.hash_password(new_password)

    # パスワードを更新
    current_user.hashed_password = hashed_new_password
    current_user.updated_at = datetime.now(timezone.utc)

    db.commit()

    return {"message": "パスワードが正常に変更されました"}

@router.get(
    "/settings",
    summary="認証設定取得",
    description="現在の認証設定情報を取得します。"
)
async def get_auth_settings():
    """
    ## 認証設定取得

    現在の認証設定情報を取得します。

    ### レスポンス
    - **200**: 認証設定情報を返します
    - **500**: サーバーエラー
    """
    try:
        from ..auth.jwt_handler import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

        # 設定ファイルから認証設定を取得
        auth_settings = default_settings_service.get_auth_settings()

        return {
            "access_token_expire_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token_expire_days": REFRESH_TOKEN_EXPIRE_DAYS,
            "access_token_expire_hours": ACCESS_TOKEN_EXPIRE_MINUTES / 60,
            "session_timeout_minutes": auth_settings.get("session_timeout_minutes", 360),
            "auto_refresh_threshold_minutes": auth_settings.get("auto_refresh_threshold_minutes", 30),
            "algorithm": auth_settings.get("algorithm", "HS256"),
            "password_hash_schemes": auth_settings.get("password_hash_schemes", ["bcrypt", "argon2"])
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"認証設定の取得に失敗: {str(e)}"
        )