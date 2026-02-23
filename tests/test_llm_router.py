import pytest
import yaml
from app.services.llm_router import LLMRouter


@pytest.mark.asyncio
async def test_router_selects_ollama_first():
    """Should prioritize Ollama (local, no limits)"""
    router = LLMRouter()
    await router.initialize()

    selected = await router.select_provider()
    assert selected == "ollama"
    assert router.providers["ollama"]["status"] == "available"


@pytest.mark.asyncio
async def test_router_fallback_when_provider_down():
    """Should fall back to next provider if current is unavailable"""
    router = LLMRouter()
    await router.initialize()
    router.providers["ollama"]["status"] = "unavailable"

    selected = await router.select_provider()
    assert selected == "anthropic"


def test_config_loads():
    """Config file should load without errors"""
    with open("app/config/llm_config.yaml") as f:
        config = yaml.safe_load(f)

    assert "llm_providers" in config
    assert "ollama" in config["llm_providers"]
    assert config["llm_providers"]["ollama"]["priority"] == 1
