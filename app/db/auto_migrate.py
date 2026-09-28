from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def run_auto_migration(engine):
    with engine.begin() as conn:
        try:
            # 1. Pure Indonesian table renames first (if old tables still exist)
            conn.execute(text("""
                DO $$
                BEGIN
                    -- provinces -> kst_provinsi
                    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'provinces' AND table_type = 'BASE TABLE') THEN
                        ALTER TABLE provinces RENAME TO kst_provinsi;
                    END IF;
                    -- regencies -> kst_kabupaten_kota
                    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'regencies' AND table_type = 'BASE TABLE') THEN
                        ALTER TABLE regencies RENAME TO kst_kabupaten_kota;
                    END IF;
                    -- kst_pengguna -> users (table name users as requested)
                    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'kst_pengguna' AND table_type = 'BASE TABLE') THEN
                        ALTER TABLE kst_pengguna RENAME TO users;
                    END IF;
                    -- kst_locations -> kst_lokasi
                    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'kst_locations' AND table_type = 'BASE TABLE') THEN
                        ALTER TABLE kst_locations RENAME TO kst_lokasi;
                    END IF;
                    -- kst_themeriset -> kst_tema_riset
                    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'kst_themeriset' AND table_type = 'BASE TABLE') THEN
                        ALTER TABLE kst_themeriset RENAME TO kst_tema_riset;
                    END IF;
                    -- kst_facilities -> kst_fasilitas
                    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'kst_facilities' AND table_type = 'BASE TABLE') THEN
                        ALTER TABLE kst_facilities RENAME TO kst_fasilitas;
                    END IF;
                    -- kst_collaborations -> kst_kolaborasi
                    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'kst_collaborations' AND table_type = 'BASE TABLE') THEN
                        ALTER TABLE kst_collaborations RENAME TO kst_kolaborasi;
                    END IF;

                    -- Drop legacy English views (users is a real table, not dropped)
                    DROP VIEW IF EXISTS provinces CASCADE;
                    DROP VIEW IF EXISTS regencies CASCADE;
                    DROP VIEW IF EXISTS kst_locations CASCADE;
                    DROP VIEW IF EXISTS kst_themeriset CASCADE;
                    DROP VIEW IF EXISTS kst_facilities CASCADE;
                    DROP VIEW IF EXISTS kst_collaborations CASCADE;
                END $$;
            """))

            # 2. Table kst_jenis_kawasan (Jenis Kawasan)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS kst_jenis_kawasan (
                    id UUID PRIMARY KEY,
                    nama VARCHAR(150) NOT NULL,
                    slug VARCHAR(150) NOT NULL UNIQUE,
                    deskripsi TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """))

            conn.execute(text("ALTER TABLE kst_jenis_kawasan ADD COLUMN IF NOT EXISTS deskripsi TEXT;"))
            conn.execute(text("ALTER TABLE kst_jenis_kawasan ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;"))

            # Migrate rows from kst_kawasan or kst_instansi if needed
            check_kaw = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'kst_kawasan')")).scalar()
            if check_kaw:
                conn.execute(text("""
                    INSERT INTO kst_jenis_kawasan (id, nama, slug, deskripsi, is_active, created_at, updated_at)
                    SELECT id, nama, slug, deskripsi, is_active, created_at, updated_at FROM kst_kawasan
                    ON CONFLICT (id) DO NOTHING;
                """))
            check_inst = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'kst_instansi')")).scalar()
            if check_inst:
                conn.execute(text("""
                    INSERT INTO kst_jenis_kawasan (id, nama, slug, created_at, updated_at)
                    SELECT id, nama, slug, created_at, updated_at FROM kst_instansi
                    ON CONFLICT (id) DO NOTHING;
                """))

            # Populate default descriptions in kst_jenis_kawasan if empty
            conn.execute(text("""
                UPDATE kst_jenis_kawasan SET deskripsi = 'Pusat pengembangan riset, inovasi teknologi, inkubasi bisnis, dan kolaborasi hilirisasi sains terpadu BRIN.' WHERE slug = 'kawasan-sains-kst' AND (deskripsi IS NULL OR deskripsi = '');
                UPDATE kst_jenis_kawasan SET deskripsi = 'Badan Riset dan Inovasi Daerah yang mengkoordinasikan ekosistem riset dan pemanfaatan inovasi di tingkat daerah.' WHERE slug = 'brida' AND (deskripsi IS NULL OR deskripsi = '');
                UPDATE kst_jenis_kawasan SET deskripsi = 'Badan Perencanaan Pembangunan, Riset dan Inovasi Daerah pengintegrasi kebijakan perencanaan riset daerah.' WHERE slug = 'bapperida' AND (deskripsi IS NULL OR deskripsi = '');
                UPDATE kst_jenis_kawasan SET deskripsi = 'Badan Perencanaan Pembangunan Daerah mitra perencanaan dan pemetaan kebutuhan inovasi daerah.' WHERE slug = 'bappeda' AND (deskripsi IS NULL OR deskripsi = '');
            """))

            # 3. Columns & Constraints on kst_lokasi
            check_lokasi = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'kst_lokasi')")).scalar()
            if check_lokasi:
                conn.execute(text("ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS telepon VARCHAR(100);"))
                conn.execute(text("ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS website VARCHAR(255);"))
                conn.execute(text("ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS email VARCHAR(150);"))
                conn.execute(text("ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS alamat TEXT;"))
                conn.execute(text("ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS is_draft BOOLEAN DEFAULT FALSE;"))
                conn.execute(text("ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS jenis_kawasan_id UUID;"))
                conn.execute(text("ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS kawasan_id UUID;"))

                conn.execute(text("ALTER TABLE kst_lokasi DROP COLUMN IF EXISTS jenis;"))
                conn.execute(text("ALTER TABLE kst_lokasi DROP COLUMN IF EXISTS is_active;"))
                conn.execute(text("ALTER TABLE kst_lokasi DROP COLUMN IF EXISTS galeri;"))

                conn.execute(text("""
                    DO $$
                    BEGIN
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'kst_lokasi' AND column_name = 'kawasan_id') THEN
                            UPDATE kst_lokasi SET jenis_kawasan_id = kawasan_id WHERE jenis_kawasan_id IS NULL AND kawasan_id IS NOT NULL;
                        END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'kst_lokasi' AND column_name = 'instansi_id') THEN
                            UPDATE kst_lokasi SET jenis_kawasan_id = instansi_id WHERE jenis_kawasan_id IS NULL AND instansi_id IS NOT NULL;
                            UPDATE kst_lokasi SET kawasan_id = instansi_id WHERE kawasan_id IS NULL AND instansi_id IS NOT NULL;
                        END IF;
                    END $$;
                """))

                # FK constraint for jenis_kawasan_id on kst_lokasi
                conn.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint WHERE conname = 'kst_lokasi_jenis_kawasan_id_fkey'
                        ) THEN
                            ALTER TABLE kst_lokasi ADD CONSTRAINT kst_lokasi_jenis_kawasan_id_fkey FOREIGN KEY (jenis_kawasan_id) REFERENCES kst_jenis_kawasan(id) ON DELETE SET NULL;
                        END IF;
                    END $$;
                """))

            # 4. Drop obsolete urutan columns
            for tbl in ('kst_fasilitas', 'kst_dampak', 'kst_tema_riset', 'kst_kolaborasi'):
                conn.execute(text(f"""
                    DO $$
                    BEGIN
                        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{tbl}') THEN
                            ALTER TABLE {tbl} DROP COLUMN IF EXISTS urutan;
                        END IF;
                    END $$;
                """))

            # 5. Create kst_galeri table (only tipe and url as requested)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS kst_galeri (
                    id UUID PRIMARY KEY,
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

            # 6. Ensure created_at and updated_at on all active tables
            all_tables = [
                'kst_lokasi',
                'kst_galeri',
                'kst_jenis_kawasan',
                'kst_tema_riset',
                'kst_fasilitas',
                'kst_kolaborasi',
                'kst_dampak',
                'kst_provinsi',
                'kst_kabupaten_kota',
                'users'
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
            
            # 7. Migrate regional_partners if still present
            check_partner = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'regional_partners')")).scalar()
            if check_partner:
                conn.execute(text("""
                    INSERT INTO kst_lokasi (id, nama, slug, wilayah, kota_provinsi, pengelola, status, tahun_operasi, latitude, longitude, geom, telepon, website, email, alamat, created_at, updated_at)
                    SELECT 
                        id, 
                        nama_organisasi, 
                        LOWER(REPLACE(nama_organisasi, ' ', '-')) || '-' || SUBSTRING(id::text FROM 1 FOR 4), 
                        wilayah, 
                        COALESCE(wilayah, '-'), 
                        'Mitra Daerah', 
                        'Aktif', 
                        2024, 
                        latitude, 
                        longitude, 
                        geom, 
                        telepon, 
                        website, 
                        email, 
                        alamat,
                        created_at,
                        created_at
                    FROM regional_partners
                    ON CONFLICT DO NOTHING;
                """))
                conn.execute(text("DROP TABLE IF EXISTS regional_partners;"))
                print("Successfully migrated regional_partners to kst_lokasi.")
        except Exception as e:
            logger.error(f"Migration error: {e}")
            print(f"Migration error: {e}")
