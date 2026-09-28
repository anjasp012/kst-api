import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base

class KSTJenisKawasan(Base):
    __tablename__ = "kst_jenis_kawasan"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama = Column(String(150), nullable=False)
    slug = Column(String(150), nullable=False, unique=True, index=True)
    deskripsi = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Backward-compatible aliases
KSTKawasan = KSTJenisKawasan
KSTInstansi = KSTJenisKawasan
