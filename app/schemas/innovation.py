import uuid
import math
from typing import Optional, List
from pydantic import BaseModel, field_validator
from datetime import datetime
from app.schemas.zone import ZoneResponse
from app.schemas.persona import PersonaResponse
from app.core.helpers import build_full_url, build_full_url_list


class InnovationBase(BaseModel):
    zone_id: uuid.UUID
    persona_id: uuid.UUID
    title: str
    slug: str
    trl: int = 1
    short_description: str
    summary: str
    impact: str
    thumbnail_url: Optional[str] = None
    research_center: Optional[str] = None
    implementation_potential: Optional[List[str]] = []
    relevant_tags: Optional[List[str]] = []
    media_gallery: Optional[List[str]] = []
    is_active: bool = True


class InnovationCreate(InnovationBase):
    pass


class InnovationUpdate(BaseModel):
    zone_id: Optional[uuid.UUID] = None
    persona_id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    slug: Optional[str] = None
    trl: Optional[int] = None
    short_description: Optional[str] = None
    summary: Optional[str] = None
    impact: Optional[str] = None
    thumbnail_url: Optional[str] = None
    research_center: Optional[str] = None
    implementation_potential: Optional[List[str]] = None
    relevant_tags: Optional[List[str]] = None
    media_gallery: Optional[List[str]] = None
    is_active: Optional[bool] = None


class RelevanceMappingItem(BaseModel):
    persona_id: uuid.UUID
    relevance_score: int
    custom_impact: Optional[str] = None


class InnovationResponse(InnovationBase):
    id: uuid.UUID
    created_at: Optional[datetime] = None
    zone: Optional[ZoneResponse] = None
    persona: Optional[PersonaResponse] = None

    @field_validator("thumbnail_url", mode="after")
    @classmethod
    def format_thumbnail_url(cls, v: Optional[str]) -> Optional[str]:
        return build_full_url(v)

    @field_validator("media_gallery", mode="after")
    @classmethod
    def format_media_gallery(cls, v: Optional[List[str]]) -> List[str]:
        return build_full_url_list(v)

    class Config:
        from_attributes = True


class InnovationExploreCard(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    trl: int
    short_description: str
    summary: str
    impact: str
    thumbnail_url: Optional[str] = None
    research_center: Optional[str] = None
    implementation_potential: Optional[List[str]] = []
    relevant_tags: Optional[List[str]] = []
    zone_name: str
    persona_id: uuid.UUID
    persona_name: str
    relevance_score: int = 0

    @field_validator("thumbnail_url", mode="after")
    @classmethod
    def format_thumbnail_url(cls, v: Optional[str]) -> Optional[str]:
        return build_full_url(v)

    class Config:
        from_attributes = True


class InnovationExplorePaginatedResponse(BaseModel):
    items: List[InnovationExploreCard]
    total: int
    page: int
    page_size: int
    total_pages: int
