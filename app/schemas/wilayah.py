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

