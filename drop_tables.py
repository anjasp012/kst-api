import sys
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/kst_db"
engine = create_engine(DATABASE_URL)
meta = MetaData()
meta.reflect(bind=engine)

def drop_all_except():
    keep_tables = ["provinces", "regencies"]
    
    # We must drop tables that have foreign keys first, or use CASCADE
    # MetaData drop_all handles dependencies if all tables are in metadata
    
    # Filter the tables to drop
    tables_to_drop = [table for name, table in meta.tables.items() if name not in keep_tables and name != 'spatial_ref_sys']
    
    meta.drop_all(bind=engine, tables=tables_to_drop)
    print("Dropped tables:", [t.name for t in tables_to_drop])
    print("Kept tables:", keep_tables)

if __name__ == "__main__":
    drop_all_except()
