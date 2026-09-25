import re

with open("app/api/v1/endpoints/kst.py", "r") as f:
    text = f.read()

# For create
old_create_if = """    if instansi_nama:
        nama_instansi = instansi_nama.strip()
        slug_instansi = nama_instansi.lower().replace(" ", "-")
        inst_obj = db.query(KSTInstansi).filter(KSTInstansi.nama.ilike(nama_instansi)).first()"""

new_create_if = """    if instansi_nama and instansi_nama.strip():
        nama_instansi = instansi_nama.strip()
        slug_instansi = nama_instansi.lower().replace(" ", "-")
        inst_obj = db.query(KSTInstansi).filter(KSTInstansi.nama.ilike(nama_instansi)).first()"""
text = text.replace(old_create_if, new_create_if)

# For update
old_update_if = """    if instansi_nama is not None:
        nama_instansi = instansi_nama.strip()
        slug_instansi = nama_instansi.lower().replace(" ", "-")
        inst_obj = db.query(KSTInstansi).filter(KSTInstansi.nama.ilike(nama_instansi)).first()"""

new_update_if = """    if instansi_nama and instansi_nama.strip():
        nama_instansi = instansi_nama.strip()
        slug_instansi = nama_instansi.lower().replace(" ", "-")
        inst_obj = db.query(KSTInstansi).filter(KSTInstansi.nama.ilike(nama_instansi)).first()"""
text = text.replace(old_update_if, new_update_if)

with open("app/api/v1/endpoints/kst.py", "w") as f:
    f.write(text)
