"""
Script untuk membersihkan URL localhost / 127.0.0.1:8000 yang tersimpan di database,
mengubahnya menjadi path relatif (/uploads/...) agar aman diakses di VPS / production.
"""
from sqlalchemy import text
from app.db.session import engine

def clean_urls():
    tables_and_columns = [
        ("personas", "icon_url"),
        ("zones", "icon_url"),
        ("innovations", "thumbnail_url"),
    ]
    
    with engine.begin() as conn:
        for table, col in tables_and_columns:
            for host in ("http://127.0.0.1:8000", "http://localhost:8000", "https://127.0.0.1:8000", "https://localhost:8000"):
                res = conn.execute(text(f"""
                    UPDATE {table}
                    SET {col} = REPLACE({col}, '{host}', '')
                    WHERE {col} LIKE '%{host}%'
                """))
                if res.rowcount > 0:
                    print(f"[{table}.{col}] Membersihkan {res.rowcount} baris dari prefix '{host}'")
                    
    print("Pembersihan database selesai!")

if __name__ == "__main__":
    clean_urls()

