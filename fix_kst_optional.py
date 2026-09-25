import re

with open("app/schemas/kst.py", "r") as f:
    text = f.read()

text = text.replace('pengelola: str = Field(default="BRIN", example="BRIN")', 'pengelola: Optional[str] = None')
text = text.replace('status: str = Field(default="Aktif", example="Aktif")', 'status: Optional[str] = None')
text = text.replace('tahun_operasi: int = Field(default=2021, example=2021)', 'tahun_operasi: Optional[int] = None')

# In KSTMapItem, some fields are not optional
text = text.replace('pengelola: str\n    status: str', 'pengelola: Optional[str] = None\n    status: Optional[str] = None')
text = text.replace('tahun_operasi: int\n', 'tahun_operasi: Optional[int] = None\n')

with open("app/schemas/kst.py", "w") as f:
    f.write(text)

with open("app/models/kst.py", "r") as f:
    model_text = f.read()

model_text = model_text.replace('pengelola = Column(String(200), default="BRIN", nullable=False)', 'pengelola = Column(String(200), nullable=True)')
model_text = model_text.replace('status = Column(String(50), default="Aktif", nullable=False)', 'status = Column(String(50), nullable=True)')
model_text = model_text.replace('tahun_operasi = Column(Integer, default=2021, nullable=False)', 'tahun_operasi = Column(Integer, nullable=True)')

with open("app/models/kst.py", "w") as f:
    f.write(model_text)

