import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class KSTTemaRiset(Base):
    """
    Tabel terpisah untuk Tema Riset KST (Energi & Material, Maritim, Kesehatan, dll).
    """
    __tablename__ = "kst_tema_riset"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    deskripsi = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


KSTThemeRiset = KSTTemaRiset
