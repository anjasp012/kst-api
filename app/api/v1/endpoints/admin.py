import os
import shutil
import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.user import User
from app.models.kst import KSTLocation
from app.models.partner import RegionalPartner
from app.schemas.admin import UploadResponse, KSTAnalyticsResponse
from app.api.v1.deps import get_current_admin
from app.core.helpers import build_full_url
from app.core.config import UPLOADS_DIR

router = APIRouter()


# =========================================================================
# 📊 1. ANALITIK & STATISTIK KST
# =========================================================================

@router.get("/analytics", response_model=KSTAnalyticsResponse)
def get_dashboard_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Statistik ringkasan KST dan sebaran mitra daerah BRIDA.
    """
    total_kst = db.query(func.count(KSTLocation.id)).filter(KSTLocation.is_active == True).scalar() or 0
    total_partners = db.query(func.count(RegionalPartner.id)).filter(RegionalPartner.is_active == True).scalar() or 0

    # Sebaran wilayah KST
    kst_by_wilayah = (
        db.query(KSTLocation.wilayah, func.count(KSTLocation.id))
        .filter(KSTLocation.is_active == True)
        .group_by(KSTLocation.wilayah)
        .all()
    )
    wilayah_kst_distribution = {w or "Lainnya": count for w, count in kst_by_wilayah}

    # Sebaran jenis mitra (BRIDA, BAPPERIDA, BAPPEDA)
    partner_by_type = (
        db.query(RegionalPartner.jenis, func.count(RegionalPartner.id))
        .filter(RegionalPartner.is_active == True)
        .group_by(RegionalPartner.jenis)
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
    """
    Mengunggah berkas gambar/thumbnail untuk KST & Galeri Riset.
    """
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".svg", ".pdf"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Format file '{ext}' tidak didukung. Harap unggah gambar (JPG, PNG, WEBP, SVG) atau PDF."
        )

    unique_filename = f"{uuid.uuid4()}{ext}"
    destination_path = os.path.join(UPLOADS_DIR, unique_filename)

    with open(destination_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    full_url = build_full_url(f"/uploads/{unique_filename}")
    relative_url = f"/uploads/{unique_filename}"

    return UploadResponse(
        file_url=full_url,
        relative_url=relative_url,
        original_filename=file.filename
    )
