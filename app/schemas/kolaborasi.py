import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class KolaborasiItem(BaseModel):
    id: uuid.UUID
    nama: str
    slug: str
    deskripsi: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KolaborasiCreate(BaseModel):
    nama: str
    slug: Optional[str] = None
    deskripsi: Optional[str] = None
    is_active: Optional[bool] = True


class KolaborasiUpdate(BaseModel):
    nama: Optional[str] = None
    slug: Optional[str] = None
    deskripsi: Optional[str] = None
    is_active: Optional[bool] = None


CollaborationItem = KolaborasiItem
CollaborationCreate = KolaborasiCreate
CollaborationUpdate = KolaborasiUpdate
