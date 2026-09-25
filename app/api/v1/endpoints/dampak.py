import re
import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.dampak import KSTDampak
from app.models.user import User
from app.schemas.dampak import DampakItem, DampakCreate, DampakUpdate
from app.api.v1.deps import get_current_admin

router = APIRouter()


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[\s\W-]+', '-', text)
    return text.strip('-')


@router.get("", response_model=List[DampakItem])
def get_dampak_list(
    include_inactive: bool = Query(False, description="Tampilkan item nonaktif juga (untuk CMS)"),
    db: Session = Depends(get_db)
):
    """
    Mengambil daftar Pilar Dampak KST (Tabel: kst_dampak).
    """
    query = db.query(KSTDampak)
    if not include_inactive:
        query = query.filter(KSTDampak.is_active == True)
    return query.order_by(KSTDampak.urutan.asc(), KSTDampak.nama.asc()).all()


@router.post("", response_model=DampakItem, status_code=status.HTTP_201_CREATED)
def create_dampak(
    payload: DampakCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Tambah Pilar Dampak baru ke tabel kst_dampak.
    """
    slug = payload.slug or slugify(payload.nama)
    existing = db.query(KSTDampak).filter(
        (KSTDampak.slug == slug) | (KSTDampak.nama.ilike(payload.nama.strip()))
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dampak '{payload.nama}' sudah terdaftar"
        )

    item = KSTDampak(
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


@router.put("/{dampak_id}", response_model=DampakItem)
def update_dampak(
    dampak_id: uuid.UUID,
    payload: DampakUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Ubah data Pilar Dampak di tabel kst_dampak.
    """
    item = db.query(KSTDampak).filter(KSTDampak.id == dampak_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dampak tidak ditemukan")

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


@router.delete("/{dampak_id}", status_code=status.HTTP_200_OK)
def delete_dampak(
    dampak_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Hapus Pilar Dampak dari tabel kst_dampak.
    """
    item = db.query(KSTDampak).filter(KSTDampak.id == dampak_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dampak tidak ditemukan")

    nama = item.nama
    db.delete(item)
    db.commit()
    return {"status": "success", "message": f"Dampak '{nama}' berhasil dihapus"}

