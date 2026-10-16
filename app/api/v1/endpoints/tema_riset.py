import re
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tema_riset import KSTTemaRiset
from app.models.user import User
from app.schemas.tema_riset import TemaRisetItem, TemaRisetCreate, TemaRisetUpdate
from app.api.v1.deps import get_current_admin

router = APIRouter()


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[\s\W-]+', '-', text)
    return text.strip('-')


@router.get("", response_model=List[TemaRisetItem])
def get_themes(
    include_inactive: bool = Query(False, description="Tampilkan item nonaktif juga (untuk CMS)"),
    db: Session = Depends(get_db)
):
    q = db.query(KSTTemaRiset)
    if not include_inactive:
        q = q.filter(KSTTemaRiset.is_active == True)
    return q.order_by(KSTTemaRiset.created_at.asc()).all()


@router.post("", response_model=TemaRisetItem, status_code=status.HTTP_201_CREATED)
def create_theme(
    payload: TemaRisetCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    slug = payload.slug or slugify(payload.nama)
    existing = db.query(KSTTemaRiset).filter(
        (KSTTemaRiset.slug == slug) | (KSTTemaRiset.nama.ilike(payload.nama.strip()))
    ).first()
    if existing:
        return existing

    item = KSTTemaRiset(
        id=uuid.uuid4(),
        nama=payload.nama.strip(),
        slug=slug,
        is_active=payload.is_active if payload.is_active is not None else True
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{theme_id}", response_model=TemaRisetItem)
def update_theme(
    theme_id: uuid.UUID,
    payload: TemaRisetUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    item = db.query(KSTTemaRiset).filter(KSTTemaRiset.id == theme_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tema riset tidak ditemukan")

    if payload.nama is not None:
        item.nama = payload.nama.strip()
        if not payload.slug:
            item.slug = slugify(item.nama)
    if payload.slug is not None:
        item.slug = payload.slug
    if payload.is_active is not None:
        item.is_active = payload.is_active

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{theme_id}", status_code=status.HTTP_200_OK)
def delete_theme(
    theme_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    item = db.query(KSTTemaRiset).filter(KSTTemaRiset.id == theme_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tema riset tidak ditemukan")

    nama = item.nama
    db.delete(item)
    db.commit()
    return {"status": "success", "message": f"Tema riset '{nama}' berhasil dihapus"}
