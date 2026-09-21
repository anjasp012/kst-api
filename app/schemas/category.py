import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class KSTCategoryItem(BaseModel):
    id: uuid.UUID
    tipe: str
    nama: str
    slug: str
    urutan: int
    is_active: bool

    class Config:
        from_attributes = True


class KSTCategoriesGrouped(BaseModel):
    tema_riset: List[str]
    tipe_fasilitas: List[str]
    potensi_kolaborasi: List[str]
    raw: List[KSTCategoryItem]
