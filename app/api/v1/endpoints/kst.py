import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, text
from geoalchemy2.elements import WKTElement
from geoalchemy2 import functions as geofunc

from app.db.session import get_db
from app.models.kst import KSTLocation
from app.models.partner import RegionalPartner
from app.models.user import User
from app.schemas.kst import KSTMapItem, KSTDetail, KSTCreate, KSTUpdate
from app.schemas.partner import PartnerResponse, PartnerCreate, PartnerUpdate
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
            if any(fokus_lower in str(item).lower() for item in (r.fokus_utama or []))
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
        SELECT id, nama, slug, kota_provinsi, wilayah, thumbnail_url, fokus_utama,
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
# 🏛️ 2. DIREKTORI MITRA DAERAH (BAPPEDA / BAPPERIDA / BRIDA)
# =========================================================================

@router.get("/partners", response_model=List[PartnerResponse])
def get_regional_partners(
    jenis: Optional[str] = Query(None, description="Filter jenis: BRIDA, BAPPERIDA, BAPPEDA"),
    wilayah: Optional[str] = Query(None, description="Filter wilayah"),
    q: Optional[str] = Query(None, description="Cari nama organisasi / alamat"),
    limit: int = Query(100, description="Limit data"),
    db: Session = Depends(get_db)
):
    """
    Daftar Mitra Riset Daerah (BAPPEDA / BAPPERIDA / BRIDA) dari data spreadsheet.
    """
    query = db.query(RegionalPartner)
    if jenis:
        query = query.filter(RegionalPartner.jenis == jenis.upper())
    if wilayah:
        query = query.filter(RegionalPartner.wilayah.ilike(f"%{wilayah}%"))
    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                RegionalPartner.nama_organisasi.ilike(search),
                RegionalPartner.alamat.ilike(search)
            )
        )

    return query.limit(limit).all()


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
    lat = data.get("latitude")
    lon = data.get("longitude")
    data["geom"] = _set_point_geom(lat, lon)

    new_kst = KSTLocation(**data)
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

    for field, val in update_data.items():
        setattr(kst, field, val)

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


# =========================================================================
# 🛠️ 4. ADMIN CRUD MITRA DAERAH (CMS)
# =========================================================================

@router.post("/partners", response_model=PartnerResponse)
def create_regional_partner(
    payload: PartnerCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Tambah instansi mitra daerah baru via CMS.
    """
    data = payload.dict()
    lat = data.get("latitude")
    lon = data.get("longitude")
    data["geom"] = _set_point_geom(lat, lon)

    partner = RegionalPartner(**data)
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


@router.put("/partners/{partner_id}", response_model=PartnerResponse)
def update_regional_partner(
    partner_id: uuid.UUID,
    payload: PartnerUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Perbarui data mitra daerah via CMS.
    """
    partner = db.query(RegionalPartner).filter(RegionalPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Data mitra daerah tidak ditemukan")

    update_data = payload.dict(exclude_unset=True)
    if "latitude" in update_data or "longitude" in update_data:
        lat = update_data.get("latitude", partner.latitude)
        lon = update_data.get("longitude", partner.longitude)
        update_data["geom"] = _set_point_geom(lat, lon)

    for field, val in update_data.items():
        setattr(partner, field, val)

    db.commit()
    db.refresh(partner)
    return partner


@router.delete("/partners/{partner_id}")
def delete_regional_partner(
    partner_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Hapus data mitra daerah via CMS.
    """
    partner = db.query(RegionalPartner).filter(RegionalPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Data mitra daerah tidak ditemukan")

    db.delete(partner)
    db.commit()
    return {"message": "Data mitra daerah berhasil dihapus", "id": str(partner_id)}

