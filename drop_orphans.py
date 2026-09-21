"""Drop orphaned tables that are no longer in the codebase"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from sqlalchemy import text
from app.db.session import engine

with engine.connect() as conn:
    # List all existing tables
    result = conn.execute(text("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY tablename
    """))
    existing = [row[0] for row in result]
    print(f"[i] Tabel di database: {existing}")

    # Known tables that SHOULD exist
    keep = {
        'users', 'personas', 'zones', 'innovations',
        'innovation_persona_relevances', 'research_suggestions',
        'telemetry_logs'
    }

    orphans = [t for t in existing if t not in keep]
    if orphans:
        for t in orphans:
            print(f"[-] Dropping orphaned table: {t}")
            conn.execute(text(f'DROP TABLE IF EXISTS "{t}" CASCADE'))
        conn.commit()
        print(f"[+] {len(orphans)} orphaned table(s) dropped!")
    else:
        print("[+] Tidak ada tabel zombie. Database sudah bersih!")
