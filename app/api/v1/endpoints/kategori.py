from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tema_riset import KSTTemaRiset
from app.models.fasilitas import KSTFasilitas
from app.models.kolaborasi import KSTKolaborasi
from app.schemas.kategori import KSTKategoriGrouped

router = APIRouter()


@router.get("", response_model=KSTKategoriGrouped)
def get_categories(
    db: Session = Depends(get_db)
):
    themes = (
        db.query(KSTTemaRiset)
        .filter(KSTTemaRiset.is_active == True)
        .order_by(KSTTemaRiset.nama.asc())
        .all()
    )
    facilities = (
        db.query(KSTFasilitas)
        .filter(KSTFasilitas.is_active == True)
        .order_by(KSTFasilitas.nama.asc())
        .all()
    )
    collabs = (
        db.query(KSTKolaborasi)
        .filter(KSTKolaborasi.is_active == True)
        .order_by(KSTKolaborasi.nama.asc())
        .all()
    )

    return KSTKategoriGrouped(
        tema_riset=[t.nama for t in themes],
        tipe_fasilitas=[f.nama for f in facilities],
        potensi_kolaborasi=[c.nama for c in collabs],
        raw=[]
    )
