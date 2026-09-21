import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    event_type = Column(String(100), index=True, nullable=False)

    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id", ondelete="SET NULL"), nullable=True, index=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="SET NULL"), nullable=True, index=True)
    innovation_id = Column(UUID(as_uuid=True), ForeignKey("innovations.id", ondelete="SET NULL"), nullable=True, index=True)

    description = Column(Text, nullable=True)
    metadata_payload = Column(JSON, default=dict, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    persona = relationship("Persona")
    zone = relationship("Zone")
    innovation = relationship("Innovation")

    @property
    def keterangan(self):
        return self.description
