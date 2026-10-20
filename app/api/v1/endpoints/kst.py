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
)
from app.schemas.lokasi import (
    LokasiRingkasListResponse,
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

# 🗺️ 3. Daftar Seluruh Data Lokasi Ringkas (Public Frontend / Unity Default Load)
router.add_api_route(
    "/data-lokasi",
    get_all_locations_ringkas,
    methods=["GET"],
    response_model=LokasiRingkasListResponse,
    summary="Daftar Seluruh Data Lokasi Ringkas"
)

# 🔍 4. Filter Data Lokasi Multi-Kategori (Public Frontend / Unity Filter Action)
router.add_api_route(
    "/data-lokasi/filter",
    filter_locations,
    methods=["POST"],
    response_model=LokasiRingkasListResponse,
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

    # 1. Kumpulkan nilai_data_lokasi berdasarkan label_data_lokasi
    grouped = {}
    for ef in (loc.extra_fields or []):
        fl = ef.field_label
        if not fl:
            continue
        val = ef.value
        if val is None or str(val).strip() == "":
            continue

        label_key = str(fl.id)
        if label_key not in grouped:
            grouped[label_key] = {
                "label": fl.nama,
                "slug": fl.slug,
                "icon": fl.icon or "FileText",
                "values": []
            }

        parsed_val = val
        if isinstance(val, str) and (val.strip().startswith("[") or val.strip().startswith("{")):
            try:
                parsed_val = json.loads(val)
            except Exception:
                pass

        # Jika UUID fokus riset, resolve ke nama tema riset
        if isinstance(parsed_val, str) and len(parsed_val.strip()) == 36:
            try:
                u_val = uuid.UUID(parsed_val.strip())
                fr = db.query(KSTFokusRiset).filter(KSTFokusRiset.id == u_val).first()
                if fr and fr.nama:
                    parsed_val = fr.nama
            except ValueError:
                pass

        if isinstance(parsed_val, list):
            for item in parsed_val:
                if item and item not in grouped[label_key]["values"]:
                    grouped[label_key]["values"].append(item)
        else:
            if parsed_val and parsed_val not in grouped[label_key]["values"]:
                grouped[label_key]["values"].append(parsed_val)

    extra_fields = []
    for g in grouped.values():
        vals = g["values"]
        if not vals:
            continue
        is_multi = len(vals) > 1 or g["slug"] in ["fokus-riset", "fasilitas", "organisasi-riset", "pusat-riset", "pemanfaatan-layanan"]
        final_val = vals if is_multi else vals[0]
        extra_fields.append({
            "label": g["label"],
            "slug": g["slug"],
            "icon": g["icon"],
            "value": final_val
        })

    # 2. Sinkronkan galeri dengan URL lengkap dan versi thumbnail
    galeri_list = []
    video_exts = (".mp4", ".webm", ".mov", ".m4v", ".ogg", ".avi", ".mkv")
    for g in (loc.galeri or []):
        raw_u = g.get("url") if isinstance(g, dict) else g
        u_full = build_full_url(raw_u)
        is_video = any(u_full.lower().endswith(ext) for ext in video_exts) if u_full else False
        tipe_val = g.get("tipe") if isinstance(g, dict) else ("video" if is_video else "foto")
        t_full = None if is_video else build_thumbnail_url(raw_u)
        galeri_list.append({
            "tipe": tipe_val,
            "url": u_full,
            "thumbnail_url": t_full
        })

    jk_nama = loc.jenis_kawasan.nama if loc.jenis_kawasan else (getattr(loc, "jenis_kawasan_nama", None) or None)

    # 3. Payload bersih: dari kst_lokasi & nilai_data_lokasi yang terisi
    data = {
        "id": loc.id,
        "nama": loc.nama,
        "slug": loc.slug,
        "jenis_kawasan": jk_nama,
        "jenis_kawasan_nama": jk_nama,
        "pengelola": loc.pengelola or "BRIN",
        "status": loc.status or "Aktif",
        "tahun_operasi": loc.tahun_operasi,
        "alamat": loc.alamat,
        "kota_provinsi": loc.kota_provinsi,
        "wilayah": loc.wilayah,
        "provinsi": loc.provinsi.nama if loc.provinsi else None,
        "kabupaten": loc.kabupaten_kota.nama if loc.kabupaten_kota else None,
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "koordinat": {
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "lat": loc.latitude,
            "lng": loc.longitude
        },
        "luas_ha": loc.luas_ha,
        "deskripsi": loc.deskripsi,
        "galeri": galeri_list,
        "extra_fields": extra_fields
    }

    return LokasiPublikDetail.model_validate(data)
