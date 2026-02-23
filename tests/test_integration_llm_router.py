import pytest
from app.services.llm_router import LLMRouter


@pytest.mark.asyncio
async def test_telegram_bot_routes_through_llm_router():
    """Telegram bot should use router for LLM calls"""
    router = LLMRouter()
    await router.initialize()

    response = await router.call_llm("Hello, test prompt")
    assert response is not None
    assert "Response from" in response


@pytest.mark.asyncio
async def test_get_ai_response_uses_router():
    """get_ai_response helper should delegate to LLMRouter"""
    from app.cloud.telegram_bot import get_ai_response

    response = await get_ai_response("Test message")
    assert response is not None
    assert len(response) > 0
