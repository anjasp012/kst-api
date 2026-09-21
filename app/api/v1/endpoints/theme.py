import re
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.theme import KSTThemeRiset
from app.models.user import User
from app.schemas.theme import ThemeRisetItem, ThemeRisetCreate, ThemeRisetUpdate
from app.api.v1.deps import get_current_admin

router = APIRouter()


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[\s\W-]+', '-', text)
    return text.strip('-')


@router.get("", response_model=List[ThemeRisetItem])
def get_themes(
    include_inactive: bool = Query(False, description="Tampilkan item nonaktif juga (untuk CMS)"),
    db: Session = Depends(get_db)
):
    """
    Mengambil daftar Tema Riset KST (Tabel: kst_themeriset).
    """
    query = db.query(KSTThemeRiset)
    if not include_inactive:
        query = query.filter(KSTThemeRiset.is_active == True)
    return query.order_by(KSTThemeRiset.urutan.asc(), KSTThemeRiset.nama.asc()).all()


@router.post("", response_model=ThemeRisetItem, status_code=status.HTTP_201_CREATED)
def create_theme(
    payload: ThemeRisetCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Tambah Tema Riset baru ke tabel kst_themeriset.
    """
    slug = payload.slug or slugify(payload.nama)
    existing = db.query(KSTThemeRiset).filter(
        (KSTThemeRiset.slug == slug) | (KSTThemeRiset.nama.ilike(payload.nama.strip()))
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tema riset '{payload.nama}' sudah terdaftar"
        )

    item = KSTThemeRiset(
        id=uuid.uuid4(),
        nama=payload.nama.strip(),
        slug=slug,
        deskripsi=payload.deskripsi.strip() if payload.deskripsi else None,
        urutan=payload.urutan or 0,
        is_active=payload.is_active if payload.is_active is not None else True
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{theme_id}", response_model=ThemeRisetItem)
def update_theme(
    theme_id: uuid.UUID,
    payload: ThemeRisetUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Ubah data Tema Riset di tabel kst_themeriset.
    """
    item = db.query(KSTThemeRiset).filter(KSTThemeRiset.id == theme_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tema riset tidak ditemukan")

    if payload.nama is not None:
        item.nama = payload.nama.strip()
        if not payload.slug:
            item.slug = slugify(item.nama)
    if payload.slug is not None:
        item.slug = payload.slug
    if payload.deskripsi is not None:
        item.deskripsi = payload.deskripsi.strip() if payload.deskripsi else None
    if payload.urutan is not None:
        item.urutan = payload.urutan
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
    """
    Hapus Tema Riset dari tabel kst_themeriset.
    """
    item = db.query(KSTThemeRiset).filter(KSTThemeRiset.id == theme_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tema riset tidak ditemukan")

    nama = item.nama
    db.delete(item)
    db.commit()
    return {"status": "success", "message": f"Tema riset '{nama}' berhasil dihapus"}

