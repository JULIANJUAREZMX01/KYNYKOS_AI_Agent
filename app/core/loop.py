"""Main agent loop - processes messages and executes tools"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from app.config import Settings
from app.utils import get_logger
from app.core.context import AgentContext
from app.core.tools import ToolExecutor
from app.cloud.providers import ProviderManager

logger = get_logger(__name__)


class AgentLoop:
    """Main agent loop for processing user messages"""

    def __init__(self, settings: Settings, provider_manager: ProviderManager):
        self.settings = settings
        self.provider_manager = provider_manager
        self.tool_executor = ToolExecutor()

        # Initialize Sentinel with ContractSettings (via settings)
        from app.core.sentinel import LogSentinel
        self.sentinel = LogSentinel(settings)
        self.sentinel_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start background tasks like Sentinel"""
        if self.settings.contract_settings.sentinel_enabled and not self.sentinel_task:
            self.sentinel_task = asyncio.create_task(self.sentinel.run())
            logger.info("AgentLoop: Sentinel started via ContractSettings")

    async def stop(self):
        """Stop background tasks"""
        if self.sentinel_task:
            self.sentinel.stop()
            self.sentinel_task.cancel()
            try:
                await self.sentinel_task
            except asyncio.CancelledError:
                pass
            self.sentinel_task = None
            logger.info("AgentLoop: Sentinel stopped")

    async def process_message(self, ctx: AgentContext) -> str:
        """
        Process user message and generate response
        
        Args:
            ctx: AgentContext with user message
            
        Returns:
            Response text
        """
        try:
            # Get LLM provider
            provider = self.provider_manager.get_provider()
            logger.info(f"Using provider: {provider.__class__.__name__}")

            # Prepare messages for LLM
            messages = await self._format_messages(ctx)

            # Call LLM
            logger.info(f"Calling LLM with {len(messages)} messages")
            llm_response = await provider.call(messages)

            # Parse response
            response_text = llm_response.get("text", "")
            tool_calls = llm_response.get("tool_calls", [])

            # Execute tools if needed
            if tool_calls:
                logger.info(f"Executing {len(tool_calls)} tool calls")
                for tool_call in tool_calls:
                    tool_result = await self.tool_executor.execute(
                        tool_call.get("name", "unknown"),
                        tool_call.get("args", {}),
                        ctx,
                    )
                    ctx.add_message("tool", tool_result, metadata={"tool": tool_call.get("name")})

            # Add assistant response
            ctx.add_message("assistant", response_text)
            logger.info("Message processed successfully")

            return response_text

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            error_msg = f"Disculpa, ocurrió un error: {str(e)[:100]}"
            ctx.add_message("assistant", error_msg, metadata={"error": True})
            return error_msg

    async def _format_messages(self, ctx: AgentContext) -> List[Dict[str, str]]:
        """Format context messages for LLM API"""
        formatted = []

        # Add system prompt
        system_prompt = await self._build_system_prompt(ctx)
        formatted.append({"role": "system", "content": system_prompt})

        # Add conversation history
        for msg in ctx.messages:
            formatted.append({"role": msg.role, "content": msg.content})

        return formatted

    async def _build_system_prompt(self, ctx: AgentContext) -> str:
        """Build system prompt with context from workspace files"""
        
        # Base paths
        workspace_path = Path("./workspace")
        soul_file = workspace_path / "SOUL.md"
        user_file = workspace_path / "USER.md"
        agents_file = workspace_path / "AGENTS.md"
        memory_file = workspace_path / "memory" / "MEMORY.md"

        # Load content with fallbacks
        soul = soul_file.read_text(encoding="utf-8") if soul_file.exists() else "Eres Nanobot, un asistente de IA."
        user = user_file.read_text(encoding="utf-8") if user_file.exists() else f"Usuario: {getattr(ctx, 'user_id', 'Unknown')}"
        agents = agents_file.read_text(encoding="utf-8") if agents_file.exists() else "Operar con eficiencia."
        memory = memory_file.read_text(encoding="utf-8") if memory_file.exists() else ""

        # Build composite prompt
        prompt = f"""
{soul}

---
# CONTEXTO DEL USUARIO
{user}

---
# INSTRUCCIONES DE OPERACIÓN
{agents}

---
# MEMORIA PERSISTENTE RECIENTE
{memory[:2000] if memory else "No hay memoria persistente grabada."}

---
# ESTADO DEL CANAL
Usuario ID: {getattr(ctx, 'user_id', 'N/A')}
Canal: {getattr(ctx, 'channel', 'N/A')}
Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return prompt.strip()

    async def handle_tool_response(self, tool_response: str, ctx: AgentContext) -> str:
        """Handle tool response and generate follow-up"""
        try:
            # Add tool response to context
            ctx.add_message("tool", tool_response)

            # Get provider and call LLM again
            provider = self.provider_manager.get_provider()
            messages = await self._format_messages(ctx)

            llm_response = await provider.call(messages)
            response_text = llm_response.get("text", "")

            ctx.add_message("assistant", response_text)
            return response_text

        except Exception as e:
            logger.error(f"Error handling tool response: {e}")
            return f"Error procesando respuesta de herramienta: {str(e)[:100]}"
