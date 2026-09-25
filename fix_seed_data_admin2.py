import re

with open("app/seed/seed_data.py", "r") as f:
    text = f.read()

text = re.sub(r'# 1\. Admin User\n.*?existing_admin = db\.query\(User\)\.filter_by\(username=\'admin\'\)\.first\(\)\n\s*if not existing_admin:\n\s*db\.add\(admin_user\)\n\s*db\.commit\(\)\n\s*print\("\[\+\] Admin created: username=\'admin\' \(Password: admin123\)"\)', '', text, flags=re.DOTALL)

with open("app/seed/seed_data.py", "w") as f:
    f.write(text)
