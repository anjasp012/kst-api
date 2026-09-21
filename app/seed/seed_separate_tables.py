import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import text
from app.db.session import SessionLocal, Base, engine
from app.models.theme import KSTThemeRiset
from app.models.facility import KSTFacility
from app.models.collaboration import KSTCollaboration

THEME_DATA = [
    {"nama": "Energi & Material", "slug": "energi-material", "urutan": 1},
    {"nama": "Kesehatan", "slug": "kesehatan", "urutan": 2},
    {"nama": "Pangan & Pertanian", "slug": "pangan-pertanian", "urutan": 3},
    {"nama": "Lingkungan", "slug": "lingkungan", "urutan": 4},
    {"nama": "Teknologi Digital", "slug": "teknologi-digital", "urutan": 5},
    {"nama": "Maritim", "slug": "maritim", "urutan": 6},
]

FACILITY_DATA = [
    {"nama": "Laboratorium", "slug": "laboratorium", "urutan": 1},
    {"nama": "Observatorium", "slug": "observatorium", "urutan": 2},
    {"nama": "Pilot Plant", "slug": "pilot-plant", "urutan": 3},
    {"nama": "Akses Data & Koleksi", "slug": "akses-data-koleksi", "urutan": 4},
]

COLLABORATION_DATA = [
    {"nama": "Industri", "slug": "industri", "urutan": 1},
    {"nama": "Akademisi", "slug": "akademisi", "urutan": 2},
    {"nama": "Pemerintah", "slug": "pemerintah", "urutan": 3},
    {"nama": "Komunitas", "slug": "komunitas", "urutan": 4},
]


def seed_separate_tables():
    print("[+] Creating tables: kst_themeriset, kst_facilities, kst_collaborations...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed / Migrate kst_themeriset
        print("[+] Seeding kst_themeriset...")
        for item in THEME_DATA:
            existing = db.query(KSTThemeRiset).filter_by(slug=item["slug"]).first()
            if not existing:
                db.add(KSTThemeRiset(
                    nama=item["nama"],
                    slug=item["slug"],
                    urutan=item["urutan"],
                    is_active=True
                ))
            else:
                existing.nama = item["nama"]
                existing.urutan = item["urutan"]
                existing.is_active = True

        # 2. Seed / Migrate kst_facilities
        print("[+] Seeding kst_facilities...")
        for item in FACILITY_DATA:
            existing = db.query(KSTFacility).filter_by(slug=item["slug"]).first()
            if not existing:
                db.add(KSTFacility(
                    nama=item["nama"],
                    slug=item["slug"],
                    urutan=item["urutan"],
                    is_active=True
                ))
            else:
                existing.nama = item["nama"]
                existing.urutan = item["urutan"]
                existing.is_active = True

        # 3. Seed / Migrate kst_collaborations
        print("[+] Seeding kst_collaborations...")
        for item in COLLABORATION_DATA:
            existing = db.query(KSTCollaboration).filter_by(slug=item["slug"]).first()
            if not existing:
                db.add(KSTCollaboration(
                    nama=item["nama"],
                    slug=item["slug"],
                    urutan=item["urutan"],
                    is_active=True
                ))
            else:
                existing.nama = item["nama"]
                existing.urutan = item["urutan"]
                existing.is_active = True

        db.commit()

        # Optional: Drop old kst_categories table to avoid confusion
        try:
            with engine.connect() as conn:
                conn.execute(text("DROP TABLE IF EXISTS kst_categories CASCADE;"))
                conn.commit()
            print("[+] Dropped old single kst_categories table successfully!")
        except Exception as e:
            print(f"[!] Note on drop table: {e}")

        themes_cnt = db.query(KSTThemeRiset).count()
        facilities_cnt = db.query(KSTFacility).count()
        collabs_cnt = db.query(KSTCollaboration).count()

        print(f"[✓] SUCCESS! Data successfully separated into individual tables:")
        print(f"    - kst_themeriset: {themes_cnt} records")
        print(f"    - kst_facilities: {facilities_cnt} records")
        print(f"    - kst_collaborations: {collabs_cnt} records")

    except Exception as e:
        db.rollback()
        print(f"[-] Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_separate_tables()
