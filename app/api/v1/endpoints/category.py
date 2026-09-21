from typing import List, Optional, Union
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.category import KSTCategory
from app.schemas.category import KSTCategoryItem, KSTCategoriesGrouped

router = APIRouter()


@router.get("", response_model=Union[KSTCategoriesGrouped, List[KSTCategoryItem]])
def get_categories(
    tipe: Optional[str] = Query(None, description="Filter tipe kategori: 'tema_riset', 'tipe_fasilitas', 'potensi_kolaborasi'"),
    db: Session = Depends(get_db)
):
    """
    Mengambil data master kategori resmi WONDERFUL BRIN:
    - Tema Riset (6 kategori)
    - Tipe Fasilitas (4 kategori)
    - Potensi Kolaborasi (4 kategori)
    """
    query = db.query(KSTCategory).filter(KSTCategory.is_active == True)
    if tipe:
        query = query.filter(KSTCategory.tipe == tipe)
        return query.order_by(KSTCategory.urutan.asc()).all()

    all_cats = query.order_by(KSTCategory.urutan.asc()).all()

    tema_riset = [c.nama for c in all_cats if c.tipe == "tema_riset"]
    tipe_fasilitas = [c.nama for c in all_cats if c.tipe == "tipe_fasilitas"]
    potensi_kolaborasi = [c.nama for c in all_cats if c.tipe == "potensi_kolaborasi"]

    return KSTCategoriesGrouped(
        tema_riset=tema_riset,
        tipe_fasilitas=tipe_fasilitas,
        potensi_kolaborasi=potensi_kolaborasi,
        raw=[KSTCategoryItem.from_orm(c) for c in all_cats]
    )
