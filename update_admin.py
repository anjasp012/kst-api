import re

admin_path = "/Users/anjas/sites/BRIN/kst-api/app/api/v1/endpoints/admin.py"
with open(admin_path, "r") as f:
    content = f.read()

content = content.replace("from app.models.partner import RegionalPartner\n", "")
content = content.replace(
    "total_kst = db.query(func.count(KSTLocation.id)).filter(KSTLocation.is_active == True).scalar() or 0",
    "total_kst = db.query(func.count(KSTLocation.id)).filter(KSTLocation.is_active == True, KSTLocation.jenis == 'KST').scalar() or 0"
)
content = content.replace(
    "total_partners = db.query(func.count(RegionalPartner.id)).filter(RegionalPartner.is_active == True).scalar() or 0",
    "total_partners = db.query(func.count(KSTLocation.id)).filter(KSTLocation.is_active == True, KSTLocation.jenis != 'KST').scalar() or 0"
)

content = content.replace(
    ".filter(KSTLocation.is_active == True)",
    ".filter(KSTLocation.is_active == True, KSTLocation.jenis == 'KST')"
)

pbt_rep = """    partner_by_type = (
        db.query(KSTLocation.jenis, func.count(KSTLocation.id))
        .filter(KSTLocation.is_active == True, KSTLocation.jenis != 'KST')
        .group_by(KSTLocation.jenis)
        .all()
    )"""

content = re.sub(r'    partner_by_type = \([^)]+\)', pbt_rep, content)

with open(admin_path, "w") as f:
    f.write(content)

print("Updated admin.py")
