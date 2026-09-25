import re

with open("app/api/v1/endpoints/wilayah.py", "r") as f:
    text = f.read()

# Remove wilayah parameter in GET /provinces
text = re.sub(r'\s*wilayah: Optional\[str\] = Query\(None, description="Filter berdasarkan kelompok wilayah \(Sumatera, Jawa, dll\)"\),', '', text)
text = re.sub(r'\s*if wilayah and wilayah != "ALL":\n\s*query = query\.filter\(WilayahProvince\.wilayah\.ilike\(f"%\{wilayah\}%"\)\)', '', text)

# Remove wilayah assignment in WilayahProvinceItem creation (both places)
text = re.sub(r',\s*wilayah=p\.wilayah', '', text)
text = re.sub(r',\s*wilayah=prov\.wilayah', '', text)
text = re.sub(r',\s*wilayah=payload\.wilayah\.strip\(\) if payload\.wilayah else None', '', text)

# Remove payload.wilayah check in update_province
text = re.sub(r'\s*if payload\.wilayah is not None:\n\s*prov\.wilayah = payload\.wilayah\.strip\(\)', '', text)

with open("app/api/v1/endpoints/wilayah.py", "w") as f:
    f.write(text)
