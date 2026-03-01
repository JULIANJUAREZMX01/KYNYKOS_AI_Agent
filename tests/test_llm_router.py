import pytest
import yaml
from app.services.llm_router import LLMRouter


@pytest.mark.asyncio
async def test_router_selects_anthropic_first():
    """Should prioritize external providers — Anthropic is first in priority order"""
    router = LLMRouter()
    await router.initialize()

    selected = await router.select_provider()
    assert selected == "anthropic"
    assert router.providers["anthropic"]["status"] == "available"


@pytest.mark.asyncio
async def test_router_fallback_to_ollama_when_external_providers_down():
    """Should fall back to Ollama when all external providers are unavailable"""
    router = LLMRouter()
    await router.initialize()
    router.providers["anthropic"]["status"] = "unavailable"
    router.providers["groq"]["status"] = "unavailable"
    router.providers["openai"]["status"] = "unavailable"

    selected = await router.select_provider()
    assert selected == "ollama"


def test_config_loads():
    """Config file should load without errors"""
    with open("app/config/llm_config.yaml") as f:
        config = yaml.safe_load(f)

    assert "llm_providers" in config
    assert "ollama" in config["llm_providers"]
    assert config["llm_providers"]["ollama"]["priority"] == 1
