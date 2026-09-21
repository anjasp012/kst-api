from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.wilayah import WilayahProvince, WilayahRegency
from app.models.user import User
from app.schemas.wilayah import (
    WilayahProvinceItem,
    WilayahProvinceCreate,
    WilayahProvinceUpdate,
    WilayahRegencyItem
)
from app.api.v1.deps import get_current_admin

router = APIRouter()


@router.get("/provinces", response_model=List[WilayahProvinceItem])
def get_provinces(
    wilayah: Optional[str] = Query(None, description="Filter wilayah: Sumatera, Jawa, Kalimantan, Sulawesi, Nusa Tenggara, Maluku & Papua"),
    db: Session = Depends(get_db)
):
    """
    Mengambil data seluruh provinsi di Indonesia (38 Provinsi Resmi Kemendagri).
    Disimpan lokal di database agar akses cepat dan tidak tergantung API pihak ketiga.
    """
    query = db.query(WilayahProvince)
    if wilayah:
        query = query.filter(WilayahProvince.wilayah.ilike(f"%{wilayah}%"))

    provinces = query.order_by(WilayahProvince.kode.asc()).all()

    return [
        WilayahProvinceItem(
            id=p.kode,
            kode=p.kode,
            nama=p.nama,
            name=p.nama,
            wilayah=p.wilayah
        )
        for p in provinces
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
    existing = db.query(WilayahProvince).filter(WilayahProvince.kode == payload.kode).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provinsi dengan kode '{payload.kode}' sudah ada ({existing.nama})"
        )

    prov = WilayahProvince(
        kode=payload.kode.strip(),
        nama=payload.nama.strip(),
        wilayah=payload.wilayah.strip()
    )
    db.add(prov)
    db.commit()
    db.refresh(prov)
    return WilayahProvinceItem(
        id=prov.kode,
        kode=prov.kode,
        nama=prov.nama,
        name=prov.nama,
        wilayah=prov.wilayah
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
    if payload.wilayah is not None:
        prov.wilayah = payload.wilayah.strip()

    db.commit()
    db.refresh(prov)
    return WilayahProvinceItem(
        id=prov.kode,
        kode=prov.kode,
        nama=prov.nama,
        name=prov.nama,
        wilayah=prov.wilayah
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


@router.get("/regencies", response_model=List[WilayahRegencyItem])
def get_regencies(
    province_kode: Optional[str] = Query(None, description="Kode provinsi, contoh: '11', '32'"),
    province_id: Optional[str] = Query(None, description="Alias untuk province_kode"),
    q: Optional[str] = Query(None, description="Pencarian nama kabupaten/kota"),
    db: Session = Depends(get_db)
):
    """
    Mengambil data kota/kabupaten di Indonesia (514 Kota/Kabupaten Resmi Kemendagri).
    Bisa difilter berdasarkan kode provinsi.
    """
    prov_code = province_kode or province_id
    query = db.query(WilayahRegency)

    if prov_code:
        query = query.filter(WilayahRegency.province_kode == prov_code)

    if q:
        query = query.filter(WilayahRegency.nama.ilike(f"%{q}%"))

    regencies = query.order_by(WilayahRegency.nama.asc()).all()

    return [
        WilayahRegencyItem(
            id=r.kode,
            kode=r.kode,
            province_id=r.province_kode,
            province_kode=r.province_kode,
            nama=r.nama,
            name=r.nama,
            tipe=r.tipe
        )
        for r in regencies
    ]
