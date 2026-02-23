"""Main entry point for Nanobot Cloud Deployment — Phase 2 (Agent Loop)"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.config import Settings
from app.utils import get_logger
from app.cloud.dashboard import create_dashboard_routes
from app.cloud.telegram_bot import start_telegram_bot, stop_telegram_bot
from app.cloud import telegram_bot, whatsapp_bridge
from app.cloud.whatsapp_bridge import create_whatsapp_routes, init_whatsapp_bridge
from app.cloud.backup_service import BackupService
from app.core.memory import Memory
from app.cloud.sessions import SessionManager

# Configuration
settings = Settings()
# Global variables for cross-module access
_agent_loop = None
_session_manager = None
_explorer = None
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""

    logger.info("=" * 80)
    logger.info("🚀 STARTING NANOBOT CLOUD DEPLOYMENT — PHASE 2")
    logger.info("=" * 80)

    try:
        # Initialize components
        logger.info("📦 Initializing components...")

        # Memory
        memory = Memory(workspace_path="./workspace")
        logger.info("✅ Memory initialized")

        # Session manager
        session_manager = SessionManager(data_dir="./data")
        logger.info("✅ Session manager initialized")

        # Backup service
        backup_service = BackupService(settings)
        if settings.s3_bucket:
            logger.info("💾 S3 backup service available")
        else:
            logger.info("⏭️  S3 backups disabled")

        # Initialize global agent loop
        from app.cloud.providers import ProviderManager
        from app.core.loop import AgentLoop
        
        provider_manager = ProviderManager(settings)
        global _agent_loop, _session_manager
        _agent_loop = AgentLoop(settings, provider_manager)
        _session_manager = session_manager
        
        # Start AgentLoop background tasks (including Sentinel)
        await _agent_loop.start()
        logger.info("✅ Agent loop initialized (Sentinel active)")

        # Start Shadow Explorer (indexing)
        from app.core.explorer import ShadowExplorer
        explorer = ShadowExplorer(base_paths=[
            Path("C:/Users/QUINTANA/sistemas"),
            Path("C:/Users/QUINTANA/Downloads"),
            Path("C:/Users/QUINTANA/Desktop"),
        ])
        global _explorer
        _explorer = explorer
        asyncio.create_task(explorer.rebuild_index())
        logger.info("🐕 Shadow Explorer ready")

        # Start messaging bridges concurrently
        logger.info("📱 Starting messaging bridges...")
        await asyncio.gather(
            telegram_bot.start(settings),
            whatsapp_bridge.connect(settings)
        )

        logger.info("=" * 80)
        logger.info("🟢 NANOBOT IS RUNNING — READY FOR MESSAGES")
        logger.info("=" * 80)

        yield

        # Shutdown
        logger.info("=" * 80)
        logger.info("🛑 SHUTTING DOWN NANOBOT")
        logger.info("=" * 80)

        # Stop AgentLoop (stops Sentinel)
        if _agent_loop:
            await _agent_loop.stop()

        await stop_telegram_bot()

        logger.info("✅ Nanobot shut down gracefully")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Fatal error during startup: {e}")
        raise


# Create FastAPI app
app = FastAPI(
    title="Nanobot Cloud",
    description="AI Assistant for QUINTANA — Phase 2: Agent Loop",
    version="0.2.0",
    lifespan=lifespan
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (dashboard)
web_path = Path(__file__).parent.parent / "web"
if web_path.exists():
    app.mount("/static", StaticFiles(directory=web_path), name="static")


# ============================================================================
# API Routes
# ============================================================================


@app.get("/")
async def root():
    """Root endpoint — serve dashboard"""
    dashboard_path = Path(__file__).parent.parent / "web" / "index.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    return {
        "message": "Nanobot Cloud API",
        "status": "running",
        "version": "0.2.0",
        "phase": "Phase 2 - Agent Loop"
    }


@app.get("/api/status")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "0.2.0",
        "phase": "2-agent-loop",
        "environment": settings.environment,
        "telegram": True,
        "agent_loop": True,
        "sentinel": settings.contract_settings.sentinel_enabled,
        "lmm_fallback": "external -> ollama"
    }


# Register dashboard routes
app.include_router(create_dashboard_routes(), prefix="/api")

# Register WhatsApp webhook routes
app.include_router(create_whatsapp_routes(), prefix="/api")


# ============================================================================
# Startup/Shutdown Events
# ============================================================================


@app.on_event("startup")
async def startup():
    """Startup event"""
    logger.info("✅ FastAPI startup complete")


@app.on_event("shutdown")
async def shutdown():
    """Shutdown event"""
    logger.info("✅ FastAPI shutdown complete")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development"
    )
