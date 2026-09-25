import re

with open("app/seed/seed_data.py", "r") as f:
    text = f.read()

# Replace RegionalPartner import
text = re.sub(r'from app\.models\.partner import RegionalPartner\n', '', text)

# Update the partners insertion block
old_block = """        for p in partners_data:
            lat = p["latitude"]
            lon = p["longitude"]
            geom = WKTElement(f"POINT({lon} {lat})", srid=4326) if lat and lon else None
            part_obj = RegionalPartner(
                nama_organisasi=p["nama_organisasi"],
                jenis=p["jenis"],
                wilayah=p["wilayah"],
                alamat=p["alamat"],
                telepon=p["telepon"],
                website=p["website"],
                email=p["email"],
                latitude=lat,
                longitude=lon,
                geom=geom
            )
            db.add(part_obj)
        db.commit()
        print(f"[+] {len(partners_data)} Regional Partners seeded successfully!")"""

new_block = """        for p in partners_data:
            lat = p["latitude"]
            lon = p["longitude"]
            geom = WKTElement(f"POINT({lon} {lat})", srid=4326) if lat and lon else None
            
            slug = p["nama_organisasi"].lower().replace(' ', '-') + '-' + str(lat)[:4].replace('.','')
            
            part_obj = KSTLocation(
                nama=p["nama_organisasi"],
                slug=slug,
                kota_provinsi=p["wilayah"],
                pengelola="Mitra Daerah",
                jenis=p["jenis"],
                alamat=p["alamat"],
                telepon=p["telepon"],
                website=p["website"],
                email=p["email"],
                latitude=lat,
                longitude=lon,
                geom=geom
            )
            db.add(part_obj)
        db.commit()
        print(f"[+] {len(partners_data)} Regional Partners seeded successfully as KSTLocations!")"""

text = text.replace(old_block, new_block)

with open("app/seed/seed_data.py", "w") as f:
    f.write(text)
