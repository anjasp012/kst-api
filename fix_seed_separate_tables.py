import re

with open("app/seed/seed_separate_tables.py", "r") as f:
    text = f.read()

# Remove WILAYAH_DATA
text = re.sub(r'WILAYAH_DATA = \[\n.*?\]\n\n', '', text, flags=re.DOTALL)

# Remove seeding kst_wilayah block
text = re.sub(r'        # 4\. Seed / Migrate kst_wilayah\n.*?existing\.is_active = True\n', '', text, flags=re.DOTALL)

# Remove wilayah_cnt from print
text = re.sub(r'.*wilayah_cnt = db\.query\(KSTWilayahZone\)\.count\(\)\n', '', text)
text = re.sub(r'.*print\(f"    - kst_wilayah: \{wilayah_cnt\} records"\)\n', '', text)
text = re.sub(r'from app.models.wilayah_zone import KSTWilayahZone\n', '', text)

with open("app/seed/seed_separate_tables.py", "w") as f:
    f.write(text)
