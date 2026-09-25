import os

kst_model_path = "/Users/anjas/sites/BRIN/kst-api/app/models/kst.py"
with open(kst_model_path, "r") as f:
    content = f.read()

if "jenis =" not in content:
    replacement = """    status = Column(String(50), default="Aktif", nullable=False)
    jenis = Column(String(50), default="KST", nullable=False)
    telepon = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    email = Column(String(150), nullable=True)
    alamat = Column(Text, nullable=True)
    tahun_operasi = Column(Integer, default=2021, nullable=False)"""
    content = content.replace('    status = Column(String(50), default="Aktif", nullable=False)\n    tahun_operasi = Column(Integer, default=2021, nullable=False)', replacement)
    with open(kst_model_path, "w") as f:
        f.write(content)
print("Updated KST model.")
