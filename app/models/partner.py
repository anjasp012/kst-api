import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from app.db.session import Base


class RegionalPartner(Base):
    __tablename__ = "regional_partners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama_organisasi = Column(String(255), nullable=False, index=True) # e.g. BAPPEDA Kab. Bireuen
    jenis = Column(String(50), nullable=False, index=True)           # BRIDA, BAPPERIDA, BAPPEDA
    wilayah = Column(String(100), nullable=True, index=True)         # Sumatera, Jawa, Kalimantan, dll.
    alamat = Column(Text, nullable=True)
    telepon = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    email = Column(String(150), nullable=True)

    # Koordinat Spasial PostGIS
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

