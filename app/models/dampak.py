import uuid
from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class KSTDampak(Base):
    """
    Tabel terpisah untuk Pilar Dampak KST (Penguatan Iptek, Daya Saing Industri, Kesejahteraan Masyarakat, dll).
    """
    __tablename__ = "kst_dampak"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    deskripsi = Column(String(255), nullable=True)
    urutan = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
