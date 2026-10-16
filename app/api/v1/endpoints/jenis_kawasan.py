import re
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.jenis_kawasan import KSTJenisKawasan
from app.models.user import User
from app.schemas.jenis_kawasan import (
    KSTJenisKawasanItem,
    KSTJenisKawasanCreate,
    KSTJenisKawasanUpdate,
)
from app.api.v1.deps import get_current_admin

router = APIRouter()


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')


@router.get("", response_model=List[KSTJenisKawasanItem])
def get_jenis_kawasan_list(
    include_inactive: bool = Query(True, description="Sertakan data nonaktif"),
    db: Session = Depends(get_db)
):
    query = db.query(KSTJenisKawasan)
    if not include_inactive:
        query = query.filter(KSTJenisKawasan.is_active == True)
    items = query.order_by(KSTJenisKawasan.parent_id.nullsfirst(), KSTJenisKawasan.nama.asc()).all()
    results = []
    for it in items:
        res = KSTJenisKawasanItem.model_validate(it)
        res.parent_nama = it.parent.nama if it.parent else None
        results.append(res)
    return results


@router.post("", response_model=KSTJenisKawasanItem, status_code=status.HTTP_201_CREATED)
def create_jenis_kawasan(
    payload: KSTJenisKawasanCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    nama = payload.nama.strip()
    slug = (payload.slug.strip().lower() if payload.slug else slugify(nama))

    existing = db.query(KSTJenisKawasan).filter(
        (KSTJenisKawasan.slug == slug) | (KSTJenisKawasan.nama.ilike(nama))
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data Jenis Kawasan dengan nama atau slug ini sudah terdaftar."
        )

    item = KSTJenisKawasan(
        nama=nama,
        slug=slug,
        deskripsi=payload.deskripsi.strip() if payload.deskripsi else None,
        parent_id=payload.parent_id,
        is_active=payload.is_active if payload.is_active is not None else True
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    res = KSTJenisKawasanItem.model_validate(item)
    res.parent_nama = item.parent.nama if item.parent else None
    return res


@router.put("/{id}", response_model=KSTJenisKawasanItem)
def update_jenis_kawasan(
    id: uuid.UUID,
    payload: KSTJenisKawasanUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    item = db.query(KSTJenisKawasan).filter(KSTJenisKawasan.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Data jenis kawasan tidak ditemukan.")

    if "nama" in payload.model_fields_set and payload.nama is not None:
        item.nama = payload.nama.strip()
    if "slug" in payload.model_fields_set and payload.slug is not None:
        item.slug = payload.slug.strip().lower()
    if "deskripsi" in payload.model_fields_set:
        item.deskripsi = payload.deskripsi.strip() if payload.deskripsi else None
    if "is_active" in payload.model_fields_set and payload.is_active is not None:
        item.is_active = payload.is_active
    if "parent_id" in payload.model_fields_set:
        if payload.parent_id == id:
            raise HTTPException(status_code=400, detail="Kategori tidak dapat menjadi parent untuk dirinya sendiri.")
        item.parent_id = payload.parent_id

    from datetime import datetime
    item.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(item)
    res = KSTJenisKawasanItem.model_validate(item)
    res.parent_nama = item.parent.nama if item.parent else None
    return res


@router.delete("/{id}")
def delete_jenis_kawasan(
    id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    item = db.query(KSTJenisKawasan).filter(KSTJenisKawasan.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Data jenis kawasan tidak ditemukan.")

    # 1. Periksa apakah jenis kawasan masih digunakan oleh data lokasi kawasan
    from app.models.lokasi import KSTLokasi
    lokasi_count = db.query(KSTLokasi).filter(KSTLokasi.jenis_kawasan_id == id).count()
    if lokasi_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Tidak dapat menghapus jenis kawasan '{item.nama}' karena masih digunakan oleh {lokasi_count} data lokasi. Harap ubah jenis kawasan pada data lokasi terkait terlebih dahulu."
        )

    # 2. Periksa apakah kategori ini memiliki sub-jenis di bawahnya
    sub_count = db.query(KSTJenisKawasan).filter(KSTJenisKawasan.parent_id == id).count()
    if sub_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Tidak dapat menghapus kategori '{item.nama}' karena masih memiliki {sub_count} sub-jenis di dalamnya. Harap hapus sub-jenis terlebih dahulu."
        )

    try:
        db.delete(item)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Gagal menghapus jenis kawasan '{item.nama}' karena masih terhubung dengan data lain di sistem."
        )
    return {"status": "success", "message": f"Data jenis kawasan '{item.nama}' berhasil dihapus"}
