import re

with open("app/api/v1/endpoints/kst.py", "r") as f:
    text = f.read()

# Fix create_kst_location
old_create = """    data = payload.dict()
    lat = data.get("latitude")
    lon = data.get("longitude")
    data["geom"] = _set_point_geom(lat, lon)

    new_kst = KSTLocation(**data)
    db.add(new_kst)
    db.commit()"""

new_create = """    data = payload.dict()
    instansi_nama = data.pop("instansi_nama", None)

    lat = data.get("latitude")
    lon = data.get("longitude")
    data["geom"] = _set_point_geom(lat, lon)

    new_kst = KSTLocation(**data)
    
    instansi_id = None
    if instansi_nama:
        nama_instansi = instansi_nama.strip()
        slug_instansi = nama_instansi.lower().replace(" ", "-")
        inst_obj = db.query(KSTInstansi).filter(KSTInstansi.nama.ilike(nama_instansi)).first()
        if not inst_obj:
            inst_obj = KSTInstansi(nama=nama_instansi, slug=slug_instansi)
            db.add(inst_obj)
            db.commit()
            db.refresh(inst_obj)
        instansi_id = inst_obj.id
    new_kst.instansi_id = instansi_id

    db.add(new_kst)
    db.commit()"""

text = text.replace(old_create, new_create)

# Fix update_kst_location
old_update = """    for field, val in update_data.items():
        setattr(kst, field, val)

    db.commit()"""

new_update = """    instansi_nama = update_data.pop("instansi_nama", None)
    for field, val in update_data.items():
        setattr(kst, field, val)

    if instansi_nama is not None:
        nama_instansi = instansi_nama.strip()
        slug_instansi = nama_instansi.lower().replace(" ", "-")
        inst_obj = db.query(KSTInstansi).filter(KSTInstansi.nama.ilike(nama_instansi)).first()
        if not inst_obj:
            inst_obj = KSTInstansi(nama=nama_instansi, slug=slug_instansi)
            db.add(inst_obj)
            db.commit()
            db.refresh(inst_obj)
        kst.instansi_id = inst_obj.id

    db.commit()"""

text = text.replace(old_update, new_update)

with open("app/api/v1/endpoints/kst.py", "w") as f:
    f.write(text)
