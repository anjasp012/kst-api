import re

with open("app/seed/seed_separate_tables.py", "r") as f:
    text = f.read()

# Add KSTInstansi to imports
if "from app.models.instansi import KSTInstansi" not in text:
    text = text.replace("from app.db.session import SessionLocal, Base, engine", "from app.db.session import SessionLocal, Base, engine\nfrom app.models.instansi import KSTInstansi")

# Add INSTANSI_DATA
if "INSTANSI_DATA = [" not in text:
    instansi_data = """
INSTANSI_DATA = [
    {"nama": "Kawasan Sains (KST)", "slug": "kawasan-sains-kst", "deskripsi": "Kawasan Sains dan Teknologi utama (KST).", "urutan": 1},
    {"nama": "BRIDA", "slug": "brida", "deskripsi": "Badan Riset dan Inovasi Daerah.", "urutan": 2},
    {"nama": "BAPPERIDA", "slug": "bapperida", "deskripsi": "Badan Perencanaan Pembangunan, Riset dan Inovasi Daerah.", "urutan": 3},
    {"nama": "BAPPEDA", "slug": "bappeda", "deskripsi": "Badan Perencanaan Pembangunan Daerah.", "urutan": 4},
]
"""
    text = text.replace("THEME_DATA = [", instansi_data + "\nTHEME_DATA = [")

# Add seeding logic
if "Seeding kst_instansi" not in text:
    seeding_logic = """
        # 0. Seed kst_instansi
        print("[+] Seeding kst_instansi...")
        for item in INSTANSI_DATA:
            existing = db.query(KSTInstansi).filter_by(slug=item["slug"]).first()
            if not existing:
                db.add(KSTInstansi(
                    nama=item["nama"],
                    slug=item["slug"],
                    deskripsi=item["deskripsi"],
                    urutan=item["urutan"],
                    is_active=True
                ))
            else:
                existing.nama = item["nama"]
                existing.deskripsi = item["deskripsi"]
                existing.urutan = item["urutan"]
                existing.is_active = True
"""
    text = text.replace("print(\"[+] Seeding kst_themeriset...\")", seeding_logic + "\n        print(\"[+] Seeding kst_themeriset...\")")

with open("app/seed/seed_separate_tables.py", "w") as f:
    f.write(text)
