import uuid
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class UserData(BaseModel):
    id: uuid.UUID
    username: str
    email: Optional[str] = None
    full_name: str
    role: str
    is_active: int
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    responseCode: str = "2000000"
    responseMessage: str = "Success"
    data: UserData
