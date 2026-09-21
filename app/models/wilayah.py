from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class WilayahProvince(Base):
    __tablename__ = "wilayah_provinces"

    kode = Column(String(10), primary_key=True, index=True)
    nama = Column(String(100), nullable=False, index=True)
    wilayah = Column(String(50), nullable=False, index=True)  # Sumatera, Jawa, Kalimantan, Sulawesi, Nusa Tenggara, Maluku & Papua

    regencies = relationship("WilayahRegency", back_populates="province", cascade="all, delete-orphan", order_by="WilayahRegency.nama")


class WilayahRegency(Base):
    __tablename__ = "wilayah_regencies"

    kode = Column(String(10), primary_key=True, index=True)
    province_kode = Column(String(10), ForeignKey("wilayah_provinces.kode", ondelete="CASCADE"), nullable=False, index=True)
    nama = Column(String(150), nullable=False, index=True)
    tipe = Column(String(20), nullable=True)  # Kabupaten / Kota

    province = relationship("WilayahProvince", back_populates="regencies")

