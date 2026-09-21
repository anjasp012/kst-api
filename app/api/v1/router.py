from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    admin,
    kst,
    wilayah,
    category,
    theme,
    facility,
    collaboration,
)

api_router = APIRouter()

# 🗺️ KST & PostGIS Geospatial (Peta Interaktif & Mitra Daerah)
api_router.include_router(
    kst.router,
    prefix="/kst",
    tags=["KST & Geospatial (Wonderful BRIN)"]
)

# 🧪 1. Tabel Terpisah: Tema Riset (kst_themeriset)
api_router.include_router(
    theme.router,
    prefix="/kst/themeriset",
    tags=["Tema Riset (kst_themeriset)"]
)
api_router.include_router(
    theme.router,
    prefix="/kst/research-themes",
    tags=["Tema Riset (kst_themeriset)"]
)

# 🏢 2. Tabel Terpisah: Tipe Fasilitas (kst_facilities)
api_router.include_router(
    facility.router,
    prefix="/kst/facilities",
    tags=["Fasilitas Riset (kst_facilities)"]
)

# 🤝 3. Tabel Terpisah: Potensi Kolaborasi (kst_collaborations)
api_router.include_router(
    collaboration.router,
    prefix="/kst/collaborations",
    tags=["Potensi Kolaborasi (kst_collaborations)"]
)

# 🏷️ Master Kategori Gabungan (Aggregated dari 3 tabel di atas)
api_router.include_router(
    category.router,
    prefix="/kst/categories",
    tags=["Master Kategori KST (Aggregated)"]
)
api_router.include_router(
    category.router,
    prefix="/categories",
    tags=["Master Kategori KST (Aggregated)"]
)

# 🇮🇩 Wilayah Indonesia (38 Provinsi & 514 Kota/Kabupaten)
api_router.include_router(
    wilayah.router,
    prefix="/kst/wilayah",
    tags=["Wilayah Indonesia"]
)
api_router.include_router(
    wilayah.router,
    prefix="/wilayah",
    tags=["Wilayah Indonesia"]
)

# 🔐 Authentication (Login, Refresh Token, Profile)
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# ⚙️ Admin CMS (Upload Media & Statistik)
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin CMS"]
)
