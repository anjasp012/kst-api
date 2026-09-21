import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class ResearchSuggestion(Base):
    __tablename__ = "research_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    visitor_name = Column(String(255), nullable=True)
    age_range = Column(String(50), nullable=True)
    topic_wanted = Column(Text, nullable=False)
    feedback = Column(Text, nullable=True)
    
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id", ondelete="SET NULL"), nullable=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    screen_context = Column(String(100), default="Explore", nullable=False)
    
    status = Column(String(50), default="NEW", nullable=False)  # NEW, REVIEWED, ARCHIVED
    admin_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    persona = relationship("Persona", back_populates="suggestions")
    zone = relationship("Zone", back_populates="suggestions")
