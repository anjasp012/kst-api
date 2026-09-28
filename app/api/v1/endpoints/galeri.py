import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.models.galeri import KSTGaleri
from app.models.lokasi import KSTLokasi
from app.models.user import User
from app.schemas.galeri import GaleriItem, GaleriCreate, GaleriUpdate
from app.api.v1.deps import get_current_admin
from app.core.helpers import build_full_url

router = APIRouter()


def _format_item(item: KSTGaleri) -> dict:
    return {
        "id": item.id,
        "lokasi_id": item.lokasi_id,
        "tipe": item.tipe or "foto",
        "url": build_full_url(item.url),
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


@router.get("", response_model=List[GaleriItem])
def get_galeri_list(
    lokasi_id: Optional[uuid.UUID] = Query(None, description="Filter berdasarkan ID Lokasi KST"),
    tipe: Optional[str] = Query(None, description="Filter tipe media ('foto' atau 'video')"),
    db: Session = Depends(get_db)
):
    query = db.query(KSTGaleri)
    if lokasi_id:
        query = query.filter(KSTGaleri.lokasi_id == lokasi_id)
    if tipe:
        query = query.filter(KSTGaleri.tipe == tipe.lower().strip())
    
    query = query.order_by(desc(KSTGaleri.created_at))
    items = query.all()
    return [_format_item(item) for item in items]


@router.get("/{galeri_id}", response_model=GaleriItem)
def get_galeri_detail(
    galeri_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    item = db.query(KSTGaleri).filter(KSTGaleri.id == galeri_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item galeri tidak ditemukan")
    return _format_item(item)


@router.post("", response_model=GaleriItem, status_code=status.HTTP_201_CREATED)
def create_galeri(
    payload: GaleriCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    loc = db.query(KSTLokasi).filter(KSTLokasi.id == payload.lokasi_id).first()
    if not loc:
        raise HTTPException(status_code=400, detail="Lokasi KST tidak ditemukan")

    tipe_val = (payload.tipe or "foto").lower().strip()
    if tipe_val not in ("foto", "video"):
        tipe_val = "foto"

    new_item = KSTGaleri(
        lokasi_id=payload.lokasi_id,
        tipe=tipe_val,
        url=payload.url,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return _format_item(new_item)


@router.put("/{galeri_id}", response_model=GaleriItem)
def update_galeri(
    galeri_id: uuid.UUID,
    payload: GaleriUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    item = db.query(KSTGaleri).filter(KSTGaleri.id == galeri_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item galeri tidak ditemukan")

    update_dict = payload.dict(exclude_unset=True)
    if "tipe" in update_dict and update_dict["tipe"]:
        update_dict["tipe"] = update_dict["tipe"].lower().strip()

    for key, val in update_dict.items():
        setattr(item, key, val)

    db.commit()
    db.refresh(item)
    return _format_item(item)


@router.delete("/{galeri_id}")
def delete_galeri(
    galeri_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    item = db.query(KSTGaleri).filter(KSTGaleri.id == galeri_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item galeri tidak ditemukan")

    db.delete(item)
    db.commit()
    return {"message": "Item galeri berhasil dihapus", "id": str(galeri_id)}
