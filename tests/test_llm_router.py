import asyncio
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


@pytest.mark.asyncio
async def test_stop_cancels_active_task():
    """LLMRouter.stop() should cancel the background reset task and set it to None"""
    router = LLMRouter()

    # Manually create a task for testing
    async def dummy_task():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            pass

    task = asyncio.create_task(dummy_task())
    router._reset_task = task

    assert router._reset_task is not None
    assert not router._reset_task.done()

    router.stop()

    assert router._reset_task is None
    # cancel() schedules cancellation. In some python versions,
    # we may need to check .cancelled() or .cancelling()
    assert task.cancelled() or (hasattr(task, 'cancelling') and task.cancelling() > 0)


@pytest.mark.asyncio
async def test_stop_handles_no_task():
    """LLMRouter.stop() should handle cases where there is no task"""
    router = LLMRouter()
    router._reset_task = None

    # Should not raise any error
    router.stop()
    assert router._reset_task is None


@pytest.mark.asyncio
async def test_stop_handles_already_done_task():
    """LLMRouter.stop() should not set the task to None if it's already done"""
    router = LLMRouter()

    async def dummy_task():
        return True

    task = asyncio.create_task(dummy_task())
    await task # ensure it is done

    router._reset_task = task
    router.stop()

    # Current implementation only clears if not done()
    assert router._reset_task is task
