import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Settings:
    PROJECT_NAME: str = "PocketSmart AI"
    PROJECT_DESCRIPTION: str = "Your Smart Budget & Recommendation Assistant"
    VERSION: str = "1.0.0"
    
    # Gemini AI configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    
    # Security & Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "pocketsmart_super_secure_jwt_secret_key_change_in_production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/pocketsmart.db")
    
    # CORS
    raw_origins = os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000,http://localhost:3000")
    ALLOWED_ORIGINS: list[str] = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    
    # Uploads
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    MAX_IMAGE_SIZE_MB: int = 5
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp", "image/jpg"]

settings = Settings()

# Ensure critical directories exist
os.makedirs(BASE_DIR / "data", exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
