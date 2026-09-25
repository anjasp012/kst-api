import re

with open("app/schemas/kst.py", "r") as f:
    text = f.read()

# Change instansi_id back to instansi_nama in create/update
text = text.replace("instansi_id: Optional[uuid.UUID] = None", "instansi_nama: Optional[str] = Field(None, example=\"Kawasan Sains (KST)\")")

with open("app/schemas/kst.py", "w") as f:
    f.write(text)

with open("app/api/v1/endpoints/kst.py", "r") as f:
    api_text = f.read()

# Add KSTInstansi logic in create_kst
if "from app.models.instansi import KSTInstansi" not in api_text:
    api_text = api_text.replace("from app.models.kst import KSTLocation", "from app.models.kst import KSTLocation\nfrom app.models.instansi import KSTInstansi")

create_logic_old = """    db.add(item)
    db.commit()"""

create_logic_new = """
    instansi_id = None
    if payload.instansi_nama:
        nama_instansi = payload.instansi_nama.strip()
        slug_instansi = nama_instansi.lower().replace(" ", "-")
        inst_obj = db.query(KSTInstansi).filter(KSTInstansi.nama.ilike(nama_instansi)).first()
        if not inst_obj:
            inst_obj = KSTInstansi(nama=nama_instansi, slug=slug_instansi)
            db.add(inst_obj)
            db.commit()
            db.refresh(inst_obj)
        instansi_id = inst_obj.id

    item.instansi_id = instansi_id
    db.add(item)
    db.commit()"""

api_text = api_text.replace(create_logic_old, create_logic_new)

# Add logic in update_kst
update_logic_old = """    if payload.is_active is not None:
        item.is_active = payload.is_active"""

update_logic_new = """    if payload.is_active is not None:
        item.is_active = payload.is_active

    if getattr(payload, 'instansi_nama', None) is not None:
        nama_instansi = payload.instansi_nama.strip()
        slug_instansi = nama_instansi.lower().replace(" ", "-")
        inst_obj = db.query(KSTInstansi).filter(KSTInstansi.nama.ilike(nama_instansi)).first()
        if not inst_obj:
            inst_obj = KSTInstansi(nama=nama_instansi, slug=slug_instansi)
            db.add(inst_obj)
            db.commit()
            db.refresh(inst_obj)
        item.instansi_id = inst_obj.id
"""
api_text = api_text.replace(update_logic_old, update_logic_new)

with open("app/api/v1/endpoints/kst.py", "w") as f:
    f.write(api_text)

