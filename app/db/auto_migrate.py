from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def run_auto_migration(engine):
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE kst_locations ADD COLUMN IF NOT EXISTS jenis VARCHAR(50) DEFAULT 'KST' NOT NULL;"))
            conn.execute(text("ALTER TABLE kst_locations ADD COLUMN IF NOT EXISTS telepon VARCHAR(100);"))
            conn.execute(text("ALTER TABLE kst_locations ADD COLUMN IF NOT EXISTS website VARCHAR(255);"))
            conn.execute(text("ALTER TABLE kst_locations ADD COLUMN IF NOT EXISTS email VARCHAR(150);"))
            conn.execute(text("ALTER TABLE kst_locations ADD COLUMN IF NOT EXISTS alamat TEXT;"))
            
            check_partner = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'regional_partners')")).scalar()
            if check_partner:
                conn.execute(text("""
                    INSERT INTO kst_locations (id, nama, slug, wilayah, kota_provinsi, pengelola, status, tahun_operasi, latitude, longitude, geom, jenis, telepon, website, email, alamat, created_at, updated_at)
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
                        jenis, 
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
                print("Successfully migrated regional_partners to kst_locations.")
        except Exception as e:
            print(f"Migration error: {e}")
