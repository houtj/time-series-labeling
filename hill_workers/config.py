"""
Configuration Settings for Workers
Load settings from environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Worker settings from environment variables"""
    
    # ===== Database =====
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://root:example@localhost:27017/")
    DATABASE_NAME: str = "hill_ts"
    
    # ===== Redis =====
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    
    # ===== Paths =====
    DATA_FOLDER_PATH: Path = Path(os.getenv("DATA_FOLDER_PATH", "/home/thou2/projects/hill-app/app_data"))
    
    # ===== Worker Configuration =====
    WORKER_NAME: str = os.getenv("WORKER_NAME", "file-parser-1")
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "10"))
    BLOCK_TIME_MS: int = int(os.getenv("BLOCK_TIME_MS", "5000"))  # 5 seconds
    
    # ===== Logging =====
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "worker.log")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

settings = Settings()

