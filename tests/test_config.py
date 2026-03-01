"""Tests for configuration"""

import os
import pytest
from app.config import Settings
from app.config.schema import ContractSettings


def test_settings_from_env():
    """Test settings loading from environment"""
    os.environ["TELEGRAM_TOKEN"] = "test_token"
    os.environ["GROQ_API_KEY"] = "test_groq"
    os.environ["ANTHROPIC_API_KEY"] = "test_anthropic"
    
    settings = Settings()
    assert settings.telegram_token == "test_token"
    assert settings.groq_api_key == "test_groq"
    assert settings.anthropic_api_key == "test_anthropic"


def test_settings_defaults():
    """Test default settings"""
    os.environ["TELEGRAM_TOKEN"] = "token"
    os.environ["GROQ_API_KEY"] = "groq"
    os.environ["ANTHROPIC_API_KEY"] = "anthropic"
    
    settings = Settings()
    assert settings.environment == "development"
    assert settings.port == 8000
    assert settings.host == "0.0.0.0"


def test_contract_settings_defaults():
    """ContractSettings should have expected defaults"""
    contract = ContractSettings()
    assert contract.sentinel_enabled is True
    assert contract.auto_healing_enabled is True
    assert contract.log_check_interval == 5
    assert contract.max_retries == 3
    assert contract.alert_on_failure is True


def test_contract_settings_env_override():
    """ContractSettings should read values from CONTRACT_* env vars"""
    os.environ["CONTRACT_SENTINEL_ENABLED"] = "false"
    os.environ["CONTRACT_LOG_CHECK_INTERVAL"] = "30"
    os.environ["CONTRACT_MAX_RETRIES"] = "5"

    try:
        contract = ContractSettings()
        assert contract.sentinel_enabled is False
        assert contract.log_check_interval == 30
        assert contract.max_retries == 5
    finally:
        del os.environ["CONTRACT_SENTINEL_ENABLED"]
        del os.environ["CONTRACT_LOG_CHECK_INTERVAL"]
        del os.environ["CONTRACT_MAX_RETRIES"]


def test_settings_contract_integration():
    """Settings should expose a ContractSettings instance"""
    os.environ["TELEGRAM_TOKEN"] = "token"
    os.environ["GROQ_API_KEY"] = "groq"
    os.environ["ANTHROPIC_API_KEY"] = "anthropic"

    settings = Settings()
    assert isinstance(settings.contract_settings, ContractSettings)
    assert settings.contract_settings.sentinel_enabled is True
