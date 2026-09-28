import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class KSTKolaborasi(Base):
    """
    Tabel terpisah untuk Potensi Mitra Kolaborasi KST (Industri, Akademisi, Pemerintah, Komunitas, dll).
    """
    __tablename__ = "kst_kolaborasi"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    deskripsi = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


KSTCollaboration = KSTKolaborasi
