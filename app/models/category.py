import uuid
from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class KSTCategory(Base):
    __tablename__ = "kst_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipe = Column(String(50), nullable=False, index=True)  # 'tema_riset', 'tipe_fasilitas', 'potensi_kolaborasi'
    nama = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, index=True)
    urutan = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

