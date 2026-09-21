import re
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.facility import KSTFacility
from app.models.user import User
from app.schemas.facility import FacilityItem, FacilityCreate, FacilityUpdate
from app.api.v1.deps import get_current_admin

router = APIRouter()


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[\s\W-]+', '-', text)
    return text.strip('-')


@router.get("", response_model=List[FacilityItem])
def get_facilities(
    include_inactive: bool = Query(False, description="Tampilkan item nonaktif juga (untuk CMS)"),
    db: Session = Depends(get_db)
):
    """
    Mengambil daftar Tipe / Jenis Fasilitas KST (Tabel: kst_facilities).
    """
    query = db.query(KSTFacility)
    if not include_inactive:
        query = query.filter(KSTFacility.is_active == True)
    return query.order_by(KSTFacility.urutan.asc(), KSTFacility.nama.asc()).all()


@router.post("", response_model=FacilityItem, status_code=status.HTTP_201_CREATED)
def create_facility(
    payload: FacilityCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Tambah Fasilitas baru ke tabel kst_facilities.
    """
    slug = payload.slug or slugify(payload.nama)
    existing = db.query(KSTFacility).filter(
        (KSTFacility.slug == slug) | (KSTFacility.nama.ilike(payload.nama.strip()))
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fasilitas '{payload.nama}' sudah terdaftar"
        )

    item = KSTFacility(
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


@router.put("/{facility_id}", response_model=FacilityItem)
def update_facility(
    facility_id: uuid.UUID,
    payload: FacilityUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Ubah data Fasilitas di tabel kst_facilities.
    """
    item = db.query(KSTFacility).filter(KSTFacility.id == facility_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fasilitas tidak ditemukan")

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


@router.delete("/{facility_id}", status_code=status.HTTP_200_OK)
def delete_facility(
    facility_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Hapus Fasilitas dari tabel kst_facilities.
    """
    item = db.query(KSTFacility).filter(KSTFacility.id == facility_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fasilitas tidak ditemukan")

    nama = item.nama
    db.delete(item)
    db.commit()
    return {"status": "success", "message": f"Fasilitas '{nama}' berhasil dihapus"}
