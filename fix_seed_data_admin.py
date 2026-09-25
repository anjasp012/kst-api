import re

with open("app/seed/seed_data.py", "r") as f:
    text = f.read()

text = text.replace("db.add(admin_user)", "existing_admin = db.query(User).filter_by(username='admin').first()\n        if not existing_admin:\n            db.add(admin_user)\n            db.commit()\n            print(\"[+] Admin created: username='admin' (Password: admin123)\")")
text = text.replace('db.commit()\n        print("[+] Admin created: username=\'admin\' (Password: admin123)")', '')

with open("app/seed/seed_data.py", "w") as f:
    f.write(text)
