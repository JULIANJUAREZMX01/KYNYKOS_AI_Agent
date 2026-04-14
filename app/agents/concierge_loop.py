"""
KynicOS — ConciergeAgentLoop v2
Motor central. Integra SkillEngine, Personas, tool-calling semántico.

Arquitectura de decisión (sin framework externo):
  1. SkillRouter: detecta intención por keywords → ejecuta skill directamente
  2. MemoryInject: carga memoria relevante antes del LLM
  3. LLM call: con system prompt de la persona activa + docs de skills
  4. ToolParser: extrae comandos del LLM si usa sintaxis de herramientas
  5. AutoMemory: guarda respuestas importantes automáticamente

El agente puede:
  - Ejecutar skills existentes
  - Pedir al SkillEngine que construya nuevos skills
  - Investigar tecnologías antes de implementar
  - Recordar y olvidar (ignorar) información

Filosofía: sin LangChain, sin LangGraph, sin CrewAI.
El nanobot es su propio framework.
"""

import asyncio
import re
from typing import Optional, List, Dict
from pathlib import Path

from app.core.loop import AgentLoop
from app.core.context import AgentContext
from app.cloud.providers import ProviderManager, truncate_messages
from app.concierge.persona import get_persona, Persona, KYNIKOS
from app.config import Settings
from app.utils import get_logger

logger = get_logger(__name__)


# ── Keyword Router ─────────────────────────────────────────────────────────────
# Mapea patrones de mensaje a skills. Sin LLM, sin latencia.
# Formato: (regex_pattern, skill_name, arg_extractor_fn)

def _extract_query(text: str, patterns: List[str]) -> str:
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            try:
                return m.group(1).strip()
            except IndexError:
                pass
    return text

SKILL_ROUTES = [
    # HVAC
    (r"(aire|ac\b|a/c|clima|acondicionado|calor|frío|frío|no enfría|gotea|ruido.*ac)",
     "hvac_triage",
     lambda t: {"message": t}),

    # Transporte MueveCancún
    (r"(autobús|ruta|transporte|cómo llego|cómo ir|taxi|combi|ado|zona hotelera|aeropuerto|playa del carmen|tulum|r1\b|r2\b|r10\b)",
     "mueve_cancun",
     lambda t: {"message": t}),

    # Investigación web
    (r"(?:busca|investiga|googlea|search|encuentra)\s+(.+)",
     "web_research",
     lambda t: {"query": _extract_query(t, [r"(?:busca|investiga|googlea|search|encuentra)\s+(.+)"])}),

    # GitHub
    (r"(?:busca en github|github\s+.{3,}|repo(?:sitorio)?\s+de\s+)(.+)",
     "web_research",
     lambda t: {"query": _extract_query(t, [r"(.+)"]), "source": "github"}),

    # Tendencias
    (r"(?:tendencia|trending|novedades|últimos?\s+(?:30\s+)?días?|qué hay de nuevo en)\s+(.+)",
     "last30days",
     lambda t: {"topic": _extract_query(t, [r"(?:tendencia|trending|novedades|últimos?\s+(?:30\s+)?días?|qué hay de nuevo en)\s+(.+)"])}),

    # Memory
    (r"(?:recuerda|memoriza|guarda(?:\s+en memoria)?)[:\s]+(.+)",
     "memory_manager",
     lambda t: {"action": "remember",
                "key": t[:50],
                "value": _extract_query(t, [r"(?:recuerda|memoriza|guarda)[:\s]+(.+)"])}),

    (r"(?:qué recuerdas|recuerda(?:me)?|busca en memoria|memoria)\s+(?:de|sobre|acerca de)?\s+(.+)",
     "memory_manager",
     lambda t: {"action": "recall",
                "key": _extract_query(t, [r"(?:qué recuerdas|recuerda(?:me)?|busca en memoria|memoria)\s+(?:de|sobre|acerca de)?\s+(.+)"])}),

    # SkillBuilder meta
    (r"(?:construye|crea|build|desarrolla)\s+(?:un\s+)?skill\s+(?:de|para|llamado)?\s+(.+)",
     "skill_builder",
     lambda t: {"action": "build",
                "name": _extract_query(t, [r"(?:construye|crea|build|desarrolla)\s+(?:un\s+)?skill\s+(?:de|para|llamado)?\s+(.+)"]),
                "description": t}),

    (r"(?:lista|muestra|qué|cuales?)\s+(?:son\s+)?(?:mis\s+)?skills?",
     "skill_builder",
     lambda t: {"action": "list"}),
]


# ── Tool-call parser ──────────────────────────────────────────────────────────
# El LLM puede usar sintaxis: [SKILL: nombre_skill(arg=valor)]
TOOL_CALL_RE = re.compile(r"\[SKILL:\s*(\w+)\(([^)]*)\)\]", re.I)

def parse_tool_calls(text: str) -> List[Dict]:
    """Extrae llamadas a skills del output del LLM."""
    calls = []
    for match in TOOL_CALL_RE.finditer(text):
        skill_name = match.group(1)
        args_raw = match.group(2)
        args = {}
        for part in args_raw.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                args[k.strip()] = v.strip().strip('"').strip("'")
        calls.append({"skill": skill_name, "args": args})
    return calls


# ── ConciergeAgentLoop ────────────────────────────────────────────────────────

class ConciergeAgentLoop(AgentLoop):
    """
    Loop principal de KynicOS con:
    - SkillEngine integrado
    - Skill routing semántico (sin LLM para skills detectables)
    - Tool-calling vía sintaxis en texto
    - AutoMemory para respuestas importantes
    - Multi-persona (KYNIKOS, Leo, MueveCancún)
    """

    def __init__(
        self,
        settings: Settings,
        provider_manager: ProviderManager,
        persona: Optional[Persona] = None,
    ):
        super().__init__(settings, provider_manager)
        self.persona = persona or KYNIKOS

        # SkillEngine lazy-loaded
        self._skill_engine = None
        logger.info(f"[ConciergeLoop] Persona: {self.persona.name}")

    @property
    def skill_engine(self):
        if self._skill_engine is None:
            from app.core.skill_engine import SkillEngine
            self._skill_engine = SkillEngine()
        return self._skill_engine

    async def process_message(self, ctx: AgentContext) -> str:
        """Pipeline principal de procesamiento."""
        if not ctx.messages:
            return self.persona.greeting

        last_msg = ctx.messages[-1].content
        user_id = ctx.user_id

        # ── 1. Skill Router (sin LLM) ──────────────────────────────────
        for pattern, skill_name, arg_fn in SKILL_ROUTES:
            if re.search(pattern, last_msg, re.I):
                try:
                    args = arg_fn(last_msg)
                    result = await self.skill_engine.execute(skill_name, args)
                    ctx.add_message("assistant", result)
                    logger.info(f"[Router] {skill_name} → {len(result)} chars")
                    # AutoMemory: guardar si fue una consulta técnica
                    if skill_name in ("web_research", "last30days"):
                        asyncio.create_task(self._auto_remember(last_msg, result))
                    return result
                except Exception as e:
                    logger.warning(f"[Router] {skill_name} error: {e}")
                    # No retornar error — caer al LLM

        # ── 2. LLM con inyección de contexto ──────────────────────────
        return await self._llm_pipeline(ctx)

    async def _llm_pipeline(self, ctx: AgentContext) -> str:
        """Llama al LLM con system prompt enriquecido y parsea tool calls."""

        # Memoria relevante
        memory_context = await self._get_relevant_memory(ctx.messages[-1].content)

        # Construir mensajes
        messages = await self._format_messages(ctx, extra_context=memory_context)

        # Llamar al LLM
        try:
            llm_response = await self.provider_manager.call(messages, max_tokens=2048)
            response_text = llm_response.get("text", "")
        except Exception as e:
            logger.error(f"[LLM] Error: {e}")
            return "⚠️ Error al procesar. Usa /reset si persiste."

        # ── 3. Tool-call parser ────────────────────────────────────────
        tool_calls = parse_tool_calls(response_text)
        if tool_calls:
            results = []
            clean_text = TOOL_CALL_RE.sub("", response_text).strip()
            for tc in tool_calls:
                result = await self.skill_engine.execute(tc["skill"], tc["args"])
                results.append(f"**{tc['skill']}:** {result}")
            final_response = clean_text + ("\n\n" + "\n\n".join(results) if results else "")
        else:
            final_response = response_text

        ctx.add_message("assistant", final_response)
        return final_response

    async def _build_system_prompt(self, ctx: AgentContext) -> str:
        """System prompt de la persona activa + docs de skills."""
        # Prompt base de la persona
        base = self.persona.system_prompt

        # Documentación compacta de skills disponibles
        skill_docs = self.skill_engine.get_skill_docs()

        prompt = f"""{base}

---
## 🛠 Skills Disponibles
Puedes ejecutar skills usando: [SKILL: nombre_skill(arg=valor)]
Ejemplo: [SKILL: web_research(query=fastapi best practices)]

{skill_docs[:2000]}

---
## 📅 Contexto
Usuario: {ctx.user_id} | Canal: {ctx.channel}
Fecha: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')} (Cancún)
"""
        return prompt.strip()

    async def _format_messages(
        self,
        ctx: AgentContext,
        extra_context: str = "",
    ) -> List[Dict[str, str]]:
        """Formatea mensajes con truncado automático."""
        system_prompt = await self._build_system_prompt(ctx)
        if extra_context:
            system_prompt += f"\n\n---\n## 🧠 Memoria Relevante\n{extra_context[:800]}"

        messages = [{"role": "system", "content": system_prompt}]
        for msg in ctx.messages:
            if msg.role in ("user", "assistant"):
                messages.append({"role": msg.role, "content": msg.content})

        # Truncar si es necesario (fix 413)
        return truncate_messages(messages, max_tokens=7000)

    async def _get_relevant_memory(self, query: str) -> str:
        """Busca en memoria persistente si hay algo relevante."""
        try:
            from app.skills.memory_manager import recall
            result = recall(query.split()[0] if query else "")
            if "Sin resultados" not in result and "📭" not in result:
                return result
        except Exception:
            pass
        return ""

    async def _auto_remember(self, query: str, response: str) -> None:
        """Guarda automáticamente resultados de investigaciones importantes."""
        try:
            from app.skills.memory_manager import remember
            key = f"research:{query[:50]}"
            remember(key, response[:300], category="auto")
        except Exception:
            pass

    def switch_persona(self, persona_name: str) -> str:
        """Cambia la persona activa en runtime."""
        new_persona = get_persona(persona_name)
        self.persona = new_persona
        logger.info(f"[ConciergeLoop] Persona → {new_persona.name}")
        return new_persona.greeting
