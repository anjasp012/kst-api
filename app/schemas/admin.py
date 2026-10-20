from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class UploadResponse(BaseModel):
    file_url: str
    relative_url: str
    original_filename: str
    tipe: str = "foto"
    thumbnail_url: Optional[str] = None
    thumbnail_relative_url: Optional[str] = None


class KSTAnalyticsResponse(BaseModel):
    total_kst: int
    total_partners: int
    wilayah_kst_distribution: Dict[str, int]
    partner_type_distribution: Dict[str, int]
