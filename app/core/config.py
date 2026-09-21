import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "KST BRIN API")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/kst_db"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "e17ef79abd36271f6808535fe5016a2acf77defc6d8a3b879495ff109886c6e4")
    ACCESS_TOKEN: str = os.getenv("ACCESS_TOKEN", "3bcd41cd73ea9337c54a4d503b606171c01de8907681cd25b4924b9cce442c07")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "").rstrip("/")
    JWT_EXPIRE_SECONDS: int = 3600
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 7 * 24 * 3600


settings = Settings()

# Uploads directory configuration (absolute path to project root/uploads)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
try:
    os.makedirs(UPLOADS_DIR, exist_ok=True)
except Exception:
    pass
