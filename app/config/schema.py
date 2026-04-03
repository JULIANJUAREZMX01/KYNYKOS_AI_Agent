"""KynicOS / KYNYKOS — Pydantic Settings"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
import json


class ContractSettings(BaseSettings):
    """Settings for Sentinel and contract monitoring"""
    sentinel_enabled: bool = False

    class Config:
        env_prefix = "SENTINEL_"
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Todos los campos son opcionales excepto TELEGRAM_TOKEN y GROQ_API_KEY.
    """

    # ── Identidad ─────────────────────────────────────────────
    persona: str = "kynikos"  # kynikos | leo | nexus | mueve

    # ── Hotel Config (modo LEO/concierge) ──────────────────────
    hotel_name: str = "KynicOS Hotel"
    hotel_location: str = "Cancún, México"
    hotel_currency: str = "USD"
    hotel_timezone: str = "America/Mexico_City"

    # ── Telegram ──────────────────────────────────────────────
    telegram_token: str
    telegram_user_id: str = "8247886073"
    # Chat ID del técnico de mantenimiento (escalación HVAC)
    tech_telegram_chat_id: Optional[str] = None

    # ── LLM — Groq (PRIMARIO, gratuito) ───────────────────────
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    # ── LLM — Together AI (FALLBACK gratuito) ─────────────────
    # Regístrate en https://api.together.xyz — $25 créditos gratis
    together_api_key: Optional[str] = None

    # ── LLM — OpenRouter (FALLBACK modelos públicos) ──────────
    # Regístrate en https://openrouter.ai — modelos gratis disponibles
    openrouter_api_key: Optional[str] = None

    # ── LLM — Ollama local (sin costo, sin límites) ───────────
    # Configura OLLAMA_URL=http://localhost:11434 si tienes Ollama
    ollama_url: Optional[str] = None
    ollama_model: str = "llama3"

    # ── OpenAI (solo para Whisper STT) ────────────────────────
    openai_api_key: Optional[str] = None

    # ── WhatsApp (Twilio) ─────────────────────────────────────
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_from: str = "+14155238886"
    twilio_whatsapp_to: Optional[str] = None

    # ── Stripe Connect (Fase 2 — pagos) ───────────────────────
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_hotel_account_id: Optional[str] = None
    stripe_nexus_account_id: Optional[str] = None
    stripe_commission_percentage: int = 5

    # ── Base de Datos (Fase 2) ────────────────────────────────
    database_url: Optional[str] = None
    redis_url: Optional[str] = None

    # ── AWS S3 (backups opcionales) ───────────────────────────
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket: Optional[str] = None

    # ── App ───────────────────────────────────────────────────
    environment: str = "production"
    log_level: str = "INFO"
    port: int = 8000
    host: str = "0.0.0.0"

    # ── Sentinel (sub-settings) ───────────────────────────────
    @property
    def contract_settings(self) -> ContractSettings:
        return ContractSettings()

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
