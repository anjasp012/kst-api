from typing import Optional
from pydantic import BaseModel


class WilayahProvinceItem(BaseModel):
    id: str
    kode: str
    nama: str
    name: str
    wilayah: str

    class Config:
        from_attributes = True


class WilayahProvinceCreate(BaseModel):
    kode: str
    nama: str
    wilayah: str


class WilayahProvinceUpdate(BaseModel):
    nama: Optional[str] = None
    wilayah: Optional[str] = None


class WilayahRegencyItem(BaseModel):
    id: str
    kode: str
    province_id: str
    province_kode: str
    nama: str
    name: str
    tipe: Optional[str] = None

    class Config:
        from_attributes = True
