from pydantic import BaseModel
from typing import Dict, Any, List


class UploadResponse(BaseModel):
    file_url: str
    relative_url: str
    original_filename: str


class KSTAnalyticsResponse(BaseModel):
    total_kst: int
    total_partners: int
    wilayah_kst_distribution: Dict[str, int]
    partner_type_distribution: Dict[str, int]
