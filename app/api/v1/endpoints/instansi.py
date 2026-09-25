from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from app.db.session import get_db
from app.models.instansi import KSTInstansi
from app.models.user import User
from app.schemas.instansi import KSTInstansiItem, KSTInstansiCreate, KSTInstansiUpdate
from app.api.v1.deps import get_current_admin

router = APIRouter()

@router.get("", response_model=List[KSTInstansiItem])
def get_instansi(
    include_inactive: bool = Query(False, description="Tampilkan juga data yang tidak aktif"),
    db: Session = Depends(get_db)
):
    query = db.query(KSTInstansi)
    if not include_inactive:
        query = query.filter(KSTInstansi.is_active == True)
    return query.order_by(KSTInstansi.urutan.asc(), KSTInstansi.nama.asc()).all()

@router.post("", response_model=KSTInstansiItem, status_code=status.HTTP_201_CREATED)
def create_instansi(
    payload: KSTInstansiCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    slug = payload.slug.strip().lower()
    existing = db.query(KSTInstansi).filter((KSTInstansi.slug == slug) | (KSTInstansi.nama.ilike(payload.nama.strip()))).first()
    if existing:
        raise HTTPException(status_code=400, detail="Data Instansi dengan nama/slug ini sudah ada.")

    item = KSTInstansi(
        nama=payload.nama.strip(),
        slug=slug,
        deskripsi=payload.deskripsi.strip() if payload.deskripsi else None,
        urutan=payload.urutan,
        is_active=payload.is_active
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.put("/{id}", response_model=KSTInstansiItem)
def update_instansi(
    id: uuid.UUID,
    payload: KSTInstansiUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    item = db.query(KSTInstansi).filter(KSTInstansi.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")

    if payload.nama is not None:
        item.nama = payload.nama.strip()
    if payload.slug is not None:
        item.slug = payload.slug.strip().lower()
    if payload.deskripsi is not None:
        item.deskripsi = payload.deskripsi.strip()
    if payload.urutan is not None:
        item.urutan = payload.urutan
    if payload.is_active is not None:
        item.is_active = payload.is_active

    db.commit()
    db.refresh(item)
    return item

@router.delete("/{id}")
def delete_instansi(
    id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    item = db.query(KSTInstansi).filter(KSTInstansi.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")
    db.delete(item)
    db.commit()
    return {"status": "success", "message": "Data berhasil dihapus"}
