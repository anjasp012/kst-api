import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from app.db.session import Base


class KSTLocation(Base):
    __tablename__ = "kst_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    wilayah = Column(String(100), nullable=False, index=True)  # Sumatera, Jawa, Kalimantan, Sulawesi, Nusa Tenggara, Maluku & Papua
    kota_provinsi = Column(String(255), nullable=False)        # e.g. Bandung, Jawa Barat
    pengelola = Column(String(150), default="BRIN", nullable=False)
    status = Column(String(50), default="Aktif", nullable=False)
    tahun_operasi = Column(Integer, default=2021, nullable=False)
    thumbnail_url = Column(String(500), nullable=True)

    # Koordinat Spasial PostGIS
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)

    # --- 6 TAB DATA KST ---
    # Tab 1: Profil
    deskripsi_profil = Column(Text, nullable=True)
    peran_kawasan = Column(Text, nullable=True)
    fokus_utama = Column(JSON, default=list)        # ["Pangan", "Energi", "Laut", "Teknologi Digital"]
    terhubung_dengan = Column(Text, nullable=True)  # "Peneliti, industri, pemerintah, komunitas, dan mitra pendidikan."

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

