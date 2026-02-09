"""
Configuration Settings
Manages environment variables and application settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root .env
# In Docker, env vars are set via docker-compose environment section
_env_path = Path(__file__).parent.parent / '.env'
load_dotenv(_env_path)


class Settings:
    """Application settings from environment variables"""
    
    # Database
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://root:example@localhost:27017/")
    DATABASE_NAME: str = "hill_ts"
    
    # Paths
    DATA_FOLDER_PATH: Path = Path(os.getenv("DATA_FOLDER_PATH", "./data_folder"))
    
    # API Security
    DOWNLOAD_PASSWORD: str = os.getenv(
        "DOWNLOAD_PASSWORD",
        "NPeGBxS4hmP8NJh4H4C0BDuQnR6B4pT2ySEHmiNVi0WDbeTJfHdiuT0BNtuyyMUN1cDenSkk9M2tKVJ0rSaxY8zo8OcGPg5o"
    )
    
    # Upload limits
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "1024"))
    MAX_UPLOAD_SIZE_BYTES: int = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    # CORS
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Redis (for task queue)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    
    # Azure OpenAI (for chatbot)
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1")
    AZURE_API_VERSION: str = os.getenv("API_VERSION", "2024-02-01")
    AZURE_API_KEY: str = os.getenv("API_KEY", "")
    AZURE_ENDPOINT: str = os.getenv("API_ENDPOINT", "")
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True


# Global settings instance
settings = Settings()

