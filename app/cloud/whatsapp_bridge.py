"""WhatsApp bridge integration via Twilio for Nanobot"""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Form, Request, Response
from twilio.rest import Client
from twilio.request_validator import RequestValidator

from app.config import Settings
from app.core.context import AgentContext
from app.utils import get_logger

logger = get_logger(__name__)

_twilio_client: Optional[Client] = None
_settings: Optional[Settings] = None


def init_whatsapp_bridge(settings: Settings) -> None:
    """Initialize the Twilio client for WhatsApp"""
    global _twilio_client, _settings
    _settings = settings

    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        logger.warning("⚠️  Twilio credentials not configured — WhatsApp bridge disabled")
        return

    _twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    logger.info("✅ WhatsApp bridge (Twilio) initialized")


def create_whatsapp_routes() -> APIRouter:
    """Return an APIRouter with the Twilio WhatsApp webhook endpoint"""
    router = APIRouter()

    @router.post("/webhook/whatsapp")
    async def whatsapp_webhook(
        request: Request,
        From: str = Form(...),
        Body: str = Form(""),
        MediaUrl0: Optional[str] = Form(None),
        MediaContentType0: Optional[str] = Form(None),
        NumMedia: int = Form(0),
    ) -> Response:
        """Handle incoming WhatsApp messages from Twilio"""
        # Reject requests when Twilio credentials are not configured
        if not _settings or not _settings.twilio_auth_token:
            logger.warning("Twilio WhatsApp webhook called but credentials are not configured — request rejected")
            return Response(content="Service unavailable", status_code=503)

        # Validate Twilio signature when auth token is available
        validator = RequestValidator(_settings.twilio_auth_token)
        signature = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        form_data = dict(await request.form())
        if not validator.validate(url, form_data, signature):
            logger.warning("Invalid Twilio signature — request rejected")
            return Response(content="Forbidden", status_code=403)

        # Strip "whatsapp:" prefix added by Twilio
        user_phone = From.replace("whatsapp:", "")
        logger.info(f"WhatsApp message from {user_phone}: {Body[:60]}...")

        response_text = await _process_with_agent(user_phone, Body, MediaUrl0)
        _send_whatsapp_reply(user_phone, response_text)

        # Return empty TwiML so Twilio doesn't attempt its own reply
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml",
        )

    return router


async def send_whatsapp_alert(message_text: str, settings: Settings) -> bool:
    """Send a proactive WhatsApp alert to the configured phone number"""
    global _twilio_client
    if not _twilio_client or not settings.twilio_whatsapp_from or not settings.twilio_whatsapp_to:
        return False

    try:
        _twilio_client.messages.create(
            from_=f"whatsapp:{settings.twilio_whatsapp_from}",
            to=f"whatsapp:{settings.twilio_whatsapp_to}",
            body=f"🐕 *CENTINELA KYNIKOS ALERT*:\n\n{message_text}",
        )
        return True
    except Exception as e:
        logger.error(f"Error sending WhatsApp alert: {e}")
        return False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _send_whatsapp_reply(to_phone: str, text: str) -> None:
    """Send a WhatsApp reply via Twilio REST API"""
    if not _twilio_client or not _settings or not _settings.twilio_whatsapp_from:
        logger.warning("Twilio client not ready — cannot send WhatsApp reply")
        return

    # Twilio message body max is 1600 chars; split if needed
    max_len = 1600
    chunks = [text[i : i + max_len] for i in range(0, len(text), max_len)]

    for chunk in chunks:
        try:
            _twilio_client.messages.create(
                from_=f"whatsapp:{_settings.twilio_whatsapp_from}",
                to=f"whatsapp:{to_phone}",
                body=chunk,
            )
        except Exception as e:
            logger.error(f"Error sending WhatsApp message to {to_phone}: {e}")


async def _process_with_agent(user_phone: str, text: str, media_url: Optional[str]) -> str:
    """Process an incoming WhatsApp message through the agent loop"""
    try:
        from app.main import _agent_loop, _session_manager

        if not _agent_loop:
            return "❌ Agent loop no iniciado"

        session_id = f"whatsapp_{user_phone}"
        ctx = await _session_manager.load_session(session_id)
        if not ctx:
            ctx = AgentContext(
                session_id=session_id,
                user_id=user_phone,
                channel="whatsapp",
            )

        # If a media attachment was received, note it in the message
        if media_url:
            text = f"{text}\n[Adjunto: {media_url}]".strip()

        ctx.add_message("user", text)
        response = await _agent_loop.process_message(ctx)
        await _session_manager.save_session(ctx)
        return response

    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {e}", exc_info=True)
        return f"❌ Error: {str(e)[:120]}"
