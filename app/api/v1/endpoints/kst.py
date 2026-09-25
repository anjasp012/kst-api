import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, text
from geoalchemy2.elements import WKTElement
from geoalchemy2 import functions as geofunc

from app.db.session import get_db
from app.models.kst import KSTLocation
from app.models.instansi import KSTInstansi
from app.models.user import User
from app.schemas.kst import KSTMapItem, KSTDetail, KSTCreate, KSTUpdate
from app.api.v1.deps import get_current_admin

router = APIRouter()


def _set_point_geom(lat: Optional[float], lon: Optional[float]):
    if lat is not None and lon is not None:
        return WKTElement(f"POINT({lon} {lat})", srid=4326)
    return None


# =========================================================================
# 🗺️ 1. PETA INTERAKTIF WONDERFUL BRIN & SPASIAL (PUBLIC)
# =========================================================================

@router.get("/map", response_model=List[KSTMapItem])
def get_map_locations(
    wilayah: Optional[str] = Query(None, description="Filter wilayah: Sumatera, Jawa, Kalimantan, Sulawesi, Nusa Tenggara, Maluku & Papua"),
    fokus: Optional[str] = Query(None, description="Filter tema riset / fokus utama"),
    fasilitas: Optional[str] = Query(None, description="Filter tipe fasilitas"),
    kolaborasi: Optional[str] = Query(None, description="Filter potensi kolaborasi"),
    q: Optional[str] = Query(None, description="Pencarian bebas nama / kota / deskripsi"),
    db: Session = Depends(get_db)
):
    """
    Endpoint untuk Peta Interaktif Wonderful BRIN.
    Mengembalikan titik pin KST di seluruh Indonesia dengan dukungan filter multi-kategori.
    """
    query = db.query(KSTLocation).filter(KSTLocation.is_active == True)

    if wilayah:
        query = query.filter(KSTLocation.wilayah.ilike(f"%{wilayah}%"))

    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                KSTLocation.nama.ilike(search),
                KSTLocation.kota_provinsi.ilike(search),
                KSTLocation.deskripsi_profil.ilike(search)
            )
        )

    results = query.all()

    # Filter in-memory untuk JSON array fields jika disediakan
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


@router.get("/locations/{id_or_slug}", response_model=KSTDetail)
def get_kst_detail(id_or_slug: str, db: Session = Depends(get_db)):
    """
    Mengambil data detail lengkap KST (6 Tab: Profil, Fasilitas, Riset, Dampak, Kolaborasi, Galeri)
    berdasarkan UUID atau slug URL.
    """
    kst = None
    try:
        val_uuid = uuid.UUID(id_or_slug)
        kst = db.query(KSTLocation).filter(KSTLocation.id == val_uuid).first()
    except ValueError:
        pass

    if not kst:
        kst = db.query(KSTLocation).filter(KSTLocation.slug == id_or_slug).first()

    if not kst:
        raise HTTPException(status_code=404, detail="Data KST tidak ditemukan")

    return kst


@router.get("/nearby")
def get_nearby_kst(
    lat: float = Query(..., description="Latitude lokasi acuan"),
    lon: float = Query(..., description="Longitude lokasi acuan"),
    radius_km: float = Query(250.0, description="Radius pencarian dalam kilometer"),
    limit: int = Query(10, description="Maksimal hasil"),
    db: Session = Depends(get_db)
):
    """
    Query spasial PostGIS untuk menemukan KST terdekat dari koordinat tertentu.
    Menggunakan fungsi ST_DistanceSphere pada koordinat WGS84.
    """
    radius_meters = radius_km * 1000.0
    sql = text("""
        SELECT id, nama, slug, kota_provinsi, wilayah, thumbnail_url,
               latitude, longitude,
               ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) / 1000.0 AS distance_km
        FROM kst_locations
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
# 🛠️ 3. ADMIN CRUD KST (CMS)
# =========================================================================

@router.post("/locations", response_model=KSTDetail)
def create_kst_location(
    payload: KSTCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Tambah data Kawasan Sains dan Teknologi (KST) baru via CMS.
    """
    existing = db.query(KSTLocation).filter(KSTLocation.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Slug '{payload.slug}' sudah digunakan.")

    data = payload.dict()
    instansi_nama = data.pop("instansi_nama", None)

    lat = data.get("latitude")
    lon = data.get("longitude")
    data["geom"] = _set_point_geom(lat, lon)

    new_kst = KSTLocation(**data)
    
    instansi_id = None
    if instansi_nama and instansi_nama.strip():
        nama_instansi = instansi_nama.strip()
        slug_instansi = nama_instansi.lower().replace(" ", "-")
        inst_obj = db.query(KSTInstansi).filter(KSTInstansi.nama.ilike(nama_instansi)).first()
        if not inst_obj:
            inst_obj = KSTInstansi(nama=nama_instansi, slug=slug_instansi)
            db.add(inst_obj)
            db.commit()
            db.refresh(inst_obj)
        instansi_id = inst_obj.id
    new_kst.instansi_id = instansi_id

    db.add(new_kst)
    db.commit()
    db.refresh(new_kst)
    return new_kst


@router.put("/locations/{kst_id}", response_model=KSTDetail)
def update_kst_location(
    kst_id: uuid.UUID,
    payload: KSTUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Perbarui data KST via CMS.
    """
    kst = db.query(KSTLocation).filter(KSTLocation.id == kst_id).first()
    if not kst:
        raise HTTPException(status_code=404, detail="Data KST tidak ditemukan")

    update_data = payload.dict(exclude_unset=True)
    if "slug" in update_data and update_data["slug"] != kst.slug:
        check_slug = db.query(KSTLocation).filter(KSTLocation.slug == update_data["slug"]).first()
        if check_slug:
            raise HTTPException(status_code=400, detail="Slug sudah dipakai oleh KST lain.")

    # Sinkronisasi PostGIS Geometry jika koordinat berubah
    if "latitude" in update_data or "longitude" in update_data:
        lat = update_data.get("latitude", kst.latitude)
        lon = update_data.get("longitude", kst.longitude)
        update_data["geom"] = _set_point_geom(lat, lon)

    instansi_nama = update_data.pop("instansi_nama", None)
    for field, val in update_data.items():
        setattr(kst, field, val)

    if instansi_nama and instansi_nama.strip():
        nama_instansi = instansi_nama.strip()
        slug_instansi = nama_instansi.lower().replace(" ", "-")
        inst_obj = db.query(KSTInstansi).filter(KSTInstansi.nama.ilike(nama_instansi)).first()
        if not inst_obj:
            inst_obj = KSTInstansi(nama=nama_instansi, slug=slug_instansi)
            db.add(inst_obj)
            db.commit()
            db.refresh(inst_obj)
        kst.instansi_id = inst_obj.id

    db.commit()
    db.refresh(kst)
    return kst


@router.delete("/locations/{kst_id}")
def delete_kst_location(
    kst_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Hapus data KST via CMS.
    """
    kst = db.query(KSTLocation).filter(KSTLocation.id == kst_id).first()
    if not kst:
        raise HTTPException(status_code=404, detail="Data KST tidak ditemukan")

    db.delete(kst)
    db.commit()
    return {"message": "Data KST berhasil dihapus", "id": str(kst_id)}


