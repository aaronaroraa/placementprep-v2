from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    DATABASE_URL: str = "postgresql+asyncpg://ppai:ppaipass@localhost:5432/placementprep"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "dev_secret_change_in_prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google OAuth + Calendar
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"
    FRONTEND_URL: str = "http://localhost:5173"

    # LLM
    LLM_PROVIDER: Literal["gemini", "openai", "none"] = "none"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Judge0
    JUDGE0_API_KEY: str = ""
    JUDGE0_HOST: str = "judge0-ce.p.rapidapi.com"

    # Files
    RESUME_UPLOAD_DIR: str = "./uploads/resumes"
    MAX_RESUME_SIZE_MB: int = 5
    APP_ENV: str = "development"


settings = Settings()
