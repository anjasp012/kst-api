from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from jose import jwt, JWTError
import bcrypt
from app.core.config import settings

ALGORITHM = "HS256"
JWT_EXPIRE_SECONDS = 3600                     # 1 jam
REFRESH_TOKEN_EXPIRE_SECONDS = 7 * 24 * 3600  # 7 hari


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(seconds=JWT_EXPIRE_SECONDS)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(seconds=REFRESH_TOKEN_EXPIRE_SECONDS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_auth_tokens(username: str) -> Dict[str, Any]:
    """Menghasilkan pasangan jwt dan refresh_token"""
    jwt_token = create_access_token({"sub": username})
    refresh_token = create_refresh_token({"sub": username})
    return {
        "jwt": jwt_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": JWT_EXPIRE_SECONDS
    }


def decode_token(token: str, expected_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Mendekode dan memvalidasi tipe token (access / refresh)"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if expected_type and payload.get("type") != expected_type:
            return None
        return payload
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
