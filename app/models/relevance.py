import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base


class InnovationPersonaRelevance(Base):
    __tablename__ = "innovation_persona_relevance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    innovation_id = Column(UUID(as_uuid=True), ForeignKey("innovations.id", ondelete="CASCADE"), nullable=False, index=True)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)
    relevance_score = Column(Integer, default=50, nullable=False)
    custom_impact = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("innovation_id", "persona_id", name="uq_innovation_persona"),
    )

    innovation = relationship("Innovation", back_populates="persona_relevances")
    persona = relationship("Persona", back_populates="relevance_mappings")
