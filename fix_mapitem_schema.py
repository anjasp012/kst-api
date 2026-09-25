import re

with open("app/schemas/kst.py", "r") as f:
    text = f.read()

text = text.replace("    is_active: bool\n\n    @field_validator", "    tema_riset: List[str] = []\n    is_active: bool\n\n    @field_validator")

with open("app/schemas/kst.py", "w") as f:
    f.write(text)

with open("app/api/v1/endpoints/kst.py", "r") as f:
    text = f.read()

text = text.replace("item.fokus_utama", "item.tema_riset")

# Actually we need a property in KSTLocation to extract tema_riset
with open("app/models/kst.py", "r") as f:
    text_model = f.read()

tema_riset_prop = """
    @property
    def instansi_nama(self):
        return self.instansi.nama if self.instansi else None

    @property
    def tema_riset(self):
        if not self.riset:
            return []
        themes = []
        for r in self.riset:
            if r.get('tema') and r.get('tema') not in themes:
                themes.append(r.get('tema'))
        return themes
"""

text_model = text_model.replace("""
    @property
    def instansi_nama(self):
        return self.instansi.nama if self.instansi else None
""", tema_riset_prop)

with open("app/models/kst.py", "w") as f:
    f.write(text_model)

print("Done")
