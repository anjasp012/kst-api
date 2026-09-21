import re
import urllib.request
from app.db.session import SessionLocal, Base, engine
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


def seed_wilayah_data():
    print("[+] Seeding Wilayah Indonesia (38 Provinsi & 514 Kota/Kabupaten)...")
    req = urllib.request.urlopen(SQL_URL)
    content = req.read().decode("utf-8")

    province_matches = re.findall(r"\('(\d{2})','([^']+)'\)", content)
    regency_matches = re.findall(r"\('(\d{2}\.\d{2})','([^']+)'\)", content)

    db = SessionLocal()
    try:
        # Seed 38 Provinces
        for kode, nama in province_matches:
            wilayah_region = map_province_wilayah(kode, nama)
            prov = db.query(WilayahProvince).filter_by(kode=kode).first()
            if not prov:
                prov = WilayahProvince(kode=kode, nama=nama, wilayah=wilayah_region)
                db.add(prov)
            else:
                prov.nama = nama
                prov.wilayah = wilayah_region
        db.commit()

        # Seed 514 Regencies
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

        print(f"[+] {len(province_matches)} Provinsi & {len(regency_matches)} Kota/Kabupaten seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"[-] Error seeding wilayah: {e}")
        raise
    finally:
        db.close()
