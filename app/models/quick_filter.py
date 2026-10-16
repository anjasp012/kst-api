import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base

class KSTQuickFilter(Base):
    __tablename__ = "kst_quick_filter"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama = Column(String(150), nullable=False)
    slug = Column(String(150), nullable=False, unique=True, index=True)
    filter_data = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Backward-compatible alias
QuickFilter = KSTQuickFilter
