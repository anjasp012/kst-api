import uuid
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.core.helpers import build_full_url, build_full_url_list


class LokasiBase(BaseModel):
    nama: str = Field(..., example="KST Jawa Barat")
    slug: str = Field(..., example="kst-jawa-barat")
    wilayah: Optional[str] = Field(None, example="Jawa")
    kota_provinsi: str = Field(..., example="Bandung, Jawa Barat")
    pengelola: Optional[str] = None
    status: Optional[str] = None
    jenis_kawasan_nama: Optional[str] = Field(None, example="Kawasan Sains (KST)")
    kawasan_nama: Optional[str] = Field(None, example="Kawasan Sains (KST)")
    instansi_nama: Optional[str] = Field(None, example="Kawasan Sains (KST)")
    telepon: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    alamat: Optional[str] = None
    tahun_operasi: Optional[int] = None
    thumbnail_url: Optional[str] = None
    latitude: Optional[float] = Field(None, example=-6.917464)
    longitude: Optional[float] = Field(None, example=107.619122)

    # 6 Tab Data Kawasan / Lokasi
    deskripsi_profil: Optional[str] = None
    peran_kawasan: Optional[str] = None
    fasilitas: List[Any] = Field(default_factory=list)
    riset: List[Any] = Field(default_factory=list)
    dampak: List[Any] = Field(default_factory=list)
    potensi_kolaborasi: List[str] = Field(default_factory=list)
    daftar_kolaborasi: List[Any] = Field(default_factory=list)
    galeri: List[Any] = Field(default_factory=list)
    is_draft: bool = False


class LokasiCreate(LokasiBase):
    pass


class LokasiUpdate(BaseModel):
    nama: Optional[str] = None
    slug: Optional[str] = None
    wilayah: Optional[str] = None
    kota_provinsi: Optional[str] = None
    pengelola: Optional[str] = None
    status: Optional[str] = None
    jenis_kawasan_nama: Optional[str] = Field(None, example="Kawasan Sains (KST)")
    kawasan_nama: Optional[str] = Field(None, example="Kawasan Sains (KST)")
    instansi_nama: Optional[str] = Field(None, example="Kawasan Sains (KST)")
    telepon: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    alamat: Optional[str] = None
    tahun_operasi: Optional[int] = None
    thumbnail_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    deskripsi_profil: Optional[str] = None
    peran_kawasan: Optional[str] = None
    fasilitas: Optional[List[Any]] = None
    riset: Optional[List[Any]] = None
    dampak: Optional[List[Any]] = None
    potensi_kolaborasi: Optional[List[str]] = None
    daftar_kolaborasi: Optional[List[Any]] = None
    galeri: Optional[List[Any]] = None
    is_draft: Optional[bool] = None


class LokasiMapItem(BaseModel):
    id: uuid.UUID
    nama: str
    slug: str
    wilayah: Optional[str] = None
    kota_provinsi: str
    pengelola: Optional[str] = None
    status: Optional[str] = None
    jenis_kawasan_nama: Optional[str] = Field(None, example="Kawasan Sains (KST)")
    kawasan_nama: Optional[str] = Field(None, example="Kawasan Sains (KST)")
    instansi_nama: Optional[str] = Field(None, example="Kawasan Sains (KST)")
    telepon: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    alamat: Optional[str] = None
    tahun_operasi: Optional[int] = None
    thumbnail_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    tema_riset: List[str] = []
    is_draft: bool = False

    @field_validator("thumbnail_url", mode="after")
    @classmethod
    def resolve_thumb(cls, v):
        return build_full_url(v)

    class Config:
        from_attributes = True


class WilayahRingkas(BaseModel):
    provinsi: Optional[str] = ""
    kabupaten: Optional[str] = ""


class KoordinatRingkas(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class LokasiRingkasItem(BaseModel):
    id: uuid.UUID
    nama: str
    slug: str
    wilayah: WilayahRingkas
    koordinat: KoordinatRingkas
    deskripsi: Optional[str] = None
    fokus_riset: List[str] = []

    class Config:
        from_attributes = True


class LokasiRingkasListResponse(BaseModel):
    total: int
    data: List[LokasiRingkasItem]


class LokasiFilterRequest(BaseModel):
    wilayah: Optional[List[str]] = Field(default=None, description="Filter wilayah/provinsi (bisa lebih dari 1, null jika tidak difilter)")
    jenis_kawasan: Optional[List[str]] = Field(default=None, description="Filter jenis kawasan (bisa lebih dari 1, null jika tidak difilter)")
    fokus_riset: Optional[List[str]] = Field(default=None, description="Filter fokus riset (bisa lebih dari 1, null jika tidak difilter)")
    input: Optional[str] = Field(default=None, description="Input teks pencarian bebas (nama lokasi, kota, deskripsi)")
    q: Optional[str] = Field(default=None, description="Alias untuk input")

    @field_validator("wilayah", "jenis_kawasan", "fokus_riset", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v_str = v.strip()
            return [v_str] if v_str else None
        if isinstance(v, list):
            res = [str(x).strip() for x in v if str(x).strip()]
            return res if res else None
        return v


class LokasiDetail(LokasiBase):
    id: uuid.UUID
    gambar: List[str] = Field(default_factory=list, description="Daftar URL gambar/foto lokasi")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("thumbnail_url", mode="after")
    @classmethod
    def resolve_thumb(cls, v):
        return build_full_url(v)

    @field_validator("galeri", mode="after")
    @classmethod
    def resolve_gallery(cls, v):
        if not v:
            return []
        video_exts = (".mp4", ".webm", ".mov", ".m4v", ".ogg", ".avi", ".mkv")
        resolved = []
        for item in v:
            if isinstance(item, str):
                is_video = any(item.lower().endswith(ext) for ext in video_exts)
                resolved.append({
                    "tipe": "video" if is_video else "foto",
                    "url": build_full_url(item)
                })
            elif isinstance(item, dict):
                url_val = build_full_url(item.get("url", ""))
                tipe_val = item.get("tipe") or ("video" if any(url_val.lower().endswith(ext) for ext in video_exts) else "foto")
                entry = {
                    "tipe": tipe_val,
                    "url": url_val
                }
                if "id" in item and item["id"]:
                    entry["id"] = item["id"]
                if "lokasi_id" in item and item["lokasi_id"]:
                    entry["lokasi_id"] = item["lokasi_id"]
                resolved.append(entry)
            else:
                resolved.append(item)
        return resolved

    class Config:
        from_attributes = True


# Aliases for backward compatibility
LokasiRingkas = LokasiRingkasItem
LocationRingkasItem = LokasiRingkasItem

LocationBase = LokasiBase
LocationCreate = LokasiCreate
LocationUpdate = LokasiUpdate
LocationMapItem = LokasiMapItem
LocationDetail = LokasiDetail

KSTBase = LokasiBase
KSTCreate = LokasiCreate
KSTUpdate = LokasiUpdate
KSTMapItem = LokasiMapItem
KSTDetail = LokasiDetail
