"""
Core configuration module for ESG Analytics System.
Uses Pydantic Settings for environment variable management.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service metadata
    SERVICE_NAME: str = Field(default="esg-analytics")
    SERVICE_VERSION: str = Field(default="1.0.0")
    GIT_SHA: str = Field(default="unknown")
    ENVIRONMENT: str = Field(default="development")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://esg_user:esg_password@localhost:5432/esg_analytics"
    )
    
    # Security
    ADMIN_API_KEY: str = Field(default="dev-admin-key-change-me")
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production-min-32-chars")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    
    # Feature flags
    ENABLE_XGBOOST: bool = Field(default=True)
    
    # CORS – comma-separated allowed origins
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://localhost:3002,http://127.0.0.1:3000"
    )

    # Paths
    ARTIFACTS_PATH: str = Field(default="./artifacts")
    MODELS_PATH: str = Field(default="./artifacts/models")
    FEATURE_SCHEMAS_PATH: str = Field(default="./artifacts/feature_schemas")
    EVAL_REPORTS_PATH: str = Field(default="./artifacts/eval_reports")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
