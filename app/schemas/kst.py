import uuid
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.core.helpers import build_full_url, build_full_url_list


class KSTBase(BaseModel):
    nama: str = Field(..., example="KST Jawa Barat")
    slug: str = Field(..., example="kst-jawa-barat")
    wilayah: str = Field(..., example="Jawa")
    kota_provinsi: str = Field(..., example="Bandung, Jawa Barat")
    pengelola: str = Field(default="BRIN", example="BRIN")
    status: str = Field(default="Aktif", example="Aktif")
    tahun_operasi: int = Field(default=2021, example=2021)
    thumbnail_url: Optional[str] = None
    latitude: Optional[float] = Field(None, example=-6.917464)
    longitude: Optional[float] = Field(None, example=107.619122)

    # 6 Tab Data KST
    deskripsi_profil: Optional[str] = None
    peran_kawasan: Optional[str] = None
    fokus_utama: List[str] = Field(default_factory=list, example=["Pangan", "Energi", "Laut", "Teknologi Digital"])
    terhubung_dengan: Optional[str] = None
    fasilitas: List[Any] = Field(default_factory=list)
    riset: List[Any] = Field(default_factory=list)
    dampak: List[Any] = Field(default_factory=list)
    potensi_kolaborasi: List[str] = Field(default_factory=list)
    daftar_kolaborasi: List[Any] = Field(default_factory=list)
    galeri: List[str] = Field(default_factory=list)
    is_active: bool = True


class KSTCreate(KSTBase):
    pass


class KSTUpdate(BaseModel):
    nama: Optional[str] = None
    slug: Optional[str] = None
    wilayah: Optional[str] = None
    kota_provinsi: Optional[str] = None
    pengelola: Optional[str] = None
    status: Optional[str] = None
    tahun_operasi: Optional[int] = None
    thumbnail_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    deskripsi_profil: Optional[str] = None
    peran_kawasan: Optional[str] = None
    fokus_utama: Optional[List[str]] = None
    terhubung_dengan: Optional[str] = None
    fasilitas: Optional[List[Any]] = None
    riset: Optional[List[Any]] = None
    dampak: Optional[List[Any]] = None
    potensi_kolaborasi: Optional[List[str]] = None
    daftar_kolaborasi: Optional[List[Any]] = None
    galeri: Optional[List[str]] = None
    is_active: Optional[bool] = None


class KSTMapItem(BaseModel):
    id: uuid.UUID
    nama: str
    slug: str
    wilayah: str
    kota_provinsi: str
    pengelola: str
    status: str
    tahun_operasi: int
    thumbnail_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    fokus_utama: List[str] = []
    is_active: bool

    @field_validator("thumbnail_url", mode="after")
    @classmethod
    def resolve_thumb(cls, v):
        return build_full_url(v)

    class Config:
        from_attributes = True


class KSTDetail(KSTBase):
    id: uuid.UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("thumbnail_url", mode="after")
    @classmethod
    def resolve_thumb(cls, v):
        return build_full_url(v)

    @field_validator("galeri", mode="after")
    @classmethod
    def resolve_gallery(cls, v):
        return build_full_url_list(v)

    class Config:
        from_attributes = True

