import re

with open("app/seed/seed_separate_tables.py", "r") as f:
    text = f.read()

text = re.sub(r'from app\.models\.wilayah_zone import KSTWilayahZone\n', '', text)

text = re.sub(r'    wilayah_zones = \[.*?\]\n\n    print\("Seeding KSTWilayahZone\.\.\."\)\n    for item in wilayah_zones:\n.*?print\("KSTWilayahZone seeded successfully\."\)\n', '', text, flags=re.DOTALL)
text = re.sub(r'        wilayah_cnt = db\.query\(KSTWilayahZone\)\.count\(\)\n', '', text)
text = re.sub(r'        "Wilayah Zones": wilayah_cnt,\n', '', text)

with open("app/seed/seed_separate_tables.py", "w") as f:
    f.write(text)
