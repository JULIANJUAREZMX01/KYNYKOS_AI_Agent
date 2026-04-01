"""Tests for Settings validation and configuration loading"""

import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict
from app.config import Settings

@pytest.fixture
def clean_env(monkeypatch):
    """Ensure required environment variables are not set"""
    for var in ["TELEGRAM_TOKEN", "GROQ_API_KEY", "ANTHROPIC_API_KEY"]:
        monkeypatch.delenv(var, raising=False)

def test_settings_missing_required_fields(clean_env):
    """Test that Settings raises ValidationError when required fields are missing"""
    # Overriding model_config to ignore .env files during test
    class TestSettings(Settings):
        model_config = SettingsConfigDict(env_file=None)

    with pytest.raises(ValidationError):
        TestSettings()

def test_settings_with_required_fields(monkeypatch):
    """Test that Settings initializes correctly with required fields provided"""
    monkeypatch.setenv("TELEGRAM_TOKEN", "test-token")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")

    # Overriding model_config to ignore .env files during test
    class TestSettings(Settings):
        model_config = SettingsConfigDict(env_file=None)

    settings = TestSettings()
    assert settings.telegram_token == "test-token"
    assert settings.groq_api_key == "test-groq-key"
    assert settings.anthropic_api_key == "test-anthropic-key"

def test_settings_partial_missing_fields(monkeypatch, clean_env):
    """Test that Settings raises ValidationError when only some required fields are provided"""
    monkeypatch.setenv("TELEGRAM_TOKEN", "test-token")

    # Overriding model_config to ignore .env files during test
    class TestSettings(Settings):
        model_config = SettingsConfigDict(env_file=None)

    with pytest.raises(ValidationError):
        TestSettings()
