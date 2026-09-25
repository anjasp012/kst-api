import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, String, Integer, Float, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from app.db.session import Base


class KSTLocation(Base):
    __tablename__ = "kst_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    wilayah = Column(String(100), nullable=True, index=True)  # Optional / deprecated
    kota_provinsi = Column(String(255), nullable=False)        # e.g. Bandung, Jawa Barat
    pengelola = Column(String(150), default="BRIN", nullable=False)
    status = Column(String(50), nullable=True)
    instansi_id = Column(UUID(as_uuid=True), ForeignKey("kst_instansi.id"), nullable=True)
    instansi = relationship("KSTInstansi")
    telepon = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    email = Column(String(150), nullable=True)
    alamat = Column(Text, nullable=True)
    tahun_operasi = Column(Integer, nullable=True)
    thumbnail_url = Column(String(500), nullable=True)

    # Koordinat Spasial PostGIS
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)

    # --- 6 TAB DATA KST ---
    # Tab 1: Profil
    deskripsi_profil = Column(Text, nullable=True)
    peran_kawasan = Column(Text, nullable=True)

    # Tab 2: Fasilitas
    fasilitas = Column(JSON, default=list)         # [{"nama": "Lab Biofarmaka", "tipe": "Laboratorium", "deskripsi": "..."}]

    # Tab 3: Riset
    riset = Column(JSON, default=list)             # [{"judul": "Riset Bioenergi", "bidang": "Energi", "deskripsi": "..."}]

    # Tab 4: Dampak
    dampak = Column(JSON, default=list)            # [{"judul": "Pemberdayaan Petani", "keterangan": "..."}]

    # Tab 5: Kolaborasi
    potensi_kolaborasi = Column(JSON, default=list) # ["Industri", "Akademisi", "Pemerintah", "Komunitas"]
    daftar_kolaborasi = Column(JSON, default=list)

    # Tab 6: Galeri
    galeri = Column(JSON, default=list)            # ["/uploads/img1.jpg", "/uploads/img2.jpg"]

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    @property
    def instansi_nama(self):
        return self.instansi.nama if self.instansi else None

    @property
    def tema_riset(self):
        if not self.riset:
            return []
        themes = []
        for r in self.riset:
            val = r.get('tema') or r.get('bidang')
            if val and val not in themes:
                themes.append(val)
        return themes
