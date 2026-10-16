import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base

class KSTJenisKawasan(Base):
    __tablename__ = "kst_jenis_kawasan"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("kst_jenis_kawasan.id", ondelete="SET NULL"), nullable=True)
    nama = Column(String(150), nullable=False)
    slug = Column(String(150), nullable=False, unique=True, index=True)
    deskripsi = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = relationship("KSTJenisKawasan", remote_side=[id], backref="children")

# Backward-compatible aliases
KSTKawasan = KSTJenisKawasan
KSTInstansi = KSTJenisKawasan
