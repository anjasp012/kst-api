with open("app/main.py", "r") as f:
    text = f.read()

text = text.replace(
    "# Auto create tables on startup\nBase.metadata.create_all(bind=engine)",
    "# Auto create tables on startup\nBase.metadata.create_all(bind=engine)\n\nfrom app.db.auto_migrate import run_auto_migration\nrun_auto_migration(engine)"
)

with open("app/main.py", "w") as f:
    f.write(text)
