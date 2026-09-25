import re

with open("app/seed/seed_data.py", "r") as f:
    text = f.read()

text = text.replace("from app.seed.seed_categories import seed_categories_data", "from app.seed.seed_separate_tables import seed_separate_tables")
text = text.replace("seed_categories_data()", "seed_separate_tables()")

with open("app/seed/seed_data.py", "w") as f:
    f.write(text)
