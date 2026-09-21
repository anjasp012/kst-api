import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.seed.seed_data import seed_database

if __name__ == "__main__":
    seed_database()

