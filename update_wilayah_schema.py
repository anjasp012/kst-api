import re

with open("app/schemas/wilayah.py", "r") as f:
    text = f.read()

text = re.sub(r'\s*wilayah:\s*Optional\[str\] = .*?\n', '\n', text)
text = re.sub(r'\s*wilayah:\s*Optional\[str\]\n', '\n', text)

with open("app/schemas/wilayah.py", "w") as f:
    f.write(text)
