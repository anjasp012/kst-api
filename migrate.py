import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy import create_engine
from app.core.config import settings

def main():
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    with engine.connect() as conn:
        conn.execute('''
            ALTER TABLE innovations 
            ADD COLUMN IF NOT EXISTS persona_id INTEGER REFERENCES personas(id) ON DELETE CASCADE;
        ''')
        print("Successfully added persona_id to innovations table.")

if __name__ == "__main__":
    main()
