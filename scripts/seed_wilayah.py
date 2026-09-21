import os
import sys
import re
import urllib.request

# Ensure app is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import engine, SessionLocal, Base
from app.models.wilayah import WilayahProvince, WilayahRegency

SQL_URL = "https://raw.githubusercontent.com/cahyadsn/wilayah/master/db/wilayah.sql"


def map_province_wilayah(kode: str, name: str) -> str:
    """
    Memetakan kode provinsi ke 6 Wilayah Utama BRIN:
    Sumatera, Jawa, Kalimantan, Sulawesi, Nusa Tenggara, Maluku & Papua
    """
    try:
        k = int(kode)
    except ValueError:
        return "Jawa"

    if 11 <= k <= 21:
        return "Sumatera"
    elif 31 <= k <= 36:
        return "Jawa"
    elif 51 <= k <= 53:
        return "Nusa Tenggara"
    elif 61 <= k <= 65:
        return "Kalimantan"
    elif 71 <= k <= 76:
        return "Sulawesi"
    elif (81 <= k <= 82) or (91 <= k <= 96):
        return "Maluku & Papua"
    return "Jawa"


def seed_wilayah():
    print("🚀 Initializing tables in database...")
    Base.metadata.create_all(bind=engine)

    print(f"📥 Downloading wilayah SQL data from: {SQL_URL}")
    req = urllib.request.urlopen(SQL_URL)
    content = req.read().decode("utf-8")

    # Regex patterns for provinces and regencies/cities
    province_matches = re.findall(r"\('(\d{2})','([^']+)'\)", content)
    regency_matches = re.findall(r"\('(\d{2}\.\d{2})','([^']+)'\)", content)

    print(f"🔍 Found {len(province_matches)} provinces and {len(regency_matches)} regencies/cities.")

    db = SessionLocal()
    try:
        # 1. Seed Provinces
        print("🌱 Seeding provinces...")
        prov_map = {}
        for kode, nama in province_matches:
            wilayah_region = map_province_wilayah(kode, nama)
            prov = db.query(WilayahProvince).filter_by(kode=kode).first()
            if not prov:
                prov = WilayahProvince(kode=kode, nama=nama, wilayah=wilayah_region)
                db.add(prov)
            else:
                prov.nama = nama
                prov.wilayah = wilayah_region
            prov_map[kode] = prov

        db.commit()
        print(f"✅ {len(province_matches)} provinces seeded successfully.")

        # 2. Seed Regencies / Cities
        print("🌱 Seeding regencies and cities...")
        for kode, nama in regency_matches:
            prov_kode = kode.split(".")[0]
            tipe = "Kabupaten" if nama.startswith("Kabupaten") else "Kota"
            reg = db.query(WilayahRegency).filter_by(kode=kode).first()
            if not reg:
                reg = WilayahRegency(
                    kode=kode,
                    province_kode=prov_kode,
                    nama=nama,
                    tipe=tipe
                )
                db.add(reg)
            else:
                reg.province_kode = prov_kode
                reg.nama = nama
                reg.tipe = tipe

        db.commit()
        print(f"✅ {len(regency_matches)} regencies/cities seeded successfully.")

        # Summary check
        total_p = db.query(WilayahProvince).count()
        total_r = db.query(WilayahRegency).count()
        print("🎉 Wilayah Seeding Completed Successfully!")
        print(f"   Total Provinces in DB: {total_p} (Target: 38)")
        print(f"   Total Regencies in DB: {total_r} (Target: 514)")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_wilayah()

