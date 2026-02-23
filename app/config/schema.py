"""Pydantic models for configuration"""

import yaml
from pathlib import Path
from pydantic import Field, ConfigDict
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
    
    # Twilio WhatsApp Bridge
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_from: Optional[str] = None  # e.g. +14155238886 (Twilio sandbox number)
    twilio_whatsapp_to: Optional[str] = None    # e.g. +521XXXXXXXXXX (owner's number for alerts)

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
    
    # LLM Router
    llm_config_path: str = Field(
        default="app/config/llm_config.yaml",
        validation_alias="LLM_CONFIG_PATH"
    )

    # App
    environment: str = "development"
    log_level: str = "INFO"
    port: int = 8000
    host: str = "0.0.0.0"

    @property
    def llm_providers(self):
        """Load LLM provider config"""
        config_path = Path(self.llm_config_path)
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f).get("llm_providers", {})
        return {}

    model_config = ConfigDict(env_file=".env", case_sensitive=False, extra="ignore")
