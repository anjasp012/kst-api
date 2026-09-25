import re

with open("app/models/wilayah.py", "r") as f:
    text = f.read()

text = text.replace('__tablename__ = "wilayah_provinces"', '__tablename__ = "provinces"')
text = text.replace('__tablename__ = "wilayah_regencies"', '__tablename__ = "regencies"')

# Remove wilayah column
text = re.sub(r'\s*wilayah = Column\(String\(50\), nullable=True, index=True\)', '', text)

# Fix Foreign Key
text = text.replace('ForeignKey("wilayah_provinces.kode"', 'ForeignKey("provinces.kode"')

with open("app/models/wilayah.py", "w") as f:
    f.write(text)
