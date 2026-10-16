import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

class QuickFilterBase(BaseModel):
    nama: str = Field(..., description="Nama Quick Filter")
    slug: Optional[str] = Field(None, description="Slug URL unik")
    filter_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Kriteria filter")

class QuickFilterCreate(QuickFilterBase):
    pass

class QuickFilterUpdate(BaseModel):
    nama: Optional[str] = None
    slug: Optional[str] = None
    filter_data: Optional[Dict[str, Any]] = None

class QuickFilterResponse(BaseModel):
    id: uuid.UUID
    nama: str
    slug: str
    filter_data: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class QuickFilterListResponse(BaseModel):
    total: int
    data: List[QuickFilterResponse]
