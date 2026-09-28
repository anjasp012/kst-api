import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.db.session import engine, Base

def update_schema():
    print("[+] Memeriksa dan memperbarui schema database...")
    
    # 1. Pastikan seluruh tabel baru dibuat jika belum ada
    Base.metadata.create_all(bind=engine)

    # 2. Tambahkan kolom-kolom baru jika tabel lama sudah ada di DB
    alter_queries = [
        # users
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE;",
        # kst_lokasi
        "ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE kst_lokasi ADD COLUMN IF NOT EXISTS is_draft BOOLEAN DEFAULT FALSE;",
        # kst_galeri
        "ALTER TABLE kst_galeri ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE kst_galeri ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
    ]

    with engine.begin() as conn:
        for q in alter_queries:
            try:
                conn.execute(text(q))
            except Exception as e:
                print(f"[!] Warning on query '{q}': {e}")

    print("[OK] Schema database berhasil disinkronkan dan siap digunakan!")

if __name__ == "__main__":
    update_schema()
