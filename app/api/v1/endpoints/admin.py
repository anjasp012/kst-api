import os
import shutil
import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.db.session import get_db
from app.models.user import User
from app.models.lokasi import KSTLokasi
from app.models.jenis_kawasan import KSTJenisKawasan
from app.schemas.admin import UploadResponse, KSTAnalyticsResponse
from app.api.v1.deps import get_current_admin
from app.core.helpers import build_full_url
from app.core.config import UPLOADS_DIR

from app.api.v1.endpoints import (
    lokasi,
    wilayah,
    jenis_kawasan,
    tema_riset,
    fasilitas,
    kolaborasi,
    dampak,
    galeri,
    kategori,
)

router = APIRouter()


# =========================================================================
# 📊 1. ANALITIK & STATISTIK KST
# =========================================================================

@router.get("/analytics", response_model=KSTAnalyticsResponse)
def get_dashboard_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    jk_condition = or_(
        KSTLokasi.jenis_kawasan_id == KSTJenisKawasan.id,
        KSTLokasi.kawasan_id == KSTJenisKawasan.id
    )

    total_kst = db.query(func.count(KSTLokasi.id)).join(KSTJenisKawasan, jk_condition).filter(KSTJenisKawasan.nama.ilike('%KST%')).scalar() or 0
    total_partners = db.query(func.count(KSTLokasi.id)).join(KSTJenisKawasan, jk_condition).filter(~KSTJenisKawasan.nama.ilike('%KST%')).scalar() or 0

    # Sebaran wilayah KST
    kst_by_wilayah = (
        db.query(KSTLokasi.wilayah, func.count(KSTLokasi.id))
        .join(KSTJenisKawasan, jk_condition).filter(KSTJenisKawasan.nama.ilike('%KST%'))
        .group_by(KSTLokasi.wilayah)
        .all()
    )
    wilayah_kst_distribution = {w or "Lainnya": count for w, count in kst_by_wilayah}

    # Sebaran jenis mitra (BRIDA, BAPPERIDA, BAPPEDA)
    partner_by_type = (
        db.query(KSTJenisKawasan.nama, func.count(KSTLokasi.id))
        .join(KSTJenisKawasan, jk_condition)
        .filter(~KSTJenisKawasan.nama.ilike('%KST%'))
        .group_by(KSTJenisKawasan.nama)
        .all()
    )
    partner_type_distribution = {t or "Lainnya": count for t, count in partner_by_type}

    return KSTAnalyticsResponse(
        total_kst=total_kst,
        total_partners=total_partners,
        wilayah_kst_distribution=wilayah_kst_distribution,
        partner_type_distribution=partner_type_distribution,
    )


# =========================================================================
# 📁 2. UPLOAD FILE & GAMBAR
# =========================================================================

@router.post("/upload", response_model=UploadResponse)
def upload_file(
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin)
):
    video_extensions = {".mp4", ".webm", ".mov", ".m4v", ".ogg"}
    image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".svg", ".pdf"}
    allowed_extensions = image_extensions | video_extensions

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Format file '{ext}' tidak didukung. Harap unggah gambar (JPG, PNG, WEBP, SVG) atau video (MP4, WEBM, MOV)."
        )

    unique_filename = f"{uuid.uuid4()}{ext}"
    destination_path = os.path.join(UPLOADS_DIR, unique_filename)

    with open(destination_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    full_url = build_full_url(f"/uploads/{unique_filename}")
    relative_url = f"/uploads/{unique_filename}"
    media_tipe = "video" if ext in video_extensions else "foto"

    return UploadResponse(
        file_url=full_url,
        relative_url=relative_url,
        original_filename=file.filename,
        tipe=media_tipe
    )


# =========================================================================
# ⚙️ 3. SUB-ROUTER MANAJEMEN CMS
# =========================================================================
router.include_router(lokasi.admin_router, prefix="/lokasi")
router.include_router(wilayah.router, prefix="/wilayah")
router.include_router(jenis_kawasan.router, prefix="/jenis-kawasan")
router.include_router(tema_riset.router, prefix="/fokus-riset")
router.include_router(fasilitas.router, prefix="/fasilitas")
router.include_router(kolaborasi.router, prefix="/kolaborasi")
router.include_router(dampak.router, prefix="/dampak")
router.include_router(galeri.router, prefix="/galeri")
router.include_router(kategori.router, prefix="/kategori")
