import re
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.quick_filter import KSTQuickFilter
from app.models.user import User
from app.schemas.quick_filter import (
    QuickFilterResponse,
    QuickFilterCreate,
    QuickFilterUpdate,
)
from app.api.v1.deps import get_current_admin

admin_router = APIRouter()


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')


# =========================================================================
# ⚙️ ADMIN CMS: CRUD PRESET QUICK FILTER (SIMPLE)
# =========================================================================

@admin_router.get("", response_model=List[QuickFilterResponse])
def get_all_quick_filters_admin(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    return db.query(KSTQuickFilter).order_by(KSTQuickFilter.created_at.asc()).all()


@admin_router.post("", response_model=QuickFilterResponse, status_code=status.HTTP_201_CREATED)
def create_quick_filter(
    payload: QuickFilterCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    nama = payload.nama.strip()
    slug = (payload.slug.strip().lower() if payload.slug else slugify(nama))
    if not slug:
        slug = f"filter-{uuid.uuid4().hex[:6]}"

    existing = db.query(KSTQuickFilter).filter(
        (KSTQuickFilter.slug == slug) | (KSTQuickFilter.nama.ilike(nama))
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quick Filter dengan nama atau slug ini sudah terdaftar."
        )

    clean_filter_data = payload.filter_data or {}
    filter_dict = {
        "wilayah": clean_filter_data.get("wilayah", []),
        "jenis_kawasan": clean_filter_data.get("jenis_kawasan", []),
        "fokus_riset": clean_filter_data.get("fokus_riset", []),
        "search_input": clean_filter_data.get("search_input", "") or "",
    }

    item = KSTQuickFilter(
        nama=nama,
        slug=slug,
        filter_data=filter_dict,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@admin_router.get("/{id}", response_model=QuickFilterResponse)
def get_quick_filter_by_id(
    id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        val_uuid = uuid.UUID(id)
        item = db.query(KSTQuickFilter).filter(KSTQuickFilter.id == val_uuid).first()
    except ValueError:
        item = db.query(KSTQuickFilter).filter(KSTQuickFilter.slug == id).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quick Filter tidak ditemukan."
        )
    return item


@admin_router.put("/{id}", response_model=QuickFilterResponse)
def update_quick_filter(
    id: str,
    payload: QuickFilterUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        val_uuid = uuid.UUID(id)
        item = db.query(KSTQuickFilter).filter(KSTQuickFilter.id == val_uuid).first()
    except ValueError:
        item = db.query(KSTQuickFilter).filter(KSTQuickFilter.slug == id).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quick Filter tidak ditemukan."
        )

    if payload.nama is not None:
        nama = payload.nama.strip()
        new_slug = payload.slug.strip().lower() if payload.slug else slugify(nama)

        conflict = db.query(KSTQuickFilter).filter(
            KSTQuickFilter.id != item.id,
            (KSTQuickFilter.slug == new_slug) | (KSTQuickFilter.nama.ilike(nama))
        ).first()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quick Filter dengan nama atau slug ini sudah terdaftar."
            )
        item.nama = nama
        item.slug = new_slug

    if payload.filter_data is not None:
        clean_filter_data = payload.filter_data or {}
        item.filter_data = {
            "wilayah": clean_filter_data.get("wilayah", []),
            "jenis_kawasan": clean_filter_data.get("jenis_kawasan", []),
            "fokus_riset": clean_filter_data.get("fokus_riset", []),
            "search_input": clean_filter_data.get("search_input", "") or "",
        }

    db.commit()
    db.refresh(item)
    return item


@admin_router.delete("/{id}")
def delete_quick_filter(
    id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        val_uuid = uuid.UUID(id)
        item = db.query(KSTQuickFilter).filter(KSTQuickFilter.id == val_uuid).first()
    except ValueError:
        item = db.query(KSTQuickFilter).filter(KSTQuickFilter.slug == id).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quick Filter tidak ditemukan."
        )

    db.delete(item)
    db.commit()
    return {"message": "Quick Filter berhasil dihapus"}


# =========================================================================
# 🌐 PUBLIC API: DAFTAR QUICK FILTER
# =========================================================================

def get_public_quick_filters(
    db: Session = Depends(get_db)
):
    """
    Mengambil daftar preset Quick Filter yang tersimpan di sistem.
    """
    return db.query(KSTQuickFilter).order_by(KSTQuickFilter.created_at.asc()).all()
