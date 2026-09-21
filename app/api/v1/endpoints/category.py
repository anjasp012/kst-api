from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.theme import KSTThemeRiset
from app.models.facility import KSTFacility
from app.models.collaboration import KSTCollaboration
from app.schemas.category import KSTCategoriesGrouped

router = APIRouter()


@router.get("", response_model=KSTCategoriesGrouped)
def get_categories(
    db: Session = Depends(get_db)
):
    """
    Mengambil data master kategori gabungan untuk Filter Wonderful BRIN dan Form KST.
    Sumber data diambil langsung dari 3 tabel terpisah:
    - Tema Riset dari tabel: kst_themeriset
    - Tipe Fasilitas dari tabel: kst_facilities
    - Potensi Kolaborasi dari tabel: kst_collaborations
    """
    themes = (
        db.query(KSTThemeRiset)
        .filter(KSTThemeRiset.is_active == True)
        .order_by(KSTThemeRiset.urutan.asc(), KSTThemeRiset.nama.asc())
        .all()
    )
    facilities = (
        db.query(KSTFacility)
        .filter(KSTFacility.is_active == True)
        .order_by(KSTFacility.urutan.asc(), KSTFacility.nama.asc())
        .all()
    )
    collabs = (
        db.query(KSTCollaboration)
        .filter(KSTCollaboration.is_active == True)
        .order_by(KSTCollaboration.urutan.asc(), KSTCollaboration.nama.asc())
        .all()
    )

    return KSTCategoriesGrouped(
        tema_riset=[t.nama for t in themes],
        tipe_fasilitas=[f.nama for f in facilities],
        potensi_kolaborasi=[c.nama for c in collabs],
        raw=[]
    )
