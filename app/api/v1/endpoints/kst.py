import uuid
import json
import re
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.helpers import build_full_url, build_thumbnail_url
from app.api.v1.endpoints.master import get_master_data
from app.api.v1.endpoints.lokasi import (
    get_all_locations_ringkas,
    filter_locations,
    get_location_detail,
    format_lokasi_publik,
)
from app.schemas.lokasi import (
    LokasiRingkasListResponse,
    LokasiPublikListResponse,
    LokasiPublikDetail,
)
from app.models.tema_riset import KSTFokusRiset
from app.api.v1.endpoints.quick_filter import get_public_quick_filters
from app.schemas.quick_filter import QuickFilterResponse
from typing import List

router = APIRouter()

# 👑 1. Master Data Terpadu
router.add_api_route(
    "/master",
    get_master_data,
    methods=["GET"],
    summary="Master Data Terpadu"
)

# ⚡ 2. Daftar Quick Filter
router.add_api_route(
    "/quick-filter",
    get_public_quick_filters,
    methods=["GET"],
    response_model=List[QuickFilterResponse],
    summary="Daftar Quick Filter"
)

# 🗺️ 3. Daftar Seluruh Data Lokasi (Public Frontend / Unity - Mendukung GET dan POST)
router.add_api_route(
    "/data-lokasi",
    get_all_locations_ringkas,
    methods=["GET"],
    response_model=LokasiPublikListResponse,
    summary="Daftar Seluruh Data Lokasi (GET)"
)

# Mendukung POST langsung ke /data-lokasi (dengan filter atau tanpa body)
router.add_api_route(
    "/data-lokasi",
    filter_locations,
    methods=["POST"],
    response_model=LokasiPublikListResponse,
    summary="Filter / Ambil Data Lokasi (POST)"
)

# 🔍 4. Filter Data Lokasi Multi-Kategori (Public Frontend / Unity Filter Action)
router.add_api_route(
    "/data-lokasi/filter",
    filter_locations,
    methods=["POST"],
    response_model=LokasiPublikListResponse,
    summary="Filter Data Lokasi"
)

# 📄 4. Detail Lokasi
@router.get(
    "/data-lokasi/{id}",
    response_model=LokasiPublikDetail,
    summary="Detail Lokasi"
)
def get_public_location_detail(id: str, db: Session = Depends(get_db)):
    loc = get_location_detail(id, db)
    return format_lokasi_publik(loc, db)
