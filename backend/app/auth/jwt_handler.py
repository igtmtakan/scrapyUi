import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import os
import warnings
from passlib.context import CryptContext

# bcryptの警告を抑制
warnings.filterwarnings("ignore", message=".*bcrypt version.*")

# JWT設定
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# パスワードハッシュ化（bcryptとargon2の両方をサポート）
pwd_context = CryptContext(
    schemes=["bcrypt", "argon2"],
    deprecated="auto",
    bcrypt__rounds=12,
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=1,
)

class JWTHandler:
    """JWT トークンの生成と検証を行うクラス"""

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """アクセストークンを生成"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """リフレッシュトークンを生成"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """トークンを検証してペイロードを返す"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except (jwt.PyJWTError, jwt.DecodeError, jwt.ExpiredSignatureError):
            return None

    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """トークンをデコードする（期限切れでもデコード）"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
            return payload
        except (jwt.PyJWTError, jwt.DecodeError, jwt.ExpiredSignatureError):
            return None

class PasswordHandler:
    """パスワードのハッシュ化と検証を行うクラス"""

    @staticmethod
    def hash_password(password: str) -> str:
        """パスワードをハッシュ化"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """パスワードを検証"""
        return pwd_context.verify(plain_password, hashed_password)

# トークン生成のヘルパー関数
def create_tokens(user_data: Dict[str, Any]) -> Dict[str, str]:
    """アクセストークンとリフレッシュトークンを生成"""
    access_token = JWTHandler.create_access_token(data={"sub": user_data["email"], "user_id": user_data["id"]})
    refresh_token = JWTHandler.create_refresh_token(data={"sub": user_data["email"], "user_id": user_data["id"]})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
