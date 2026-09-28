import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class KSTKategoriItem(BaseModel):
    id: uuid.UUID
    tipe: str
    nama: str
    slug: str
    urutan: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True


class KSTKategoriGrouped(BaseModel):
    tema_riset: List[str]
    tipe_fasilitas: List[str]
    potensi_kolaborasi: List[str]
    raw: Optional[List[Any]] = []


class KSTKategoriCreate(BaseModel):
    tipe: str
    nama: str
    slug: Optional[str] = None
    urutan: Optional[int] = 0
    is_active: Optional[bool] = True


class KSTKategoriUpdate(BaseModel):
    nama: Optional[str] = None
    slug: Optional[str] = None
    urutan: Optional[int] = None
    is_active: Optional[bool] = None


KSTCategoryItem = KSTKategoriItem
KSTCategoriesGrouped = KSTKategoriGrouped
KSTCategoryCreate = KSTKategoriCreate
KSTCategoryUpdate = KSTKategoriUpdate
