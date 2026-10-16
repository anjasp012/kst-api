import io
import csv
import re
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.lokasi import KSTLokasi
from app.models.jenis_kawasan import KSTJenisKawasan
from app.models.wilayah import WilayahProvinsi, WilayahKabupatenKota
from app.models.tema_riset import KSTFokusRiset
from app.models.field_location import LabelDataLokasi, NilaiDataLokasi
from app.api.v1.endpoints.lokasi import _set_point_geom

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


TEMPLATE_COLUMNS = [
    ("nama", "Nama Lokasi *", "Wajib diisi. Nama lengkap kawasan/lokasi (cth: BRIDA Kota Medan)"),
    ("jenis_kawasan", "Jenis Kawasan", "Nama kategori (cth: BRIDA, Kawasan Sains dan Teknologi (KST), Kebun Raya)"),
    ("provinsi", "Provinsi", "Nama Provinsi (cth: Sumatera Utara, Jawa Timur, DKI Jakarta)"),
    ("kabupaten_kota", "Kabupaten / Kota", "Nama Kabupaten atau Kota (cth: Kota Medan, Kab. Pelalawan)"),
    ("alamat", "Alamat", "Alamat jalan atau komplek kantor"),
    ("latitude", "Latitude", "Garis Lintang dalam angka desimal (cth: 3.543473)"),
    ("longitude", "Longitude", "Garis Bujur dalam angka desimal (cth: 98.673736)"),
    ("deskripsi", "Deskripsi", "Deskripsi profil atau keterangan tentang kawasan"),
    ("telepon", "Nomor Telepon", "Nomor kontak / call center (cth: (061) 7873439)"),
    ("website", "Website Resmi", "Alamat URL website (cth: http://brida.pemkomedan.go.id/)"),
    ("email", "Email Resmi", "Alamat email resmi (cth: brida@medan.go.id)"),
    ("saluran_digital", "Saluran Komunikasi & Akses Digital", "Teks biasa kontak / medsos resmi (cth: IG: kebunrayabalangan | Youtube: KebunRayaBalangan)"),
    ("fokus_riset", "Fokus Riset", "Topik / fokus riset dipisahkan dengan koma (cth: Pertanian, Energi Terbarukan, Bioteknologi)"),
    ("fasilitas", "Fasilitas & Laboratorium", "Daftar fasilitas / lab, dipisahkan dengan titik koma (;) untuk tiap item fasilitas (cth: Ruang Tracking; Ruang Pengujian)"),
    ("pemanfaatan_layanan", "Pemanfaatan & Layanan", "Daftar pemanfaatan / layanan, dipisahkan dengan titik koma (;) untuk tiap item layanan (cth: Layanan Fasilitasi Penelitian; Layanan Pendidikan Lingkungan untuk siswa)"),
    ("koleksi_unggulan", "Koleksi Unggulan", "Teks biasa penjelasan koleksi unggulan kawasan (boleh menggunakan poin atau paragraf biasa)"),
    ("yang_bisa_ditemui", "Yang Bisa Ditemui & Dilakukan", "Kegiatan dan aktivitas yang bisa ditemui atau dilakukan di kawasan, dipisahkan titik koma (;) (cth: Edukasi Botani; Wisata Edukasi; Konservasi Alam)"),
    ("or_terkait", "Organisasi Riset Terkait (OR)", "Daftar Organisasi Riset BRIN terkait, dipisahkan titik koma (;) (cth: OR Hayati dan Lingkungan; OR Nanoteknologi dan Material)"),
    ("pr_terkait", "Pusat Riset Terkait (PR)", "Daftar Pusat Riset BRIN terkait, dipisahkan titik koma (;) (cth: PR Konservasi Tumbuhan, Kebun Raya dan Kehutanan; PR Biosistematika dan Evolusi)"),
    ("pengelola", "Pengelola", "Instansi pengelola (default: BRIN)"),
    ("status", "Status", "Status operasional (cth: Aktif, Beroperasi, Pembangunan)"),
    ("tahun_operasi", "Tahun Operasi", "Tahun mulai beroperasi dalam angka (cth: 2021)"),
    ("luas_ha", "Luas Kawasan (Ha)", "Luas area dalam Hektar (cth: 25.5)"),
]

SAMPLE_ROWS = [
    {
        "nama": "BRIDA Kota Medan",
        "jenis_kawasan": "BRIDA",
        "provinsi": "Sumatera Utara",
        "kabupaten_kota": "Kota Medan",
        "alamat": "Jl. Jenderal Besar A.H. Nasution No.32, Pangkalan Masyhur, Kec. Medan Johor",
        "latitude": 3.543473,
        "longitude": 98.673736,
        "deskripsi": "Badan Riset dan Inovasi Daerah Kota Medan bertugas memperkuat ekosistem riset terapan dan inovasi daerah.",
        "telepon": "(061) 7873439",
        "website": "http://brida.pemkomedan.go.id/",
        "email": "brida@medan.go.id",
        "saluran_digital": "Telp: (061) 7873439\nWebsite: http://brida.pemkomedan.go.id/\nEmail: brida@medan.go.id",
        "fokus_riset": "Tata Kelola Pemerintahan, Ekonomi Digital",
        "fasilitas": "Laboratorium Riset Terapan; Ruang Inkubasi Startup; Ruang Pengujian Produk",
        "pemanfaatan_layanan": "Layanan Fasilitasi Penelitian; Konsultasi Inovasi Daerah; Pendampingan HKI",
        "koleksi_unggulan": "• Data produk inovasi daerah\n• Purwarupa teknologi tepat guna UMKM",
        "yang_bisa_ditemui": "Konsultasi Kebijakan Riset Daerah; Pelatihan Inovasi UMKM",
        "or_terkait": "OR Tata Kelola Pemerintahan, Ekonomi, dan Kesejahteraan Masyarakat",
        "pr_terkait": "Pusat Riset Kebijakan Publik",
        "pengelola": "Pemerintah Kota Medan",
        "status": "Beroperasi",
        "tahun_operasi": 2022,
        "luas_ha": 2.5
    },
    {
        "nama": "Kebun Raya Balangan",
        "jenis_kawasan": "Kebun Raya",
        "provinsi": "Kalimantan Selatan",
        "kabupaten_kota": "Kab. Balangan",
        "alamat": "Kecamatan Paringin Selatan, Kabupaten Balangan",
        "latitude": -2.342100,
        "longitude": 115.482300,
        "deskripsi": "Kawasan konservasi ex-situ tumbuhan dataran rendah Kalimantan.",
        "telepon": "",
        "website": "",
        "email": "",
        "saluran_digital": "IG: kebunrayabalangan\nYoutube: KebunRayaBalangan",
        "fokus_riset": "Konservasi Tumbuhan, Botani Kalimantan",
        "fasilitas": "Rumah Kaca Pembibitan; Kantor Pengelola; Herbarium Mini",
        "pemanfaatan_layanan": "Layanan Fasilitasi Penelitian; Layanan Pendidikan Lingkungan untuk siswa; Layanan praktik lapangan untuk mahasiswa",
        "koleksi_unggulan": "• Tumbuhan spontan seperti Canthium glabrum, Vitex pinnata, dan Cryptocarya ferrea telah banyak ditemukan, tetapi belum diregistrasi sebagai koleksi.\n• Kawasan juga memiliki tanaman hasil penghijauan, antara lain Aquilaria beccariana dan Cinnamomum verum.",
        "yang_bisa_ditemui": "Edukasi Konservasi Tumbuhan; Pengamatan Burung dan Satwa; Wisata Edukasi Alam",
        "or_terkait": "OR Hayati dan Lingkungan",
        "pr_terkait": "PR Konservasi Tumbuhan, Kebun Raya dan Kehutanan; PR Biosistematika dan Evolusi",
        "pengelola": "Pemerintah Kabupaten Balangan",
        "status": "Beroperasi",
        "tahun_operasi": 2018,
        "luas_ha": 110.0
    }
]


def generate_template(db: Session, format: str = "xlsx") -> tuple[io.BytesIO, str, str]:
    """
    Menghasilkan file template import (Excel .xlsx atau CSV) lengkap dengan baris contoh dan master data.
    """
    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        # Header
        headers = [col[1] for col in TEMPLATE_COLUMNS]
        writer.writerow(headers)
        # Sample rows
        for sample in SAMPLE_ROWS:
            row = [sample.get(col[0], "") for col in TEMPLATE_COLUMNS]
            writer.writerow(row)
        
        bytes_io = io.BytesIO(output.getvalue().encode("utf-8-sig"))
        filename = "template_import_lokasi.csv"
        media_type = "text/csv"
        return bytes_io, filename, media_type

    # Excel (.xlsx)
    wb = openpyxl.Workbook()
    
    # Sheet 1: Template
    ws = wb.active
    ws.title = "Template Lokasi"
    ws.views.sheetView[0].showGridLines = True

    # Styling Palettes
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_align = Alignment(horizontal="left", vertical="center")
    thin_border_side = Side(border_style="thin", color="CBD5E1")
    cell_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)

    # Write Headers
    for col_idx, (_, col_title, _) in enumerate(TEMPLATE_COLUMNS, 1):
        cell = ws.cell(row=1, column=col_idx, value=col_title)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = cell_border
    ws.row_dimensions[1].height = 28

    # Write Sample Rows
    sample_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    sample_font = Font(name="Calibri", size=10, italic=False, color="334155")
    
    for r_idx, sample in enumerate(SAMPLE_ROWS, 2):
        for c_idx, (field_key, _, _) in enumerate(TEMPLATE_COLUMNS, 1):
            val = sample.get(field_key, "")
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.font = sample_font
            cell.fill = sample_fill
            cell.border = cell_border
            if field_key in ["latitude", "longitude", "tahun_operasi", "luas_ha"]:
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = left_align
        ws.row_dimensions[r_idx].height = 22

    # Auto-adjust column widths
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 15)

    # Freeze header row
    ws.freeze_panes = "A2"

    # Sheet 2: Petunjuk & Referensi
    ws_ref = wb.create_sheet(title="Petunjuk & Referensi")
    ws_ref.views.sheetView[0].showGridLines = True

    guide_title = ws_ref.cell(row=1, column=1, value="PANDUAN PENGISIAN TEMPLATE IMPORT LOKASI")
    guide_title.font = Font(name="Calibri", size=13, bold=True, color="1E3A8A")
    
    instructions = [
        "1. Kolom bertanda bintang (*) pada sheet 'Template Lokasi' WAJIB diisi.",
        "2. Kolom 'Nama Lokasi' harus unik atau jelas mengidentifikasi kawasan.",
        "3. Kolom 'Jenis Kawasan' dapat diisi dengan nama kategori (misal: BRIDA, Kawasan Sains dan Teknologi (KST), Kebun Raya).",
        "4. Kolom 'Provinsi' dan 'Kabupaten / Kota' akan dicocokkan secara otomatis dengan data master wilayah Indonesia.",
        "5. Koordinat 'Latitude' & 'Longitude' menggunakan angka desimal dengan titik (.) sebagai pemisah desimal.",
        "6. Kolom 'Fokus Riset' dapat berisi lebih dari satu topik, pisahkan dengan tanda koma (,).",
        "7. Kolom 'Fasilitas & Laboratorium', 'Pemanfaatan & Layanan', 'Yang Bisa Ditemui & Dilakukan', 'Organisasi Riset Terkait (OR)', dan 'Pusat Riset Terkait (PR)' jika memiliki beberapa data, pisahkan dengan tanda titik koma (;).",
        "8. Kolom 'Saluran Komunikasi & Akses Digital' dan 'Koleksi Unggulan' diisi teks biasa (boleh multiline / baris baru).",
        "9. Baris contoh pada baris 2 & 3 boleh dihapus atau ditimpa dengan data Anda.",
    ]
    for idx, inst in enumerate(instructions, 3):
        ws_ref.cell(row=idx, column=1, value=inst).font = Font(name="Calibri", size=10)

    # Add Reference: Available Jenis Kawasan
    ref_row_start = len(instructions) + 5
    ws_ref.cell(row=ref_row_start, column=1, value="DAFTAR JENIS KAWASAN TERSEDIA").font = Font(name="Calibri", size=11, bold=True, color="1E3A8A")
    
    jk_list = db.query(KSTJenisKawasan).order_by(KSTJenisKawasan.nama).all()
    for j_idx, jk in enumerate(jk_list, ref_row_start + 1):
        ws_ref.cell(row=j_idx, column=1, value=f"- {jk.nama}").font = Font(name="Calibri", size=10)

    # Add Reference: Sample Provinsi
    prov_col_start = 4
    ws_ref.cell(row=ref_row_start, column=prov_col_start, value="CONTOH DAFTAR PROVINSI").font = Font(name="Calibri", size=11, bold=True, color="1E3A8A")
    prov_list = db.query(WilayahProvinsi).order_by(WilayahProvinsi.nama).all()
    for p_idx, prov in enumerate(prov_list[:25], ref_row_start + 1):
        ws_ref.cell(row=p_idx, column=prov_col_start, value=f"- {prov.nama}").font = Font(name="Calibri", size=10)

    ws_ref.column_dimensions["A"].width = 80
    ws_ref.column_dimensions["D"].width = 35

    bytes_io = io.BytesIO()
    wb.save(bytes_io)
    bytes_io.seek(0)
    filename = "template_import_lokasi.xlsx"
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return bytes_io, filename, media_type


def export_lokasi(db: Session, format: str = "xlsx", search: Optional[str] = None) -> tuple[io.BytesIO, str, str]:
    """
    Mengekspor seluruh data lokasi dari database ke Excel atau CSV.
    """
    query = db.query(KSTLokasi).order_by(KSTLokasi.created_at.desc())
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                KSTLokasi.nama.ilike(term),
                KSTLokasi.alamat.ilike(term),
                KSTLokasi.status.ilike(term)
            )
        )
    locations = query.all()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    # Prepare data rows
    data_rows = []
    for loc in locations:
        fokus_items = loc.tema_riset or []
        fokus_str = ", ".join(fokus_items) if isinstance(fokus_items, list) else str(fokus_items)
        # Saluran Komunikasi & Akses Digital
        sal_texts = []
        for ef in (loc.extra_fields or []):
            lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
            if "saluran" in lbl or "digital" in lbl or "komunikasi" in lbl:
                if ef.value:
                    val_s = str(ef.value)
                    val_clean = re.sub(r'<br\s*/?>|</p>', '\n', val_s, flags=re.IGNORECASE)
                    val_clean = re.sub(r'<[^>]+>', '', val_clean).strip()
                    if val_clean:
                        sal_texts.append(val_clean)
        saluran_str = "\n".join(sal_texts)

        # Fasilitas & Laboratorium
        fas_items = []
        for ef in (loc.extra_fields or []):
            lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
            if "fasilitas" in lbl or "lab" in lbl:
                if ef.value:
                    c = re.sub(r'<[^>]*>', '', str(ef.value)).strip()
                    if c and c not in fas_items:
                        fas_items.append(c)
        fas_str = "; ".join(fas_items)

        # Pemanfaatan & Layanan
        lay_items = []
        for ef in (loc.extra_fields or []):
            lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
            if "pemanfaatan" in lbl or "layanan" in lbl:
                if ef.value:
                    c = re.sub(r'<[^>]*>', '', str(ef.value)).strip()
                    if c and c not in lay_items:
                        lay_items.append(c)
        lay_str = "; ".join(lay_items)

        # Koleksi Unggulan
        kol_items = []
        for ef in (loc.extra_fields or []):
            lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
            if "koleksi" in lbl or "unggulan" in lbl:
                if ef.value:
                    val_s = str(ef.value)
                    val_clean = re.sub(r'<br\s*/?>|</p>', '\n', val_s, flags=re.IGNORECASE)
                    val_clean = re.sub(r'<[^>]+>', '', val_clean).strip()
                    if val_clean and val_clean not in kol_items:
                        kol_items.append(val_clean)
        kol_str = "\n".join(kol_items)

        # Yang Bisa Ditemui & Dilakukan
        temui_items = []
        for ef in (loc.extra_fields or []):
            lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
            if "temui" in lbl or "dilakukan" in lbl:
                if ef.value:
                    c = re.sub(r'<[^>]*>', '', str(ef.value)).strip()
                    if c and c not in temui_items:
                        temui_items.append(c)
        temui_str = "; ".join(temui_items)

        # Organisasi Riset Terkait (OR)
        or_items = []
        for ef in (loc.extra_fields or []):
            lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
            if "or-terkait" in lbl or "organisasi" in lbl:
                if ef.value:
                    c = re.sub(r'<[^>]*>', '', str(ef.value)).strip()
                    if c and c not in or_items:
                        or_items.append(c)
        or_str = "; ".join(or_items)

        # Pusat Riset Terkait (PR)
        pr_items = []
        for ef in (loc.extra_fields or []):
            lbl = (ef.field_label.slug if ef.field_label else (ef.label or "")).lower()
            if "pr-terkait" in lbl or "pusat riset" in lbl:
                if ef.value:
                    c = re.sub(r'<[^>]*>', '', str(ef.value)).strip()
                    if c and c not in pr_items:
                        pr_items.append(c)
        pr_str = "; ".join(pr_items)

        row_dict = {
            "nama": loc.nama or "",
            "jenis_kawasan": loc.jenis_kawasan.nama if loc.jenis_kawasan else "",
            "provinsi": loc.provinsi.nama if loc.provinsi else "",
            "kabupaten_kota": loc.kabupaten_kota.nama if loc.kabupaten_kota else "",
            "alamat": loc.alamat or "",
            "latitude": loc.latitude if loc.latitude is not None else "",
            "longitude": loc.longitude if loc.longitude is not None else "",
            "deskripsi": loc.deskripsi or "",
            "telepon": loc.telepon or "",
            "website": loc.website or "",
            "email": loc.email or "",
            "saluran_digital": saluran_str,
            "fokus_riset": fokus_str,
            "fasilitas": fas_str,
            "pemanfaatan_layanan": lay_str,
            "koleksi_unggulan": kol_str,
            "yang_bisa_ditemui": temui_str,
            "or_terkait": or_str,
            "pr_terkait": pr_str,
            "pengelola": loc.pengelola or "BRIN",
            "status": loc.status or "",
            "tahun_operasi": loc.tahun_operasi if loc.tahun_operasi is not None else "",
            "luas_ha": loc.luas_ha if loc.luas_ha is not None else "",
        }
        data_rows.append(row_dict)

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([col[1] for col in TEMPLATE_COLUMNS])
        for r in data_rows:
            writer.writerow([r.get(col[0], "") for col in TEMPLATE_COLUMNS])
        
        bytes_io = io.BytesIO(output.getvalue().encode("utf-8-sig"))
        filename = f"export_data_lokasi_{timestamp}.csv"
        media_type = "text/csv"
        return bytes_io, filename, media_type

    # Excel export
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data Lokasi BRIN"
    ws.views.sheetView[0].showGridLines = True

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_align = Alignment(horizontal="left", vertical="center")
    thin_border_side = Side(border_style="thin", color="E2E8F0")
    cell_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)

    # Headers
    for c_idx, (_, col_title, _) in enumerate(TEMPLATE_COLUMNS, 1):
        cell = ws.cell(row=1, column=c_idx, value=col_title)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = cell_border
    ws.row_dimensions[1].height = 28

    # Rows
    for r_idx, r_data in enumerate(data_rows, 2):
        for c_idx, (field_key, _, _) in enumerate(TEMPLATE_COLUMNS, 1):
            val = r_data.get(field_key, "")
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.font = Font(name="Calibri", size=10)
            cell.border = cell_border
            if field_key in ["latitude", "longitude", "tahun_operasi", "luas_ha"]:
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = left_align
        ws.row_dimensions[r_idx].height = 20

    # Auto-adjust column widths
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[col_letter].width = min(max(max_len + 4, 14), 60)

    ws.freeze_panes = "A2"

    bytes_io = io.BytesIO()
    wb.save(bytes_io)
    bytes_io.seek(0)
    filename = f"export_data_lokasi_{timestamp}.xlsx"
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return bytes_io, filename, media_type


def _normalize_header(header: str) -> str:
    h = str(header or "").strip().lower()
    h = re.sub(r'[^a-z0-9]+', ' ', h).strip()
    return h


def _split_items_by_semicolon_or_lines(raw_val: str) -> list[str]:
    if not raw_val:
        return []
    val_str = str(raw_val).strip()
    if ";" in val_str:
        items = []
        for segment in val_str.split(";"):
            cleaned = re.sub(r'<[^>]*>', '', segment).strip()
            if cleaned:
                items.append(cleaned)
        return items
    elif "\n" in val_str:
        items = []
        for line in val_str.splitlines():
            cleaned = re.sub(r'<[^>]*>', '', line).strip()
            if cleaned:
                items.append(cleaned)
        return items
    else:
        cleaned = re.sub(r'<[^>]*>', '', val_str).strip()
        return [cleaned] if cleaned else []


def import_lokasi(
    db: Session,
    file_bytes: bytes,
    filename: str,
    mode: str = "create_or_update"
) -> dict:
    """
    Mengimpor data lokasi dari file Excel (.xlsx / .xls) atau CSV.
    """
    is_csv = filename.lower().endswith(".csv")
    raw_rows = []

    if is_csv:
        try:
            content = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            content = file_bytes.decode("latin-1")
        reader = csv.reader(io.StringIO(content))
        for row in reader:
            if any(str(c).strip() for c in row):
                raw_rows.append(row)
    else:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        ws = wb["Template Lokasi"] if "Template Lokasi" in wb.sheetnames else wb.active
        for row in ws.iter_rows(values_only=True):
            if any(c is not None and str(c).strip() for c in row):
                raw_rows.append([c if c is not None else "" for c in row])

    if not raw_rows or len(raw_rows) < 2:
        return {
            "success": False,
            "message": "File kosong atau tidak memiliki baris data setelah header.",
            "total_rows": 0,
            "imported": 0,
            "updated": 0,
            "skipped": 0,
            "errors": ["File tidak memuat baris data yang valid."]
        }

    headers = [_normalize_header(c) for c in raw_rows[0]]
    
    col_map: Dict[str, int] = {}
    
    aliases = {
        "nama": ["nama lokasi", "nama kawasan", "nama kst", "nama"],
        "jenis_kawasan": ["jenis kawasan", "kategori", "jenis", "tipe kawasan", "instansi"],
        "provinsi": ["provinsi", "nama provinsi", "prov"],
        "kabupaten_kota": ["kabupaten kota", "kabupaten", "kota", "kab kota", "kabupaten atau kota"],
        "alamat": ["alamat lengkap", "alamat kantor", "alamat", "domisili"],
        "latitude": ["latitude", "lat", "lintang", "garis lintang"],
        "longitude": ["longitude", "lon", "lng", "bujur", "garis bujur"],
        "deskripsi": ["deskripsi", "deskripsi profil", "keterangan", "profil"],
        "telepon": ["nomor telepon", "telepon", "telp", "no telp", "no telepon", "phone"],
        "website": ["website resmi", "website", "web", "url", "situs"],
        "email": ["email resmi", "email", "surel"],
        "saluran_digital": ["saluran komunikasi & akses digital", "saluran komunikasi dan akses digital", "saluran komunikasi", "saluran digital", "saluran", "kontak & media sosial", "akses digital", "media sosial"],
        "fokus_riset": ["fokus riset", "fokus", "tema riset", "topik riset", "bidang riset"],
        "fasilitas": ["fasilitas & laboratorium", "fasilitas", "laboratorium", "fasilitas dan laboratorium", "lab", "sarana & prasarana", "sarana", "daftar fasilitas"],
        "pemanfaatan_layanan": ["pemanfaatan & layanan", "pemanfaatan dan layanan", "pemanfaatan", "layanan", "layanan kawasan", "daftar layanan"],
        "koleksi_unggulan": ["koleksi unggulan", "koleksi", "koleksi tanaman", "flora unggulan", "koleksi tumbuhan", "koleksi flora"],
        "yang_bisa_ditemui": [
            "yang bisa ditemui dilakukan",
            "yang bisa ditemui dan dilakukan",
            "yang bisa di temui dan dilakukan",
            "yang bisa di temui dilakukan",
            "yang bisa ditemui",
            "yang bisa di temui",
            "ditemui dilakukan",
            "ditemui dan dilakukan",
            "aktivitas kawasan",
            "kegiatan kawasan"
        ],
        "or_terkait": [
            "organisasi riset terkait or",
            "organisasi riset terkait",
            "organisasi terkait",
            "or terkait",
            "or brin terkait",
            "organisasi riset"
        ],
        "pr_terkait": [
            "pusat riset terkait pr",
            "pusat riset terkait",
            "pusat riset",
            "pr terkait",
            "pusat riset brin terkait"
        ],
        "pengelola": ["pengelola", "institusi", "badan pengelola"],
        "status": ["status", "status operasional"],
        "tahun_operasi": ["tahun operasi", "tahun operasional", "tahun"],
        "luas_ha": ["luas kawasan ha", "luas kawasan", "luas ha", "luas"],
    }

    # Pass 1: Exact matches
    for standard_key, alias_list in aliases.items():
        if standard_key in col_map:
            continue
        for idx, h in enumerate(headers):
            if idx in col_map.values():
                continue
            if h in alias_list:
                col_map[standard_key] = idx
                break

    # Pass 2: Partial matches for unmapped columns
    for standard_key, alias_list in aliases.items():
        if standard_key in col_map:
            continue
        for idx, h in enumerate(headers):
            if idx in col_map.values():
                continue
            if any(a in h for a in alias_list):
                col_map[standard_key] = idx
                break

    if "nama" not in col_map:
        return {
            "success": False,
            "message": "Kolom 'Nama Lokasi' tidak ditemukan dalam file header.",
            "total_rows": len(raw_rows) - 1,
            "imported": 0,
            "updated": 0,
            "skipped": 0,
            "errors": [f"Header yang terbaca: {headers}. Diperlukan kolom 'Nama Lokasi'."]
        }

    # Pre-cache master references
    jenis_kawasan_map = {jk.nama.lower(): jk for jk in db.query(KSTJenisKawasan).all()}
    provinsi_list = db.query(WilayahProvinsi).all()
    kabupaten_list = db.query(WilayahKabupatenKota).all()

    # Pre-cache Label Data Lokasi
    saluran_label = db.query(LabelDataLokasi).filter(LabelDataLokasi.slug == 'saluran-digital').first()
    if not saluran_label:
        saluran_label = LabelDataLokasi(
            nama="Saluran Komunikasi & Akses Digital",
            slug="saluran-digital",
            icon="Globe"
        )
        db.add(saluran_label)
        db.flush()

    fokus_label = db.query(LabelDataLokasi).filter(LabelDataLokasi.slug == 'fokus-riset').first()
    if not fokus_label:
        fokus_label = LabelDataLokasi(
            nama="Fokus Riset",
            slug="fokus-riset",
            icon="Atom"
        )
        db.add(fokus_label)
        db.flush()

    fasilitas_label = db.query(LabelDataLokasi).filter((LabelDataLokasi.slug == 'fasilitas') | (LabelDataLokasi.nama.ilike('%fasilitas%'))).first()
    if not fasilitas_label:
        fasilitas_label = LabelDataLokasi(
            nama="Fasilitas & Laboratorium",
            slug="fasilitas",
            icon="Compass"
        )
        db.add(fasilitas_label)
        db.flush()

    layanan_label = db.query(LabelDataLokasi).filter((LabelDataLokasi.slug == 'pemanfaatan-layanan') | (LabelDataLokasi.nama.ilike('%pemanfaatan%'))).first()
    if not layanan_label:
        layanan_label = LabelDataLokasi(
            nama="Pemanfaatan & Layanan",
            slug="pemanfaatan-layanan",
            icon="Briefcase"
        )
        db.add(layanan_label)
        db.flush()

    koleksi_label = db.query(LabelDataLokasi).filter((LabelDataLokasi.slug == 'koleksi-unggulan') | (LabelDataLokasi.nama.ilike('%koleksi%'))).first()
    if not koleksi_label:
        koleksi_label = LabelDataLokasi(
            nama="Koleksi Unggulan",
            slug="koleksi-unggulan",
            icon="TreePine"
        )
        db.add(koleksi_label)
        db.flush()

    temui_label = db.query(LabelDataLokasi).filter((LabelDataLokasi.slug == 'yang-bisa-ditemui') | (LabelDataLokasi.nama.ilike('%ditemui%'))).first()
    if not temui_label:
        temui_label = LabelDataLokasi(
            nama="Yang Bisa Ditemui & Dilakukan",
            slug="yang-bisa-ditemui",
            icon="Sparkles"
        )
        db.add(temui_label)
        db.flush()

    or_label = db.query(LabelDataLokasi).filter((LabelDataLokasi.slug == 'or-terkait') | (LabelDataLokasi.nama.ilike('%organisasi%'))).first()
    if not or_label:
        or_label = LabelDataLokasi(
            nama="Organisasi Riset Terkait (OR)",
            slug="or-terkait",
            icon="Building2"
        )
        db.add(or_label)
        db.flush()

    pr_label = db.query(LabelDataLokasi).filter((LabelDataLokasi.slug == 'pr-terkait') | (LabelDataLokasi.nama.ilike('%pusat riset%'))).first()
    if not pr_label:
        pr_label = LabelDataLokasi(
            nama="Pusat Riset Terkait (PR)",
            slug="pr-terkait",
            icon="Atom"
        )
        db.add(pr_label)
        db.flush()

    # Dynamic mapping for other unmapped columns that match LabelDataLokasi
    all_db_labels = db.query(LabelDataLokasi).all()
    dynamic_label_cols = {}
    for idx, h in enumerate(headers):
        if idx in col_map.values():
            continue
        for lbl in all_db_labels:
            if lbl.slug in [
                "saluran-digital", "fokus-riset", "fasilitas",
                "pemanfaatan-layanan", "koleksi-unggulan",
                "yang-bisa-ditemui", "or-terkait", "pr-terkait"
            ]:
                continue
            norm_lbl = _normalize_header(lbl.nama)
            if norm_lbl == h or lbl.slug.replace("-", " ") == h:
                dynamic_label_cols[lbl.id] = idx
                break

    total_data_rows = 0
    imported_count = 0
    updated_count = 0
    skipped_count = 0
    errors = []

    for row_idx, row in enumerate(raw_rows[1:], 2):
        def get_val(key: str) -> str:
            idx = col_map.get(key)
            if idx is not None and idx < len(row):
                v = row[idx]
                return str(v).strip() if v is not None else ""
            return ""

        nama = get_val("nama")
        if not nama:
            continue

        total_data_rows += 1

        try:
            # Match Jenis Kawasan
            jk_name = get_val("jenis_kawasan")
            jk_obj = None
            if jk_name:
                jk_key = jk_name.lower()
                jk_obj = jenis_kawasan_map.get(jk_key)
                if not jk_obj:
                    for k, v in jenis_kawasan_map.items():
                        if jk_key in k or k in jk_key:
                            jk_obj = v
                            break
                if not jk_obj:
                    slug_jk = re.sub(r'[^a-z0-9]+', '-', jk_key).strip('-') or f"jk-{uuid.uuid4().hex[:6]}"
                    jk_obj = KSTJenisKawasan(nama=jk_name, slug=slug_jk)
                    db.add(jk_obj)
                    db.flush()
                    jenis_kawasan_map[jk_key] = jk_obj

            # Match Wilayah (Provinsi & Kabupaten)
            prov_input = get_val("provinsi")
            kab_input = get_val("kabupaten_kota")
            
            matched_prov = None
            matched_kab = None

            if prov_input:
                p_clean = prov_input.lower().replace("provinsi", "").replace("prov.", "").strip()
                for p in provinsi_list:
                    if p_clean == p.nama.lower() or p_clean in p.nama.lower():
                        matched_prov = p
                        break

            if kab_input:
                k_clean = kab_input.lower().replace("kabupaten", "").replace("kab.", "").replace("kota", "").strip()
                candidates = []
                for k in kabupaten_list:
                    k_name_clean = k.nama.lower().replace("kabupaten", "").replace("kab.", "").replace("kota", "").strip()
                    if k_clean == k_name_clean or k_clean in k_name_clean:
                        candidates.append(k)

                if matched_prov and candidates:
                    for c in candidates:
                        c_pk = getattr(c, "province_kode", getattr(c, "provinsi_kode", None))
                        if c_pk == matched_prov.kode:
                            matched_kab = c
                            break
                    if not matched_kab:
                        matched_kab = candidates[0]
                elif candidates:
                    matched_kab = candidates[0]
                    c_pk = getattr(matched_kab, "province_kode", getattr(matched_kab, "provinsi_kode", None))
                    if not matched_prov and c_pk:
                        matched_prov = next((p for p in provinsi_list if p.kode == c_pk), None)

            # Coordinates
            lat_str = get_val("latitude")
            lon_str = get_val("longitude")
            lat = None
            lon = None
            if lat_str:
                try:
                    lat = float(lat_str.replace(",", "."))
                except ValueError:
                    pass
            if lon_str:
                try:
                    lon = float(lon_str.replace(",", "."))
                except ValueError:
                    pass

            geom_point = _set_point_geom(lat, lon) if (lat is not None and lon is not None) else None

            # Numeric fields
            tahun_str = get_val("tahun_operasi")
            tahun_operasi = None
            if tahun_str:
                try:
                    tahun_operasi = int(float(tahun_str))
                except ValueError:
                    pass

            luas_str = get_val("luas_ha")
            luas_ha = None
            if luas_str:
                try:
                    luas_ha = float(luas_str.replace(",", "."))
                except ValueError:
                    pass

            # Check if location already exists
            existing_loc = db.query(KSTLokasi).filter(KSTLokasi.nama.ilike(nama)).first()
            if not existing_loc:
                slug_candidate = re.sub(r'[^a-z0-9]+', '-', nama.lower()).strip('-')
                existing_loc = db.query(KSTLokasi).filter(KSTLokasi.slug == slug_candidate).first()

            if existing_loc and mode == "skip_existing":
                skipped_count += 1
                continue

            target_loc = existing_loc
            is_new = target_loc is None

            if is_new:
                base_slug = re.sub(r'[^a-z0-9]+', '-', nama.lower()).strip('-') or f"lokasi-{uuid.uuid4().hex[:6]}"
                final_slug = base_slug
                cnt = 1
                while db.query(KSTLokasi).filter(KSTLokasi.slug == final_slug).first():
                    final_slug = f"{base_slug}-{cnt}"
                    cnt += 1

                target_loc = KSTLokasi(
                    nama=nama,
                    slug=final_slug,
                    jenis_kawasan_id=jk_obj.id if jk_obj else None,
                    provinsi_kode=matched_prov.kode if matched_prov else None,
                    kabupaten_kota_kode=matched_kab.kode if matched_kab else None,
                    alamat=get_val("alamat") or None,
                    latitude=lat,
                    longitude=lon,
                    geom=geom_point,
                    deskripsi=get_val("deskripsi") or None,
                    pengelola=get_val("pengelola") or "BRIN",
                    status=get_val("status") or "Beroperasi",
                    tahun_operasi=tahun_operasi,
                    luas_ha=luas_ha
                )
                db.add(target_loc)
                db.flush()
                imported_count += 1
            else:
                # Update existing location: jika kolom ada di file dan nilainya kosong, set jadi None / kosong
                if "jenis_kawasan" in col_map:
                    target_loc.jenis_kawasan_id = jk_obj.id if jk_obj else None
                if "provinsi" in col_map:
                    target_loc.provinsi_kode = matched_prov.kode if matched_prov else None
                if "kabupaten_kota" in col_map:
                    target_loc.kabupaten_kota_kode = matched_kab.kode if matched_kab else None
                if "alamat" in col_map:
                    target_loc.alamat = get_val("alamat") or None
                if "latitude" in col_map:
                    target_loc.latitude = lat
                if "longitude" in col_map:
                    target_loc.longitude = lon
                if "latitude" in col_map or "longitude" in col_map:
                    target_loc.geom = geom_point
                if "deskripsi" in col_map:
                    target_loc.deskripsi = get_val("deskripsi") or None
                if "pengelola" in col_map:
                    target_loc.pengelola = get_val("pengelola") or None
                if "status" in col_map:
                    target_loc.status = get_val("status") or None
                if "tahun_operasi" in col_map:
                    target_loc.tahun_operasi = tahun_operasi
                if "luas_ha" in col_map:
                    target_loc.luas_ha = luas_ha
                
                db.flush()
                updated_count += 1

            # Handle Saluran Komunikasi (telepon, website, email, saluran_digital)
            has_contact_col = any(c in col_map for c in ["saluran_digital", "telepon", "website", "email"])
            if has_contact_col:
                saluran_raw = get_val("saluran_digital") if "saluran_digital" in col_map else ""
                combined_saluran = ""
                if saluran_raw:
                    lines = [l.strip() for l in saluran_raw.splitlines() if l.strip()]
                    combined_saluran = "".join([f"<p>{l}</p>" if not l.startswith("<p>") else l for l in lines]) or f"<p>{saluran_raw}</p>"
                else:
                    telepon = get_val("telepon")
                    website = get_val("website")
                    email = get_val("email")
                    saluran_parts = []
                    if telepon:
                        saluran_parts.append(f"<p><b>nomor telepon </b>: {telepon}</p>")
                    if website:
                        saluran_parts.append(f"<p><b>website resmi </b> : {website}</p>")
                    if email:
                        saluran_parts.append(f"<p><b>email resmi </b> : {email}</p>")
                    if saluran_parts:
                        combined_saluran = "".join(saluran_parts)

                if combined_saluran:
                    existing_sal_records = db.query(NilaiDataLokasi).filter(
                        NilaiDataLokasi.lokasi_id == target_loc.id,
                        NilaiDataLokasi.field_label_id == saluran_label.id
                    ).all()
                    if existing_sal_records:
                        existing_sal_records[0].value = combined_saluran
                        for extra_rec in existing_sal_records[1:]:
                            db.delete(extra_rec)
                    else:
                        new_sal = NilaiDataLokasi(
                            lokasi_id=target_loc.id,
                            field_label_id=saluran_label.id,
                            value=combined_saluran
                        )
                        db.add(new_sal)
                else:
                    # User emptied all saluran columns in file! Delete saluran!
                    db.query(NilaiDataLokasi).filter(
                        NilaiDataLokasi.lokasi_id == target_loc.id,
                        NilaiDataLokasi.field_label_id == saluran_label.id
                    ).delete()

            # Handle Fokus Riset
            if "fokus_riset" in col_map:
                fokus_raw = get_val("fokus_riset")
                # Hapus fokus riset lama untuk lokasi ini
                db.query(NilaiDataLokasi).filter(
                    NilaiDataLokasi.lokasi_id == target_loc.id,
                    NilaiDataLokasi.field_label_id == fokus_label.id
                ).delete()

                if fokus_raw:
                    f_items = [f.strip() for f in fokus_raw.replace(";", ",").split(",") if f.strip()]
                    for f_name in f_items:
                        fr_obj = db.query(KSTFokusRiset).filter(KSTFokusRiset.nama.ilike(f_name)).first()
                        if not fr_obj:
                            slug_fr = re.sub(r'[^a-z0-9]+', '-', f_name.lower()).strip('-') or f"fr-{uuid.uuid4().hex[:6]}"
                            fr_obj = KSTFokusRiset(nama=f_name, slug=slug_fr)
                            db.add(fr_obj)
                            db.flush()
                        
                        db.add(NilaiDataLokasi(
                            lokasi_id=target_loc.id,
                            field_label_id=fokus_label.id,
                            value=str(fr_obj.id)
                        ))

            # Handle Fasilitas & Laboratorium (pecah bila ada ';')
            if "fasilitas" in col_map:
                fas_raw = get_val("fasilitas")
                db.query(NilaiDataLokasi).filter(
                    NilaiDataLokasi.lokasi_id == target_loc.id,
                    NilaiDataLokasi.field_label_id == fasilitas_label.id
                ).delete()

                if fas_raw:
                    f_items = _split_items_by_semicolon_or_lines(fas_raw)
                    for f_name in f_items:
                        db.add(NilaiDataLokasi(
                            lokasi_id=target_loc.id,
                            field_label_id=fasilitas_label.id,
                            value=f"<p>{f_name}</p>"
                        ))

            # Handle Pemanfaatan & Layanan (pecah bila ada ';')
            if "pemanfaatan_layanan" in col_map:
                lay_raw = get_val("pemanfaatan_layanan")
                db.query(NilaiDataLokasi).filter(
                    NilaiDataLokasi.lokasi_id == target_loc.id,
                    NilaiDataLokasi.field_label_id == layanan_label.id
                ).delete()

                if lay_raw:
                    l_items = _split_items_by_semicolon_or_lines(lay_raw)
                    for l_name in l_items:
                        db.add(NilaiDataLokasi(
                            lokasi_id=target_loc.id,
                            field_label_id=layanan_label.id,
                            value=f"<p>{l_name}</p>"
                        ))

            # Handle Koleksi Unggulan (teks biasa, tidak dipecah ';')
            if "koleksi_unggulan" in col_map:
                kol_raw = get_val("koleksi_unggulan")
                db.query(NilaiDataLokasi).filter(
                    NilaiDataLokasi.lokasi_id == target_loc.id,
                    NilaiDataLokasi.field_label_id == koleksi_label.id
                ).delete()

                if kol_raw:
                    lines = [l.strip() for l in kol_raw.splitlines() if l.strip()]
                    kol_html = "".join([f"<p>{l}</p>" if not l.startswith("<p>") else l for l in lines]) or f"<p>{kol_raw}</p>"
                    db.add(NilaiDataLokasi(
                        lokasi_id=target_loc.id,
                        field_label_id=koleksi_label.id,
                        value=kol_html
                    ))

            # Handle Yang Bisa Ditemui & Dilakukan (pecah bila ada ';')
            if "yang_bisa_ditemui" in col_map:
                temui_raw = get_val("yang_bisa_ditemui")
                db.query(NilaiDataLokasi).filter(
                    NilaiDataLokasi.lokasi_id == target_loc.id,
                    NilaiDataLokasi.field_label_id == temui_label.id
                ).delete()

                if temui_raw:
                    t_items = _split_items_by_semicolon_or_lines(temui_raw)
                    for t_name in t_items:
                        db.add(NilaiDataLokasi(
                            lokasi_id=target_loc.id,
                            field_label_id=temui_label.id,
                            value=f"<p>{t_name}</p>"
                        ))

            # Handle Organisasi Riset Terkait (OR) (pecah bila ada ';')
            if "or_terkait" in col_map:
                or_raw = get_val("or_terkait")
                db.query(NilaiDataLokasi).filter(
                    NilaiDataLokasi.lokasi_id == target_loc.id,
                    NilaiDataLokasi.field_label_id == or_label.id
                ).delete()

                if or_raw:
                    o_items = _split_items_by_semicolon_or_lines(or_raw)
                    for o_name in o_items:
                        db.add(NilaiDataLokasi(
                            lokasi_id=target_loc.id,
                            field_label_id=or_label.id,
                            value=f"<p>{o_name}</p>"
                        ))

            # Handle Pusat Riset Terkait (PR) (pecah bila ada ';')
            if "pr_terkait" in col_map:
                pr_raw = get_val("pr_terkait")
                db.query(NilaiDataLokasi).filter(
                    NilaiDataLokasi.lokasi_id == target_loc.id,
                    NilaiDataLokasi.field_label_id == pr_label.id
                ).delete()

                if pr_raw:
                    p_items = _split_items_by_semicolon_or_lines(pr_raw)
                    for p_name in p_items:
                        db.add(NilaiDataLokasi(
                            lokasi_id=target_loc.id,
                            field_label_id=pr_label.id,
                            value=f"<p>{p_name}</p>"
                        ))

            # Handle dynamic extra columns from Excel (pecah bila ada ';')
            for lbl_id, col_idx in dynamic_label_cols.items():
                if col_idx < len(row):
                    col_val = str(row[col_idx] or "").strip()
                    db.query(NilaiDataLokasi).filter(
                        NilaiDataLokasi.lokasi_id == target_loc.id,
                        NilaiDataLokasi.field_label_id == lbl_id
                    ).delete()
                    if col_val:
                        sub_items = [x.strip() for x in col_val.split(";") if x.strip()]
                        for sub_str in sub_items:
                            db.add(NilaiDataLokasi(
                                lokasi_id=target_loc.id,
                                field_label_id=lbl_id,
                                value=f"<p>{sub_str}</p>"
                            ))

        except Exception as e:
            errors.append(f"Baris {row_idx} ('{nama}'): {str(e)}")

    db.commit()

    return {
        "success": True,
        "total_rows": total_data_rows,
        "imported": imported_count,
        "updated": updated_count,
        "skipped": skipped_count,
        "errors": errors
    }
