import re

with open("app/api/v1/endpoints/admin.py", "r") as f:
    text = f.read()

# Add KSTInstansi to imports
if "from app.models.instansi import KSTInstansi" not in text:
    text = text.replace("from app.models.kst import KSTLocation", "from app.models.kst import KSTLocation\nfrom app.models.instansi import KSTInstansi")

# Fix KST vs Partner count
text = re.sub(r"total_kst = db\.query\(func\.count\(KSTLocation\.id\)\)\.filter\(KSTLocation\.is_active == True, KSTLocation\.jenis == 'KST'\)\.scalar\(\) or 0", "total_kst = db.query(func.count(KSTLocation.id)).join(KSTInstansi).filter(KSTLocation.is_active == True, KSTInstansi.nama.ilike('%KST%')).scalar() or 0", text)

text = re.sub(r"total_partners = db\.query\(func\.count\(KSTLocation\.id\)\)\.filter\(KSTLocation\.is_active == True, KSTLocation\.jenis != 'KST'\)\.scalar\(\) or 0", "total_partners = db.query(func.count(KSTLocation.id)).join(KSTInstansi).filter(KSTLocation.is_active == True, ~KSTInstansi.nama.ilike('%KST%')).scalar() or 0", text)

text = re.sub(r"        \.filter\(KSTLocation\.is_active == True, KSTLocation\.jenis == 'KST'\)", "        .join(KSTInstansi).filter(KSTLocation.is_active == True, KSTInstansi.nama.ilike('%KST%'))", text)

# Fix Sebaran jenis mitra
old_sebaran = """    # Sebaran jenis mitra (BRIDA, BAPPERIDA, BAPPEDA)
    partner_stats = (
        db.query(KSTLocation.jenis, func.count(KSTLocation.id))
        .filter(KSTLocation.is_active == True, KSTLocation.jenis != 'KST')
        .group_by(KSTLocation.jenis)
        .all()
    )"""

new_sebaran = """    # Sebaran jenis mitra
    partner_stats = (
        db.query(KSTInstansi.nama, func.count(KSTLocation.id))
        .join(KSTInstansi)
        .filter(KSTLocation.is_active == True, ~KSTInstansi.nama.ilike('%KST%'))
        .group_by(KSTInstansi.nama)
        .all()
    )"""

text = text.replace(old_sebaran, new_sebaran)

# Also there's a reference to RegionalPartner.jenis that was left over?
text = re.sub(r"\.group_by\(RegionalPartner\.jenis\)", ".group_by(KSTInstansi.nama)", text)


with open("app/api/v1/endpoints/admin.py", "w") as f:
    f.write(text)
