"""
KynicOS / KYNYKOS_AI_Agent — Main Entry Point
Monorepo unificado: nanobot-cloud + KYNYKOS + skills propios

Personas:
  PERSONA=kynikos  → Perro guardián técnico de Julián (default, SOUL.md)
  PERSONA=leo      → Concierge de lujo para turistas (MVP Nexus Pilot)
  PERSONA=mueve    → Guía de transporte MueveCancún
  PERSONA=nexus    → Superagente admin

Deploy en Render: https://nanobot-cloud-zjr0.onrender.com
Service ID: srv-d6b9sihr0fns739m446g
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
from app.cloud.backup_service import BackupService
from app.core.memory import Memory
from app.cloud.sessions import SessionManager

logger = get_logger(__name__)

# Globals accesibles desde otros módulos (telegram_bot, etc.)
_agent_loop = None
_session_manager = None
settings: Settings = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / Shutdown"""
    global _agent_loop, _session_manager, settings

    logger.info("=" * 65)
    logger.info("🐕 KYNIKOS OS — STARTING")
    logger.info("=" * 65)

    settings = Settings()

    # Determinar persona activa
    persona_name = os.getenv("PERSONA", "kynikos")
    logger.info(f"👤 Persona configurada: {persona_name}")

    try:
        # Memoria y sesiones
        Memory(workspace_path="./workspace")
        _session_manager = SessionManager(data_dir="./data")
        logger.info("✅ Memory + Sessions OK")

        # LLM Provider chain (Groq → Together → OpenRouter, SIN Anthropic)
        from app.cloud.providers import ProviderManager
        provider_manager = ProviderManager(settings)

        # Agent Loop con skills de concierge
        try:
            from app.agents.concierge_loop import ConciergeAgentLoop
            from app.concierge.persona import get_persona
            persona = get_persona(persona_name)
            _agent_loop = ConciergeAgentLoop(settings, provider_manager, persona=persona)
            logger.info(f"✅ ConciergeAgentLoop ({persona.name}) OK")
        except ImportError:
            # Fallback al AgentLoop base si los módulos de concierge no están aún
            from app.core.loop import AgentLoop
            _agent_loop = AgentLoop(settings, provider_manager)
            logger.info("✅ AgentLoop base OK (concierge skills no disponibles)")

        # Iniciar tareas de background del agent loop (Sentinel, etc.)
        if hasattr(_agent_loop, 'start'):
            await _agent_loop.start()

        # WhatsApp bridge (Twilio) — opcional
        if settings.twilio_account_sid and settings.twilio_auth_token:
            try:
                from app.cloud.whatsapp_bridge import init_whatsapp_bridge
                init_whatsapp_bridge(settings)
                logger.info("✅ WhatsApp bridge (Twilio) OK")
            except Exception as e:
                logger.warning(f"WhatsApp bridge: {e}")
        else:
            logger.info("⏭️  WhatsApp bridge omitido (sin credenciales Twilio)")

        # Telegram Bot
        logger.info("📱 Iniciando Telegram bot...")
        telegram_task = asyncio.create_task(start_telegram_bot(settings))

        logger.info("=" * 65)
        logger.info(f"🟢 KYNIKOS OS ACTIVO")
        logger.info("=" * 65)

        yield

        # Shutdown limpio
        if hasattr(_agent_loop, 'stop'):
            await _agent_loop.stop()
        telegram_task.cancel()
        try:
            await telegram_task
        except asyncio.CancelledError:
            pass
        await stop_telegram_bot()
        logger.info("✅ KynicOS shutdown OK")

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        raise


# ── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="KynicOS — KYNIKOS AI Agent",
    description=(
        "Sistema operativo IA para hospitalidad de lujo, transporte y DevSecOps. "
        "Telegram + WhatsApp + HVAC Triage + MueveCancún."
    ),
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

# Static files
web_path = Path(__file__).parent.parent / "web"
if web_path.exists():
    app.mount("/static", StaticFiles(directory=web_path), name="static")


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    dashboard_path = Path(__file__).parent.parent / "web" / "index.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    return JSONResponse({
        "name": "KynicOS",
        "version": "2.0.0",
        "status": "running",
        "persona": os.getenv("PERSONA", "kynikos"),
        "docs": "/docs",
        "skills": ["hvac_triage", "mueve_cancun", "concierge_llm", "whisper_stt"],
    })


@app.get("/api/status")
async def status():
    persona_name = os.getenv("PERSONA", "kynikos")
    providers = []
    if _agent_loop and hasattr(_agent_loop, 'provider_manager'):
        providers = [p.name for p in _agent_loop.provider_manager._providers]

    return JSONResponse({
        "status": "ok",
        "version": "2.0.0",
        "persona": persona_name,
        "agent_loop": _agent_loop is not None,
        "llm_chain": providers,
        "channels": ["telegram", "whatsapp"],
        "skills": ["hvac_triage", "mueve_cancun", "concierge_llm"],
        "deploy_url": "https://nanobot-cloud-zjr0.onrender.com",
        "fixes": [
            "Groq 413 → truncado automático + modelo fallback",
            "Telegram Conflict → drop_pending_updates=True",
            "Sin Anthropic → cadena: Groq → Together → OpenRouter",
        ],
    })


# WhatsApp webhook
try:
    from app.cloud.whatsapp_bridge import create_whatsapp_routes
    app.include_router(create_whatsapp_routes(), prefix="/api")
except Exception:
    pass

# Dashboard routes
try:
    from app.cloud.dashboard import create_dashboard_routes
    app.include_router(create_dashboard_routes(), prefix="/api")
except Exception:
    pass


# ── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    s = Settings()
    uvicorn.run("app.main:app", host=s.host, port=s.port, reload=s.environment == "development")
