"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables can be set in .env file or system environment.
    """

    # Database
    DATABASE_URL: str = "postgresql://cuasuser:cuaspass@localhost:5432/cuasdb"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production

    # Model config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra env vars
    )


# Global settings instance
settings = Settings()
