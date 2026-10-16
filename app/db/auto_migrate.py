import os
import json
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


def run_auto_migration(engine):
    """
    Menjalankan migrasi otomatis dan inisialisasi skema database KST BRIN.
    Idempoten dan aman dijalankan berulang kali saat startup FastAPI maupun deployment VPS baru.
    """
    logger.info("Memulai sinkronisasi dan migrasi skema database...")

    with engine.begin() as conn:
        try:
            # 1. Pastikan ekstensi PostgreSQL yang dibutuhkan aktif
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))

            # 2. Rename & bersihkan tabel/view lama secara aman
            rename_pairs = [
                ('provinces', 'kst_provinsi'),
                ('regencies', 'kst_kabupaten_kota'),
                ('kst_pengguna', 'users'),
                ('kst_locations', 'kst_lokasi'),
                ('kst_themeriset', 'kst_fokus_riset'),
                ('field_label_location', 'label_data_lokasi'),
                ('field_value_location', 'nilai_data_lokasi'),
            ]
            for old_t, new_t in rename_pairs:
                exists_old = conn.execute(text(
                    "SELECT 1 FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = :t AND table_type = 'BASE TABLE'"
                ), {"t": old_t}).scalar()
                if exists_old:
                    exists_new = conn.execute(text(
                        "SELECT 1 FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = :t AND table_type = 'BASE TABLE'"
                    ), {"t": new_t}).scalar()
                    if not exists_new:
                        conn.execute(text(f'ALTER TABLE "{old_t}" RENAME TO "{new_t}";'))
                    else:
                        conn.execute(text(f'DROP TABLE IF EXISTS "{old_t}" CASCADE;'))

            # Bersihkan tabel & view lama yang sudah tidak digunakan secara dinamis
            obsolete_objects = [
                'provinces', 'regencies', 'kst_locations', 'kst_themeriset',
                'kst_facilities', 'kst_collaborations', 'kst_tema_riset',
                'kst_dampak', 'kst_fasilitas', 'kst_kolaborasi', 'regional_partners'
            ]
            for obj_name in obsolete_objects:
                relkind = conn.execute(text("""
                    SELECT c.relkind 
                    FROM pg_class c 
                    JOIN pg_namespace n ON n.oid = c.relnamespace 
                    WHERE n.nspname = ANY(current_schemas(false)) AND c.relname = :t
                """), {"t": obj_name}).scalar()
                if relkind == 'v':
                    conn.execute(text(f'DROP VIEW IF EXISTS "{obj_name}" CASCADE;'))
                elif relkind == 'm':
                    conn.execute(text(f'DROP MATERIALIZED VIEW IF EXISTS "{obj_name}" CASCADE;'))
                elif relkind in ('r', 'p', 'f'):
                    conn.execute(text(f'DROP TABLE IF EXISTS "{obj_name}" CASCADE;'))

            # 3. Tabel users (Admin CMS)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE,
                    hashed_password VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255) DEFAULT 'Admin' NOT NULL,
                    role VARCHAR(50) DEFAULT 'admin' NOT NULL,
                    is_active INTEGER DEFAULT 1 NOT NULL,
                    last_login_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """))

            # Inisialisasi admin default jika tabel users masih kosong
            user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
            if user_count == 0:
                from app.core.security import get_password_hash
                admin_pw = get_password_hash("admin123")
                conn.execute(text("""
                    INSERT INTO users (id, username, email, hashed_password, full_name, role, is_active, created_at, updated_at)
                    VALUES (gen_random_uuid(), 'admin', 'admin@brin.go.id', :pw, 'Administrator KST BRIN', 'superadmin', 1, NOW(), NOW())
                    ON CONFLICT (username) DO NOTHING;
                """), {"pw": admin_pw})
                logger.info("Admin default berhasil dibuat: admin / admin123")

            # 4. Tabel Wilayah (kst_provinsi & kst_kabupaten_kota)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS kst_provinsi (
                    kode VARCHAR(10) PRIMARY KEY,
                    nama VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS kst_kabupaten_kota (
                    kode VARCHAR(10) PRIMARY KEY,
                    province_kode VARCHAR(10) REFERENCES kst_provinsi(kode) ON DELETE CASCADE,
                    nama VARCHAR(150) NOT NULL,
                    tipe VARCHAR(20) DEFAULT 'Kabupaten',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_kst_kabupaten_kota_province_kode ON kst_kabupaten_kota(province_kode);
            """))

            # Auto-seed Wilayah dari bundle JSON lokal jika tabel kst_provinsi masih kosong
            prov_count = conn.execute(text("SELECT COUNT(*) FROM kst_provinsi")).scalar() or 0
            if prov_count == 0:
                json_path = os.path.join(os.path.dirname(__file__), "..", "seed", "wilayah_data.json")
                if os.path.exists(json_path):
                    with open(json_path, "r", encoding="utf-8") as f:
                        w_data = json.load(f)
                    for p in w_data.get("provinces", []):
                        conn.execute(text("""
                            INSERT INTO kst_provinsi (kode, nama, created_at, updated_at)
                            VALUES (:kode, :nama, NOW(), NOW())
                            ON CONFLICT (kode) DO UPDATE SET nama = EXCLUDED.nama;
                        """), {"kode": p["kode"], "nama": p["nama"]})
                    for r in w_data.get("regencies", []):
                        conn.execute(text("""
                            INSERT INTO kst_kabupaten_kota (kode, province_kode, nama, tipe, created_at, updated_at)
                            VALUES (:kode, :province_kode, :nama, :tipe, NOW(), NOW())
                            ON CONFLICT (kode) DO UPDATE SET nama = EXCLUDED.nama, tipe = EXCLUDED.tipe, province_kode = EXCLUDED.province_kode;
                        """), {
                            "kode": r["kode"],
                            "province_kode": r["province_kode"],
                            "nama": r["nama"],
                            "tipe": r.get("tipe", "Kabupaten"),
                        })
                    logger.info("38 Provinsi & 514 Kab/Kota berhasil diinisialisasi dari wilayah_data.json.")

            # 5. Tabel kst_jenis_kawasan (Hierarki Kawasan / BRIDA / Kebun Raya)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS kst_jenis_kawasan (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    parent_id UUID REFERENCES kst_jenis_kawasan(id) ON DELETE SET NULL,
                    nama VARCHAR(150) NOT NULL,
                    slug VARCHAR(150) NOT NULL UNIQUE,
                    deskripsi TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                ALTER TABLE kst_jenis_kawasan ADD COLUMN IF NOT EXISTS parent_id UUID REFERENCES kst_jenis_kawasan(id) ON DELETE SET NULL;
                ALTER TABLE kst_jenis_kawasan ADD COLUMN IF NOT EXISTS deskripsi TEXT;
                ALTER TABLE kst_jenis_kawasan ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
            """))

            # Seed 3 Kategori Utama
            conn.execute(text("""
                INSERT INTO kst_jenis_kawasan (id, nama, slug, deskripsi, parent_id, is_active, created_at, updated_at)
                VALUES 
                    (gen_random_uuid(), 'Kawasan', 'kawasan', 'Pilar Induk Kawasan Riset & Inovasi', NULL, TRUE, NOW(), NOW()),
                    (gen_random_uuid(), 'BRIDA', 'brida', 'Riset & Inovasi Daerah', NULL, TRUE, NOW(), NOW()),
                    (gen_random_uuid(), 'Kebun Raya', 'kebun-raya', 'Botani & Konservasi Ex-situ', NULL, TRUE, NOW(), NOW())
                ON CONFLICT (slug) DO UPDATE SET deskripsi = EXCLUDED.deskripsi;
            """))

            # Seed Sub-Kategori di bawah Induk 'Kawasan'
            kawasan_id = conn.execute(text("SELECT id FROM kst_jenis_kawasan WHERE slug = 'kawasan'")).scalar()
            if kawasan_id:
                sub_items = [
                    ('Kawasan Sains dan Teknologi', 'kawasan-sains-dan-teknologi', 'KST terpadu hilirisasi riset & kemitraan industri'),
                    ('Kawasan Sains (KS)', 'kawasan-sains-ks', 'Pusat riset sains dasar dan aplikasi laboratorium'),
                    ('Kawasan Sains, Teknologi, dan Edukasi', 'kawasan-sains-teknologi-edukasi', 'Pusat riset dan edukasi publik'),
                    ('Kawasan Konservasi Ilmiah', 'kawasan-konservasi-ilmiah', 'Konservasi ilmiah dan riset lingkungan'),
                    ('Kawasan Stasiun Lapangan', 'kawasan-stasiun-lapangan', 'Stasiun observasi dan penelitian lapangan'),
                    ('Kawasan Kerja Bersama', 'kawasan-kerja-bersama', 'Co-working space dan kolaborasi peneliti'),
                    ('Kawasan Administrasi', 'kawasan-administrasi', 'Layanan administrasi dan pendukung kawasan'),
                ]
                for ch_nama, ch_slug, ch_desk in sub_items:
                    conn.execute(text("""
                        INSERT INTO kst_jenis_kawasan (id, nama, slug, deskripsi, parent_id, is_active, created_at, updated_at)
                        VALUES (gen_random_uuid(), :nama, :slug, :deskripsi, :parent_id, TRUE, NOW(), NOW())
                        ON CONFLICT (slug) DO UPDATE SET parent_id = EXCLUDED.parent_id, deskripsi = EXCLUDED.deskripsi;
                    """), {"nama": ch_nama, "slug": ch_slug, "deskripsi": ch_desk, "parent_id": kawasan_id})

            # 6. Tabel kst_fokus_riset (Master Fokus Riset)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS kst_fokus_riset (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    nama VARCHAR(150) NOT NULL UNIQUE,
                    slug VARCHAR(150) NOT NULL UNIQUE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                ALTER TABLE kst_fokus_riset DROP COLUMN IF EXISTS deskripsi CASCADE;

                INSERT INTO kst_fokus_riset (id, nama, slug, is_active, created_at, updated_at)
                VALUES 
                    (gen_random_uuid(), 'Energi & Material', 'energi-material', TRUE, NOW(), NOW()),
                    (gen_random_uuid(), 'Kesehatan & Obat', 'kesehatan-obat', TRUE, NOW(), NOW()),
                    (gen_random_uuid(), 'Pangan & Pertanian', 'pangan-pertanian', TRUE, NOW(), NOW()),
                    (gen_random_uuid(), 'Teknologi Digital & Robotika', 'teknologi-digital', TRUE, NOW(), NOW()),
                    (gen_random_uuid(), 'Kemaritiman & Kelautan', 'maritim', TRUE, NOW(), NOW()),
                    (gen_random_uuid(), 'Lingkungan & Kebencanaan', 'lingkungan-kebencanaan', TRUE, NOW(), NOW())
                ON CONFLICT (slug) DO NOTHING;
            """))

            # 7. Tabel label_data_lokasi & nilai_data_lokasi (Sistem Tab Dinamis)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS label_data_lokasi (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    nama VARCHAR(150) NOT NULL UNIQUE,
                    slug VARCHAR(150) NOT NULL UNIQUE,
                    placeholder VARCHAR(255),
                    icon VARCHAR(50) DEFAULT 'FileText',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                ALTER TABLE IF EXISTS label_data_lokasi DROP COLUMN IF EXISTS tipe CASCADE;
                ALTER TABLE IF EXISTS label_data_lokasi DROP COLUMN IF EXISTS kategori CASCADE;
                ALTER TABLE IF EXISTS label_data_lokasi DROP COLUMN IF EXISTS urutan CASCADE;
                ALTER TABLE IF EXISTS label_data_lokasi DROP COLUMN IF EXISTS is_active CASCADE;

                DELETE FROM label_data_lokasi WHERE slug IN ('website', 'nomor-telepon', 'email') OR nama IN ('Website Resmi', 'Nomor Telepon', 'Email Resmi');

                INSERT INTO label_data_lokasi (nama, slug, placeholder, icon)
                VALUES 
                    ('Fokus Riset', 'fokus-riset', 'Bidang keilmuan atau fokus riset', 'Atom'),
                    ('Fasilitas & Laboratorium', 'fasilitas', 'Laboratorium dan sarana pendukung', 'Compass'),
                    ('Pemanfaatan & Layanan', 'pemanfaatan-layanan', 'Layanan pengujian, sertifikasi, kemitraan', 'Handshake'),
                    ('Saluran Komunikasi & Akses Digital', 'saluran-digital', 'Website, email, telepon, media sosial, atau kanal resmi...', 'Globe'),
                    ('Koleksi Unggulan', 'koleksi-unggulan', 'Daftar tanaman / spesimen unggulan', 'TreePine'),
                    ('Yang Bisa Ditemui & Dilakukan', 'yang-bisa-ditemui', 'Aktivitas eduwisata dan observasi', 'Sparkles'),
                    ('Tata Kelola & Legalitas', 'tata-kelola', 'UPTD / Pengelola / Kewenangan', 'ShieldCheck'),
                    ('Pendamping / PIC', 'pendamping-pic', 'Nama pejabat atau tim pendamping', 'Users'),
                    ('Organisasi Riset Terkait (OR)', 'or-terkait', 'Daftar OR BRIN', 'Building2'),
                    ('Pusat Riset Terkait (PR)', 'pr-terkait', 'Daftar PR BRIN', 'FlaskConical'),
                    ('Program Inovasi Daerah', 'program-inovasi', 'Inkubasi dan program inovasi daerah', 'Award'),
                    ('Sumber & Catatan Tambahan', 'catatan', 'Catatan informasi atau sumber referensi', 'FileText')
                ON CONFLICT (slug) DO NOTHING;
            """))

            # 8. Tabel kst_lokasi (Data Peta & Profil Lokasi Kawasan)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS kst_lokasi (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    nama VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) UNIQUE,
                    jenis_kawasan_id UUID REFERENCES kst_jenis_kawasan(id) ON DELETE SET NULL,
                    provinsi_kode VARCHAR(10) REFERENCES kst_provinsi(kode) ON DELETE SET NULL,
                    kabupaten_kota_kode VARCHAR(10) REFERENCES kst_kabupaten_kota(kode) ON DELETE SET NULL,
                    pengelola VARCHAR(150) DEFAULT 'BRIN',
                    status VARCHAR(50) DEFAULT 'Aktif',
                    tahun_operasi INTEGER,
                    luas_ha DOUBLE PRECISION,
                    alamat TEXT,
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    geom Geometry(POINT, 4326),
                    deskripsi TEXT,
                    is_draft BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS alamat TEXT;
                ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS luas_ha DOUBLE PRECISION;
                ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS is_draft BOOLEAN DEFAULT FALSE;
                ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS jenis_kawasan_id UUID;
                ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS tahun_operasi INTEGER;
                ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS deskripsi TEXT;
                ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS provinsi_kode VARCHAR(10);
                ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS kabupaten_kota_kode VARCHAR(10);
                ALTER TABLE kst_lokasi ALTER COLUMN pengelola DROP NOT NULL;
                ALTER TABLE kst_lokasi ALTER COLUMN pengelola SET DEFAULT 'BRIN';
                ALTER TABLE kst_lokasi ALTER COLUMN slug DROP NOT NULL;
            """))

            # Drop obsolete columns
            obsolete_cols = [
                'kawasan_id', 'instansi_id', 'peran_kawasan', 'fasilitas', 'riset',
                'dampak', 'potensi_kolaborasi', 'daftar_kolaborasi', 'tata_kelola',
                'info_profil', 'info_ekosistem', 'info_utama', 'jenis', 'is_active',
                'galeri', 'thumbnail_url', 'telepon', 'website', 'email', 'wilayah',
                'kota_provinsi', 'deskripsi_profil'
            ]
            for col in obsolete_cols:
                conn.execute(text(f"ALTER TABLE kst_lokasi DROP COLUMN IF EXISTS {col} CASCADE;"))

            # Pastikan Foreign Keys pada kst_lokasi
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'kst_lokasi_jenis_kawasan_id_fkey') THEN
                        ALTER TABLE kst_lokasi ADD CONSTRAINT kst_lokasi_jenis_kawasan_id_fkey FOREIGN KEY (jenis_kawasan_id) REFERENCES kst_jenis_kawasan(id) ON DELETE SET NULL;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'kst_lokasi_provinsi_kode_fkey') THEN
                        ALTER TABLE kst_lokasi ADD CONSTRAINT kst_lokasi_provinsi_kode_fkey FOREIGN KEY (provinsi_kode) REFERENCES kst_provinsi(kode) ON DELETE SET NULL;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'kst_lokasi_kabupaten_kota_kode_fkey') THEN
                        ALTER TABLE kst_lokasi ADD CONSTRAINT kst_lokasi_kabupaten_kota_kode_fkey FOREIGN KEY (kabupaten_kota_kode) REFERENCES kst_kabupaten_kota(kode) ON DELETE SET NULL;
                    END IF;
                END $$;
            """))

            # 9. Tabel kst_galeri
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS kst_galeri (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    lokasi_id UUID NOT NULL REFERENCES kst_lokasi(id) ON DELETE CASCADE,
                    tipe VARCHAR(20) NOT NULL DEFAULT 'foto',
                    url TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_kst_galeri_lokasi_id ON kst_galeri(lokasi_id);
                ALTER TABLE kst_galeri DROP COLUMN IF EXISTS judul;
                ALTER TABLE kst_galeri DROP COLUMN IF EXISTS thumbnail_url;
                ALTER TABLE kst_galeri DROP COLUMN IF EXISTS keterangan;
                ALTER TABLE kst_galeri DROP COLUMN IF EXISTS urutan;
            """))

            # 10. Tabel nilai_data_lokasi
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS nilai_data_lokasi (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    lokasi_id UUID NOT NULL REFERENCES kst_lokasi(id) ON DELETE CASCADE,
                    field_label_id UUID NOT NULL REFERENCES label_data_lokasi(id) ON DELETE CASCADE,
                    value TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_nilai_data_lokasi_lokasi_id ON nilai_data_lokasi(lokasi_id);
                CREATE INDEX IF NOT EXISTS idx_nilai_data_lokasi_field_label_id ON nilai_data_lokasi(field_label_id);
                ALTER TABLE IF EXISTS nilai_data_lokasi DROP COLUMN IF EXISTS tipe CASCADE;
                ALTER TABLE IF EXISTS nilai_data_lokasi DROP COLUMN IF EXISTS urutan CASCADE;
                ALTER TABLE IF EXISTS nilai_data_lokasi DROP COLUMN IF EXISTS label CASCADE;
            """))

            # 11. Tabel kst_quick_filter (Preset Quick Filter untuk Admin & API Publik)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS kst_quick_filter (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    nama VARCHAR(150) NOT NULL,
                    slug VARCHAR(150) NOT NULL UNIQUE,
                    filter_data JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_kst_quick_filter_slug ON kst_quick_filter(slug);

                -- Bersihkan kolom yang tidak diperlukan agar simpel
                ALTER TABLE IF EXISTS kst_quick_filter DROP COLUMN IF EXISTS deskripsi CASCADE;
                ALTER TABLE IF EXISTS kst_quick_filter DROP COLUMN IF EXISTS icon CASCADE;
                ALTER TABLE IF EXISTS kst_quick_filter DROP COLUMN IF EXISTS warna CASCADE;
                ALTER TABLE IF EXISTS kst_quick_filter DROP COLUMN IF EXISTS urutan CASCADE;
                ALTER TABLE IF EXISTS kst_quick_filter DROP COLUMN IF EXISTS is_active CASCADE;
            """))

            qf_count = conn.execute(text("SELECT COUNT(*) FROM kst_quick_filter")).scalar() or 0
            if qf_count == 0:
                conn.execute(text("""
                    INSERT INTO kst_quick_filter (id, nama, slug, filter_data, created_at, updated_at)
                    VALUES 
                        (gen_random_uuid(), 'KST Terpadu di Jawa', 'kst-jawa', '{"wilayah": ["Jawa"], "jenis_kawasan": ["kawasan-sains-dan-teknologi"], "fokus_riset": [], "search_input": ""}'::jsonb, NOW(), NOW()),
                        (gen_random_uuid(), 'Ekosistem BRIDA Seluruh Indonesia', 'brida-indonesia', '{"wilayah": [], "jenis_kawasan": ["brida"], "fokus_riset": [], "search_input": ""}'::jsonb, NOW(), NOW()),
                        (gen_random_uuid(), 'Kebun Raya & Konservasi Ilmiah', 'kebun-raya-konservasi', '{"wilayah": [], "jenis_kawasan": ["kebun-raya", "kawasan-konservasi-ilmiah"], "fokus_riset": [], "search_input": ""}'::jsonb, NOW(), NOW()),
                        (gen_random_uuid(), 'Riset Pangan & Pertanian', 'riset-pangan-pertanian', '{"wilayah": [], "jenis_kawasan": [], "fokus_riset": ["pangan-pertanian"], "search_input": ""}'::jsonb, NOW(), NOW())
                    ON CONFLICT (slug) DO NOTHING;
                """))
                logger.info("Seed data kst_quick_filter berhasil diinisialisasi.")

            # 12. Pastikan created_at & updated_at ada di semua tabel aktif
            all_tables = [
                'kst_lokasi', 'kst_galeri', 'kst_jenis_kawasan',
                'label_data_lokasi', 'nilai_data_lokasi', 'kst_provinsi',
                'kst_kabupaten_kota', 'kst_quick_filter', 'users'
            ]
            for tbl in all_tables:
                conn.execute(text(f"""
                    DO $$
                    BEGIN
                        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{tbl}' AND table_type = 'BASE TABLE') THEN
                            ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                            ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                        END IF;
                    END $$;
                """))

            logger.info("Migrasi skema database berhasil diselesaikan.")
            print("Auto-migration completed successfully.")

        except Exception as e:
            logger.error(f"Migration error: {e}")
            print(f"Migration error: {e}")
            raise
