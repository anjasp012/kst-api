from app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE kst_locations ALTER COLUMN pengelola DROP NOT NULL;"))
    conn.execute(text("ALTER TABLE kst_locations ALTER COLUMN status DROP NOT NULL;"))
    conn.execute(text("ALTER TABLE kst_locations ALTER COLUMN tahun_operasi DROP NOT NULL;"))
    conn.commit()

print("Altered columns successfully!")
