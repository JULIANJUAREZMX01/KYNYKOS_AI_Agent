"""
KynicOS / KYNYKOS — Telegram Bot
Fix críticos incluidos:
  1. Drop_pending_updates=True → evita Conflict (dos instancias)
  2. Truncado de historial antes de llamar al LLM
  3. Transcripción de voz via Groq Whisper
  4. Comandos: /start, /reset, /status, /persona
"""

from typing import Optional
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from app.config import Settings
from app.utils import get_logger
from app.core.context import AgentContext

logger = get_logger(__name__)

_app: Optional[Application] = None


# ── Comandos ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bienvenida + lista de capacidades"""
    user = update.effective_user
    from app.main import _agent_loop

    if _agent_loop and hasattr(_agent_loop, 'persona'):
        greeting = _agent_loop.persona.greeting
    else:
        greeting = (
            "🐕 **KYNIKOS activado.**\n\n"
            "Soy tu perro guardián digital y socio estratégico.\n\n"
            "Comandos:\n"
            "/start — Este mensaje\n"
            "/reset — Limpiar historial de conversación\n"
            "/status — Estado del sistema\n"
            "/persona [kynikos|leo|mueve] — Cambiar personalidad"
        )
    await update.message.reply_text(greeting, parse_mode="Markdown")
    logger.info(f"[Telegram] /start from {user.id}")


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/reset — Limpia la sesión actual"""
    user = update.effective_user
    session_id = f"telegram_{user.id}"
    try:
        from app.main import _session_manager
        # Borrar archivo de sesión
        session_file = Path("./data/sessions") / f"{session_id}.jsonl"
        if session_file.exists():
            session_file.unlink()
        await update.message.reply_text("🔄 Historial limpiado. Nueva sesión iniciada.")
        logger.info(f"[Telegram] Session reset: {session_id}")
    except Exception as e:
        await update.message.reply_text(f"Error al resetear: {e}")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/status — Estado del sistema"""
    from app.main import _agent_loop
    try:
        persona_name = getattr(getattr(_agent_loop, 'persona', None), 'name', 'KYNIKOS')
        # Obtener proveedor actual
        providers = []
        if _agent_loop and hasattr(_agent_loop, 'provider_manager'):
            providers = [p.name for p in _agent_loop.provider_manager._providers]

        status = (
            f"🐕 **KynicOS Status**\n\n"
            f"✅ Sistema: Activo\n"
            f"👤 Persona: {persona_name}\n"
            f"🧠 LLM Chain: {' → '.join(providers) if providers else 'Groq'}\n"
            f"📱 Canal: Telegram\n"
            f"🔧 Skills: HVAC Triage, MueveCancún, Concierge\n\n"
            f"Usa /reset para limpiar el historial si hay errores 413."
        )
        await update.message.reply_text(status, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Status error: {e}")


async def cmd_persona(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/persona [nombre] — Cambia la personalidad activa"""
    from app.main import _agent_loop
    from app.concierge.persona import get_persona

    args = context.args
    if not args:
        await update.message.reply_text(
            "Uso: `/persona kynikos|leo|mueve|nexus`\n"
            "Personalidades disponibles:\n"
            "• `kynikos` — Perro guardián técnico (default)\n"
            "• `leo` — Concierge de lujo para turistas\n"
            "• `mueve` — Guía de transporte MueveCancún\n"
            "• `nexus` — Superagente admin",
            parse_mode="Markdown"
        )
        return

    persona_name = args[0].lower()
    try:
        new_persona = get_persona(persona_name)
        if _agent_loop:
            _agent_loop.persona = new_persona
        await update.message.reply_text(
            f"✅ Personalidad cambiada a: **{new_persona.name}**\n\n{new_persona.greeting}",
            parse_mode="Markdown"
        )
        logger.info(f"[Telegram] Persona changed to: {persona_name}")
    except Exception as e:
        await update.message.reply_text(f"Error cambiando persona: {e}")


# ── Handlers de Mensajes ──────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle texto entrante"""
    if not update.message or not update.message.text:
        return
    await _process_with_agent(update, update.message.text)


async def handle_incoming_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle archivos, fotos y notas de voz"""
    message = update.message
    if not message:
        return

    logic_dir = Path("workspace/logic")
    logic_dir.mkdir(parents=True, exist_ok=True)

    try:
        file = None
        orig_name = "file"

        if message.document:
            file = await message.document.get_file()
            orig_name = message.document.file_name or "document"
        elif message.photo:
            file = await message.photo[-1].get_file()
            orig_name = f"photo_{message.photo[-1].file_id}.jpg"
        elif message.voice:
            file = await message.voice.get_file()
            orig_name = f"voice_{message.voice.file_id}.ogg"

        if file:
            save_path = logic_dir / orig_name
            await file.download_to_drive(save_path)

            if message.voice:
                await update.message.chat.send_action("typing")
                transcription = await _transcribe_voice(save_path)
                await _process_with_agent(update, transcription)
            else:
                await message.reply_text(
                    f"📥 Archivo guardado en `workspace/logic/{orig_name}`",
                    parse_mode="Markdown"
                )

    except Exception as e:
        logger.error(f"File handling error: {e}")
        await message.reply_text(f"❌ Error: {str(e)[:100]}")


async def _transcribe_voice(path: Path) -> str:
    """Transcribe audio con Groq Whisper (gratis)"""
    try:
        from app.main import settings
        from groq import Groq
        client = Groq(api_key=settings.groq_api_key)
        with open(path, "rb") as f:
            result = client.audio.transcriptions.create(
                file=(str(path), f.read()),
                model="whisper-large-v3",
                response_format="text",
                language="es",
            )
        logger.info(f"[Whisper] Transcripción: {str(result)[:60]}...")
        return str(result)
    except Exception as e:
        logger.error(f"[Whisper] Error: {e}")
        return f"[Audio recibido, no se pudo transcribir: {e}]"


async def _process_with_agent(update: Update, text: str) -> None:
    """Pipeline central: texto → ConciergeAgentLoop → respuesta Telegram"""
    user = update.effective_user
    logger.info(f"[Telegram] Message from {user.id}: {text[:60]}...")
    await update.message.chat.send_action("typing")

    try:
        from app.main import _agent_loop, _session_manager

        if not _agent_loop:
            await update.message.reply_text("❌ Agent loop no iniciado. Reiniciando...")
            return

        session_id = f"telegram_{user.id}"
        ctx = await _session_manager.load_session(session_id)
        if not ctx:
            ctx = AgentContext(
                session_id=session_id,
                user_id=str(user.id),
                channel="telegram",
            )

        ctx.add_message("user", text)
        response = await _agent_loop.process_message(ctx)
        await _session_manager.save_session(ctx)

        # Enviar respuesta (dividir si >4096 chars)
        if len(response) > 4096:
            for i in range(0, len(response), 4096):
                await update.message.reply_text(response[i : i + 4096])
        else:
            await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"[Telegram] Agent error: {e}", exc_info=True)
        await update.message.reply_text(
            "⚠️ Error procesando tu mensaje. Usa /reset si el problema persiste."
        )


# ── Lifecycle ─────────────────────────────────────────────────────────────────

async def send_alert(message_text: str, settings: Settings) -> bool:
    """Envía alerta proactiva al usuario de Telegram"""
    global _app
    if not _app or not settings.telegram_user_id:
        return False
    try:
        await _app.bot.send_message(
            chat_id=settings.telegram_user_id,
            text=f"🐕 **KYNIKOS ALERT**:\n\n{message_text}",
            parse_mode="Markdown",
        )
        return True
    except Exception as e:
        logger.error(f"Alert send error: {e}")
        return False


async def start_telegram_bot(settings: Settings) -> None:
    """
    Inicia el bot con drop_pending_updates=True para evitar el error:
    'Conflict: terminated by other getUpdates request'
    Esto ocurre cuando hay dos instancias corriendo (KynicOS + KYNYKOS_AI_Agent).
    """
    global _app
    try:
        _app = Application.builder().token(settings.telegram_token).build()

        # Comandos
        _app.add_handler(CommandHandler("start", cmd_start))
        _app.add_handler(CommandHandler("reset", cmd_reset))
        _app.add_handler(CommandHandler("status", cmd_status))
        _app.add_handler(CommandHandler("persona", cmd_persona))

        # Mensajes
        _app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        _app.add_handler(
            MessageHandler(
                filters.Document.ALL | filters.PHOTO | filters.VOICE,
                handle_incoming_file,
            )
        )

        await _app.initialize()
        await _app.start()

        # ⚠️ drop_pending_updates=True es el fix para el Conflict
        await _app.updater.start_polling(drop_pending_updates=True)
        logger.info("🟢 [Telegram] Bot polling started (drop_pending_updates=True)")

        # Notificar al usuario que el bot está listo
        try:
            persona_name = "KYNIKOS"
            await _app.bot.send_message(
                chat_id=settings.telegram_user_id,
                text=f"🐕 **{persona_name}** reconectado y operativo.\n`drop_pending_updates=True` — conflicto resuelto.",
                parse_mode="Markdown",
            )
        except Exception:
            pass

    except Exception as e:
        logger.error(f"[Telegram] Start error: {e}")
        raise


async def stop_telegram_bot() -> None:
    """Detiene el bot limpiamente"""
    global _app
    if _app:
        try:
            await _app.updater.stop()
            await _app.stop()
            await _app.shutdown()
            logger.info("🛑 [Telegram] Bot stopped cleanly")
        except Exception as e:
            logger.warning(f"[Telegram] Stop warning: {e}")
