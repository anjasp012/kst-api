import re

# Fix models/kst.py
with open("app/models/kst.py", "r") as f:
    text = f.read()

text = re.sub(r'    fokus_utama = Column\(JSON, default=list\).*?\n', '', text)
text = re.sub(r'    terhubung_dengan = Column\(Text, nullable=True\).*?\n', '', text)

with open("app/models/kst.py", "w") as f:
    f.write(text)

# Fix schemas/kst.py
with open("app/schemas/kst.py", "r") as f:
    text = f.read()

text = re.sub(r'    fokus_utama: List\[str\] = Field\(default_factory=list, example=\["Pangan", "Energi", "Laut", "Teknologi Digital"\]\)\n', '', text)
text = re.sub(r'    terhubung_dengan: Optional\[str\] = None\n', '', text)

text = re.sub(r'    fokus_utama: Optional\[List\[str\]\] = None\n', '', text)
text = re.sub(r'    fokus_utama: List\[str\] = \[\]\n', '', text)

with open("app/schemas/kst.py", "w") as f:
    f.write(text)

print("Done")
