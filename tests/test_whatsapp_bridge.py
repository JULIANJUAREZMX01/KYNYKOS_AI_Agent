"""Tests for the WhatsApp Bridge (Twilio integration)"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.config import Settings
from app.cloud.whatsapp_bridge import (
    _chunk_message,
    create_whatsapp_routes,
    init_whatsapp_bridge,
    send_whatsapp_alert,
    _send_whatsapp_reply,
)


@pytest.fixture(autouse=True)
def reset_bridge_state():
    """Restore global bridge state after every test to prevent test pollution."""
    import app.cloud.whatsapp_bridge as bridge_module

    original_client = bridge_module._twilio_client
    original_settings = bridge_module._settings
    yield
    bridge_module._twilio_client = original_client
    bridge_module._settings = original_settings


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

    init_whatsapp_bridge(settings_no_twilio)
    assert bridge_module._twilio_client is None


def test_init_whatsapp_bridge_with_credentials(settings_with_twilio):
    """Bridge should create a Twilio client when credentials are present"""
    import app.cloud.whatsapp_bridge as bridge_module

    with patch("app.cloud.whatsapp_bridge.Client") as MockClient:
        init_whatsapp_bridge(settings_with_twilio)
        MockClient.assert_called_once_with("ACtest000", "authtest000")
        assert bridge_module._twilio_client is MockClient.return_value


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


def test_send_whatsapp_reply_no_client():
    """Reply should silently skip when no client is available"""
    import app.cloud.whatsapp_bridge as bridge_module

    bridge_module._twilio_client = None
    # Should not raise
    _send_whatsapp_reply("+521xxxxxxxxxx", "Hello")


def test_send_whatsapp_reply_long_message(settings_with_twilio):
    """Long messages should be split into chunks with indicators"""
    import app.cloud.whatsapp_bridge as bridge_module

    mock_client = MagicMock()
    bridge_module._twilio_client = mock_client
    bridge_module._settings = settings_with_twilio

    # 3300 chars → more than one 1600-char chunk
    long_text = "A" * 3300
    _send_whatsapp_reply("+521xxxxxxxxxx", long_text)

    # At least 2 API calls for a message spanning multiple chunks
    assert mock_client.messages.create.call_count >= 2


# ---------------------------------------------------------------------------
# _chunk_message
# ---------------------------------------------------------------------------


def test_chunk_message_short_text():
    """Text within max_len should be returned as a single chunk without indicator"""
    chunks = _chunk_message("Hello", 1600)
    assert chunks == ["Hello"]


def test_chunk_message_multi_chunk():
    """Text exceeding max_len should be split and include (n/total) indicators"""
    # 3300 chars with max_len=1600
    chunks = _chunk_message("A" * 3300, 1600)
    assert len(chunks) >= 2
    # Each chunk except possibly the last should end with a "(n/total)" indicator
    for chunk in chunks:
        assert "(" in chunk and "/" in chunk


def test_chunk_message_indicators_ordered():
    """Chunk indicators should be sequential"""
    chunks = _chunk_message("B" * 3300, 1600)
    for idx, chunk in enumerate(chunks, start=1):
        assert f"({idx}/{len(chunks)})" in chunk


# ---------------------------------------------------------------------------
# create_whatsapp_routes / webhook endpoint
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


def test_webhook_returns_503_when_unconfigured():
    """Webhook should return 503 when Twilio credentials are not configured"""
    import app.cloud.whatsapp_bridge as bridge_module
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    # Ensure bridge is not configured
    bridge_module._settings = None

    test_app = FastAPI()
    test_app.include_router(create_whatsapp_routes())
    client = TestClient(test_app, raise_server_exceptions=False)

    resp = client.post(
        "/webhook/whatsapp",
        data={"From": "whatsapp:+521xxxxxxxxxx", "Body": "Hola"},
    )
    assert resp.status_code == 503


def test_webhook_returns_403_on_invalid_signature(settings_with_twilio):
    """Webhook should return 403 when Twilio signature is invalid"""
    import app.cloud.whatsapp_bridge as bridge_module
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    bridge_module._settings = settings_with_twilio

    test_app = FastAPI()
    test_app.include_router(create_whatsapp_routes())
    client = TestClient(test_app, raise_server_exceptions=False)

    # No X-Twilio-Signature header → validation will fail
    resp = client.post(
        "/webhook/whatsapp",
        data={"From": "whatsapp:+521xxxxxxxxxx", "Body": "Hola"},
    )
    assert resp.status_code == 403


def test_webhook_returns_xml_on_valid_signature(settings_with_twilio):
    """Webhook should return TwiML XML when signature is valid"""
    import app.cloud.whatsapp_bridge as bridge_module
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from twilio.request_validator import RequestValidator

    bridge_module._settings = settings_with_twilio
    mock_client = MagicMock()
    bridge_module._twilio_client = mock_client

    test_app = FastAPI()
    test_app.include_router(create_whatsapp_routes())
    test_client = TestClient(test_app, raise_server_exceptions=False)

    # Build a valid Twilio signature for the test request
    form_data = {"From": "whatsapp:+521xxxxxxxxxx", "Body": "Hola"}
    url = "http://testserver/webhook/whatsapp"
    validator = RequestValidator(settings_with_twilio.twilio_auth_token)
    signature = validator.compute_signature(url, form_data)

    with patch(
        "app.cloud.whatsapp_bridge._process_with_agent",
        new=AsyncMock(return_value="Respuesta de prueba"),
    ):
        resp = test_client.post(
            "/webhook/whatsapp",
            data=form_data,
            headers={"X-Twilio-Signature": signature},
        )

    assert resp.status_code == 200
    assert "application/xml" in resp.headers["content-type"]
    assert "<Response>" in resp.text

