"""Tests for configuration"""

import os
import pytest
from app.config import Settings
from app.config.schema import ContractSettings


def test_settings_from_env():
    """Test settings loading from environment"""
    os.environ["TELEGRAM_TOKEN"] = "test_token"
    os.environ["GROQ_API_KEY"] = "test_groq"
    os.environ["TOGETHER_API_KEY"] = "test_together"
    
    settings = Settings()
    assert settings.telegram_token == "test_token"
    assert settings.groq_api_key == "test_groq"
    assert settings.together_api_key == "test_together"


def test_settings_defaults():
    """Test default settings"""
    os.environ["TELEGRAM_TOKEN"] = "token"
    os.environ["GROQ_API_KEY"] = "groq"
    
    settings = Settings()
    assert settings.environment == "production"
    assert settings.port == 8000
    assert settings.host == "0.0.0.0"


def test_contract_settings_defaults():
    """ContractSettings should have expected defaults"""
    contract = ContractSettings()
    assert contract.sentinel_enabled is False


def test_contract_settings_env_override():
    """ContractSettings should read values from SENTINEL_* env vars (env_prefix)"""
    os.environ["SENTINEL_SENTINEL_ENABLED"] = "true"

    try:
        contract = ContractSettings()
        assert contract.sentinel_enabled is True
    finally:
        del os.environ["SENTINEL_SENTINEL_ENABLED"]


def test_settings_contract_integration():
    """Settings should expose a ContractSettings instance"""
    os.environ["TELEGRAM_TOKEN"] = "token"
    os.environ["GROQ_API_KEY"] = "groq"

    settings = Settings()
    assert isinstance(settings.contract_settings, ContractSettings)
    assert settings.contract_settings.sentinel_enabled is False

def test_telegram_drop_pending_updates_default():
    """telegram_drop_pending_updates should default to True"""
    os.environ["TELEGRAM_TOKEN"] = "token"
    os.environ["GROQ_API_KEY"] = "groq"

    settings = Settings()
    assert settings.telegram_drop_pending_updates is True

def test_telegram_drop_pending_updates_override():
    """telegram_drop_pending_updates should be overridable by env var"""
    os.environ["TELEGRAM_TOKEN"] = "token"
    os.environ["GROQ_API_KEY"] = "groq"
    os.environ["TELEGRAM_DROP_PENDING_UPDATES"] = "false"

    try:
        settings = Settings()
        assert settings.telegram_drop_pending_updates is False
    finally:
        del os.environ["TELEGRAM_DROP_PENDING_UPDATES"]
