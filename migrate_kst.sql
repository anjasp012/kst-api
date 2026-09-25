ALTER TABLE kst_locations ADD COLUMN IF NOT EXISTS jenis VARCHAR(50) DEFAULT 'KST' NOT NULL;
ALTER TABLE kst_locations ADD COLUMN IF NOT EXISTS telepon VARCHAR(100);
ALTER TABLE kst_locations ADD COLUMN IF NOT EXISTS website VARCHAR(255);
ALTER TABLE kst_locations ADD COLUMN IF NOT EXISTS email VARCHAR(150);
ALTER TABLE kst_locations ADD COLUMN IF NOT EXISTS alamat TEXT;

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

DROP TABLE IF EXISTS regional_partners;
