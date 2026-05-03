import os
from dotenv import load_dotenv

# Load from .env if present
load_dotenv()

class Config:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./valura.db")
    APP_ENV: str = os.getenv("APP_ENV", "development")

settings = Config()
