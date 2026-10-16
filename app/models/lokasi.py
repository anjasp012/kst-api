import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, String, Integer, Float, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from app.db.session import Base

from app.models.jenis_kawasan import KSTJenisKawasan
from app.models.galeri import KSTGaleri
from app.models.field_location import NilaiDataLokasi, FieldValueLocation
from app.models.wilayah import WilayahProvinsi, WilayahKabupatenKota



class KSTLokasi(Base):
    __tablename__ = "kst_lokasi"

    # 1. Identitas Utama Lokasi (Tab Utama)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=True)
    deskripsi = Column(Text, nullable=True)

    # 2. Kategori / Jenis Kawasan
    jenis_kawasan_id = Column(UUID(as_uuid=True), ForeignKey("kst_jenis_kawasan.id"), nullable=True)
    jenis_kawasan = relationship("KSTJenisKawasan", foreign_keys=[jenis_kawasan_id])

    # 3. Pengelola & Status
    pengelola = Column(String(150), default="BRIN", nullable=True)
    status = Column(String(50), nullable=True)
    tahun_operasi = Column(Integer, nullable=True)
    is_draft = Column(Boolean, default=False)

    # 4. Relasi Wilayah (Provinsi & Kabupaten/Kota) & Alamat
    provinsi_kode = Column(String(10), ForeignKey("kst_provinsi.kode", ondelete="SET NULL"), nullable=True, index=True)
    kabupaten_kota_kode = Column(String(10), ForeignKey("kst_kabupaten_kota.kode", ondelete="SET NULL"), nullable=True, index=True)
    provinsi = relationship("WilayahProvinsi", foreign_keys=[provinsi_kode])
    kabupaten_kota = relationship("WilayahKabupatenKota", foreign_keys=[kabupaten_kota_kode])
    alamat = Column(Text, nullable=True)

    # 5. Dimensi & Koordinat Spasial PostGIS
    luas_ha = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)

    # 6. Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 7. Relasi Child: Galeri & Nilai Data Lokasi (Tab Dinamis)
    galeri_items = relationship("KSTGaleri", back_populates="lokasi", cascade="all, delete-orphan", order_by="KSTGaleri.created_at")
    extra_fields = relationship("NilaiDataLokasi", back_populates="lokasi", cascade="all, delete-orphan", order_by="NilaiDataLokasi.created_at")

    # --- Property Accessors for Relational & Dynamic Fields ---
    @property
    def provinsi_nama(self):
        return self.provinsi.nama if self.provinsi else None

    @property
    def kabupaten_kota_nama(self):
        return self.kabupaten_kota.nama if self.kabupaten_kota else None

    @property
    def kota_provinsi(self):
        k_nama = self.kabupaten_kota.nama if self.kabupaten_kota else ""
        p_nama = self.provinsi.nama if self.provinsi else ""
        if k_nama and p_nama:
            return f"{k_nama}, {p_nama}"
        return k_nama or p_nama or None

    @kota_provinsi.setter
    def kota_provinsi(self, val):
        pass

    @property
    def wilayah(self):
        if not self.provinsi:
            return None
        p_name = (self.provinsi.nama or "").lower()
        if any(x in p_name for x in ["jawa", "banten", "dki", "jakarta", "yogyakarta"]):
            return "Jawa"
        if any(x in p_name for x in ["sumatera", "aceh", "riau", "jambi", "bengkulu", "lampung", "bangka"]):
            return "Sumatera"
        if "kalimantan" in p_name:
            return "Kalimantan"
        if "sulawesi" in p_name or "gorontalo" in p_name:
            return "Sulawesi"
        if "bali" in p_name or "nusa tenggara" in p_name:
            return "Bali-Nusa Tenggara"
        if "maluku" in p_name:
            return "Maluku"
        if "papua" in p_name:
            return "Papua"
        return "Lainnya"

    @wilayah.setter
    def wilayah(self, val):
        pass

    @property
    def thumbnail_url(self):
        if hasattr(self, "_thumbnail_url") and self._thumbnail_url:
            return self._thumbnail_url
        if self.galeri_items:
            for g in self.galeri_items:
                if (g.tipe or "foto") == "foto" and g.url:
                    return g.url
        return None

    @thumbnail_url.setter
    def thumbnail_url(self, val):
        self._thumbnail_url = val

    @property
    def telepon(self):
        for ef in (self.extra_fields or []):
            lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
            if "telepon" in lbl or "telp" in lbl or "phone" in lbl or "kontak" in lbl:
                return ef.value
        # Fallback: check Saluran Komunikasi & Akses Digital
        for ef in (self.extra_fields or []):
            lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
            if "saluran" in lbl or "digital" in lbl or "komunikasi" in lbl:
                raw_str = str(ef.value or "").strip()
                import re
                val = re.sub(r'<br\s*/?>|</p>', '\n', raw_str, flags=re.IGNORECASE)
                clean = re.sub(r'<[^>]+>', '', val).strip()
                for line in clean.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if "telepon" in line.lower() or "telp" in line.lower():
                        parts = line.split(":", 1)
                        return parts[1].strip() if len(parts) > 1 else line
                    if any(c.isdigit() for c in line) and "@" not in line and "http" not in line and ".go.id" not in line and ".com" not in line:
                        return line
        return None

    @telepon.setter
    def telepon(self, val):
        pass

    @property
    def website(self):
        for ef in (self.extra_fields or []):
            lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
            if "website" in lbl or "web" in lbl or "portal" in lbl:
                return ef.value
        # Fallback: check Saluran Komunikasi & Akses Digital
        for ef in (self.extra_fields or []):
            lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
            if "saluran" in lbl or "digital" in lbl or "komunikasi" in lbl:
                raw_str = str(ef.value or "").strip()
                import re
                val = re.sub(r'<br\s*/?>|</p>', '\n', raw_str, flags=re.IGNORECASE)
                clean = re.sub(r'<[^>]+>', '', val).strip()
                for line in clean.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if "website" in line.lower() or "web" in line.lower() or "portal" in line.lower():
                        parts = line.split(":", 1)
                        return parts[1].strip() if len(parts) > 1 else line
                    if ("http" in line.lower() or ".go.id" in line.lower() or ".com" in line.lower() or ".id" in line.lower()) and "@" not in line:
                        return line
        return None

    @website.setter
    def website(self, val):
        pass

    @property
    def email(self):
        for ef in (self.extra_fields or []):
            lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
            if "email" in lbl or "mail" in lbl:
                return ef.value
        # Fallback: check Saluran Komunikasi & Akses Digital
        for ef in (self.extra_fields or []):
            lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
            if "saluran" in lbl or "digital" in lbl or "komunikasi" in lbl:
                raw_str = str(ef.value or "").strip()
                import re
                val = re.sub(r'<br\s*/?>|</p>', '\n', raw_str, flags=re.IGNORECASE)
                clean = re.sub(r'<[^>]+>', '', val).strip()
                for line in clean.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if "@" in line:
                        if "email" in line.lower() or "mail" in line.lower():
                            parts = line.split(":", 1)
                            return parts[1].strip() if len(parts) > 1 else line
                        return line
        return None

    @email.setter
    def email(self, val):
        pass
    @property
    def jenis_kawasan_nama(self):
        if self.jenis_kawasan:
            return self.jenis_kawasan.nama
        return None

    @jenis_kawasan_nama.setter
    def jenis_kawasan_nama(self, val):
        pass

    @property
    def kawasan_nama(self):
        return self.jenis_kawasan_nama

    @kawasan_nama.setter
    def kawasan_nama(self, val):
        pass

    @property
    def instansi_nama(self):
        return self.jenis_kawasan_nama

    @instansi_nama.setter
    def instansi_nama(self, val):
        pass

    @property
    def kawasan_id(self):
        return self.jenis_kawasan_id

    @kawasan_id.setter
    def kawasan_id(self, val):
        if val is not None:
            self.jenis_kawasan_id = val

    @property
    def instansi_id(self):
        return self.jenis_kawasan_id

    @instansi_id.setter
    def instansi_id(self, val):
        if val is not None:
            self.jenis_kawasan_id = val

    @property
    def tema_riset(self):
        themes = []
        if self.extra_fields:
            import json, uuid
            from app.db.session import SessionLocal
            from app.models.tema_riset import KSTFokusRiset

            uuid_candidates = []
            for ef in self.extra_fields:
                lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
                if "riset" in lbl or "penelitian" in lbl or "fokus" in lbl:
                    val = ef.value
                    if not val:
                        continue
                    if isinstance(val, str) and val.strip().startswith("["):
                        try:
                            val = json.loads(val)
                        except Exception:
                            pass

                    items = val if isinstance(val, list) else [val]
                    for item in items:
                        if not item:
                            continue
                        str_item = str(item).strip()
                        try:
                            u = uuid.UUID(str_item)
                            uuid_candidates.append(u)
                        except ValueError:
                            if str_item and str_item not in themes:
                                themes.append(str_item)

            if uuid_candidates:
                db = SessionLocal()
                try:
                    records = db.query(KSTFokusRiset).filter(KSTFokusRiset.id.in_(uuid_candidates)).all()
                    for r in records:
                        if r.nama and r.nama not in themes:
                            themes.append(r.nama)
                finally:
                    db.close()
        return themes

    @tema_riset.setter
    def tema_riset(self, val):
        pass

    @property
    def fokus_riset(self):
        return self.tema_riset

    @fokus_riset.setter
    def fokus_riset(self, val):
        pass

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

    @galeri.setter
    def galeri(self, val):
        pass

    @property
    def fasilitas(self):
        items = []
        if self.extra_fields:
            import re
            for ef in self.extra_fields:
                lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
                if "fasilitas" in lbl or "lab" in lbl:
                    val = ef.value
                    if not val:
                        continue
                    clean = re.sub(r'<[^>]+>', '', str(val)).strip()
                    subparts = [p.strip() for p in re.split(r'[;\n]+', clean) if p.strip()]
                    for sp in subparts:
                        if sp and sp not in items:
                            items.append(sp)
        return items

    @fasilitas.setter
    def fasilitas(self, val):
        pass

    @property
    def pemanfaatan_layanan(self):
        items = []
        if self.extra_fields:
            import re
            for ef in self.extra_fields:
                lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
                if "pemanfaatan" in lbl or "layanan" in lbl:
                    val = ef.value
                    if not val:
                        continue
                    clean = re.sub(r'<[^>]+>', '', str(val)).strip()
                    subparts = [p.strip() for p in re.split(r'[;\n]+', clean) if p.strip()]
                    for sp in subparts:
                        if sp and sp not in items:
                            items.append(sp)
        return items

    @pemanfaatan_layanan.setter
    def pemanfaatan_layanan(self, val):
        pass

    @property
    def koleksi_unggulan(self):
        if self.extra_fields:
            import re
            for ef in self.extra_fields:
                lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
                if "koleksi" in lbl or "unggulan" in lbl:
                    val = ef.value
                    if not val:
                        continue
                    clean = re.sub(r'<br\s*/?>|</p>', '\n', str(val), flags=re.IGNORECASE)
                    clean = re.sub(r'<[^>]+>', '', clean).strip()
                    return clean
        return None

    @koleksi_unggulan.setter
    def koleksi_unggulan(self, val):
        pass

    @property
    def yang_bisa_ditemui(self):
        items = []
        if self.extra_fields:
            import re
            for ef in self.extra_fields:
                lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
                if "temui" in lbl or "dilakukan" in lbl:
                    val = ef.value
                    if not val:
                        continue
                    clean = re.sub(r'<[^>]+>', '', str(val)).strip()
                    subparts = [p.strip() for p in re.split(r'[;\n]+', clean) if p.strip()]
                    for sp in subparts:
                        if sp and sp not in items:
                            items.append(sp)
        return items

    @yang_bisa_ditemui.setter
    def yang_bisa_ditemui(self, val):
        pass

    @property
    def or_terkait(self):
        items = []
        if self.extra_fields:
            import re
            for ef in self.extra_fields:
                lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
                if "or-terkait" in lbl or "organisasi" in lbl:
                    val = ef.value
                    if not val:
                        continue
                    clean = re.sub(r'<[^>]+>', '', str(val)).strip()
                    subparts = [p.strip() for p in re.split(r'[;\n]+', clean) if p.strip()]
                    for sp in subparts:
                        if sp and sp not in items:
                            items.append(sp)
        return items

    @or_terkait.setter
    def or_terkait(self, val):
        pass

    @property
    def pr_terkait(self):
        items = []
        if self.extra_fields:
            import re
            for ef in self.extra_fields:
                lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
                if "pr-terkait" in lbl or "pusat riset" in lbl:
                    val = ef.value
                    if not val:
                        continue
                    clean = re.sub(r'<[^>]+>', '', str(val)).strip()
                    subparts = [p.strip() for p in re.split(r'[;\n]+', clean) if p.strip()]
                    for sp in subparts:
                        if sp and sp not in items:
                            items.append(sp)
        return items

    @pr_terkait.setter
    def pr_terkait(self, val):
        pass

    @property
    def saluran_digital(self):
        if self.extra_fields:
            import re
            for ef in self.extra_fields:
                lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
                if "saluran" in lbl or "digital" in lbl or "komunikasi" in lbl:
                    val = ef.value
                    if not val:
                        continue
                    clean = re.sub(r'<br\s*/?>|</p>', '\n', str(val), flags=re.IGNORECASE)
                    clean = re.sub(r'<[^>]+>', '', clean).strip()
                    return clean
        return None

    @saluran_digital.setter
    def saluran_digital(self, val):
        pass

    @property
    def tata_kelola(self):
        return {}

    @tata_kelola.setter
    def tata_kelola(self, val):
        pass

    @property
    def info_profil(self):
        return []

    @info_profil.setter
    def info_profil(self, val):
        pass

    @property
    def info_ekosistem(self):
        return []

    @info_ekosistem.setter
    def info_ekosistem(self, val):
        pass

    @property
    def info_utama(self):
        return []

    @info_utama.setter
    def info_utama(self, val):
        pass


# Alias backward compatibility
KSTLocation = KSTLokasi
