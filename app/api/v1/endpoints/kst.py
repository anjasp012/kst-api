from typing import List, Optional
from fastapi import APIRouter
from app.api.v1.endpoints.master import get_master_data
from app.api.v1.endpoints.lokasi import (
    get_all_locations_ringkas,
    filter_locations,
    get_location_detail,
    get_nearby_locations,
    get_map_locations,
)
from app.schemas.lokasi import (
    LokasiRingkasItem, 
    LokasiRingkasListResponse,
    LokasiDetail, 
    LokasiMapItem
)

router = APIRouter()

# 👑 1. Master Data Terpadu (Wilayah, Jenis Kawasan, Fokus Riset)
router.add_api_route(
    "/master",
    get_master_data,
    methods=["GET"],
    summary="Master Data Terpadu (Wilayah, Jenis Kawasan, Fokus Riset)"
)

# 🗺️ 2. Daftar Seluruh Data Lokasi Ringkas (Public Frontend / Unity Default Load)
router.add_api_route(
    "/data-lokasi",
    get_all_locations_ringkas,
    methods=["GET"],
    response_model=LokasiRingkasListResponse,
    summary="Daftar Seluruh Data Lokasi Ringkas"
)

# 🔍 3. Filter Data Lokasi Multi-Kategori (Public Frontend / Unity Filter Action)
router.add_api_route(
    "/data-lokasi/filter",
    filter_locations,
    methods=["POST"],
    response_model=LokasiRingkasListResponse,
    summary="Filter Data Lokasi Multi-Kategori"
)

# 📍 4. Peta Interaktif
router.add_api_route(
    "/peta",
    get_map_locations,
    methods=["GET"],
    response_model=List[LokasiMapItem],
    summary="Daftar Titik Peta Interaktif"
)

# 📌 5. Lokasi Terdekat Spasial PostGIS
router.add_api_route(
    "/data-lokasi/terdekat",
    get_nearby_locations,
    methods=["GET"],
    summary="Pencarian Spasial Lokasi Terdekat (PostGIS)"
)

# 📄 6. Detail Lokasi Lengkap + Gambar & Galeri
router.add_api_route(
    "/data-lokasi/{id}",
    get_location_detail,
    methods=["GET"],
    response_model=LokasiDetail,
    summary="Detail Lengkap Lokasi Termasuk Gambar & Galeri"
)
