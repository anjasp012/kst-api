from typing import Optional
from pydantic import BaseModel


class WilayahProvinceItem(BaseModel):
    id: str
    kode: str
    nama: str
    name: Optional[str] = None
    total_regencies: Optional[int] = 0

    class Config:
        from_attributes = True


class WilayahProvinceCreate(BaseModel):
    kode: str
    nama: str


class WilayahProvinceUpdate(BaseModel):
    nama: Optional[str] = None


class WilayahRegencyItem(BaseModel):
    id: str
    kode: str
    province_kode: str
    province_name: Optional[str] = None
    nama: str
    name: Optional[str] = None
    tipe: Optional[str] = None

    class Config:
        from_attributes = True


class WilayahRegencyCreate(BaseModel):
    kode: str
    province_kode: str
    nama: str
    tipe: Optional[str] = None


class WilayahRegencyUpdate(BaseModel):
    nama: Optional[str] = None
    province_kode: Optional[str] = None
    tipe: Optional[str] = None

