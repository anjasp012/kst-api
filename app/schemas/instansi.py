import uuid
from typing import Optional
from pydantic import BaseModel

class KSTInstansiItem(BaseModel):
    id: uuid.UUID
    nama: str
    slug: str
    deskripsi: Optional[str] = None
    urutan: int = 0
    is_active: bool

    class Config:
        from_attributes = True

class KSTInstansiCreate(BaseModel):
    nama: str
    slug: str
    deskripsi: Optional[str] = None
    urutan: Optional[int] = 0
    is_active: Optional[bool] = True

class KSTInstansiUpdate(BaseModel):
    nama: Optional[str] = None
    slug: Optional[str] = None
    deskripsi: Optional[str] = None
    urutan: Optional[int] = None
    is_active: Optional[bool] = None
