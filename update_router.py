import re

with open("app/api/v1/router.py", "r") as f:
    text = f.read()

# Add import
text = text.replace("    wilayah,", "    wilayah,\n    instansi,")

# Add router inclusion
router_block = """
# 🏢 Jenis Instansi (kst_instansi)
api_router.include_router(
    instansi.router,
    prefix="/kst/instansi",
    tags=["Jenis Instansi (kst_instansi)"]
)
"""
text = text + router_block

with open("app/api/v1/router.py", "w") as f:
    f.write(text)
