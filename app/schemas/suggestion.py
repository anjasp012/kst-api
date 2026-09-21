import uuid
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class SuggestionCreate(BaseModel):
    visitor_name: Optional[str] = None
    age_range: Optional[str] = None
    topic_wanted: str
    feedback: Optional[str] = None
    persona_id: Optional[uuid.UUID] = None
    zone_id: Optional[uuid.UUID] = None
    screen_context: Optional[str] = "Explore"


class SuggestionStatusUpdate(BaseModel):
    status: str
    admin_notes: Optional[str] = None


class SuggestionResponse(BaseModel):
    id: uuid.UUID
    visitor_name: Optional[str] = None
    age_range: Optional[str] = None
    topic_wanted: str
    feedback: Optional[str] = None
    persona_id: Optional[uuid.UUID] = None
    persona_name: Optional[str] = None
    zone_id: Optional[uuid.UUID] = None
    zone_name: Optional[str] = None
    screen_context: str
    status: str
    admin_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
