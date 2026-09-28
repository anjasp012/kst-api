from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base


class WilayahProvinsi(Base):
    """
    Tabel Master Provinsi di Indonesia (38 Provinsi)
    """
    __tablename__ = "kst_provinsi"

    kode = Column(String(10), primary_key=True, index=True)
    nama = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    kabupaten_kota = relationship("WilayahKabupatenKota", back_populates="provinsi", cascade="all, delete-orphan", order_by="WilayahKabupatenKota.nama")

    @property
    def regencies(self):
        return self.kabupaten_kota


class WilayahKabupatenKota(Base):
    """
    Tabel Master Kabupaten dan Kota di Indonesia (514 Kab/Kota)
    """
    __tablename__ = "kst_kabupaten_kota"

    kode = Column(String(10), primary_key=True, index=True)
    province_kode = Column(String(10), ForeignKey("kst_provinsi.kode", ondelete="CASCADE"), nullable=False, index=True)
    nama = Column(String(150), nullable=False, index=True)
    tipe = Column(String(20), nullable=True)  # Kabupaten / Kota
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    provinsi = relationship("WilayahProvinsi", back_populates="kabupaten_kota")

    @property
    def province(self):
        return self.provinsi


# Backward compatibility aliases
WilayahProvince = WilayahProvinsi
WilayahRegency = WilayahKabupatenKota
