import re

with open("app/seed/seed_data.py", "r") as f:
    text = f.read()

# I will just remove the whole admin_user creation block because it already exists
text = re.sub(r'# 1\. Admin User.*?admin_user = User\(.*?\)\s*#.*?#\s*#', '', text, flags=re.DOTALL)
text = re.sub(r'admin_user = User\(\n.*?\n\)\n', '', text, flags=re.DOTALL)

with open("app/seed/seed_data.py", "w") as f:
    f.write(text)
