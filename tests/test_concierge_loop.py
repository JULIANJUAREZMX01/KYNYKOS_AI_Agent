"""Tests for ConciergeAgentLoop skill routing and performance optimization."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.concierge_loop import ConciergeAgentLoop, SKILL_ROUTES, _extract_query
from app.core.context import AgentContext
from app.config import Settings


@pytest.fixture
def mock_settings():
    return Settings(
        persona="kynikos",
        hotel_name="Test Hotel",
        telegram_token="test_token",
        telegram_user_id="test_user",
        anthropic_api_key="sk-test",
        openai_api_key="sk-test",
        groq_api_key="gsk-test",
    )


@pytest.fixture
def mock_provider_manager():
    manager = MagicMock()
    provider = MagicMock()
    provider.call = AsyncMock(return_value={"text": "LLM response", "tool_calls": []})
    manager.get_provider.return_value = provider
    manager.call = AsyncMock(return_value={"text": "LLM response", "tool_calls": []})
    return manager


@pytest.fixture
def concierge_loop(mock_settings, mock_provider_manager, monkeypatch):
    loop = ConciergeAgentLoop(mock_settings, mock_provider_manager)
    loop._skill_engine = MagicMock()
    loop._skill_engine.execute = AsyncMock(return_value="Skill output executed")
    # Mock auto_remember to avoid writing to workspace/memory/MEMORY.md on disk during tests
    monkeypatch.setattr(loop, "_auto_remember", AsyncMock())
    return loop


def test_skill_routes_precompiled():
    """Verify that all regex patterns in SKILL_ROUTES are pre-compiled Pattern objects."""
    import re
    for pattern, skill_name, arg_fn in SKILL_ROUTES:
        assert isinstance(pattern, re.Pattern), f"Pattern for {skill_name} should be a precompiled Pattern"
        assert callable(arg_fn), f"Argument extractor for {skill_name} should be callable"


def test_extract_query_helper():
    """Verify _extract_query works with both strings and compiled regexes."""
    import re
    compiled = re.compile(r"busca\s+(.+)", re.I)
    assert _extract_query("busca restaurantes en cancun", [compiled]) == "restaurantes en cancun"
    assert _extract_query("busca hoteles", [r"busca\s+(.+)"]) == "hoteles"
    assert _extract_query("nada que ver", [compiled]) == "nada que ver"


@pytest.mark.asyncio
async def test_route_hvac_triage(concierge_loop):
    ctx = AgentContext(session_id="s1", user_id="u1", channel="test")
    ctx.add_message("user", "El aire acondicionado no enfría en mi habitación")
    res = await concierge_loop.process_message(ctx)

    assert res == "Skill output executed"
    concierge_loop.skill_engine.execute.assert_awaited_once_with(
        "hvac_triage", {"message": "El aire acondicionado no enfría en mi habitación"}
    )


@pytest.mark.asyncio
async def test_route_mueve_cancun(concierge_loop):
    ctx = AgentContext(session_id="s2", user_id="u1", channel="test")
    ctx.add_message("user", "¿Cómo llego al aeropuerto desde la zona hotelera?")
    res = await concierge_loop.process_message(ctx)

    assert res == "Skill output executed"
    concierge_loop.skill_engine.execute.assert_awaited_once_with(
        "mueve_cancun", {"message": "¿Cómo llego al aeropuerto desde la zona hotelera?"}
    )


@pytest.mark.asyncio
async def test_route_web_research(concierge_loop):
    ctx = AgentContext(session_id="s3", user_id="u1", channel="test")
    ctx.add_message("user", "investiga fastapi best practices")
    res = await concierge_loop.process_message(ctx)

    assert res == "Skill output executed"
    concierge_loop.skill_engine.execute.assert_awaited_once_with(
        "web_research", {"query": "fastapi best practices"}
    )


@pytest.mark.asyncio
async def test_route_last30days(concierge_loop):
    ctx = AgentContext(session_id="s4", user_id="u1", channel="test")
    ctx.add_message("user", "tendencia python 3.12")
    res = await concierge_loop.process_message(ctx)

    assert res == "Skill output executed"
    concierge_loop.skill_engine.execute.assert_awaited_once_with(
        "last30days", {"topic": "python 3.12"}
    )


@pytest.mark.asyncio
async def test_route_memory_remember(concierge_loop):
    ctx = AgentContext(session_id="s5", user_id="u1", channel="test")
    ctx.add_message("user", "recuerda: el huésped prefiere almohadas de pluma")
    res = await concierge_loop.process_message(ctx)

    assert res == "Skill output executed"
    args = concierge_loop.skill_engine.execute.call_args[0][1]
    assert args["action"] == "remember"
    assert "almohadas de pluma" in args["value"]


@pytest.mark.asyncio
async def test_route_skill_builder_list(concierge_loop):
    ctx = AgentContext(session_id="s6", user_id="u1", channel="test")
    ctx.add_message("user", "muestra mis skills")
    res = await concierge_loop.process_message(ctx)

    assert res == "Skill output executed"
    concierge_loop.skill_engine.execute.assert_awaited_once_with(
        "skill_builder", {"action": "list"}
    )


@pytest.mark.asyncio
async def test_unmatched_falls_back_to_llm(concierge_loop):
    ctx = AgentContext(session_id="s7", user_id="u1", channel="test")
    ctx.add_message("user", "Hola, buenas tardes, me gustaría información general")
    res = await concierge_loop.process_message(ctx)

    assert res == "LLM response"
    concierge_loop.skill_engine.execute.assert_not_called()
