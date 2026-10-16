import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, String, Integer, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base
from app.models.tema_riset import KSTFokusRiset

class LabelDataLokasi(Base):
    __tablename__ = "label_data_lokasi"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama = Column(String(150), nullable=False, unique=True)
    slug = Column(String(150), nullable=False, unique=True)
    placeholder = Column(String(255), nullable=True)
    icon = Column(String(50), default="FileText")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def tipe(self):
        return None

    @tipe.setter
    def tipe(self, val):
        pass


class NilaiDataLokasi(Base):
    __tablename__ = "nilai_data_lokasi"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lokasi_id = Column(UUID(as_uuid=True), ForeignKey("kst_lokasi.id", ondelete="CASCADE"), nullable=False)
    field_label_id = Column(UUID(as_uuid=True), ForeignKey("label_data_lokasi.id", ondelete="CASCADE"), nullable=False)
    value = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lokasi = relationship("KSTLokasi", back_populates="extra_fields")
    field_label = relationship("LabelDataLokasi")

    @property
    def label(self):
        return self.field_label.nama if self.field_label else None

    @property
    def tipe(self):
        return None

    @tipe.setter
    def tipe(self, val):
        pass



# Backward compatibility aliases
FieldLabelLocation = LabelDataLokasi
FieldValueLocation = NilaiDataLokasi

