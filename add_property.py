with open("app/models/kst.py", "r") as f:
    text = f.read()

prop = """
    @property
    def instansi_nama(self):
        return self.instansi.nama if self.instansi else None
"""
text = text + prop

with open("app/models/kst.py", "w") as f:
    f.write(text)
