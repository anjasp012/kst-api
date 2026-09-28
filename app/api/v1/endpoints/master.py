from typing import List, Optional, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.jenis_kawasan import KSTJenisKawasan
from app.models.tema_riset import KSTTemaRiset
from app.api.v1.endpoints.wilayah import _get_active_location_wilayah_map

router = APIRouter()


@router.get("")
def get_master_data(
    db: Session = Depends(get_db)
):
    # 1. Wilayah (Hanya yang ada data lokasinya)
    prov_map = _get_active_location_wilayah_map(db)
    wilayah_list = []
    for p_kode in sorted(prov_map.keys()):
        p_data = prov_map[p_kode]
        kabs_list = list(p_data["kabupaten_kota"].values())
        kabs_list.sort(key=lambda x: x["nama"])
        wilayah_list.append({
            "kode": p_data["kode"],
            "nama": p_data["nama"],
            "total_lokasi": p_data["total_lokasi"],
            "kabupaten_kota": kabs_list
        })

    # 2. Jenis Kawasan
    jenis_kawasan_items = (
        db.query(KSTJenisKawasan)
        .filter(KSTJenisKawasan.is_active == True)
        .order_by(KSTJenisKawasan.nama.asc())
        .all()
    )
    jk_list = [
        {
            "id": str(jk.id),
            "nama": jk.nama,
            "slug": jk.slug,
            "deskripsi": jk.deskripsi
        }
        for jk in jenis_kawasan_items
    ]

    # 3. Fokus Riset
    tema_items = (
        db.query(KSTTemaRiset)
        .filter(KSTTemaRiset.is_active == True)
        .order_by(KSTTemaRiset.nama.asc())
        .all()
    )
    fokus_list = [
        {
            "id": str(t.id),
            "nama": t.nama,
            "slug": t.slug,
            "deskripsi": t.deskripsi
        }
        for t in tema_items
    ]

    return {
        "total_wilayah": len(wilayah_list),
        "total_jenis_kawasan": len(jk_list),
        "total_fokus_riset": len(fokus_list),
        "wilayah": wilayah_list,
        "jenis_kawasan": jk_list,
        "fokus_riset": fokus_list
    }
