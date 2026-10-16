import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class KSTJenisKawasanItem(BaseModel):
    id: uuid.UUID
    parent_id: Optional[uuid.UUID] = Field(None, description="ID Kategori Induk")
    parent_nama: Optional[str] = Field(None, description="Nama Kategori Induk")
    nama: str = Field(..., description="Nama Jenis Kawasan")
    slug: str = Field(..., description="Slug Jenis Kawasan")
    deskripsi: Optional[str] = Field(None, description="Deskripsi Jenis Kawasan")
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class KSTJenisKawasanCreate(BaseModel):
    nama: str
    slug: Optional[str] = None
    deskripsi: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = True

class KSTJenisKawasanUpdate(BaseModel):
    nama: Optional[str] = None
    slug: Optional[str] = None
    deskripsi: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None

# Backward-compatible aliases
KSTKawasanItem = KSTJenisKawasanItem
KSTKawasanCreate = KSTJenisKawasanCreate
KSTKawasanUpdate = KSTJenisKawasanUpdate

KSTInstansiItem = KSTJenisKawasanItem
KSTInstansiCreate = KSTJenisKawasanCreate
KSTInstansiUpdate = KSTJenisKawasanUpdate
