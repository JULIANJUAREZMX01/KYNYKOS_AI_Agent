"""Tests for agent loop and LLM integration"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.loop import AgentLoop
from app.core.context import AgentContext
from app.config import Settings


@pytest.fixture
def settings():
    """Test settings"""
    return Settings(
        telegram_token="test_token",
        telegram_user_id="test_user",
        groq_api_key="test_groq",
        anthropic_api_key="test_anthropic"
    )


@pytest.fixture
def agent_loop(settings):
    """Agent loop instance"""
    from app.cloud.providers import ProviderManager
    mock_provider = MagicMock(spec=ProviderManager)
    return AgentLoop(settings, mock_provider)


@pytest.fixture
def agent_context():
    """Agent context"""
    ctx = AgentContext(
        session_id="test_session",
        user_id="test_user",
        channel="test"
    )
    ctx.add_message("user", "Hello, how are you?")
    return ctx


@pytest.mark.asyncio
async def test_agent_loop_basic(agent_loop, agent_context):
    """Test basic agent loop processing"""
    # Mock the LLM call inside the provider manager
    agent_loop.provider_manager.get_provider.return_value.call = AsyncMock(return_value={
        "text": "I'm doing well, thanks for asking!",
        "tool_calls": []
    })

    # Process message
    response = await agent_loop.process_message(agent_context)

    # Verify response
    assert response == "I'm doing well, thanks for asking!"
    assert len(agent_context.messages) == 2
    assert agent_context.messages[-1].role == "assistant"


@pytest.mark.asyncio
async def test_agent_context_messages(agent_context):
    """Test agent context message handling"""
    assert len(agent_context.messages) == 1
    assert agent_context.messages[0].role == "user"
    assert agent_context.messages[0].content == "Hello, how are you?"

    # Add assistant message
    agent_context.add_message("assistant", "Hi there!")
    assert len(agent_context.messages) == 2


def test_agent_context_to_dict(agent_context):
    """Test converting context to dictionary"""
    ctx_dict = agent_context.to_dict()

    assert ctx_dict["session_id"] == "test_session"
    assert ctx_dict["user_id"] == "test_user"
    assert ctx_dict["channel"] == "test"
    assert len(ctx_dict["messages"]) == 1
