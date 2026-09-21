from fastapi import APIRouter
from app.api.v1.endpoints import auth, admin, kst, wilayah

api_router = APIRouter()

# 🗺️ KST & PostGIS Geospatial (Peta Interaktif & Mitra Daerah)
api_router.include_router(
    kst.router,
    prefix="/kst",
    tags=["KST & Geospatial (Wonderful BRIN)"]
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
