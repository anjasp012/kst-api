from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.wilayah import WilayahProvince, WilayahRegency, WilayahProvinsi, WilayahKabupatenKota
from app.models.lokasi import KSTLokasi
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


def _get_active_location_wilayah_map(db: Session):
    """
    Mengembalikan pemetaan provinsi & kabupaten yang memiliki data lokasi KST di database.
    """
    locs = db.query(KSTLokasi).all()
    all_provs = db.query(WilayahProvinsi).all()
    all_kabs = db.query(WilayahKabupatenKota).all()

    prov_map = {}
    for loc in locs:
        kp = (loc.kota_provinsi or "").lower()
        wil = (loc.wilayah or "").lower()

        matched_prov = None
        for p in all_provs:
            p_nama = p.nama.lower()
            if p_nama in kp or (wil and p_nama in wil):
                matched_prov = p
                break

        if not matched_prov and loc.kota_provinsi:
            parts = [x.strip() for x in loc.kota_provinsi.split(",")]
            if len(parts) >= 2:
                last_part = parts[-1].lower()
                for p in all_provs:
                    if p.nama.lower() in last_part or last_part in p.nama.lower():
                        matched_prov = p
                        break

        if not matched_prov:
            continue

        p_kode = matched_prov.kode
        if p_kode not in prov_map:
            prov_map[p_kode] = {
                "kode": p_kode,
                "nama": matched_prov.nama,
                "total_lokasi": 0,
                "kabupaten_kota": {}
            }
        prov_map[p_kode]["total_lokasi"] += 1

        matched_kab = None
        for k in all_kabs:
            if k.province_kode == p_kode:
                k_clean = k.nama.lower().replace("kota ", "").replace("kabupaten ", "").replace("kab. ", "").strip()
                if k_clean and (k_clean in kp or kp in k_clean):
                    matched_kab = k
                    break

        if matched_kab:
            k_kode = matched_kab.kode
            if k_kode not in prov_map[p_kode]["kabupaten_kota"]:
                prov_map[p_kode]["kabupaten_kota"][k_kode] = {
                    "kode": k_kode,
                    "nama": matched_kab.nama,
                    "tipe": matched_kab.tipe,
                    "total_lokasi": 0
                }
            prov_map[p_kode]["kabupaten_kota"][k_kode]["total_lokasi"] += 1

    return prov_map


# ==========================================
# 🇮🇩 0. MASTER WILAYAH (Hanya yang Ada Lokasinya)
# ==========================================

@router.get("")
def get_master_wilayah(
    ada_lokasi: bool = Query(True, description="Hanya tampilkan wilayah yang memiliki data lokasi"),
    db: Session = Depends(get_db)
):
    prov_map = _get_active_location_wilayah_map(db)

    if ada_lokasi:
        results = []
        for p_kode in sorted(prov_map.keys()):
            p_data = prov_map[p_kode]
            kabs_list = list(p_data["kabupaten_kota"].values())
            kabs_list.sort(key=lambda x: x["nama"])
            results.append({
                "kode": p_data["kode"],
                "nama": p_data["nama"],
                "total_lokasi": p_data["total_lokasi"],
                "kabupaten_kota": kabs_list
            })
        return results

    all_provs = db.query(WilayahProvinsi).order_by(WilayahProvinsi.kode.asc()).all()
    return [
        {
            "kode": p.kode,
            "nama": p.nama,
            "total_lokasi": prov_map.get(p.kode, {}).get("total_lokasi", 0),
            "kabupaten_kota": [
                {
                    "kode": k.kode,
                    "nama": k.nama,
                    "tipe": k.tipe,
                    "total_lokasi": prov_map.get(p.kode, {}).get("kabupaten_kota", {}).get(k.kode, {}).get("total_lokasi", 0)
                }
                for k in p.kabupaten_kota
            ]
        }
        for p in all_provs
    ]


# ==========================================
# 🇮🇩 1. PROVINSI (kst_provinsi)
# ==========================================

@router.get("/provinsi", response_model=List[WilayahProvinceItem])
def get_provinces(
    ada_lokasi: Optional[bool] = Query(None, description="Hanya tampilkan provinsi yang memiliki data lokasi"),
    wilayah: Optional[str] = Query(None, description="Filter zona wilayah: Sumatera, Jawa, Kalimantan, dll."),
    q: Optional[str] = Query(None, description="Pencarian nama atau kode provinsi"),
    db: Session = Depends(get_db)
):
    query = db.query(
        WilayahProvince,
        func.count(WilayahRegency.kode).label("total_regencies")
    ).outerjoin(WilayahRegency, WilayahProvince.kode == WilayahRegency.province_kode)

    if ada_lokasi:
        prov_map = _get_active_location_wilayah_map(db)
        active_codes = list(prov_map.keys())
        query = query.filter(WilayahProvince.kode.in_(active_codes))

    if q:
        search = f"%{q.strip()}%"
        query = query.filter((WilayahProvince.nama.ilike(search)) | (WilayahProvince.kode.ilike(search)))

    results = query.group_by(WilayahProvince.kode).order_by(WilayahProvince.kode.asc()).all()

    return [
        WilayahProvinceItem(
            id=p.kode,
            kode=p.kode,
            nama=p.nama,
            total_kabupaten_kota=total or 0,
            total_regencies=total or 0
        )
        for p, total in results
    ]


@router.post("/provinsi", response_model=WilayahProvinceItem, status_code=status.HTTP_201_CREATED)
def create_province(
    payload: WilayahProvinceCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
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
        total_kabupaten_kota=0,
        total_regencies=0
    )


@router.put("/provinsi/{kode}", response_model=WilayahProvinceItem)
def update_province(
    kode: str,
    payload: WilayahProvinceUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
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
        total_kabupaten_kota=total,
        total_regencies=total
    )


@router.delete("/provinsi/{kode}", status_code=status.HTTP_200_OK)
def delete_province(
    kode: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    prov = db.query(WilayahProvince).filter(WilayahProvince.kode == kode).first()
    if not prov:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provinsi tidak ditemukan")

    nama = prov.nama
    db.delete(prov)
    db.commit()
    return {"status": "success", "message": f"Provinsi '{nama}' berhasil dihapus"}


# ==========================================
# 🏙️ 2. KABUPATEN / KOTA (kst_kabupaten_kota)
# ==========================================

@router.get("/kabupaten-kota", response_model=List[WilayahRegencyItem])
def get_regencies(
    ada_lokasi: Optional[bool] = Query(None, description="Hanya tampilkan kabupaten/kota yang memiliki data lokasi"),
    province_kode: Optional[str] = Query(None, description="Kode provinsi, contoh: '11', '32'"),
    q: Optional[str] = Query(None, description="Pencarian nama atau kode kabupaten/kota"),
    limit: Optional[int] = Query(1000, description="Maksimal jumlah data"),
    db: Session = Depends(get_db)
):
    query = db.query(WilayahRegency, WilayahProvince.nama.label("province_name")).join(
        WilayahProvince, WilayahRegency.province_kode == WilayahProvince.kode
    )

    if ada_lokasi:
        prov_map = _get_active_location_wilayah_map(db)
        active_kab_codes = []
        for p_data in prov_map.values():
            active_kab_codes.extend(p_data["kabupaten_kota"].keys())
        query = query.filter(WilayahRegency.kode.in_(active_kab_codes))

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


@router.post("/kabupaten-kota", response_model=WilayahRegencyItem, status_code=status.HTTP_201_CREATED)
def create_regency(
    payload: WilayahRegencyCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
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


@router.put("/kabupaten-kota/{kode}", response_model=WilayahRegencyItem)
def update_regency(
    kode: str,
    payload: WilayahRegencyUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
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


@router.delete("/kabupaten-kota/{kode}", status_code=status.HTTP_200_OK)
def delete_regency(
    kode: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    item = db.query(WilayahRegency).filter(WilayahRegency.kode == kode).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kabupaten/Kota tidak ditemukan")

    nama = item.nama
    db.delete(item)
    db.commit()
    return {"status": "success", "message": f"Kabupaten/Kota '{nama}' berhasil dihapus"}
