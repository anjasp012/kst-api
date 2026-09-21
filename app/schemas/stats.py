import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class TelemetryEventCreate(BaseModel):
    event_type: str
    persona_id: Optional[uuid.UUID] = None
    zone_id: Optional[uuid.UUID] = None
    innovation_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    keterangan: Optional[str] = None
    metadata_payload: Optional[Dict[str, Any]] = None


class DashboardStatsResponse(BaseModel):
    total_innovations: int
    total_personas: int
    total_zones: int
    total_suggestions: int
    new_suggestions_count: int
    top_zones: List[Dict[str, Any]]
    top_personas: List[Dict[str, Any]]
    trl_distribution: Dict[str, int]
