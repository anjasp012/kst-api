import os
import sys
import json
import re
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.db.session import SessionLocal, Base, engine
from app.models.wilayah import WilayahProvince, WilayahRegency

SQL_URL = "https://raw.githubusercontent.com/cahyadsn/wilayah/master/db/wilayah.sql"
JSON_PATH = os.path.join(os.path.dirname(__file__), "wilayah_data.json")


def seed_wilayah_data():
    print("[+] Seeding Wilayah Indonesia (38 Provinsi & 514 Kota/Kabupaten)...")
    db = SessionLocal()
    try:
        if os.path.exists(JSON_PATH):
            print(f"  -> Memuat data wilayah dari file lokal: {JSON_PATH}")
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                w_data = json.load(f)

            for p in w_data.get("provinces", []):
                prov = db.query(WilayahProvince).filter_by(kode=p["kode"]).first()
                if not prov:
                    prov = WilayahProvince(kode=p["kode"], nama=p["nama"])
                    db.add(prov)
                else:
                    prov.nama = p["nama"]
            db.commit()

            for r in w_data.get("regencies", []):
                reg = db.query(WilayahRegency).filter_by(kode=r["kode"]).first()
                if not reg:
                    reg = WilayahRegency(
                        kode=r["kode"],
                        province_kode=r["province_kode"],
                        nama=r["nama"],
                        tipe=r.get("tipe", "Kabupaten")
                    )
                    db.add(reg)
                else:
                    reg.province_kode = r["province_kode"]
                    reg.nama = r["nama"]
                    reg.tipe = r.get("tipe", "Kabupaten")
            db.commit()
        else:
            print(f"  -> File lokal tidak ditemukan, mengunduh dari: {SQL_URL}")
            req = urllib.request.Request(
                SQL_URL,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode("utf-8")

            province_matches = re.findall(r"\('(\d{2})','([^']+)'\)", content)
            regency_matches = re.findall(r"\('(\d{2}\.\d{2})','([^']+)'\)", content)

            for kode, nama in province_matches:
                prov = db.query(WilayahProvince).filter_by(kode=kode).first()
                if not prov:
                    prov = WilayahProvince(kode=kode, nama=nama)
                    db.add(prov)
                else:
                    prov.nama = nama
            db.commit()

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

        p_count = db.query(WilayahProvince).count()
        r_count = db.query(WilayahRegency).count()
        print(f"[+] {p_count} Provinsi & {r_count} Kota/Kabupaten seeded successfully into database!")
    except Exception as e:
        db.rollback()
        print(f"[-] Error seeding wilayah: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_wilayah_data()
