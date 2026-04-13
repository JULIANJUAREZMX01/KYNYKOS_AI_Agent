"""Tests for LLM providers"""

import pytest
from app.cloud.providers import ProviderManager


@pytest.fixture
def provider_manager():
    """Create provider manager with test settings"""
    from app.config import Settings
    import os
    
    # Use environment variables
    settings = Settings()
    return ProviderManager(settings)


def test_provider_manager_initialization(provider_manager):
    """Test provider manager initialization"""
    assert provider_manager is not None
    # At least one provider should be available
    assert (provider_manager.groq_provider is not None or
            provider_manager.anthropic_provider is not None)


def test_groq_provider_groq(provider_manager):
    """Test Groq provider initialization"""
    # Groq should be primary
    if provider_manager.groq_provider:
        assert provider_manager.groq_provider.__class__.__name__ == "GroqProvider"


def test_anthropic_provider_anthropic(provider_manager):
    """Test Anthropic provider initialization"""
    # Anthropic should be fallback
    if provider_manager.anthropic_provider:
        assert provider_manager.anthropic_provider.__class__.__name__ == "AnthropicProvider"
