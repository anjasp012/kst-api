import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, text
from geoalchemy2.elements import WKTElement
from geoalchemy2 import functions as geofunc

from app.db.session import get_db
from app.models.lokasi import KSTLokasi
from app.models.jenis_kawasan import KSTJenisKawasan
from app.models.galeri import KSTGaleri
from app.models.user import User
from app.schemas.lokasi import (
    LokasiMapItem, 
    LokasiDetail, 
    LokasiCreate, 
    LokasiUpdate, 
    LokasiRingkasItem,
    LokasiRingkasListResponse,
    LokasiFilterRequest
)
from app.core.helpers import build_full_url
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
    
    for item in galeri_data:
        if isinstance(item, str):
            url_str = item.strip()
            if not url_str:
                continue
            is_video = any(url_str.lower().endswith(ext) for ext in video_exts)
            tipe = "video" if is_video else "foto"
            new_g = KSTGaleri(
                lokasi_id=lokasi_id,
                tipe=tipe,
                url=url_str
            )
            db.add(new_g)
        elif isinstance(item, dict):
            url_str = item.get("url", "").strip()
            if not url_str:
                continue
            tipe = (item.get("tipe") or "foto").lower().strip()
            if tipe not in ("foto", "video"):
                is_video = any(url_str.lower().endswith(ext) for ext in video_exts)
                tipe = "video" if is_video else "foto"
            new_g = KSTGaleri(
                lokasi_id=lokasi_id,
                tipe=tipe,
                url=url_str
            )
            db.add(new_g)
    db.flush()


# =========================================================================
# 🗺️ 1. PETA INTERAKTIF JELAJAHI KAWASAN TERPADU BRIN & SPASIAL (PUBLIC)
# =========================================================================

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

    results = []
    for loc in rows:
        prov = ""
        kab = ""
        if loc.kota_provinsi:
            parts = [p.strip() for p in loc.kota_provinsi.split(",")]
            if len(parts) >= 2:
                kab = parts[0]
                prov = parts[1]
            else:
                kab = parts[0]
                prov = loc.wilayah or ""
        elif loc.wilayah:
            prov = loc.wilayah

        fokus_list = []
        if loc.riset and isinstance(loc.riset, list):
            for r in loc.riset:
                if isinstance(r, dict):
                    val = r.get("tema") or r.get("bidang")
                    if val and val not in fokus_list:
                        fokus_list.append(val)
                elif isinstance(r, str) and r not in fokus_list:
                    fokus_list.append(r)

        if hasattr(loc, "tema_riset") and loc.tema_riset:
            for t in loc.tema_riset:
                if t and t not in fokus_list:
                    fokus_list.append(t)

        results.append({
            "id": loc.id,
            "nama": loc.nama,
            "slug": loc.slug,
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
            "deskripsi": loc.deskripsi_profil,
            "fokus_riset": fokus_list
        })
    return {
        "total": len(results),
        "data": results
    }


@router.post("/filter", response_model=LokasiRingkasListResponse)
def filter_locations(
    payload: Optional[LokasiFilterRequest] = None,
    db: Session = Depends(get_db)
):
    query = db.query(KSTLokasi).filter(KSTLokasi.is_draft == False)

    wilayah_list = payload.wilayah if payload and payload.wilayah else []
    jenis_kawasan_list = payload.jenis_kawasan if payload and payload.jenis_kawasan else []
    fokus_riset_list = payload.fokus_riset if payload and payload.fokus_riset else []
    search_text = (payload.input or payload.q or "").strip() if payload else ""

    # 1. Filter input teks pencarian bebas
    if search_text:
        s = f"%{search_text}%"
        query = query.filter(
            or_(
                KSTLokasi.nama.ilike(s),
                KSTLokasi.kota_provinsi.ilike(s),
                KSTLokasi.deskripsi_profil.ilike(s)
            )
        )

    # 2. Filter wilayah (bisa lebih dari 1 wilayah)
    if wilayah_list:
        wil_conditions = []
        for w in wilayah_list:
            if w and w.strip():
                clean_w = f"%{w.strip()}%"
                wil_conditions.append(KSTLokasi.wilayah.ilike(clean_w))
                wil_conditions.append(KSTLokasi.kota_provinsi.ilike(clean_w))
        if wil_conditions:
            query = query.filter(or_(*wil_conditions))

    # 3. Filter jenis kawasan (bisa lebih dari 1 jenis kawasan)
    if jenis_kawasan_list:
        jk_conditions = []
        for jk in jenis_kawasan_list:
            if jk and jk.strip():
                clean_jk = f"%{jk.strip()}%"
                jk_conditions.append(KSTJenisKawasan.nama.ilike(clean_jk))
        if jk_conditions:
            query = query.join(
                KSTJenisKawasan,
                or_(
                    KSTLokasi.jenis_kawasan_id == KSTJenisKawasan.id,
                    KSTLokasi.kawasan_id == KSTJenisKawasan.id
                )
            ).filter(or_(*jk_conditions))

    rows = query.order_by(KSTLokasi.nama.asc()).all()

    # 4. Filter fokus riset (bisa lebih dari 1 fokus riset)
    if fokus_riset_list:
        clean_fokus = [f.lower().strip() for f in fokus_riset_list if f and f.strip()]
        if clean_fokus:
            filtered_rows = []
            for loc in rows:
                loc_themes = []
                if loc.riset and isinstance(loc.riset, list):
                    for r in loc.riset:
                        if isinstance(r, dict):
                            val = r.get("tema") or r.get("bidang")
                            if val:
                                loc_themes.append(str(val).lower().strip())
                        elif isinstance(r, str):
                            loc_themes.append(r.lower().strip())
                if hasattr(loc, "tema_riset") and loc.tema_riset:
                    for t in loc.tema_riset:
                        if t:
                            loc_themes.append(str(t).lower().strip())

                # Cek apakah lokasi memiliki salah satu fokus yang dipilih
                match = any(
                    any(target in lt or lt in target for lt in loc_themes)
                    for target in clean_fokus
                )
                if match:
                    filtered_rows.append(loc)
            rows = filtered_rows

    results = []
    for loc in rows:
        prov = ""
        kab = ""
        if loc.kota_provinsi:
            parts = [p.strip() for p in loc.kota_provinsi.split(",")]
            if len(parts) >= 2:
                kab = parts[0]
                prov = parts[1]
            else:
                kab = parts[0]
                prov = loc.wilayah or ""
        elif loc.wilayah:
            prov = loc.wilayah

        fokus_list = []
        if loc.riset and isinstance(loc.riset, list):
            for r in loc.riset:
                if isinstance(r, dict):
                    val = r.get("tema") or r.get("bidang")
                    if val and val not in fokus_list:
                        fokus_list.append(val)
                elif isinstance(r, str) and r not in fokus_list:
                    fokus_list.append(r)

        if hasattr(loc, "tema_riset") and loc.tema_riset:
            for t in loc.tema_riset:
                if t and t not in fokus_list:
                    fokus_list.append(t)

        results.append({
            "id": loc.id,
            "nama": loc.nama,
            "slug": loc.slug,
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
            "deskripsi": loc.deskripsi_profil,
            "fokus_riset": fokus_list
        })
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
    query = db.query(KSTLokasi)

    if is_draft is not None:
        query = query.filter(KSTLokasi.is_draft == is_draft)

    if wilayah:
        query = query.filter(KSTLokasi.wilayah.ilike(f"%{wilayah}%"))

    filter_jk = jenis_kawasan or kawasan
    if filter_jk:
        query = query.join(
            KSTJenisKawasan, 
            or_(
                KSTLokasi.jenis_kawasan_id == KSTJenisKawasan.id,
                KSTLokasi.kawasan_id == KSTJenisKawasan.id
            )
        ).filter(KSTJenisKawasan.nama.ilike(f"%{filter_jk}%"))

    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                KSTLokasi.nama.ilike(search),
                KSTLokasi.kota_provinsi.ilike(search),
                KSTLokasi.deskripsi_profil.ilike(search)
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
            if any(kolab_lower in str(item).lower() for item in (r.potensi_kolaborasi or []))
        ]

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
        raise HTTPException(status_code=404, detail="Data lokasi tidak ditemukan")

    # Sinkronisasi data galeri dari tabel kst_galeri jika ada relasi
    galeri_list = []
    if loc.galeri_items:
        galeri_list = [
            {
                "id": str(g.id),
                "lokasi_id": str(g.lokasi_id),
                "tipe": g.tipe or "foto",
                "url": g.url,
            }
            for g in loc.galeri_items
        ]
        loc.galeri = galeri_list

    # Kumpulkan seluruh daftar gambar foto lokasi (thumbnail + galeri foto)
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

    setattr(loc, "gambar", gambar_urls)

    return loc


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
        SELECT id, nama, slug, kota_provinsi, wilayah, thumbnail_url,
               latitude, longitude,
               ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) / 1000.0 AS distance_km
        FROM kst_lokasi
        WHERE geom IS NOT NULL
          AND ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius_meters)
        ORDER BY distance_km ASC
        LIMIT :limit;
    """)

    rows = db.execute(sql, {
        "lat": lat,
        "lon": lon,
        "radius_meters": radius_meters,
        "limit": limit
    }).mappings().all()

    return [dict(r) for r in rows]


# =========================================================================
# 🛠️ 2. ADMIN CRUD LOKASI / KST (CMS)
# =========================================================================

@router.post("", response_model=LokasiDetail, status_code=status.HTTP_201_CREATED)
def create_location(
    payload: LokasiCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(KSTLokasi).filter(KSTLokasi.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Slug '{payload.slug}' sudah digunakan.")

    data = payload.dict()
    galeri_data = data.pop("galeri", None)
    jenis_kawasan_nama = (
        data.pop("jenis_kawasan_nama", None) 
        or data.pop("kawasan_nama", None) 
        or data.pop("instansi_nama", None)
    )

    lat = data.get("latitude")
    lon = data.get("longitude")
    data["geom"] = _set_point_geom(lat, lon)

    new_loc = KSTLokasi(**data)
    
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
    new_loc.kawasan_id = jenis_kawasan_id
    new_loc.instansi_id = jenis_kawasan_id

    db.add(new_loc)
    db.commit()
    db.refresh(new_loc)

    if galeri_data:
        _sync_galeri_items(db, new_loc.id, galeri_data)
        db.commit()
        db.refresh(new_loc)

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
    if "slug" in update_data and update_data["slug"] != loc.slug:
        check_slug = db.query(KSTLokasi).filter(KSTLokasi.slug == update_data["slug"]).first()
        if check_slug:
            raise HTTPException(status_code=400, detail="Slug sudah dipakai oleh lokasi lain.")

    if "latitude" in update_data or "longitude" in update_data:
        lat = update_data.get("latitude", loc.latitude)
        lon = update_data.get("longitude", loc.longitude)
        update_data["geom"] = _set_point_geom(lat, lon)

    jenis_kawasan_nama = (
        update_data.pop("jenis_kawasan_nama", None) 
        or update_data.pop("kawasan_nama", None) 
        or update_data.pop("instansi_nama", None)
    )

    for field, val in update_data.items():
        setattr(loc, field, val)

    if jenis_kawasan_nama and jenis_kawasan_nama.strip():
        nama_jk = jenis_kawasan_nama.strip()
        slug_jk = nama_jk.lower().replace(" ", "-")
        jk_obj = db.query(KSTJenisKawasan).filter(KSTJenisKawasan.nama.ilike(nama_jk)).first()
        if not jk_obj:
            jk_obj = KSTJenisKawasan(nama=nama_jk, slug=slug_jk)
            db.add(jk_obj)
            db.commit()
            db.refresh(jk_obj)
        loc.jenis_kawasan_id = jk_obj.id
        loc.kawasan_id = jk_obj.id
        loc.instansi_id = jk_obj.id

    if galeri_data is not None:
        _sync_galeri_items(db, loc.id, galeri_data)

    db.commit()
    db.refresh(loc)
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
