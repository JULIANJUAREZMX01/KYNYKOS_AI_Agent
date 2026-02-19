"""Pydantic models for configuration"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Telegram
    telegram_token: str
    telegram_user_id: str = "8247886073"
    
    # LLM Providers
    groq_api_key: str
    anthropic_api_key: str
    gemini_api_key: Optional[str] = None
    gemini_googleai_studio_api_key: Optional[str] = None
    
    # Cloud Services
    render_api_key: Optional[str] = None
    jules_api_key: Optional[str] = None
    desktop_commander_api_key: Optional[str] = None
    
    # AWS S3
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket: Optional[str] = None
    
    # Database
    db2_connection_string: Optional[str] = None
    
    # App
    environment: str = "development"
    log_level: str = "INFO"
    port: int = 8000
    host: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
