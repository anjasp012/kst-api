import uuid
from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from app.core.helpers import build_full_url, build_full_url_list


class WilayahRingkas(BaseModel):
    provinsi: Optional[str] = ""
    kabupaten: Optional[str] = ""


class KoordinatRingkas(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class LokasiBase(BaseModel):
    nama: str = Field(..., example="KST Jawa Barat")
    slug: Optional[str] = Field(None, example="kst-jawa-barat")
    provinsi_kode: Optional[str] = None
    kabupaten_kota_kode: Optional[str] = None
    provinsi_nama: Optional[str] = None
    kabupaten_kota_nama: Optional[str] = None
    provinsi: Optional[str] = None
    kabupaten: Optional[str] = None
    wilayah: Optional[str] = Field(None, example="Jawa")
    wilayah_detail: Optional[WilayahRingkas] = None
    kota_provinsi: Optional[str] = Field(None, example="Bandung, Jawa Barat")
    pengelola: Optional[str] = None
    status: Optional[str] = None
    jenis_kawasan: Optional[str] = Field(None, example="Kawasan Sains (KST)")
    jenis_kawasan_id: Optional[uuid.UUID] = None
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
    koordinat: Optional[KoordinatRingkas] = None
    luas_ha: Optional[float] = Field(None, example=309.0)

    # Deskripsi & Galeri
    deskripsi: Optional[str] = None
    galeri: List[Any] = Field(default_factory=list)
    extra_fields: List[Any] = Field(default_factory=list)
    is_draft: bool = False

    @field_validator("jenis_kawasan", "provinsi", "kabupaten", mode="before")
    @classmethod
    def resolve_rel_strings(cls, v):
        if hasattr(v, "nama"):
            return getattr(v, "nama", None)
        return v


class LokasiCreate(LokasiBase):
    pass


class LokasiUpdate(BaseModel):
    nama: Optional[str] = None
    slug: Optional[str] = None
    provinsi_kode: Optional[str] = None
    kabupaten_kota_kode: Optional[str] = None
    wilayah: Optional[str] = None
    kota_provinsi: Optional[str] = None
    pengelola: Optional[str] = None
    status: Optional[str] = None
    jenis_kawasan_id: Optional[uuid.UUID] = None
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
    luas_ha: Optional[float] = None
    deskripsi: Optional[str] = None
    galeri: Optional[List[Any]] = None
    extra_fields: Optional[List[Any]] = None
    is_draft: Optional[bool] = None


class LokasiMapItem(BaseModel):
    id: uuid.UUID
    nama: str
    slug: str
    provinsi_kode: Optional[str] = None
    kabupaten_kota_kode: Optional[str] = None
    provinsi_nama: Optional[str] = None
    kabupaten_kota_nama: Optional[str] = None
    wilayah: Optional[str] = None
    kota_provinsi: Optional[str] = None
    pengelola: Optional[str] = None
    status: Optional[str] = None
    jenis_kawasan_id: Optional[uuid.UUID] = None
    jenis_kawasan_nama: Optional[str] = Field(None, example="Kawasan Sains (KST)")
    kawasan_nama: Optional[str] = Field(None, example="Kawasan Sains (KST)")
    instansi_nama: Optional[str] = Field(None, example="Kawasan Sains (KST)")
    telepon: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    alamat: Optional[str] = None
    deskripsi: Optional[str] = None
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


class LokasiRingkasItem(BaseModel):
    id: uuid.UUID
    nama: str
    slug: str
    jenis_kawasan: Optional[str] = None
    jenis_kawasan_id: Optional[uuid.UUID] = None
    alamat: Optional[str] = None
    kota_provinsi: Optional[str] = None
    wilayah: WilayahRingkas
    koordinat: KoordinatRingkas
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    deskripsi: Optional[str] = None
    fokus_riset: List[str] = []

    class Config:
        from_attributes = True


class LokasiRingkasListResponse(BaseModel):
    total: int
    data: List[LokasiRingkasItem]


class LokasiFilterRequest(BaseModel):
    wilayah: Optional[List[str]] = None
    jenis_kawasan: Optional[List[str]] = None
    fokus_riset: Optional[List[str]] = None
    search_input: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def resolve_search_text(cls, data):
        if isinstance(data, dict):
            if not data.get("search_input"):
                data["search_input"] = data.get("input") or data.get("q")
        return data

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


class ItemDataTambahanPublik(BaseModel):
    label: str
    slug: str
    icon: Optional[str] = "FileText"
    value: Any

    class Config:
        from_attributes = True


class ItemDataTambahan(BaseModel):
    id: Optional[str] = None
    field_label_id: Optional[str] = None
    label: str
    slug: str
    icon: Optional[str] = "FileText"
    value: Any

    class Config:
        from_attributes = True


class LokasiDetail(LokasiBase):
    id: uuid.UUID
    gambar: List[str] = Field(default_factory=list, description="Daftar URL gambar/foto lokasi")
    extra_fields: List[ItemDataTambahan] = Field(default_factory=list)
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
                raw_url = item.get("url", "")
                if isinstance(raw_url, dict):
                    raw_url = raw_url.get("relative_url") or raw_url.get("file_url") or raw_url.get("url") or ""
                url_val = build_full_url(str(raw_url or ""))
                tipe_val = item.get("tipe") or ("video" if url_val and any(url_val.lower().endswith(ext) for ext in video_exts) else "foto")
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

    @field_validator("extra_fields", mode="before")
    @classmethod
    def resolve_extra_fields(cls, v):
        if not v:
            return []
        import json
        resolved = []
        entries_by_key = {}

        for ef in v:
            if isinstance(ef, dict):
                resolved.append(ef)
                continue
            
            parsed_val = getattr(ef, "value", None)
            try:
                if parsed_val and isinstance(parsed_val, str) and (parsed_val.startswith("[") or parsed_val.startswith("{")):
                    parsed_val = json.loads(parsed_val)
            except Exception:
                pass

            fl = getattr(ef, "field_label", None)
            lbl_name = fl.nama if fl else (getattr(ef, "label", None) or "")
            lbl_slug = fl.slug if fl else ""
            lbl_icon = fl.icon if fl else "FileText"

            is_fokus = (lbl_slug == 'fokus-riset') or ("fokus" in lbl_name.lower() and "riset" in lbl_name.lower())
            group_key = "fokus-riset" if is_fokus else (lbl_slug or lbl_name.lower().strip() or str(getattr(ef, "field_label_id", "")))

            if not group_key:
                group_key = str(getattr(ef, "id", ""))

            if group_key not in entries_by_key:
                entry = {
                    "id": str(getattr(ef, "id", "")),
                    "field_label_id": str(getattr(ef, "field_label_id", "")) if getattr(ef, "field_label_id", None) else None,
                    "label": lbl_name or ("Fokus Riset" if is_fokus else "Data Opsional"),
                    "nama": lbl_name or ("Fokus Riset" if is_fokus else "Data Opsional"),
                    "slug": "fokus-riset" if is_fokus else lbl_slug,
                    "icon": ("Atom" if is_fokus else lbl_icon) or "FileText",
                    "value": [],
                }
                entries_by_key[group_key] = entry
                resolved.append(entry)

            target_entry = entries_by_key[group_key]

            val_to_add = parsed_val
            if is_fokus and parsed_val and isinstance(parsed_val, str):
                import uuid
                try:
                    u_val = uuid.UUID(parsed_val.strip())
                    from app.db.session import SessionLocal
                    from app.models.tema_riset import KSTFokusRiset
                    db_temp = SessionLocal()
                    try:
                        fr_item = db_temp.query(KSTFokusRiset).filter(KSTFokusRiset.id == u_val).first()
                        if fr_item:
                            val_to_add = fr_item.nama
                    finally:
                        db_temp.close()
                except ValueError:
                    pass

            if isinstance(val_to_add, list):
                for vs in val_to_add:
                    if vs is not None and str(vs).strip() and vs not in target_entry["value"]:
                        target_entry["value"].append(vs)
            elif val_to_add is not None and str(val_to_add).strip():
                if val_to_add not in target_entry["value"]:
                    target_entry["value"].append(val_to_add)

        for item in resolved:
            v_list = item.get("value", [])
            is_list_field = item.get("slug") in ["fokus-riset", "fasilitas", "organisasi-riset", "pusat-riset", "pemanfaatan-layanan"] or len(v_list) > 1
            if not is_list_field and len(v_list) == 1:
                item["value"] = v_list[0]
            else:
                item["value"] = v_list

        return resolved

    @model_validator(mode="after")
    def populate_extra_details(self):
        # 1. Koordinat & Relasi Dasar
        if not self.koordinat:
            self.koordinat = KoordinatRingkas(
                latitude=self.latitude,
                longitude=self.longitude,
                lat=self.latitude,
                lng=self.longitude
            )
        if not self.jenis_kawasan:
            self.jenis_kawasan = self.jenis_kawasan_nama or self.kawasan_nama or self.instansi_nama or None
        if not self.provinsi:
            self.provinsi = self.provinsi_nama or None
        if not self.kabupaten:
            self.kabupaten = self.kabupaten_kota_nama or None
        if not self.wilayah_detail:
            self.wilayah_detail = WilayahRingkas(
                provinsi=self.provinsi or "",
                kabupaten=self.kabupaten or ""
            )

        # 2. Sinkronisasi Foto & Galeri
        if not self.gambar:
            g_list = []
            if self.thumbnail_url:
                g_list.append(self.thumbnail_url)
            for g in (self.galeri or []):
                u = g.get("url") if isinstance(g, dict) else g
                if u and u not in g_list:
                    g_list.append(u)
            self.gambar = g_list

        if not self.thumbnail_url and self.gambar:
            self.thumbnail_url = self.gambar[0]

        return self

    class Config:
        from_attributes = True


class LokasiPublikDetail(BaseModel):
    id: uuid.UUID
    nama: str
    slug: str
    jenis_kawasan: Optional[str] = Field(None, description="Kategori / Jenis Kawasan")
    jenis_kawasan_nama: Optional[str] = None
    pengelola: Optional[str] = "BRIN"
    status: Optional[str] = "Aktif"
    tahun_operasi: Optional[int] = None
    alamat: Optional[str] = None
    kota_provinsi: Optional[str] = None
    wilayah: Optional[str] = None
    provinsi: Optional[str] = None
    kabupaten: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    koordinat: Optional[KoordinatRingkas] = None
    luas_ha: Optional[float] = None
    deskripsi: Optional[str] = None
    thumbnail_url: Optional[str] = None
    galeri: List[Any] = Field(default_factory=list)
    extra_fields: List[ItemDataTambahanPublik] = Field(default_factory=list)

    @field_validator("thumbnail_url", mode="after")
    @classmethod
    def resolve_thumb(cls, v):
        return build_full_url(v)

    class Config:
        from_attributes = True


# Aliases for backward compatibility
LokasiRingkas = LokasiRingkasItem
LocationRingkasItem = LokasiRingkasItem

LokasiPublicDetail = LokasiPublikDetail
LocationPublicDetail = LokasiPublikDetail
KSTPublicDetail = LokasiPublikDetail

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


class LabelDataLokasiItem(BaseModel):
    id: str
    nama: str
    slug: str
    placeholder: Optional[str] = None
    icon: Optional[str] = "FileText"

    class Config:
        from_attributes = True


class LabelDataLokasiCreate(BaseModel):
    nama: str
    slug: Optional[str] = None
    placeholder: Optional[str] = None
    icon: Optional[str] = "FileText"


class LabelDataLokasiUpdate(BaseModel):
    nama: Optional[str] = None
    slug: Optional[str] = None
    placeholder: Optional[str] = None
    icon: Optional[str] = None

