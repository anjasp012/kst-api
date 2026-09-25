import re

with open("app/seed/seed_data.py", "r") as f:
    text = f.read()

# Add KSTInstansi to imports
if "from app.models.instansi import KSTInstansi" not in text:
    text = text.replace("from app.models.kst import KSTLocation", "from app.models.kst import KSTLocation\nfrom app.models.instansi import KSTInstansi")

# Fix KST Location
text = re.sub(r'jenis="KST",', 'instansi_id=db.query(KSTInstansi).filter(KSTInstansi.nama.ilike("%KST%")).first().id if db.query(KSTInstansi).filter(KSTInstansi.nama.ilike("%KST%")).first() else None,', text)

# Fix Regional Partner
text = re.sub(r'jenis=p\["jenis"\],', 'instansi_id=db.query(KSTInstansi).filter(KSTInstansi.nama.ilike(p["jenis"])).first().id if db.query(KSTInstansi).filter(KSTInstansi.nama.ilike(p["jenis"])).first() else None,', text)


with open("app/seed/seed_data.py", "w") as f:
    f.write(text)
