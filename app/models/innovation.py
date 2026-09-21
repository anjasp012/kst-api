import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, JSON, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Innovation(Base):
    __tablename__ = "innovations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title = Column(String(255), index=True, nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    trl = Column(Integer, default=1, nullable=False)
    
    short_description = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    impact = Column(Text, nullable=False)
    
    thumbnail_url = Column(String(500), nullable=True)
    research_center = Column(String(255), nullable=True)
    implementation_potential = Column(JSON, default=list, nullable=True)
    relevant_tags = Column(JSON, default=list, nullable=True)
    media_gallery = Column(JSON, default=list, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    zone = relationship("Zone", back_populates="innovations")
    persona = relationship("Persona", back_populates="innovations")
    persona_relevances = relationship("InnovationPersonaRelevance", back_populates="innovation", cascade="all, delete-orphan")

    @property
    def persona_name(self):
        return self.persona.name if self.persona else None
