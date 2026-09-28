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
    return query.order_by(KSTJenisKawasan.nama.asc()).all()


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
        is_active=payload.is_active if payload.is_active is not None else True
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


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

    if payload.nama is not None:
        item.nama = payload.nama.strip()
    if payload.slug is not None:
        item.slug = payload.slug.strip().lower()
    if payload.deskripsi is not None:
        item.deskripsi = payload.deskripsi.strip() if payload.deskripsi else None
    if payload.is_active is not None:
        item.is_active = payload.is_active

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{id}")
def delete_jenis_kawasan(
    id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    item = db.query(KSTJenisKawasan).filter(KSTJenisKawasan.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Data jenis kawasan tidak ditemukan.")

    db.delete(item)
    db.commit()
    return {"status": "success", "message": "Data jenis kawasan berhasil dihapus"}
