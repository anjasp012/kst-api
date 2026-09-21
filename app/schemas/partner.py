import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PartnerBase(BaseModel):
    nama_organisasi: str = Field(..., example="BAPPEDA Kab. Bireuen")
    jenis: str = Field(..., example="BAPPEDA")
    wilayah: Optional[str] = Field(None, example="Sumatera")
    alamat: Optional[str] = None
    telepon: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PartnerCreate(PartnerBase):
    pass


class PartnerUpdate(BaseModel):
    nama_organisasi: Optional[str] = None
    jenis: Optional[str] = None
    wilayah: Optional[str] = None
    alamat: Optional[str] = None
    telepon: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PartnerResponse(PartnerBase):
    id: uuid.UUID
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

