import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, String, Integer, Float, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from app.db.session import Base

from app.models.jenis_kawasan import KSTJenisKawasan
from app.models.galeri import KSTGaleri


class KSTLokasi(Base):
    __tablename__ = "kst_lokasi"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    wilayah = Column(String(100), nullable=True, index=True)
    kota_provinsi = Column(String(255), nullable=False)        # contoh: Bandung, Jawa Barat
    pengelola = Column(String(150), default="BRIN", nullable=False)
    status = Column(String(50), nullable=True)
    is_draft = Column(Boolean, default=False)
    jenis_kawasan_id = Column(UUID(as_uuid=True), ForeignKey("kst_jenis_kawasan.id"), nullable=True)
    jenis_kawasan = relationship("KSTJenisKawasan", foreign_keys=[jenis_kawasan_id])
    kawasan_id = Column(UUID(as_uuid=True), ForeignKey("kst_jenis_kawasan.id"), nullable=True)
    kawasan = relationship("KSTJenisKawasan", foreign_keys=[kawasan_id])
    instansi_id = Column(UUID(as_uuid=True), ForeignKey("kst_jenis_kawasan.id"), nullable=True)
    instansi = relationship("KSTJenisKawasan", foreign_keys=[instansi_id])
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

    # --- DATA PROFIL & 5 TAB ---
    deskripsi_profil = Column(Text, nullable=True)
    peran_kawasan = Column(Text, nullable=True)
    fasilitas = Column(JSON, default=list)
    riset = Column(JSON, default=list)
    dampak = Column(JSON, default=list)
    potensi_kolaborasi = Column(JSON, default=list)
    daftar_kolaborasi = Column(JSON, default=list)
    galeri_items = relationship("KSTGaleri", back_populates="lokasi", cascade="all, delete-orphan", order_by="KSTGaleri.created_at")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def jenis_kawasan_nama(self):
        if self.jenis_kawasan:
            return self.jenis_kawasan.nama
        if self.kawasan:
            return self.kawasan.nama
        if self.instansi:
            return self.instansi.nama
        return None

    @property
    def kawasan_nama(self):
        return self.jenis_kawasan_nama

    @property
    def instansi_nama(self):
        return self.jenis_kawasan_nama

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

    @property
    def galeri(self):
        if not self.galeri_items:
            return []
        return [
            {
                "id": str(g.id),
                "lokasi_id": str(g.lokasi_id),
                "tipe": g.tipe or "foto",
                "url": g.url,
            }
            for g in self.galeri_items
        ]



# Alias backward compatibility
KSTLocation = KSTLokasi
