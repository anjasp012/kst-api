import os
import sys
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.db.session import SessionLocal, Base, engine
from app.models.category import KSTCategory

CATEGORIES_DATA = [
    # 1. Tema Riset (Sesuai Filter WONDERFUL BRIN)
    {"tipe": "tema_riset", "nama": "Energi & Material", "slug": "energi-material", "urutan": 1},
    {"tipe": "tema_riset", "nama": "Kesehatan", "slug": "kesehatan", "urutan": 2},
    {"tipe": "tema_riset", "nama": "Pangan & Pertanian", "slug": "pangan-pertanian", "urutan": 3},
    {"tipe": "tema_riset", "nama": "Lingkungan", "slug": "lingkungan", "urutan": 4},
    {"tipe": "tema_riset", "nama": "Teknologi Digital", "slug": "teknologi-digital", "urutan": 5},
    {"tipe": "tema_riset", "nama": "Maritim", "slug": "maritim", "urutan": 6},

    # 2. Tipe Fasilitas
    {"tipe": "tipe_fasilitas", "nama": "Laboratorium", "slug": "laboratorium", "urutan": 1},
    {"tipe": "tipe_fasilitas", "nama": "Observatorium", "slug": "observatorium", "urutan": 2},
    {"tipe": "tipe_fasilitas", "nama": "Pilot Plant", "slug": "pilot-plant", "urutan": 3},
    {"tipe": "tipe_fasilitas", "nama": "Akses Data & Koleksi", "slug": "akses-data-koleksi", "urutan": 4},

    # 3. Potensi Kolaborasi
    {"tipe": "potensi_kolaborasi", "nama": "Industri", "slug": "industri", "urutan": 1},
    {"tipe": "potensi_kolaborasi", "nama": "Akademisi", "slug": "akademisi", "urutan": 2},
    {"tipe": "potensi_kolaborasi", "nama": "Pemerintah", "slug": "pemerintah", "urutan": 3},
    {"tipe": "potensi_kolaborasi", "nama": "Komunitas", "slug": "komunitas", "urutan": 4},
]


def seed_categories_data():
    print("[+] Ensuring kst_categories table exists...")
    Base.metadata.create_all(bind=engine)

    print("[+] Seeding Master Categories (Tema Riset, Fasilitas, Kolaborasi)...")
    db = SessionLocal()
    try:
        count = 0
        for item in CATEGORIES_DATA:
            existing = db.query(KSTCategory).filter_by(tipe=item["tipe"], nama=item["nama"]).first()
            if not existing:
                cat = KSTCategory(
                    tipe=item["tipe"],
                    nama=item["nama"],
                    slug=item["slug"],
                    urutan=item["urutan"],
                    is_active=True
                )
                db.add(cat)
                count += 1
            else:
                existing.urutan = item["urutan"]
                existing.slug = item["slug"]
                existing.is_active = True
        db.commit()
        total = db.query(KSTCategory).count()
        print(f"[+] Master Categories seeded successfully! ({total} active categories in database)")
    except Exception as e:
        db.rollback()
        print(f"[-] Error seeding categories: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_categories_data()
