import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Persona(Base):
    __tablename__ = "personas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    tagline = Column(Text, nullable=False)
    icon_url = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    relevance_mappings = relationship("InnovationPersonaRelevance", back_populates="persona", cascade="all, delete-orphan")
    innovations = relationship("Innovation", back_populates="persona", cascade="all, delete-orphan")
    suggestions = relationship("ResearchSuggestion", back_populates="persona")
