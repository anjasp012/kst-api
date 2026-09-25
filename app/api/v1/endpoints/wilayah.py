from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.wilayah import WilayahProvince, WilayahRegency
from app.models.user import User
from app.schemas.wilayah import (
    WilayahProvinceItem,
    WilayahProvinceCreate,
    WilayahProvinceUpdate,
    WilayahRegencyItem,
    WilayahRegencyCreate,
    WilayahRegencyUpdate,
)
from app.api.v1.deps import get_current_admin

router = APIRouter()


# ==========================================
# 🇮🇩 1. PROVINSI
# ==========================================

@router.get("/provinces", response_model=List[WilayahProvinceItem])
def get_provinces(
    wilayah: Optional[str] = Query(None, description="Filter zona wilayah: Sumatera, Jawa, Kalimantan, dll."),
    q: Optional[str] = Query(None, description="Pencarian nama atau kode provinsi"),
    db: Session = Depends(get_db)
):
    """
    Mengambil daftar resmi Provinsi di Indonesia.
    """
    query = db.query(
        WilayahProvince,
        func.count(WilayahRegency.kode).label("total_regencies")
    ).outerjoin(WilayahRegency, WilayahProvince.kode == WilayahRegency.province_kode)
    if q:
        search = f"%{q.strip()}%"
        query = query.filter((WilayahProvince.nama.ilike(search)) | (WilayahProvince.kode.ilike(search)))

    results = query.group_by(WilayahProvince.kode).order_by(WilayahProvince.kode.asc()).all()

    return [
        WilayahProvinceItem(
            id=p.kode,
            kode=p.kode,
            nama=p.nama,
            name=p.nama,
            total_regencies=total or 0
        )
        for p, total in results
    ]


@router.post("/provinces", response_model=WilayahProvinceItem, status_code=status.HTTP_201_CREATED)
def create_province(
    payload: WilayahProvinceCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Tambah provinsi baru ke database.
    """
    existing = db.query(WilayahProvince).filter(WilayahProvince.kode == payload.kode.strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provinsi dengan kode '{payload.kode}' sudah ada ({existing.nama})"
        )

    prov = WilayahProvince(
        kode=payload.kode.strip(),
        nama=payload.nama.strip()
    )
    db.add(prov)
    db.commit()
    db.refresh(prov)
    return WilayahProvinceItem(
        id=prov.kode,
        kode=prov.kode,
        nama=prov.nama,
        name=prov.nama,
        total_regencies=0
    )


@router.put("/provinces/{kode}", response_model=WilayahProvinceItem)
def update_province(
    kode: str,
    payload: WilayahProvinceUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Ubah data provinsi (nama atau kelompok wilayah).
    """
    prov = db.query(WilayahProvince).filter(WilayahProvince.kode == kode).first()
    if not prov:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provinsi tidak ditemukan")

    if payload.nama is not None:
        prov.nama = payload.nama.strip()

    db.commit()
    db.refresh(prov)
    total = db.query(WilayahRegency).filter(WilayahRegency.province_kode == kode).count()
    return WilayahProvinceItem(
        id=prov.kode,
        kode=prov.kode,
        nama=prov.nama,
        name=prov.nama,
        total_regencies=total
    )


@router.delete("/provinces/{kode}", status_code=status.HTTP_200_OK)
def delete_province(
    kode: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Hapus data provinsi dari database.
    """
    prov = db.query(WilayahProvince).filter(WilayahProvince.kode == kode).first()
    if not prov:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provinsi tidak ditemukan")

    nama = prov.nama
    db.delete(prov)
    db.commit()
    return {"status": "success", "message": f"Provinsi '{nama}' berhasil dihapus"}


# ==========================================
# 🏙️ 2. KABUPATEN / KOTA
# ==========================================

@router.get("/regencies", response_model=List[WilayahRegencyItem])
def get_regencies(
    province_kode: Optional[str] = Query(None, description="Kode provinsi, contoh: '11', '32'"),
    q: Optional[str] = Query(None, description="Pencarian nama atau kode kabupaten/kota"),
    limit: Optional[int] = Query(1000, description="Maksimal jumlah data"),
    db: Session = Depends(get_db)
):
    """
    Mengambil daftar Kabupaten/Kota di Indonesia.
    """
    query = db.query(WilayahRegency, WilayahProvince.nama.label("province_name")).join(
        WilayahProvince, WilayahRegency.province_kode == WilayahProvince.kode
    )

    if province_kode:
        query = query.filter(WilayahRegency.province_kode == province_kode)
    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            (WilayahRegency.nama.ilike(search)) |
            (WilayahRegency.kode.ilike(search)) |
            (WilayahProvince.nama.ilike(search))
        )

    results = query.order_by(WilayahRegency.kode.asc()).limit(limit).all()

    return [
        WilayahRegencyItem(
            id=r.kode,
            kode=r.kode,
            province_kode=r.province_kode,
            province_name=prov_name,
            nama=r.nama,
            name=r.nama,
            tipe=r.tipe
        )
        for r, prov_name in results
    ]


@router.post("/regencies", response_model=WilayahRegencyItem, status_code=status.HTTP_201_CREATED)
def create_regency(
    payload: WilayahRegencyCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Tambah Kabupaten/Kota baru.
    """
    existing = db.query(WilayahRegency).filter(WilayahRegency.kode == payload.kode.strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Kabupaten/Kota dengan kode '{payload.kode}' sudah ada ({existing.nama})"
        )

    prov = db.query(WilayahProvince).filter(WilayahProvince.kode == payload.province_kode.strip()).first()
    if not prov:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provinsi induk tidak ditemukan")

    tipe = payload.tipe or ("Kota" if payload.nama.strip().lower().startswith("kota") else "Kabupaten")
    item = WilayahRegency(
        kode=payload.kode.strip(),
        province_kode=payload.province_kode.strip(),
        nama=payload.nama.strip(),
        tipe=tipe
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return WilayahRegencyItem(
        id=item.kode,
        kode=item.kode,
        province_kode=item.province_kode,
        province_name=prov.nama,
        nama=item.nama,
        name=item.nama,
        tipe=item.tipe
    )


@router.put("/regencies/{kode}", response_model=WilayahRegencyItem)
def update_regency(
    kode: str,
    payload: WilayahRegencyUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Ubah data Kabupaten/Kota.
    """
    item = db.query(WilayahRegency).filter(WilayahRegency.kode == kode).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kabupaten/Kota tidak ditemukan")

    if payload.nama is not None:
        item.nama = payload.nama.strip()
    if payload.province_kode is not None:
        item.province_kode = payload.province_kode.strip()
    if payload.tipe is not None:
        item.tipe = payload.tipe.strip()

    db.commit()
    db.refresh(item)
    prov = db.query(WilayahProvince).filter(WilayahProvince.kode == item.province_kode).first()
    return WilayahRegencyItem(
        id=item.kode,
        kode=item.kode,
        province_kode=item.province_kode,
        province_name=prov.nama if prov else None,
        nama=item.nama,
        name=item.nama,
        tipe=item.tipe
    )


@router.delete("/regencies/{kode}", status_code=status.HTTP_200_OK)
def delete_regency(
    kode: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Hapus Kabupaten/Kota.
    """
    item = db.query(WilayahRegency).filter(WilayahRegency.kode == kode).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kabupaten/Kota tidak ditemukan")

    nama = item.nama
    db.delete(item)
    db.commit()
    return {"status": "success", "message": f"Kabupaten/Kota '{nama}' berhasil dihapus"}

