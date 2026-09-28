import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class KSTGaleri(Base):
    """
    Tabel terpisah untuk Galeri Media KST (Foto & Video) dengan relasi ke kst_lokasi (lokasi_id).
    Hanya menyimpan tipe ('foto'/'video') dan url.
    """
    __tablename__ = "kst_galeri"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lokasi_id = Column(UUID(as_uuid=True), ForeignKey("kst_lokasi.id", ondelete="CASCADE"), nullable=False, index=True)
    tipe = Column(String(20), nullable=False, default="foto")  # 'foto' atau 'video'
    url = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lokasi = relationship("KSTLokasi", back_populates="galeri_items")
