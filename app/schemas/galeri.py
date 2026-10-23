import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class GaleriItem(BaseModel):
    id: uuid.UUID
    lokasi_id: uuid.UUID
    tipe: str = "foto"  # 'foto' | 'video'
    type: str = "foto"  # alias
    url: str
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = ""
    sort: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GaleriCreate(BaseModel):
    lokasi_id: uuid.UUID
    tipe: Optional[str] = "foto"
    type: Optional[str] = None
    url: str
    caption: Optional[str] = ""
    sort: Optional[int] = 0


class GaleriUpdate(BaseModel):
    lokasi_id: Optional[uuid.UUID] = None
    tipe: Optional[str] = None
    type: Optional[str] = None
    url: Optional[str] = None
    caption: Optional[str] = None
    sort: Optional[int] = None
