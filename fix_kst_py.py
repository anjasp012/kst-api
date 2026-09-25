with open("app/api/v1/endpoints/kst.py", "r") as f:
    text = f.read()

import re
# Remove imports
text = re.sub(r'from app\.models\.partner import RegionalPartner\n', '', text)
text = re.sub(r'from app\.schemas\.partner import PartnerResponse, PartnerCreate, PartnerUpdate\n', '', text)

# Delete section 2
text = re.sub(r'# =========================================================================\n# 🏛️ 2\. DIREKTORI MITRA DAERAH.*?# =========================================================================\n# 🛠️ 3\. ADMIN CRUD KST \(CMS\)', '# =========================================================================\n# 🛠️ 3. ADMIN CRUD KST (CMS)', text, flags=re.DOTALL)

# Delete section 4
text = re.sub(r'# =========================================================================\n# 🛠️ 4\. ADMIN CRUD MITRA DAERAH \(CMS\).*', '', text, flags=re.DOTALL)

with open("app/api/v1/endpoints/kst.py", "w") as f:
    f.write(text)
