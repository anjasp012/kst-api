import asyncio
import psycopg2
import sys

DB_URL = "postgresql://postgres:postgres@localhost:5432/research_table_db"

def main():
    print(f"Connecting to {DB_URL}")
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    try:
        cursor.execute('''
            ALTER TABLE innovations 
            ADD COLUMN IF NOT EXISTS persona_id INTEGER REFERENCES personas(id) ON DELETE CASCADE;
        ''')
        print("Successfully added persona_id to innovations table.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
