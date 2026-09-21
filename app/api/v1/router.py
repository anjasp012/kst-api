from fastapi import APIRouter, Depends
from app.api.v1.endpoints import auth, table, admin, kst
from app.api.v1.deps import verify_table_access_token

api_router = APIRouter()

# 🗺️ KST & PostGIS Geospatial (Peta Interaktif & Mitra Daerah)
api_router.include_router(
    kst.router,
    prefix="/kst",
    tags=["KST & Geospatial (Wonderful BRIN)"]
)

# 🔐 Authentication (Login, Refresh Token, Profile)
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# 🖥️ Interactive Table (Membutuhkan header X-Access-Token dari .env)
api_router.include_router(
    table.router,
    prefix="/table",
    tags=["Interactive Table (Public)"],
    dependencies=[Depends(verify_table_access_token)]
)

# ⚙️ Admin CMS (Membutuhkan JWT Bearer Token)
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin CMS"]
)
