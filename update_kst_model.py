import re

with open("app/models/kst.py", "r") as f:
    text = f.read()

# Add relationship import if not present
if "from sqlalchemy.orm import relationship" not in text:
    text = text.replace("from sqlalchemy import Column", "from sqlalchemy import Column, ForeignKey\nfrom sqlalchemy.orm import relationship")

text = re.sub(r'\s*jenis = Column\(String\(50\), default="KST", nullable=False\)', '\n    instansi_id = Column(UUID(as_uuid=True), ForeignKey("kst_instansi.id"), nullable=True)\n    instansi = relationship("KSTInstansi")', text)

with open("app/models/kst.py", "w") as f:
    f.write(text)
