from app.db.session import SessionLocal
from app.models.wilayah import WilayahProvince, WilayahRegency

db = SessionLocal()
provinces = db.query(WilayahProvince).count()
regencies = db.query(WilayahRegency).count()
print(f"Provinces in DB: {provinces}")
print(f"Regencies in DB: {regencies}")
