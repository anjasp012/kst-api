from app.db.session import engine, Base
from sqlalchemy import text
from app.models.kst import KSTLocation
from app.models.instansi import KSTInstansi

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS kst_locations CASCADE;"))
    conn.commit()

Base.metadata.create_all(bind=engine)
print("Recreated kst_locations and kst_instansi")
