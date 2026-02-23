"""Tests for the WhatsApp Bridge (Twilio integration)"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.config import Settings
from app.cloud.whatsapp_bridge import (
    create_whatsapp_routes,
    init_whatsapp_bridge,
    send_whatsapp_alert,
    _send_whatsapp_reply,
)


@pytest.fixture
def settings_no_twilio():
    """Settings without Twilio credentials"""
    return Settings(
        telegram_token="test_token",
        groq_api_key="test_groq",
        anthropic_api_key="test_anthropic",
        environment="test",
    )


@pytest.fixture
def settings_with_twilio():
    """Settings with Twilio credentials"""
    return Settings(
        telegram_token="test_token",
        groq_api_key="test_groq",
        anthropic_api_key="test_anthropic",
        environment="test",
        twilio_account_sid="ACtest000",
        twilio_auth_token="authtest000",
        twilio_whatsapp_from="+14155238886",
        twilio_whatsapp_to="+521xxxxxxxxxx",
    )


# ---------------------------------------------------------------------------
# init_whatsapp_bridge
# ---------------------------------------------------------------------------


def test_init_whatsapp_bridge_no_credentials(settings_no_twilio):
    """Bridge should log a warning but not raise when credentials are missing"""
    import app.cloud.whatsapp_bridge as bridge_module

    bridge_module._twilio_client = None  # reset global state
    init_whatsapp_bridge(settings_no_twilio)
    assert bridge_module._twilio_client is None


def test_init_whatsapp_bridge_with_credentials(settings_with_twilio):
    """Bridge should create a Twilio client when credentials are present"""
    import app.cloud.whatsapp_bridge as bridge_module

    with patch("app.cloud.whatsapp_bridge.Client") as MockClient:
        init_whatsapp_bridge(settings_with_twilio)
        MockClient.assert_called_once_with("ACtest000", "authtest000")
        assert bridge_module._twilio_client is not None


# ---------------------------------------------------------------------------
# send_whatsapp_alert
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_whatsapp_alert_no_client(settings_with_twilio):
    """Alert should return False when the client is not initialised"""
    import app.cloud.whatsapp_bridge as bridge_module

    bridge_module._twilio_client = None
    result = await send_whatsapp_alert("Test alert", settings_with_twilio)
    assert result is False


@pytest.mark.asyncio
async def test_send_whatsapp_alert_success(settings_with_twilio):
    """Alert should return True when Twilio call succeeds"""
    import app.cloud.whatsapp_bridge as bridge_module

    mock_client = MagicMock()
    bridge_module._twilio_client = mock_client
    bridge_module._settings = settings_with_twilio

    result = await send_whatsapp_alert("Test alert", settings_with_twilio)

    assert result is True
    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args[1]
    assert call_kwargs["to"] == "whatsapp:+521xxxxxxxxxx"
    assert "Test alert" in call_kwargs["body"]


@pytest.mark.asyncio
async def test_send_whatsapp_alert_error(settings_with_twilio):
    """Alert should return False when Twilio raises an exception"""
    import app.cloud.whatsapp_bridge as bridge_module

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("Twilio error")
    bridge_module._twilio_client = mock_client
    bridge_module._settings = settings_with_twilio

    result = await send_whatsapp_alert("Test alert", settings_with_twilio)
    assert result is False


# ---------------------------------------------------------------------------
# _send_whatsapp_reply
# ---------------------------------------------------------------------------


def test_send_whatsapp_reply_no_client(settings_with_twilio):
    """Reply should silently skip when no client is available"""
    import app.cloud.whatsapp_bridge as bridge_module

    bridge_module._twilio_client = None
    # Should not raise
    _send_whatsapp_reply("+521xxxxxxxxxx", "Hello")


def test_send_whatsapp_reply_long_message(settings_with_twilio):
    """Long messages should be split into 1600-char chunks"""
    import app.cloud.whatsapp_bridge as bridge_module

    mock_client = MagicMock()
    bridge_module._twilio_client = mock_client
    bridge_module._settings = settings_with_twilio

    long_text = "A" * 3300  # Exceeds 1600-char Twilio limit
    _send_whatsapp_reply("+521xxxxxxxxxx", long_text)

    # Should have sent 3 chunks: 1600, 1600 and 100 characters
    # (slices [0:1600], [1600:3200], [3200:3300] for a 3300-char message)
    assert mock_client.messages.create.call_count == 3
# ---------------------------------------------------------------------------
# create_whatsapp_routes
# ---------------------------------------------------------------------------


def test_create_whatsapp_routes_returns_router():
    """create_whatsapp_routes should return an APIRouter"""
    from fastapi import APIRouter

    router = create_whatsapp_routes()
    assert isinstance(router, APIRouter)


def test_whatsapp_webhook_route_exists():
    """The /webhook/whatsapp POST route should be registered"""
    router = create_whatsapp_routes()
    routes = [r.path for r in router.routes]
    assert "/webhook/whatsapp" in routes
