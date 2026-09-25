import re

with open("app/schemas/kst.py", "r") as f:
    text = f.read()

text = re.sub(r'\s*jenis: str = Field\(default="KST", example="KST"\)', '\n    instansi_id: Optional[uuid.UUID] = None', text)
text = re.sub(r'\s*jenis: str = "KST"', '\n    instansi_id: Optional[uuid.UUID] = None\n    instansi_nama: Optional[str] = None', text)
text = re.sub(r'\s*jenis: Optional\[str\] = None', '\n    instansi_id: Optional[uuid.UUID] = None', text)

with open("app/schemas/kst.py", "w") as f:
    f.write(text)
