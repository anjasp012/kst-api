import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class GaleriItem(BaseModel):
    id: uuid.UUID
    lokasi_id: uuid.UUID
    tipe: str = "foto"  # 'foto' | 'video'
    url: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GaleriCreate(BaseModel):
    lokasi_id: uuid.UUID
    tipe: str = "foto"  # 'foto' | 'video'
    url: str


class GaleriUpdate(BaseModel):
    lokasi_id: Optional[uuid.UUID] = None
    tipe: Optional[str] = None
    url: Optional[str] = None
