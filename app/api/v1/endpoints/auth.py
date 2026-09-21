import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, RefreshTokenRequest, RefreshTokenResponse
from app.schemas.user import UserResponse
from app.core.security import verify_password, create_auth_tokens, decode_token
from app.api.v1.deps import get_current_admin

router = APIRouter()


@router.post("/login", response_model=LoginResponse, summary="Login Admin CMS")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Login administrator CMS untuk mendapatkan JWT dan Refresh Token
    """
    user = db.query(User).filter(
        (User.username == payload.username) | (User.email == payload.username)
    ).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "responseCode": "4010000",
                "responseMessage": "Username atau password salah"
            }
        )
    if user.is_active != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "responseCode": "4030000",
                "responseMessage": "Akun administrator dinonaktifkan"
            }
        )

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    tokens = create_auth_tokens(user.username)
    return {
        "responseCode": "2000000",
        "responseMessage": "Login successful",
        "data": tokens
    }


@router.post("/refresh", response_model=RefreshTokenResponse, summary="Refresh Token CMS")
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Memperbarui token JWT menggunakan refresh token
    """
    token_payload = decode_token(payload.refresh_token, expected_type="refresh")
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "responseCode": "4010000",
                "responseMessage": "Refresh token tidak valid atau sudah kadaluarsa"
            }
        )

    username: str = token_payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "responseCode": "4010000",
                "responseMessage": "Payload token tidak valid"
            }
        )

    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()

    if not user or user.is_active != 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "responseCode": "4010000",
                "responseMessage": "Pengguna tidak ditemukan atau nonaktif"
            }
        )

    tokens = create_auth_tokens(user.username)
    return {
        "responseCode": "2000000",
        "responseMessage": "Token refreshed successfully",
        "data": tokens
    }


@router.get("/me", response_model=UserResponse, summary="Profil Admin Login")
def get_me(current_user: User = Depends(get_current_admin)):
    """
    Mengambil data profil administrator yang sedang login via JWT
    """
    return {
        "responseCode": "2000000",
        "responseMessage": "Success",
        "data": current_user
    }
