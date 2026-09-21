import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Zone(Base):
    __tablename__ = "zones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    icon_url = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    innovations = relationship("Innovation", back_populates="zone", cascade="all, delete-orphan")
    suggestions = relationship("ResearchSuggestion", back_populates="zone")
