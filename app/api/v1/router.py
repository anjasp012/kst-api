from fastapi import APIRouter, Depends
from app.api.v1.endpoints import auth, kst, admin
from app.api.v1.deps import verify_kst_access_token, get_current_admin

api_router = APIRouter()

# 🔐 1. Authentication (Login, Refresh Token, Profile)
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# 🗺️ 2. Kawasan Sains dan Teknologi (Public / Frontend - Membutuhkan header X-Access-Token)
api_router.include_router(
    kst.router,
    prefix="/kst",
    tags=["Kawasan Sains dan Teknologi (Public)"],
    dependencies=[Depends(verify_kst_access_token)]
)

# ⚙️ 3. Admin CMS (Membutuhkan JWT Bearer Token dari Login)
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin CMS"],
    dependencies=[Depends(get_current_admin)]
)
