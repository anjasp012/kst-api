from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.wilayah import WilayahProvince, WilayahRegency
from app.schemas.wilayah import WilayahProvinceItem, WilayahRegencyItem

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

