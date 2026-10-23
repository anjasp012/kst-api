import uuid
import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, text, Text
from geoalchemy2.elements import WKTElement
from geoalchemy2 import functions as geofunc

from app.db.session import get_db
from app.models.lokasi import KSTLokasi
from app.models.jenis_kawasan import KSTJenisKawasan
from app.models.galeri import KSTGaleri
from app.models.field_location import LabelDataLokasi, NilaiDataLokasi, FieldLabelLocation, FieldValueLocation
from app.models.wilayah import WilayahProvinsi, WilayahKabupatenKota
from app.models.tema_riset import KSTFokusRiset
from app.models.user import User
from app.schemas.lokasi import (
    LokasiMapItem, 
    LokasiDetail, 
    LokasiCreate, 
    LokasiUpdate, 
    LokasiRingkasItem,
    LokasiRingkasListResponse,
    LokasiFilterRequest,
    LabelDataLokasiCreate,
    LabelDataLokasiUpdate,
)
from app.core.helpers import build_full_url, build_thumbnail_url
from app.api.v1.deps import get_current_admin

router = APIRouter()


def _set_point_geom(lat: Optional[float], lon: Optional[float]):
    if lat is not None and lon is not None:
        return WKTElement(f"POINT({lon} {lat})", srid=4326)
    return None


def _sync_galeri_items(db: Session, lokasi_id: uuid.UUID, galeri_data: list):
    if galeri_data is None:
        return
    db.query(KSTGaleri).filter(KSTGaleri.lokasi_id == lokasi_id).delete()
    video_exts = (".mp4", ".webm", ".mov", ".m4v", ".ogg", ".avi", ".mkv")
    
    for idx, item in enumerate(galeri_data):
        if isinstance(item, str):
            url_str = item.strip()
            if not url_str:
                continue
            is_video = any(url_str.lower().endswith(ext) for ext in video_exts)
            tipe = "video" if is_video else "foto"
            new_g = KSTGaleri(
                lokasi_id=lokasi_id,
                tipe=tipe,
                url=url_str,
                caption="",
                sort=idx
            )
            db.add(new_g)
        elif isinstance(item, dict):
            raw_url = item.get("url", "")
            if isinstance(raw_url, dict):
                raw_url = raw_url.get("relative_url") or raw_url.get("file_url") or raw_url.get("url") or ""
            url_str = str(raw_url or "").strip()
            if not url_str:
                continue
            tipe = str(item.get("tipe") or item.get("type") or "foto").lower().strip()
            if tipe not in ("foto", "video"):
                is_video = any(url_str.lower().endswith(ext) for ext in video_exts)
                tipe = "video" if is_video else "foto"
            caption_val = str(item.get("caption") or item.get("keterangan") or "").strip()
            sort_val = item.get("sort")
            if sort_val is None or not isinstance(sort_val, int):
                sort_val = idx
            new_g = KSTGaleri(
                lokasi_id=lokasi_id,
                tipe=tipe,
                url=url_str,
                caption=caption_val,
                sort=sort_val
            )
            db.add(new_g)
    db.flush()


def _sync_extra_fields(db: Session, lokasi_id: uuid.UUID, extra_fields: list):
    """Sinkronisasi data dinamis opsional ke tabel nilai_data_lokasi"""
    if extra_fields is None:
        return
    db.query(NilaiDataLokasi).filter(NilaiDataLokasi.lokasi_id == lokasi_id).delete()
    import json
    import re
    for item in extra_fields:
        if not isinstance(item, dict):
            continue
        
        # Cari master field_label_id
        lbl_obj = None
        fl_id = item.get("field_label_id")
        if fl_id:
            try:
                val_uuid = uuid.UUID(str(fl_id))
                lbl_obj = db.query(LabelDataLokasi).filter(LabelDataLokasi.id == val_uuid).first()
            except ValueError:
                pass

        if not lbl_obj:
            label_name = item.get("label") or item.get("nama") or item.get("judul") or item.get("slug")
            if label_name and str(label_name).strip():
                clean_lbl = str(label_name).strip()
                import re
                base_slug = re.sub(r'[^a-zA-Z0-9]+', '-', clean_lbl.lower()).strip('-') or "field-opsional"
                lbl_obj = db.query(LabelDataLokasi).filter(
                    (LabelDataLokasi.nama.ilike(clean_lbl)) | 
                    (LabelDataLokasi.slug == clean_lbl.lower()) |
                    (LabelDataLokasi.slug == base_slug)
                ).first()
                if not lbl_obj:
                    # Auto-create new LabelDataLokasi so custom labels or typed tabs are never lost
                    final_slug = base_slug
                    counter = 1
                    while db.query(LabelDataLokasi).filter(LabelDataLokasi.slug == final_slug).first():
                        final_slug = f"{base_slug}-{counter}"
                        counter += 1
                    lbl_obj = LabelDataLokasi(
                        nama=clean_lbl,
                        slug=final_slug,
                        placeholder=f"Masukkan informasi {clean_lbl}...",
                        icon="FileText"
                    )
                    db.add(lbl_obj)
                    db.flush()

        if not lbl_obj:
            continue
        
        val = item.get("value")
        if val is None:
            val = item.get("konten") or item.get("items")

        is_fokus_riset = (lbl_obj.slug == 'fokus-riset') or ("fokus" in lbl_obj.nama.lower() and "riset" in lbl_obj.nama.lower())
        is_saluran = (lbl_obj.slug == 'saluran-digital') or ("saluran" in lbl_obj.nama.lower())
        if is_fokus_riset:
            fokus_items = []
            if isinstance(val, list):
                for v_item in val:
                    if isinstance(v_item, dict):
                        fokus_items.append(v_item.get("nama") or v_item.get("id") or str(v_item))
                    elif v_item:
                        fokus_items.append(str(v_item).strip())
            elif isinstance(val, str) and val.strip():
                if val.strip().startswith("["):
                    try:
                        parsed = json.loads(val)
                        if isinstance(parsed, list):
                            for p in parsed:
                                fokus_items.append(str(p).strip())
                    except Exception:
                        pass
                if not fokus_items:
                    parts = [p.strip() for p in val.replace("\n", ",").split(",") if p.strip()]
                    fokus_items.extend(parts)

            if fokus_items:
                for f_name in fokus_items:
                    if not f_name or not str(f_name).strip():
                        continue
                    clean_name = str(f_name).strip()
                    fr_obj = None
                    try:
                        f_uuid = uuid.UUID(clean_name)
                        fr_obj = db.query(KSTFokusRiset).filter(KSTFokusRiset.id == f_uuid).first()
                    except ValueError:
                        pass
                    if not fr_obj:
                        fr_obj = db.query(KSTFokusRiset).filter(
                            (KSTFokusRiset.nama.ilike(clean_name)) |
                            (KSTFokusRiset.slug == clean_name.lower().replace(" ", "-"))
                        ).first()
                        if not fr_obj:
                            import re
                            base_fr_slug = re.sub(r'[^a-zA-Z0-9]+', '-', clean_name.lower()).strip('-') or f"fr-{uuid.uuid4().hex[:6]}"
                            final_fr_slug = base_fr_slug
                            c = 1
                            while db.query(KSTFokusRiset).filter(KSTFokusRiset.slug == final_fr_slug).first():
                                final_fr_slug = f"{base_fr_slug}-{c}"
                                c += 1
                            fr_obj = KSTFokusRiset(
                                nama=clean_name,
                                slug=final_fr_slug
                            )
                            db.add(fr_obj)
                            db.flush()

                    new_val = NilaiDataLokasi(
                        lokasi_id=lokasi_id,
                        field_label_id=lbl_obj.id,
                        value=str(fr_obj.id) if fr_obj else clean_name
                    )
                    db.add(new_val)
        elif is_saluran:
            if isinstance(val, list):
                clean_items = [str(v).strip() for v in val if v is not None and str(v).strip()]
                if clean_items:
                    parts = []
                    for item_str in clean_items:
                        if item_str.startswith("<p>") or "<b" in item_str:
                            parts.append(item_str)
                        else:
                            parts.append(f"<p>{item_str}</p>")
                    combined_val = "".join(parts)
                else:
                    combined_val = ""
            else:
                combined_val = str(val or "").strip()

            text_only = re.sub(r'<[^>]*>', '', combined_val).strip()
            if text_only:
                new_val = NilaiDataLokasi(
                    lokasi_id=lokasi_id,
                    field_label_id=lbl_obj.id,
                    value=combined_val
                )
                db.add(new_val)
        else:
            if isinstance(val, list):
                clean_items = []
                for v in val:
                    if v is not None:
                        s = str(v).strip()
                        t = re.sub(r'<[^>]*>', '', s).strip()
                        if t or (s and not s.startswith('<')):
                            clean_items.append(s)
                for sub_val in clean_items:
                    sub_str = json.dumps(sub_val, ensure_ascii=False) if isinstance(sub_val, (dict, list)) else str(sub_val).strip()
                    new_val = NilaiDataLokasi(
                        lokasi_id=lokasi_id,
                        field_label_id=lbl_obj.id,
                        value=sub_str
                    )
                    db.add(new_val)
            else:
                s = str(val or "").strip()
                t = re.sub(r'<[^>]*>', '', s).strip()
                if t or (s and not s.startswith('<')):
                    val_str = json.dumps(val, ensure_ascii=False) if isinstance(val, dict) else s
                    new_val = NilaiDataLokasi(
                        lokasi_id=lokasi_id,
                        field_label_id=lbl_obj.id,
                        value=val_str
                    )
                    db.add(new_val)
    db.flush()


# =========================================================================
# 🗺️ 1. PETA INTERAKTIF JELAJAHI KAWASAN TERPADU BRIN & SPASIAL (PUBLIC)
# =========================================================================

def _build_ringkas_dict(loc: KSTLokasi) -> dict:
    prov = loc.provinsi.nama if loc.provinsi else ""
    kab = loc.kabupaten_kota.nama if loc.kabupaten_kota else ""
    if not prov and loc.kota_provinsi:
        parts = [p.strip() for p in loc.kota_provinsi.split(",")]
        if len(parts) >= 2:
            kab = parts[0]
            prov = parts[1]
        else:
            kab = parts[0]
            prov = loc.wilayah or ""
    elif not prov and loc.wilayah:
        prov = loc.wilayah

    fokus_list = []
    if hasattr(loc, "tema_riset") and loc.tema_riset:
        for t in loc.tema_riset:
            if t and t not in fokus_list:
                fokus_list.append(t)

    jk_name = loc.jenis_kawasan.nama if loc.jenis_kawasan else (loc.jenis_kawasan_nama or "")
    kota_prov = loc.kota_provinsi or (f"{kab}, {prov}" if kab and prov else (prov or kab or ""))

    return {
        "id": loc.id,
        "nama": loc.nama,
        "slug": loc.slug,
        "jenis_kawasan": jk_name,
        "jenis_kawasan_id": loc.jenis_kawasan_id,
        "alamat": loc.alamat or "",
        "kota_provinsi": kota_prov,
        "wilayah": {
            "provinsi": prov,
            "kabupaten": kab
        },
        "koordinat": {
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "lat": loc.latitude,
            "lng": loc.longitude
        },
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "deskripsi": loc.deskripsi,
        "fokus_riset": fokus_list
    }


@router.get("", response_model=LokasiRingkasListResponse)
def get_all_locations_ringkas(
    db: Session = Depends(get_db)
):

    rows = (
        db.query(KSTLokasi)
        .filter(KSTLokasi.is_draft == False)
        .order_by(KSTLokasi.nama.asc())
        .all()
    )

    results = [_build_ringkas_dict(loc) for loc in rows]
    return {
        "total": len(results),
        "data": results
    }


@router.post("/filter", response_model=LokasiRingkasListResponse)
def filter_locations(
    payload: Optional[LokasiFilterRequest] = None,
    db: Session = Depends(get_db)
):
    query = (
        db.query(KSTLokasi)
        .outerjoin(WilayahProvinsi, KSTLokasi.provinsi_kode == WilayahProvinsi.kode)
        .outerjoin(WilayahKabupatenKota, KSTLokasi.kabupaten_kota_kode == WilayahKabupatenKota.kode)
        .filter(KSTLokasi.is_draft == False)
    )

    def _flatten_items(items):
        res = []
        for x in (items or []):
            if not x:
                continue
            if isinstance(x, str) and "," in x:
                res.extend([s.strip() for s in x.split(",") if s.strip()])
            else:
                res.append(str(x).strip())
        return res

    wilayah_list = _flatten_items(payload.wilayah if payload and payload.wilayah else None)
    jenis_kawasan_list = _flatten_items(payload.jenis_kawasan if payload and payload.jenis_kawasan else None)
    fokus_riset_list = _flatten_items(payload.fokus_riset if payload and payload.fokus_riset else None)
    search_text = (
        (payload.search_input if payload and payload.search_input else None) or ""
    ).strip()

    # 1. Filter input teks pencarian bebas (mencakup Lokasi, Tema Riset, dan Fasilitas)
    if search_text:
        s = f"%{search_text}%"
        query = query.filter(
            or_(
                KSTLokasi.nama.ilike(s),
                WilayahProvinsi.nama.ilike(s),
                WilayahKabupatenKota.nama.ilike(s),
                func.coalesce(KSTLokasi.deskripsi, "").ilike(s),
                func.coalesce(KSTLokasi.alamat, "").ilike(s),
            )
        )

    # 2. Filter wilayah (bisa lebih dari 1 wilayah)
    if wilayah_list:
        wil_conditions = []
        for w in wilayah_list:
            if w and w.strip():
                clean_w = f"%{w.strip()}%"
                wil_conditions.append(WilayahProvinsi.nama.ilike(clean_w))
                wil_conditions.append(WilayahKabupatenKota.nama.ilike(clean_w))
                wil_conditions.append(func.coalesce(KSTLokasi.alamat, "").ilike(clean_w))
        if wil_conditions:
            query = query.filter(or_(*wil_conditions))

    # 3. Filter jenis kawasan (bisa lebih dari 1 jenis kawasan)
    if jenis_kawasan_list:
        jk_conditions = []
        for jk in jenis_kawasan_list:
            if jk and str(jk).strip():
                clean_jk = str(jk).strip()
                try:
                    val_uuid = uuid.UUID(clean_jk)
                    jk_conditions.append(KSTJenisKawasan.id == val_uuid)
                except ValueError:
                    search_jk = f"%{clean_jk}%"
                    jk_conditions.append(KSTJenisKawasan.nama.ilike(search_jk))
                    jk_conditions.append(KSTJenisKawasan.slug.ilike(search_jk))
        if jk_conditions:
            query = query.join(
                KSTJenisKawasan,
                KSTLokasi.jenis_kawasan_id == KSTJenisKawasan.id
            ).filter(or_(*jk_conditions))

    rows = query.order_by(KSTLokasi.nama.asc()).all()

    # 4. Filter fokus riset (bisa lebih dari 1 fokus riset)
    if fokus_riset_list:
        clean_fokus = [f.lower().strip() for f in fokus_riset_list if f and str(f).strip()]
        if clean_fokus:
            from app.models.tema_riset import KSTFokusRiset
            resolved_targets = []
            for f in clean_fokus:
                resolved_targets.append(f)
                try:
                    u_f = uuid.UUID(f)
                    fr_rec = db.query(KSTFokusRiset).filter(KSTFokusRiset.id == u_f).first()
                    if fr_rec and fr_rec.nama:
                        resolved_targets.append(fr_rec.nama.lower().strip())
                except ValueError:
                    fr_rec = db.query(KSTFokusRiset).filter(KSTFokusRiset.slug == f).first()
                    if fr_rec and fr_rec.nama:
                        resolved_targets.append(fr_rec.nama.lower().strip())

            filtered_rows = []
            for loc in rows:
                loc_themes = []
                if hasattr(loc, "tema_riset") and loc.tema_riset:
                    for t in loc.tema_riset:
                        if t:
                            loc_themes.append(str(t).lower().strip())

                match = any(
                    any(target in lt or lt in target for lt in loc_themes)
                    for target in resolved_targets
                )
                if match:
                    filtered_rows.append(loc)
            rows = filtered_rows

    results = [_build_ringkas_dict(loc) for loc in rows]
    return {
        "total": len(results),
        "data": results
    }


@router.get("/peta", response_model=List[LokasiMapItem])
def get_map_locations(
    wilayah: Optional[str] = Query(None, description="Filter wilayah: Sumatera, Jawa, Kalimantan, Sulawesi, Nusa Tenggara, Maluku & Papua"),
    jenis_kawasan: Optional[str] = Query(None, description="Filter jenis kawasan: Kawasan Sains (KST), BRIDA, BAPPERIDA, BAPPEDA"),
    kawasan: Optional[str] = Query(None, description="Filter jenis kawasan (alias)"),
    fokus: Optional[str] = Query(None, description="Filter tema riset / fokus utama"),
    fasilitas: Optional[str] = Query(None, description="Filter tipe fasilitas"),
    kolaborasi: Optional[str] = Query(None, description="Filter potensi kolaborasi"),
    q: Optional[str] = Query(None, description="Pencarian bebas nama / kota / deskripsi"),
    is_draft: Optional[bool] = Query(None, description="Filter status draft"),
    db: Session = Depends(get_db)
):
    query = (
        db.query(KSTLokasi)
        .outerjoin(WilayahProvinsi, KSTLokasi.provinsi_kode == WilayahProvinsi.kode)
        .outerjoin(WilayahKabupatenKota, KSTLokasi.kabupaten_kota_kode == WilayahKabupatenKota.kode)
    )

    if is_draft is not None:
        query = query.filter(KSTLokasi.is_draft == is_draft)

    if wilayah:
        w_search = f"%{wilayah.strip()}%"
        query = query.filter(
            or_(
                WilayahProvinsi.nama.ilike(w_search),
                WilayahKabupatenKota.nama.ilike(w_search)
            )
        )

    filter_jk = jenis_kawasan or kawasan
    if filter_jk:
        query = query.join(
            KSTJenisKawasan, 
            KSTLokasi.jenis_kawasan_id == KSTJenisKawasan.id
        ).filter(KSTJenisKawasan.nama.ilike(f"%{filter_jk}%"))

    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            or_(
                KSTLokasi.nama.ilike(search),
                WilayahProvinsi.nama.ilike(search),
                WilayahKabupatenKota.nama.ilike(search),
                KSTLokasi.deskripsi.ilike(search)
            )
        )

    results = query.all()

    if fokus:
        fokus_lower = fokus.lower()
        results = [
            r for r in results 
            if any(fokus_lower in str(item).lower() for item in (r.tema_riset or []))
        ]

    if fasilitas:
        fasilitas_lower = fasilitas.lower()
        results = [
            r for r in results
            if any(fasilitas_lower in str(item.get("tipe", "")).lower() or fasilitas_lower in str(item.get("nama", "")).lower() for item in (r.fasilitas or []))
        ]

    if kolaborasi:
        kolab_lower = kolaborasi.lower()
        results = [
            r for r in results
            if any(kolab_lower in str(item).lower() for item in (getattr(r, "or_terkait", None) or []))
        ]

    return results


@router.get("/field-labels")
def get_field_labels(db: Session = Depends(get_db)):
    """Daftar master label field opsional dari tabel label_data_lokasi"""
    labels = db.query(LabelDataLokasi).order_by(LabelDataLokasi.nama.asc()).all()
    return [
        {
            "id": str(lbl.id),
            "nama": lbl.nama,
            "slug": lbl.slug,
            "placeholder": lbl.placeholder,
            "icon": lbl.icon,
        }
        for lbl in labels
    ]


@router.post("/field-labels", status_code=status.HTTP_201_CREATED)
def create_field_label(
    payload: LabelDataLokasiCreate,
    db: Session = Depends(get_db)
):
    """Tambah master label data lokasi baru ke label_data_lokasi"""
    import re
    slug = payload.slug or re.sub(r'[\s\W-]+', '-', payload.nama.lower().strip()).strip('-')
    existing = db.query(LabelDataLokasi).filter(
        (LabelDataLokasi.slug == slug) | (LabelDataLokasi.nama.ilike(payload.nama.strip()))
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Label data lokasi '{payload.nama}' sudah terdaftar"
        )
    lbl = LabelDataLokasi(
        id=uuid.uuid4(),
        nama=payload.nama.strip(),
        slug=slug,
        placeholder=payload.placeholder,
        icon=payload.icon or "FileText"
    )
    db.add(lbl)
    db.commit()
    db.refresh(lbl)
    return {
        "id": str(lbl.id),
        "nama": lbl.nama,
        "slug": lbl.slug,
        "placeholder": lbl.placeholder,
        "icon": lbl.icon,
    }


@router.put("/field-labels/{id}")
def update_field_label(
    id: str,
    payload: LabelDataLokasiUpdate,
    db: Session = Depends(get_db)
):
    """Perbarui master label data lokasi di tabel label_data_lokasi"""
    try:
        val_uuid = uuid.UUID(id)
        lbl = db.query(LabelDataLokasi).filter(LabelDataLokasi.id == val_uuid).first()
    except ValueError:
        lbl = db.query(LabelDataLokasi).filter(LabelDataLokasi.slug == id).first()
    if not lbl:
        raise HTTPException(status_code=404, detail="Label data lokasi tidak ditemukan")

    if payload.nama is not None:
        lbl.nama = payload.nama.strip()
    if payload.slug is not None:
        lbl.slug = payload.slug.strip()
    if payload.placeholder is not None:
        lbl.placeholder = payload.placeholder.strip()
    if payload.icon is not None:
        lbl.icon = payload.icon.strip()

    db.commit()
    db.refresh(lbl)
    return {
        "id": str(lbl.id),
        "nama": lbl.nama,
        "slug": lbl.slug,
        "tipe": lbl.tipe,
        "placeholder": lbl.placeholder,
        "icon": lbl.icon,
    }


@router.delete("/field-labels/{id}")
def delete_field_label(
    id: str,
    db: Session = Depends(get_db)
):
    """Hapus master label data lokasi dari label_data_lokasi"""
    try:
        val_uuid = uuid.UUID(id)
        lbl = db.query(LabelDataLokasi).filter(LabelDataLokasi.id == val_uuid).first()
    except ValueError:
        lbl = db.query(LabelDataLokasi).filter(LabelDataLokasi.slug == id).first()
    if not lbl:
        raise HTTPException(status_code=404, detail="Label data lokasi tidak ditemukan")

    # Periksa apakah masih digunakan oleh data lokasi pada nilai_data_lokasi
    usage_count = db.query(NilaiDataLokasi).filter(NilaiDataLokasi.field_label_id == lbl.id).count()
    if usage_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Tidak dapat menghapus label '{lbl.nama}' karena masih digunakan oleh {usage_count} data lokasi. Harap hapus atau ubah tab data pada lokasi terkait terlebih dahulu."
        )

    try:
        db.delete(lbl)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Gagal menghapus label '{lbl.nama}' karena masih terhubung dengan data lain di sistem."
        )
    return {"message": f"Label data lokasi '{lbl.nama}' berhasil dihapus", "id": str(id)}



@router.get("/terdekat")
def get_nearby_locations(
    lat: float = Query(..., description="Latitude lokasi acuan"),
    lon: float = Query(..., description="Longitude lokasi acuan"),
    radius_km: float = Query(250.0, description="Radius pencarian dalam kilometer"),
    limit: int = Query(10, description="Maksimal hasil"),
    db: Session = Depends(get_db)
):
    radius_meters = radius_km * 1000.0
    sql = text("""
        SELECT l.id, l.nama, l.slug,
               CONCAT_WS(', ', k.nama, p.nama) AS kota_provinsi,
               p.nama AS provinsi,
               g.url AS thumbnail_url,
               l.latitude, l.longitude,
               ST_Distance(l.geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) / 1000.0 AS distance_km
        FROM kst_lokasi l
        LEFT JOIN kst_provinsi p ON l.provinsi_kode = p.kode
        LEFT JOIN kst_kabupaten_kota k ON l.kabupaten_kota_kode = k.kode
        LEFT JOIN LATERAL (
            SELECT url FROM kst_galeri WHERE lokasi_id = l.id ORDER BY created_at ASC LIMIT 1
        ) g ON true
        WHERE l.geom IS NOT NULL
          AND ST_DWithin(l.geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius_meters)
        ORDER BY distance_km ASC
        LIMIT :limit;
    """)

    rows = db.execute(sql, {
        "lat": lat,
        "lon": lon,
        "radius_meters": radius_meters,
        "limit": limit
    }).mappings().all()

    results = []
    for r in rows:
        d = dict(r)
        d["id"] = str(d["id"])
        d["thumbnail_url"] = build_full_url(d.get("thumbnail_url"))
        d["distance_km"] = round(float(d.get("distance_km") or 0.0), 2)
        d["koordinat"] = {
            "latitude": d.get("latitude"),
            "longitude": d.get("longitude"),
            "lat": d.get("latitude"),
            "lng": d.get("longitude")
        }
        results.append(d)

    return results


@router.get("/{id}", response_model=LokasiDetail)
def get_location_detail(id: str, db: Session = Depends(get_db)):
    loc = None
    try:
        val_uuid = uuid.UUID(id)
        loc = db.query(KSTLokasi).filter(KSTLokasi.id == val_uuid).first()
    except ValueError:
        pass

    if not loc:
        loc = db.query(KSTLokasi).filter(KSTLokasi.slug == id).first()

    if not loc:
        import re
        slug_alt = re.sub(r'[\s\W-]+', '-', id.lower().strip()).strip('-')
        loc = db.query(KSTLokasi).filter(KSTLokasi.slug == slug_alt).first()

    if not loc:
        loc = db.query(KSTLokasi).filter(KSTLokasi.nama.ilike(id.strip())).first()

    if not loc:
        raise HTTPException(status_code=404, detail="Data lokasi tidak ditemukan")

    # 1. Sinkronisasi data galeri dari tabel kst_galeri jika ada relasi
    galeri_list = []
    if loc.galeri_items:
        sorted_items = sorted(loc.galeri_items, key=lambda g: (g.sort if g.sort is not None else 0, g.created_at))
        galeri_list = [
            {
                "id": str(g.id),
                "lokasi_id": str(g.lokasi_id),
                "tipe": g.tipe or "foto",
                "type": g.tipe or "foto",
                "url": build_full_url(g.url),
                "thumbnail_url": build_thumbnail_url(g.url),
                "caption": g.caption or "",
                "sort": g.sort if g.sort is not None else idx,
            }
            for idx, g in enumerate(sorted_items)
        ]
        loc.galeri = galeri_list

    # 2. Kumpulkan seluruh daftar gambar foto lokasi (thumbnail + galeri foto)
    gambar_urls = []
    if loc.thumbnail_url:
        full_thumb = build_full_url(loc.thumbnail_url)
        if full_thumb:
            gambar_urls.append(full_thumb)

    for g in (loc.galeri or []):
        url = g.get("url") if isinstance(g, dict) else g
        tipe = g.get("tipe") if isinstance(g, dict) else "foto"
        if tipe == "foto" and url:
            full_u = build_full_url(url)
            if full_u and full_u not in gambar_urls:
                gambar_urls.append(full_u)

    if not getattr(loc, "thumbnail_url", None) and gambar_urls:
        setattr(loc, "thumbnail_url", gambar_urls[0])

    setattr(loc, "gambar", gambar_urls)
    setattr(loc, "deskripsi_profil", loc.deskripsi)

    # Pastikan kota_provinsi tidak kosong jika relasi wilayah tersedia
    p_nama = loc.provinsi.nama if loc.provinsi else (loc.provinsi_nama or "")
    k_nama = loc.kabupaten_kota.nama if loc.kabupaten_kota else (loc.kabupaten_kota_nama or "")
    if not loc.kota_provinsi and (p_nama or k_nama):
        loc.kota_provinsi = f"{k_nama}, {p_nama}" if k_nama and p_nama else (p_nama or k_nama or "")

    return loc


# =========================================================================
# 🛠️ 2. ADMIN CRUD LOKASI / KST (CMS)
# =========================================================================

@router.post("", response_model=LokasiDetail, status_code=status.HTTP_201_CREATED)
def create_location(
    payload: LokasiCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    import re
    final_slug = (payload.slug or "").strip()
    if not final_slug and payload.nama:
        base_slug = re.sub(r'[^a-z0-9]+', '-', payload.nama.lower()).strip('-')
        final_slug = base_slug or f"lokasi-{int(datetime.utcnow().timestamp())}"
        counter = 1
        test_slug = final_slug
        while db.query(KSTLokasi).filter(KSTLokasi.slug == test_slug).first():
            test_slug = f"{final_slug}-{counter}"
            counter += 1
        final_slug = test_slug
    elif final_slug:
        existing = db.query(KSTLokasi).filter(KSTLokasi.slug == final_slug).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Slug '{final_slug}' sudah digunakan.")

    data = payload.dict()
    data["slug"] = final_slug
    galeri_data = data.pop("galeri", None)
    extra_fields_data = data.pop("extra_fields", None)
    jenis_kawasan_nama = (
        data.pop("jenis_kawasan_nama", None) 
        or data.pop("kawasan_nama", None) 
        or data.pop("instansi_nama", None)
    )

    lat = data.get("latitude")
    lon = data.get("longitude")
    data["geom"] = _set_point_geom(lat, lon)
    if not data.get("deskripsi") and data.get("deskripsi_profil"):
        data["deskripsi"] = data["deskripsi_profil"]

    valid_cols = {c.name for c in KSTLokasi.__table__.columns}
    loc_data = {k: v for k, v in data.items() if k in valid_cols}
    new_loc = KSTLokasi(**loc_data)
    
    jenis_kawasan_id = None
    if jenis_kawasan_nama and jenis_kawasan_nama.strip():
        nama_jk = jenis_kawasan_nama.strip()
        slug_jk = nama_jk.lower().replace(" ", "-")
        jk_obj = db.query(KSTJenisKawasan).filter(KSTJenisKawasan.nama.ilike(nama_jk)).first()
        if not jk_obj:
            jk_obj = KSTJenisKawasan(nama=nama_jk, slug=slug_jk)
            db.add(jk_obj)
            db.commit()
            db.refresh(jk_obj)
        jenis_kawasan_id = jk_obj.id
    new_loc.jenis_kawasan_id = jenis_kawasan_id

    db.add(new_loc)
    db.commit()
    db.refresh(new_loc)

    if galeri_data:
        _sync_galeri_items(db, new_loc.id, galeri_data)
        db.commit()
        db.refresh(new_loc)

    if extra_fields_data:
        _sync_extra_fields(db, new_loc.id, extra_fields_data)
        db.commit()
        db.refresh(new_loc)

    setattr(new_loc, "deskripsi_profil", new_loc.deskripsi)
    return new_loc


@router.put("/{id}", response_model=LokasiDetail)
def update_location(
    id: uuid.UUID,
    payload: LokasiUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    loc = db.query(KSTLokasi).filter(KSTLokasi.id == id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Data lokasi tidak ditemukan")

    update_data = payload.dict(exclude_unset=True)
    galeri_data = update_data.pop("galeri", None)
    extra_fields_data = update_data.pop("extra_fields", None)
    if "slug" in update_data and update_data["slug"] != loc.slug:
        check_slug = db.query(KSTLokasi).filter(KSTLokasi.slug == update_data["slug"]).first()
        if check_slug:
            raise HTTPException(status_code=400, detail="Slug sudah dipakai oleh lokasi lain.")

    if "latitude" in update_data:
        loc.latitude = update_data["latitude"]
    if "longitude" in update_data:
        loc.longitude = update_data["longitude"]
    if "latitude" in update_data or "longitude" in update_data:
        loc.geom = _set_point_geom(loc.latitude, loc.longitude)

    if "deskripsi" in update_data or "deskripsi_profil" in update_data:
        d = update_data.get("deskripsi") if "deskripsi" in update_data else update_data.get("deskripsi_profil")
        clean_d = (d or "").strip()
        text_only = re.sub(r'<[^>]*>', '', clean_d).strip()
        loc.deskripsi = clean_d if text_only else None

    has_jk = any(k in update_data for k in ["jenis_kawasan_nama", "kawasan_nama", "instansi_nama", "jenis_kawasan_id"])
    if has_jk:
        jk_name = (
            update_data.pop("jenis_kawasan_nama", None) 
            or update_data.pop("kawasan_nama", None) 
            or update_data.pop("instansi_nama", None)
        )
        if jk_name and str(jk_name).strip():
            nama_jk = str(jk_name).strip()
            slug_jk = nama_jk.lower().replace(" ", "-")
            jk_obj = db.query(KSTJenisKawasan).filter(KSTJenisKawasan.nama.ilike(nama_jk)).first()
            if not jk_obj:
                jk_obj = KSTJenisKawasan(nama=nama_jk, slug=slug_jk)
                db.add(jk_obj)
                db.flush()
            loc.jenis_kawasan_id = jk_obj.id
        elif "jenis_kawasan_id" in update_data and update_data["jenis_kawasan_id"]:
            loc.jenis_kawasan_id = update_data["jenis_kawasan_id"]
        else:
            loc.jenis_kawasan_id = None

    valid_cols = {c.name for c in KSTLokasi.__table__.columns}
    for field, val in update_data.items():
        if field in valid_cols and field not in ["latitude", "longitude", "geom", "deskripsi", "jenis_kawasan_id"]:
            if isinstance(val, str):
                cleaned = val.strip()
                setattr(loc, field, cleaned if cleaned else None)
            else:
                setattr(loc, field, val)

    if galeri_data is not None:
        _sync_galeri_items(db, loc.id, galeri_data)

    if extra_fields_data is not None:
        _sync_extra_fields(db, loc.id, extra_fields_data)

    db.commit()
    db.refresh(loc)
    setattr(loc, "deskripsi_profil", loc.deskripsi)
    return loc


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_location(
    id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    loc = db.query(KSTLokasi).filter(KSTLokasi.id == id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Data lokasi tidak ditemukan")

    db.delete(loc)
    db.commit()
    return {"message": "Data lokasi berhasil dihapus", "id": str(id)}



# =========================================================================
# 📥📤 IMPORT & EXPORT DATA LOKASI (EXCEL & CSV)
# =========================================================================

@router.get("/template", summary="Unduh Template Import Lokasi (Excel / CSV)")
def download_location_template(
    format: str = Query("xlsx", pattern="^(xlsx|csv)$"),
    db: Session = Depends(get_db)
):
    from app.services.lokasi_import_export import generate_template
    bio, filename, media_type = generate_template(db, format=format)
    return Response(
        content=bio.getvalue(),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/export", summary="Export Seluruh Data Lokasi (Excel / CSV)")
def export_locations_data(
    format: str = Query("xlsx", pattern="^(xlsx|csv)$"),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    from app.services.lokasi_import_export import export_lokasi
    bio, filename, media_type = export_lokasi(db, format=format, search=search)
    return Response(
        content=bio.getvalue(),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/import", summary="Import Data Lokasi dari File Excel / CSV")
async def import_locations_data(
    file: UploadFile = File(...),
    mode: str = Form("create_or_update"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    from app.services.lokasi_import_export import import_lokasi
    ext = file.filename.lower()
    if not (ext.endswith(".xlsx") or ext.endswith(".xls") or ext.endswith(".csv")):
        raise HTTPException(
            status_code=400,
            detail="Format file tidak didukung. Harap unggah file spreadsheet Excel (.xlsx) atau file teks (.csv)."
        )
    file_bytes = await file.read()
    result = import_lokasi(db, file_bytes, file.filename, mode=mode)
    return result


# =========================================================================
# ⚙️ ADMIN ROUTER UNTUK CMS (/admin/lokasi)
# =========================================================================
admin_router = APIRouter()

admin_router.add_api_route(
    "",
    get_map_locations,
    methods=["GET"],
    response_model=List[LokasiMapItem],
    summary="Daftar Lokasi untuk Manajemen CMS"
)
admin_router.add_api_route(
    "/peta",
    get_map_locations,
    methods=["GET"],
    response_model=List[LokasiMapItem],
    summary="Daftar Lokasi Peta CMS"
)
admin_router.add_api_route(
    "/template",
    download_location_template,
    methods=["GET"],
    summary="Unduh Template Import Lokasi"
)
admin_router.add_api_route(
    "/export",
    export_locations_data,
    methods=["GET"],
    summary="Export Data Lokasi"
)
admin_router.add_api_route(
    "/import",
    import_locations_data,
    methods=["POST"],
    summary="Import Data Lokasi dari File"
)
admin_router.add_api_route(
    "/field-labels",
    get_field_labels,
    methods=["GET"],
    summary="Daftar Master Label Field Opsional"
)
admin_router.add_api_route(
    "/{id}",
    get_location_detail,
    methods=["GET"],
    response_model=LokasiDetail,
    summary="Detail Lokasi untuk Form CMS"
)
admin_router.add_api_route(
    "",
    create_location,
    methods=["POST"],
    response_model=LokasiDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Tambah Lokasi Baru"
)
admin_router.add_api_route(
    "/{id}",
    update_location,
    methods=["PUT"],
    response_model=LokasiDetail,
    summary="Perbarui Data Lokasi"
)
admin_router.add_api_route(
    "/{id}",
    delete_location,
    methods=["DELETE"],
    status_code=status.HTTP_200_OK,
    summary="Hapus Data Lokasi"
)
admin_router.add_api_route(
    "/field-labels",
    create_field_label,
    methods=["POST"],
    status_code=status.HTTP_201_CREATED,
    summary="Tambah Master Label Data Lokasi"
)
admin_router.add_api_route(
    "/field-labels/{id}",
    update_field_label,
    methods=["PUT"],
    summary="Perbarui Master Label Data Lokasi"
)
admin_router.add_api_route(
    "/field-labels/{id}",
    delete_field_label,
    methods=["DELETE"],
    status_code=status.HTTP_200_OK,
    summary="Hapus Master Label Data Lokasi"
)

