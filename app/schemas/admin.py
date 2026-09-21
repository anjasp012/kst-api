import uuid
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class BulkStatusUpdate(BaseModel):
    ids: List[uuid.UUID]
    status: str


class BulkDeleteRequest(BaseModel):
    ids: List[uuid.UUID]





class DashboardAnalyticsResponse(BaseModel):
    total_innovations: int
    total_personas: int
    total_zones: int
    total_suggestions: int
    new_suggestions: int
    reviewed_suggestions: int
    top_zones: List[Dict[str, Any]]
    top_personas: List[Dict[str, Any]]
    trl_distribution: Dict[str, int]
