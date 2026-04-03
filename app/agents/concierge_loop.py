"""KynicOS — ConciergeAgentLoop con skill routing"""
import asyncio
from typing import Optional, Dict, Any

from app.core.loop import AgentLoop
from app.core.context import AgentContext
from app.cloud.providers import ProviderManager
from app.concierge.persona import get_persona, Persona, KYNIKOS
from app.skills.hvac_triage import detect_hvac_issue, generate_hvac_response, get_ticket_priority
from app.skills.mueve_cancun import is_transport_query, get_route_info, format_route_response, get_generic_transport_response
from app.config import Settings
from app.utils import get_logger

logger = get_logger(__name__)


class ConciergeAgentLoop(AgentLoop):
    """
    Extiende AgentLoop con skill routing:
    HVAC → MueveCancún → LLM
    """
    def __init__(self, settings: Settings, provider_manager: ProviderManager, persona: Optional[Persona] = None):
        super().__init__(settings, provider_manager)
        self.persona = persona or KYNIKOS
        logger.info(f"🏨 ConciergeAgentLoop — Persona: {self.persona.name}")

    async def process_message(self, ctx: AgentContext) -> str:
        if not ctx.messages:
            return self.persona.greeting

        last_message = ctx.messages[-1].content if ctx.messages else ""

        # Skill 1: HVAC Triage
        symptom_key, issue_data = detect_hvac_issue(last_message)
        if symptom_key:
            room = getattr(ctx, 'room_number', 'su habitación')
            response = generate_hvac_response(symptom_key, issue_data, room)
            priority = get_ticket_priority(symptom_key)
            if priority in ("alta", "media"):
                asyncio.create_task(self._escalate_maintenance(ctx, symptom_key, issue_data, priority))
            ctx.add_message("assistant", response)
            return response

        # Skill 2: Transporte MueveCancún
        if is_transport_query(last_message) and self.persona.name in ("Leo", "MueveCancún"):
            route_info = get_route_info(last_message)
            response = format_route_response(route_info) if route_info else get_generic_transport_response()
            ctx.add_message("assistant", response)
            return response

        # LLM con persona
        return await super().process_message(ctx)

    async def _build_system_prompt(self, ctx: AgentContext) -> str:
        return self.persona.system_prompt

    async def _escalate_maintenance(self, ctx, symptom_key, issue_data, priority):
        try:
            room = getattr(ctx, 'room_number', '???')
            msg = (
                f"🔧 *TICKET MANTENIMIENTO*\n"
                f"Prioridad: {'🔴 ALTA' if priority == 'alta' else '🟡 MEDIA'}\n"
                f"Habitación: {room}\n"
                f"Problema: {issue_data.get('descripcion', symptom_key)}\n"
                f"ETA: {issue_data.get('eta_minutos', 30)} min\n"
                f"Diagnóstico: {issue_data['diagnostico'][0]}"
            )
            tech_chat_id = getattr(self.settings, 'tech_telegram_chat_id', None)
            if tech_chat_id and self.settings.telegram_token:
                from telegram import Bot
                bot = Bot(token=self.settings.telegram_token)
                await bot.send_message(chat_id=tech_chat_id, text=msg, parse_mode="Markdown")
                logger.info(f"[HVAC] Escalación enviada a chat {tech_chat_id}")
        except Exception as e:
            logger.error(f"[HVAC] Escalación error: {e}")
