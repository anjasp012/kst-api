import uuid
from typing import Optional, Any
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    username: str
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "admin123"
            }
        }


class RefreshTokenRequest(BaseModel):
    refresh_token: str

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class TokenData(BaseModel):
    jwt: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600


class LoginResponse(BaseModel):
    responseCode: str = "2000000"
    responseMessage: str = "Login successful"
    data: TokenData


class RefreshTokenResponse(BaseModel):
    responseCode: str = "2000000"
    responseMessage: str = "Token refreshed successfully"
    data: TokenData


class ErrorResponse(BaseModel):
    responseCode: str = "4010000"
    responseMessage: str = "Invalid username or password"
