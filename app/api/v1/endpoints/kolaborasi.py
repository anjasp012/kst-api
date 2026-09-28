import re
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.kolaborasi import KSTKolaborasi
from app.models.user import User
from app.schemas.kolaborasi import KolaborasiItem, KolaborasiCreate, KolaborasiUpdate
from app.api.v1.deps import get_current_admin

router = APIRouter()


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[\s\W-]+', '-', text)
    return text.strip('-')


@router.get("", response_model=List[KolaborasiItem])
def get_collaborations(
    include_inactive: bool = Query(False, description="Tampilkan item nonaktif juga (untuk CMS)"),
    db: Session = Depends(get_db)
):
    query = db.query(KSTKolaborasi)
    if not include_inactive:
        query = query.filter(KSTKolaborasi.is_active == True)
    return query.order_by(KSTKolaborasi.nama.asc()).all()


@router.post("", response_model=KolaborasiItem, status_code=status.HTTP_201_CREATED)
def create_collaboration(
    payload: KolaborasiCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    slug = payload.slug or slugify(payload.nama)
    existing = db.query(KSTKolaborasi).filter(
        (KSTKolaborasi.slug == slug) | (KSTKolaborasi.nama.ilike(payload.nama.strip()))
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Potensi kolaborasi '{payload.nama}' sudah terdaftar"
        )

    item = KSTKolaborasi(
        id=uuid.uuid4(),
        nama=payload.nama.strip(),
        slug=slug,
        deskripsi=payload.deskripsi.strip() if payload.deskripsi else None,
        is_active=payload.is_active if payload.is_active is not None else True
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{collab_id}", response_model=KolaborasiItem)
def update_collaboration(
    collab_id: uuid.UUID,
    payload: KolaborasiUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    item = db.query(KSTKolaborasi).filter(KSTKolaborasi.id == collab_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Potensi kolaborasi tidak ditemukan")

    if payload.nama is not None:
        item.nama = payload.nama.strip()
        if not payload.slug:
            item.slug = slugify(item.nama)
    if payload.slug is not None:
        item.slug = payload.slug
    if payload.deskripsi is not None:
        item.deskripsi = payload.deskripsi.strip() if payload.deskripsi else None
    if payload.is_active is not None:
        item.is_active = payload.is_active

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{collab_id}", status_code=status.HTTP_200_OK)
def delete_collaboration(
    collab_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    item = db.query(KSTKolaborasi).filter(KSTKolaborasi.id == collab_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Potensi kolaborasi tidak ditemukan")

    nama = item.nama
    db.delete(item)
    db.commit()
    return {"status": "success", "message": f"Potensi kolaborasi '{nama}' berhasil dihapus"}
