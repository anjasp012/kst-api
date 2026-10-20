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
from app.core.helpers import build_full_url, build_thumbnail_url
from app.core.config import UPLOADS_DIR, THUMBNAILS_DIR

from app.models.wilayah import WilayahProvinsi, WilayahKabupatenKota
from app.models.tema_riset import KSTFokusRiset
from app.models.quick_filter import KSTQuickFilter

from app.api.v1.endpoints import (
    lokasi,
    wilayah,
    jenis_kawasan,
    tema_riset,
    galeri,
    quick_filter,
)

router = APIRouter()


# =========================================================================
# 📊 1. ANALITIK & STATISTIK KST
# =========================================================================

def _resolve_region(prov_kode: Optional[str], prov_nama: Optional[str] = "") -> str:
    if prov_kode:
        p_str = str(prov_kode).strip()
        if p_str.startswith("1"): return "Sumatera"
        if p_str.startswith("3"): return "Jawa"
        if p_str.startswith("5"): return "Bali & Nusa Tenggara"
        if p_str.startswith("6"): return "Kalimantan"
        if p_str.startswith("7"): return "Sulawesi"
        if p_str.startswith("8") or p_str.startswith("9"): return "Maluku & Papua"
    p_lower = (prov_nama or "").lower()
    if any(k in p_lower for k in ["jakarta", "jawa", "banten", "yogyakarta"]): return "Jawa"
    if any(k in p_lower for k in ["aceh", "sumatera", "riau", "jambi", "bengkulu", "lampung", "bangka", "kepri"]): return "Sumatera"
    if "kalimantan" in p_lower: return "Kalimantan"
    if any(k in p_lower for k in ["sulawesi", "gorontalo"]): return "Sulawesi"
    if any(k in p_lower for k in ["bali", "nusa tenggara"]): return "Bali & Nusa Tenggara"
    if any(k in p_lower for k in ["maluku", "papua"]): return "Maluku & Papua"
    return "Lainnya"


@router.get("/dashboard/overview")
def get_dashboard_overview(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Menyediakan data ringkasan metrik statistik terpadu untuk Dashboard Overview CMS.
    """
    total_lokasi = db.query(func.count(KSTLokasi.id)).scalar() or 0
    total_jk = db.query(func.count(KSTJenisKawasan.id)).filter(KSTJenisKawasan.is_active == True).scalar() or 0
    total_fr = db.query(func.count(KSTFokusRiset.id)).filter(KSTFokusRiset.is_active == True).scalar() or 0
    total_prov = db.query(func.count(WilayahProvinsi.kode)).scalar() or 0
    total_kab = db.query(func.count(WilayahKabupatenKota.kode)).scalar() or 0
    total_qf = db.query(func.count(KSTQuickFilter.id)).scalar() or 0

    # Sebaran per Jenis Kawasan
    all_jk = db.query(KSTJenisKawasan).filter(KSTJenisKawasan.is_active == True).order_by(KSTJenisKawasan.nama.asc()).all()
    jk_distribution = []
    for jk in all_jk:
        c = db.query(func.count(KSTLokasi.id)).filter(KSTLokasi.jenis_kawasan_id == jk.id).scalar() or 0
        jk_distribution.append({
            "id": str(jk.id),
            "nama": jk.nama,
            "slug": jk.slug,
            "count": c,
            "percentage": round((c / total_lokasi * 100), 1) if total_lokasi > 0 else 0
        })
    # Sort distribution descending by count
    jk_distribution.sort(key=lambda x: x["count"], reverse=True)

    # Sebaran per Wilayah / Regional Pulau
    all_locs = (
        db.query(KSTLokasi.id, KSTLokasi.provinsi_kode, WilayahProvinsi.nama.label("provinsi_nama"))
        .outerjoin(WilayahProvinsi, KSTLokasi.provinsi_kode == WilayahProvinsi.kode)
        .all()
    )
    wil_counts = {
        "Jawa": 0,
        "Sumatera": 0,
        "Kalimantan": 0,
        "Sulawesi": 0,
        "Bali & Nusa Tenggara": 0,
        "Maluku & Papua": 0,
        "Lainnya": 0,
    }
    for loc in all_locs:
        reg = _resolve_region(loc.provinsi_kode, loc.provinsi_nama)
        wil_counts[reg] = wil_counts.get(reg, 0) + 1

    wilayah_distribution = []
    for w_name, cnt in wil_counts.items():
        if cnt > 0 or w_name != "Lainnya":
            wilayah_distribution.append({
                "wilayah": w_name,
                "count": cnt,
                "percentage": round((cnt / total_lokasi * 100), 1) if total_lokasi > 0 else 0
            })
    wilayah_distribution.sort(key=lambda x: x["count"], reverse=True)

    # 5 Lokasi Terbaru / Terakhir Diperbarui
    recent_rows = (
        db.query(KSTLokasi)
        .outerjoin(KSTJenisKawasan, KSTLokasi.jenis_kawasan_id == KSTJenisKawasan.id)
        .order_by(KSTLokasi.updated_at.desc())
        .limit(6)
        .all()
    )
    recent_lokasi = []
    for r in recent_rows:
        recent_lokasi.append({
            "id": str(r.id),
            "nama": r.nama,
            "slug": r.slug,
            "jenis_kawasan": r.jenis_kawasan.nama if r.jenis_kawasan else None,
            "kota_provinsi": r.kota_provinsi,
            "status": r.status or "Aktif",
            "is_draft": r.is_draft,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        })

    # Quick Filters
    all_qfs = (
        db.query(KSTQuickFilter)
        .order_by(KSTQuickFilter.created_at.asc())
        .all()
    )
    qf_list = []
    for qf in all_qfs:
        qf_list.append({
            "id": str(qf.id),
            "nama": qf.nama,
            "slug": qf.slug,
            "filter_data": qf.filter_data,
        })

    return {
        "stats": {
            "total_lokasi": total_lokasi,
            "total_jenis_kawasan": total_jk,
            "total_fokus_riset": total_fr,
            "total_provinsi": total_prov,
            "total_kabupaten_kota": total_kab,
            "total_quick_filter": total_qf,
        },
        "distribution_by_jenis_kawasan": jk_distribution,
        "distribution_by_wilayah": wilayah_distribution,
        "recent_lokasi": recent_lokasi,
        "quick_filters": qf_list,
    }


@router.get("/analytics", response_model=KSTAnalyticsResponse)
def get_dashboard_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    jk_condition = KSTLokasi.jenis_kawasan_id == KSTJenisKawasan.id

    total_kst = db.query(func.count(KSTLokasi.id)).join(KSTJenisKawasan, jk_condition).filter(KSTJenisKawasan.nama.ilike('%KST%')).scalar() or 0
    total_partners = db.query(func.count(KSTLokasi.id)).join(KSTJenisKawasan, jk_condition).filter(~KSTJenisKawasan.nama.ilike('%KST%')).scalar() or 0

    # Sebaran wilayah KST
    kst_locs = (
        db.query(KSTLokasi)
        .join(KSTJenisKawasan, jk_condition)
        .filter(KSTJenisKawasan.nama.ilike('%KST%'))
        .all()
    )
    wilayah_kst_distribution = {}
    for loc in kst_locs:
        w = loc.wilayah or "Lainnya"
        wilayah_kst_distribution[w] = wilayah_kst_distribution.get(w, 0) + 1

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

    media_tipe = "video" if ext in video_extensions else "foto"
    thumbnail_url = None
    thumbnail_relative_url = None

    # Jika file adalah foto/gambar, buat versi thumbnail dan optimasi foto utama
    if ext in {".jpg", ".jpeg", ".png", ".webp"}:
        try:
            from PIL import Image, ImageOps
            with Image.open(destination_path) as img_raw:
                img_raw.load()
                img = ImageOps.exif_transpose(img_raw).copy()

            is_jpeg = ext in (".jpg", ".jpeg")
            if is_jpeg and img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")

            # Simpan Thumbnail ke folder uploads/thumbnails/{unique_filename} (max 400x400)
            thumb_dest = os.path.join(THUMBNAILS_DIR, unique_filename)
            img_thumb = img.copy()
            img_thumb.thumbnail((400, 400), Image.Resampling.LANCZOS)
            if is_jpeg and img_thumb.mode != "RGB":
                img_thumb = img_thumb.convert("RGB")
            img_thumb.save(
                thumb_dest,
                format="JPEG" if is_jpeg else (img.format or "PNG"),
                quality=75,
                optimize=True
            )

            thumbnail_url = build_full_url(f"/uploads/thumbnails/{unique_filename}")
            thumbnail_relative_url = f"/uploads/thumbnails/{unique_filename}"
        except Exception as e:
            # Jika ada kendala pemrosesan gambar, fallback tanpa gagalkan upload
            print(f"Warning thumbnail generation failed: {e}")

    full_url = build_full_url(f"/uploads/{unique_filename}")
    relative_url = f"/uploads/{unique_filename}"

    return UploadResponse(
        file_url=full_url,
        relative_url=relative_url,
        thumbnail_url=thumbnail_url,
        thumbnail_relative_url=thumbnail_relative_url,
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
router.include_router(galeri.router, prefix="/galeri")
router.include_router(quick_filter.admin_router, prefix="/quick-filter")
