import re
import uuid
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.category import KSTCategory
from app.models.user import User
from app.schemas.category import (
    KSTCategoryItem,
    KSTCategoriesGrouped,
    KSTCategoryCreate,
    KSTCategoryUpdate
)
from app.api.v1.deps import get_current_admin

router = APIRouter()


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[\s\W-]+', '-', text)
    return text.strip('-')


@router.get("", response_model=Union[KSTCategoriesGrouped, List[KSTCategoryItem]])
def get_categories(
    tipe: Optional[str] = Query(None, description="Filter tipe kategori: 'tema_riset', 'tipe_fasilitas', 'potensi_kolaborasi'"),
    include_inactive: bool = Query(False, description="Tampilkan item nonaktif juga (untuk CMS)"),
    grouped: Optional[bool] = Query(None, description="Jika false, kembalikan List[KSTCategoryItem] langsung"),
    db: Session = Depends(get_db)
):
    """
    Mengambil data master kategori resmi WONDERFUL BRIN:
    - Tema Riset
    - Tipe Fasilitas
    - Potensi Kolaborasi
    """
    query = db.query(KSTCategory)
    if not include_inactive:
        query = query.filter(KSTCategory.is_active == True)
    if tipe:
        query = query.filter(KSTCategory.tipe == tipe)
        return query.order_by(KSTCategory.urutan.asc(), KSTCategory.nama.asc()).all()

    all_cats = query.order_by(KSTCategory.urutan.asc(), KSTCategory.nama.asc()).all()

    if grouped is False:
        return [KSTCategoryItem.from_orm(c) for c in all_cats]

    tema_riset = [c.nama for c in all_cats if c.tipe == "tema_riset" and c.is_active]
    tipe_fasilitas = [c.nama for c in all_cats if c.tipe == "tipe_fasilitas" and c.is_active]
    potensi_kolaborasi = [c.nama for c in all_cats if c.tipe == "potensi_kolaborasi" and c.is_active]

    return KSTCategoriesGrouped(
        tema_riset=tema_riset,
        tipe_fasilitas=tipe_fasilitas,
        potensi_kolaborasi=potensi_kolaborasi,
        raw=[KSTCategoryItem.from_orm(c) for c in all_cats]
    )


@router.post("", response_model=KSTCategoryItem, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: KSTCategoryCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Tambah data master kategori baru (Tema Riset / Tipe Fasilitas / Potensi Kolaborasi).
    """
    slug = payload.slug or slugify(payload.nama)
    existing = db.query(KSTCategory).filter(
        KSTCategory.tipe == payload.tipe,
        (KSTCategory.slug == slug) | (KSTCategory.nama.ilike(payload.nama.strip()))
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Kategori '{payload.nama}' sudah terdaftar pada tipe '{payload.tipe}'"
        )

    new_cat = KSTCategory(
        id=uuid.uuid4(),
        tipe=payload.tipe,
        nama=payload.nama.strip(),
        slug=slug,
        urutan=payload.urutan or 0,
        is_active=payload.is_active if payload.is_active is not None else True
    )
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat


@router.put("/{category_id}", response_model=KSTCategoryItem)
def update_category(
    category_id: uuid.UUID,
    payload: KSTCategoryUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Ubah data master kategori yang sudah ada.
    """
    cat = db.query(KSTCategory).filter(KSTCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kategori tidak ditemukan")

    if payload.nama is not None:
        cat.nama = payload.nama.strip()
        if not payload.slug:
            cat.slug = slugify(cat.nama)
    if payload.slug is not None:
        cat.slug = payload.slug
    if payload.urutan is not None:
        cat.urutan = payload.urutan
    if payload.is_active is not None:
        cat.is_active = payload.is_active

    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
def delete_category(
    category_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Hapus data master kategori.
    """
    cat = db.query(KSTCategory).filter(KSTCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kategori tidak ditemukan")

    nama = cat.nama
    db.delete(cat)
    db.commit()
    return {"status": "success", "message": f"Kategori '{nama}' berhasil dihapus"}
