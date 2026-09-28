import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TemaRisetItem(BaseModel):
    id: uuid.UUID
    nama: str
    slug: str
    deskripsi: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TemaRisetCreate(BaseModel):
    nama: str
    slug: Optional[str] = None
    deskripsi: Optional[str] = None
    is_active: Optional[bool] = True


class TemaRisetUpdate(BaseModel):
    nama: Optional[str] = None
    slug: Optional[str] = None
    deskripsi: Optional[str] = None
    is_active: Optional[bool] = None


ThemeRisetItem = TemaRisetItem
ThemeRisetCreate = TemaRisetCreate
ThemeRisetUpdate = TemaRisetUpdate
