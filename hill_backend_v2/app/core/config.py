"""Application configuration management using Pydantic Settings"""

from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = Field(default="Hill Sequence Backend V2", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", alias="ENVIRONMENT"
    )

    # Database
    mongodb_url: str = Field(..., alias="MONGODB_URL")
    database_name: str = Field(default="hill_ts", alias="DATABASE_NAME")

    # Storage
    data_folder_path: str = Field(default="./data_folder", alias="DATA_FOLDER_PATH")
    max_upload_size_mb: int = Field(default=100, alias="MAX_UPLOAD_SIZE_MB")

    # Security
    api_secret_key: str = Field(..., alias="API_SECRET_KEY")
    download_api_password: str = Field(..., alias="DOWNLOAD_API_PASSWORD")

    # CORS
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")

    # Azure OpenAI
    azure_openai_deployment_name: str = Field(..., alias="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_api_key: str = Field(..., alias="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str = Field(..., alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_version: str = Field(
        default="2024-02-01", alias="AZURE_OPENAI_API_VERSION"
    )
    azure_openai_temperature: float = Field(default=0.7, alias="AZURE_OPENAI_TEMPERATURE")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8002, alias="PORT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string to list"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def max_upload_size_bytes(self) -> int:
        """Convert MB to bytes"""
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

