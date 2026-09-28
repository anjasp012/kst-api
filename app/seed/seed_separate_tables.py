import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import text
from app.db.session import SessionLocal, Base, engine
from app.models.jenis_kawasan import KSTJenisKawasan
from app.models.kawasan import KSTKawasan
from app.models.instansi import KSTInstansi
from app.models.theme import KSTThemeRiset
from app.models.facility import KSTFacility
from app.models.collaboration import KSTCollaboration


JENIS_KAWASAN_DATA = [
    {"nama": "Kawasan Sains (KST)", "slug": "kawasan-sains-kst", "deskripsi": "Pusat pengembangan riset, inovasi teknologi, inkubasi bisnis, dan kolaborasi hilirisasi sains terpadu BRIN."},
    {"nama": "BRIDA", "slug": "brida", "deskripsi": "Badan Riset dan Inovasi Daerah yang mengkoordinasikan ekosistem riset dan pemanfaatan inovasi di tingkat daerah."},
    {"nama": "BAPPERIDA", "slug": "bapperida", "deskripsi": "Badan Perencanaan Pembangunan, Riset dan Inovasi Daerah pengintegrasi kebijakan perencanaan riset daerah."},
    {"nama": "BAPPEDA", "slug": "bappeda", "deskripsi": "Badan Perencanaan Pembangunan Daerah mitra perencanaan dan pemetaan kebutuhan inovasi daerah."},
]
KAWASAN_DATA = JENIS_KAWASAN_DATA
INSTANSI_DATA = JENIS_KAWASAN_DATA

THEME_DATA = [
    {"nama": "Energi & Material", "slug": "energi-material", "deskripsi": "Fokus pada material maju, energi baru terbarukan, dan efisiensi energi nasional."},
    {"nama": "Kesehatan", "slug": "kesehatan", "deskripsi": "Pengembangan riset obat, vaksin, diagnostik, dan teknologi kedokteran terpadu."},
    {"nama": "Pangan & Pertanian", "slug": "pangan-pertanian", "deskripsi": "Inovasi benih unggul, teknologi pascapanen, dan penguatan ketahanan pangan."},
    {"nama": "Lingkungan", "slug": "lingkungan", "deskripsi": "Konservasi keanekaragaman hayati, mitigasi perubahan iklim, dan pengelolaan ekosistem."},
    {"nama": "Teknologi Digital", "slug": "teknologi-digital", "deskripsi": "Kecerdasan buatan, data raya, komputasi kinerja tinggi, dan keamanan siber."},
    {"nama": "Maritim", "slug": "maritim", "deskripsi": "Riset oseanografi, bioteknologi kelautan, logistik maritim, dan keselamatan perairan."},
]

FACILITY_DATA = [
    {"nama": "Laboratorium", "slug": "laboratorium", "deskripsi": "Fasilitas instrumentasi analitik, pengujian presisi, dan riset saintifik terakreditasi."},
    {"nama": "Observatorium", "slug": "observatorium", "deskripsi": "Stasiun pengamatan fenomena atmosfer, antariksa, kebencanaan, dan geofisika."},
    {"nama": "Pilot Plant", "slug": "pilot-plant", "deskripsi": "Fasilitas uji coba skala percontohan sebelum proses produksi massal dan hilirisasi."},
    {"nama": "Akses Data & Koleksi", "slug": "akses-data-koleksi", "deskripsi": "Penyediaan repositori data riset terbuka, spesimen hayati, dan koleksi ilmiah nasional."},
]

COLLABORATION_DATA = [
    {"nama": "Industri", "slug": "industri", "deskripsi": "Kemitraan hilirisasi inovasi, alih teknologi komersial, dan pendampingan industri strategis."},
    {"nama": "Akademisi", "slug": "akademisi", "deskripsi": "Kolaborasi penelitian bersama kampus, bimbingan mahasiswa, dan pertukaran periset."},
    {"nama": "Pemerintah", "slug": "pemerintah", "deskripsi": "Dukungan data dan rekomendasi kebijakan berbasis bukti saintifik untuk instansi daerah."},
    {"nama": "Komunitas", "slug": "komunitas", "deskripsi": "Penerapan teknologi tepat guna, literasi sains publik, dan pemberdayaan masyarakat lokal."},
]



def seed_separate_tables():
    print("[+] Creating tables: kst_jenis_kawasan, kst_themeriset, kst_facilities, kst_collaborations...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 0. Seed kst_jenis_kawasan
        print("[+] Seeding kst_jenis_kawasan...")
        for item in JENIS_KAWASAN_DATA:
            existing = db.query(KSTJenisKawasan).filter_by(slug=item["slug"]).first()
            if not existing:
                db.add(KSTJenisKawasan(
                    nama=item["nama"],
                    slug=item["slug"],
                    deskripsi=item.get("deskripsi"),
                    is_active=True
                ))
            else:
                existing.nama = item["nama"]
                if item.get("deskripsi"):
                    existing.deskripsi = item.get("deskripsi")
                existing.is_active = True

        print("[+] Seeding kst_themeriset...")
        for item in THEME_DATA:
            existing = db.query(KSTThemeRiset).filter_by(slug=item["slug"]).first()
            if not existing:
                db.add(KSTThemeRiset(
                    nama=item["nama"],
                    slug=item["slug"],
                    deskripsi=item["deskripsi"],
                    is_active=True
                ))
            else:
                existing.nama = item["nama"]
                existing.deskripsi = item["deskripsi"]
                existing.is_active = True

        # 2. Seed / Migrate kst_facilities
        print("[+] Seeding kst_facilities...")
        for item in FACILITY_DATA:
            existing = db.query(KSTFacility).filter_by(slug=item["slug"]).first()
            if not existing:
                db.add(KSTFacility(
                    nama=item["nama"],
                    slug=item["slug"],
                    deskripsi=item["deskripsi"],
                    is_active=True
                ))
            else:
                existing.nama = item["nama"]
                existing.deskripsi = item["deskripsi"]
                existing.is_active = True

        # 3. Seed / Migrate kst_collaborations
        print("[+] Seeding kst_collaborations...")
        for item in COLLABORATION_DATA:
            existing = db.query(KSTCollaboration).filter_by(slug=item["slug"]).first()
            if not existing:
                db.add(KSTCollaboration(
                    nama=item["nama"],
                    slug=item["slug"],
                    deskripsi=item["deskripsi"],
                    is_active=True
                ))
            else:
                existing.nama = item["nama"]
                existing.deskripsi = item["deskripsi"]
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

        kawasan_cnt = db.query(KSTKawasan).count()
        print(f"[+] SUCCESS! Data successfully separated into individual tables:")
        print(f"    - kst_kawasan: {kawasan_cnt} records")
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

