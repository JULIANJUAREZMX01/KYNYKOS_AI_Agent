"""
KynicOS / KYNYKOS_AI_Agent — Main Entry Point v2
Autárquico, modular, sin dependencias externas obligatorias.

Canales:
  Telegram (primario) — siempre activo si hay TELEGRAM_TOKEN
  WhatsApp Evolution API (opcional, local, open-source)
  WhatsApp Twilio (fallback opcional de pago)

LLM Chain (sin Anthropic/Claude):
  Groq → Together → OpenRouter → Ollama local

Personas:
  PERSONA=kynikos  → SOUL.md (Perro guardián técnico)
  PERSONA=leo      → Concierge ultra-lujo
  PERSONA=mueve    → Guía transporte MueveCancún
  PERSONA=nexus    → Admin/superagente
"""

import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.config import Settings
from app.utils import get_logger
from app.cloud.telegram_bot import start_telegram_bot, stop_telegram_bot
from app.core.memory import Memory
from app.cloud.sessions import SessionManager

logger = get_logger(__name__)

# Globals accesibles desde módulos secundarios
_agent_loop = None
_session_manager = None
settings: Settings = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / Shutdown con arranque resiliente."""
    global _agent_loop, _session_manager, settings

    logger.info("=" * 65)
    logger.info("🐕 KYNIKOS OS v2 — STARTING")
    logger.info("=" * 65)

    settings = Settings()
    persona_name = os.getenv("PERSONA", settings.persona)
    logger.info(f"👤 Persona: {persona_name}")

    # ── Memoria y sesiones ───────────────────────────────────────
    Memory(workspace_path="./workspace")
    _session_manager = SessionManager(data_dir="./data")
    logger.info("✅ Memory + Sessions OK")

    # ── LLM Provider Chain ───────────────────────────────────────
    from app.cloud.providers import ProviderManager
    provider_manager = ProviderManager(settings)

    # ── Agent Loop ───────────────────────────────────────────────
    try:
        from app.agents.concierge_loop import ConciergeAgentLoop
        from app.concierge.persona import get_persona
        persona = get_persona(persona_name)
        _agent_loop = ConciergeAgentLoop(settings, provider_manager, persona=persona)
        logger.info(f"✅ ConciergeAgentLoop ({persona.name}) OK")
    except ImportError as e:
        logger.warning(f"ConciergeLoop no disponible ({e}), usando base AgentLoop")
        from app.core.loop import AgentLoop
        _agent_loop = AgentLoop(settings, provider_manager)

    if hasattr(_agent_loop, "start"):
        await _agent_loop.start()

    # ── WhatsApp (opcional, no bloquea arranque) ──────────────────
    try:
        from app.channels.whatsapp_evolution import init_whatsapp
        init_whatsapp(settings)
        logger.info("✅ WhatsApp Evolution API configurado")
    except Exception as e:
        logger.info(f"⏭️  WhatsApp Evolution omitido: {e}")

    # ── Telegram (primario) ───────────────────────────────────────
    logger.info("📱 Iniciando Telegram bot...")
    telegram_task = asyncio.create_task(start_telegram_bot(settings))

    logger.info("=" * 65)
    logger.info(f"🟢 KYNIKOS OS ACTIVO — Persona: {persona_name.upper()}")
    logger.info("=" * 65)

    yield  # ── App corriendo ──────────────────────────────────────

    # ── Shutdown limpio ──────────────────────────────────────────
    if hasattr(_agent_loop, "stop"):
        await _agent_loop.stop()
    telegram_task.cancel()
    try:
        await telegram_task
    except asyncio.CancelledError:
        pass
    await stop_telegram_bot()
    logger.info("✅ KynicOS shutdown OK")


# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="KynicOS",
    description="Nanobot autárquico. Telegram + WhatsApp + HVAC + MueveCancún.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Archivos estáticos
web_path = Path(__file__).parent.parent / "web"
if web_path.exists():
    app.mount("/static", StaticFiles(directory=str(web_path)), name="static")

# Rutas WhatsApp (Evolution webhook)
try:
    from app.channels.whatsapp_evolution import create_whatsapp_routes
    app.include_router(create_whatsapp_routes(), prefix="/api")
    logger.info("✅ WhatsApp routes registradas")
except Exception as e:
    logger.debug(f"WhatsApp routes omitidas: {e}")

# Dashboard
try:
    from app.cloud.dashboard import create_dashboard_routes
    app.include_router(create_dashboard_routes(), prefix="/api")
except Exception:
    pass


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    dashboard = Path(__file__).parent.parent / "web" / "index.html"
    if dashboard.exists():
        return FileResponse(str(dashboard))
    return JSONResponse({
        "name": "KynicOS",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
    })


@app.get("/api/status")
async def status():
    providers = []
    skills = []
    persona_name = os.getenv("PERSONA", "kynikos")

    if _agent_loop:
        if hasattr(_agent_loop, "provider_manager"):
            providers = [p.name for p in _agent_loop.provider_manager._providers]
        if hasattr(_agent_loop, "persona"):
            persona_name = _agent_loop.persona.name
        if hasattr(_agent_loop, "_skill_engine") and _agent_loop._skill_engine:
            skills = list(_agent_loop._skill_engine._registry.keys())

    return JSONResponse({
        "status": "ok",
        "version": "2.0.0",
        "persona": persona_name,
        "llm_chain": providers,
        "skills": skills,
        "channels": ["telegram", "whatsapp"],
        "architecture": "autarchic — no required external paid APIs",
    })


@app.get("/api/skills")
async def list_skills():
    if _agent_loop and hasattr(_agent_loop, "skill_engine"):
        return JSONResponse({"skills": _agent_loop.skill_engine.list_skills()})
    return JSONResponse({"skills": []})


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    s = Settings()
    uvicorn.run("app.main:app", host=s.host, port=s.port, reload=s.environment == "development")
