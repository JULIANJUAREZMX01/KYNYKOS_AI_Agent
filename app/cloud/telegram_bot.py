"""Telegram bot integration for Nanobot with Agent Loop"""

import asyncio
import os
from typing import Optional
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from app.config import Settings
from app.utils import get_logger
from app.core.context import AgentContext
from app.services.llm_router import LLMRouter

logger = get_logger(__name__)

_app: Optional[Application] = None
_llm_router: Optional[LLMRouter] = None
_settings: Optional[Settings] = None


async def get_ai_response(prompt: str) -> str:
    """Get AI response through multi-provider LLM router"""
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
        await _llm_router.initialize()
    return await _llm_router.call_llm(prompt)


async def send_alert(message_text: str, settings: Settings) -> bool:
    """Send a proactive alert to Julian's mobile"""
    global _app

    if not _app or not settings.telegram_user_id:
        return False
    
    try:
        await _app.bot.send_message(
            chat_id=settings.telegram_user_id,
            text=f"🐕 **CENTINELA KYNIKOS ALERT**:\n\n{message_text}"
        )
        return True
    except Exception as e:
        print(f"Error sending proactive alert: {e}")
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    message = update.message

    await message.reply_text(
        f"Hola {user.first_name}! 👋\n\n"
        "Soy **KYNIKOS**, tu perro guardián y socio estratégico.\n"
        "Control total activado. Soberanía digital confirmada.\n\n"
        "Capacidades Expandidas:\n"
        "• 👁️ Visión (Capturas de Pantalla)\n"
        "• 💀 Control de Procesos (Task Reaper)\n"
        "• 🗣️ Multimodal (Voz & Traducción)\n"
        "• 🔧 Autocuración (Self-Repair)\n"
        "• 📂 Ciclo de Datos (Móvil ↔ PC)\n"
        "• 🔓 Modo Bypass (Control Absoluto)"
    )
    logger.info(f"User {user.id} started bot")


async def handle_incoming_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming files/photos from Telegram and save them to the logic folder"""
    message = update.message
    if not message:
        return

    # Create logic dir if not exists
    logic_dir = Path("workspace/logic")
    logic_dir.mkdir(parents=True, exist_ok=True)

    try:
        file = None
        orig_name = "file"
        
        if message.document:
            file = await message.document.get_file()
            orig_name = message.document.file_name
        elif message.photo:
            file = await message.photo[-1].get_file()
            orig_name = f"photo_{message.photo[-1].file_id}.jpg"
        elif message.voice:
            file = await message.voice.get_file()
            orig_name = f"voice_{message.voice.file_id}.ogg"
            
        if file:
            save_path = logic_dir / orig_name
            await file.download_to_drive(save_path)
            
            # If it's voice, transcribe it
            transcription = ""
            if message.voice:
                transcription = await _transcribe_voice(save_path)
                
            msg_text = f"He recibido y guardado el archivo en: `{save_path}`"
            if transcription:
                msg_text += f"\n\n**Transcripción**: {transcription}"
                # Inject transcription as text to agent loop
                await _process_with_agent(update, transcription)
            else:
                await message.reply_text(msg_text)
                
            logger.info(f"File saved from mobile: {save_path}")
    except Exception as e:
        logger.error(f"Error handling incoming file: {e}")
        await message.reply_text(f"❌ Error guardando el archivo: {e}")


async def _transcribe_voice(path: Path) -> str:
    """Transcribe voice message using Groq's Whisper API"""
    try:
        if not _settings:
            return "[Audio no transcrito: settings no inicializadas]"

        from groq import Groq
        
        client = Groq(api_key=_settings.groq_api_key)
        
        with open(path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(str(path), file.read()),
                model="whisper-large-v3",
                response_format="text"
            )
        return str(transcription)
    except Exception as e:
        logger.error(f"Error transcribing voice: {e}")
        return f"[Audio no transcrito: {e}]"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages with agent loop"""
    message = update.message
    if not message or not message.text:
        return

    await _process_with_agent(update)


async def _process_with_agent(update: Update, override_text: str = None) -> None:
    """Central processing for agent loop"""
    user = update.effective_user
    message = update.message
    text = override_text or (message.text if message else None)
    
    if not user or not message:
        return

    logger.info(f"Message from {user.id}: {text[:50] if text else 'no text'}...")
    await update.message.chat.send_action("typing")

    try:
        # Authorization check: must match Julian's ID
        if not _settings or str(user.id) != str(_settings.telegram_user_id):
            logger.warning(f"Unauthorized access attempt by user {user.id}")
            await message.reply_text("❌ Acceso no autorizado")
            return

        from app.main import _agent_loop, _session_manager

        if not _agent_loop:
            await message.reply_text("❌ Agent loop no iniciado")
            return

        session_id = f"telegram_{user.id}"
        ctx = await _session_manager.load_session(session_id)
        if not ctx:
            ctx = AgentContext(session_id=session_id, user_id=str(user.id), channel="telegram")

        # Process message
        ctx.add_message("user", text)
        response = await _agent_loop.process_message(ctx)
        await _session_manager.save_session(ctx)

        # Dispatch files/audios from KYNIKOS to Mobile
        if ctx.files:
            for file_path in ctx.files:
                try:
                    p = Path(file_path)
                    if p.suffix in ['.mp3', '.ogg', '.wav']:
                        await update.message.reply_audio(audio=open(p, "rb"), caption="🗣️ KYNIKOS Voice Report")
                    elif p.suffix in ['.png', '.jpg', '.jpeg']:
                        await update.message.reply_photo(photo=open(p, "rb"), caption="👁️ KYNIKOS Vision")
                    else:
                        await update.message.reply_document(document=open(p, "rb"), caption=f"📄 {p.name}")
                except Exception as fe:
                    logger.error(f"Error sending file {file_path}: {fe}")

        # Send text response
        if len(response) > 4096:
            for i in range(0, len(response), 4096):
                await message.reply_text(response[i:i+4096])
        else:
            await message.reply_text(response)

    except Exception as e:
        logger.error(f"Error in agent processing: {e}", exc_info=True)
        await message.reply_text(f"❌ Error: {str(e)[:100]}")


async def start_telegram_bot(settings: Settings) -> None:
    """Start Telegram bot"""
    global _app, _settings
    _settings = settings
    try:
        _app = Application.builder().token(settings.telegram_token).build()
        
        # Handlers
        _app.add_handler(CommandHandler("start", start))
        _app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        _app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VOICE, handle_incoming_file))

        await _app.initialize()
        await _app.start()
        await _app.updater.start_polling()
        logger.info("🟢 Telegram bot polling started")
    except Exception as e:
        logger.error(f"Telegram bot error: {e}")


async def stop_telegram_bot() -> None:
    """Stop Telegram bot"""
    global _app
    if _app:
        try:
            await _app.stop()
            logger.info("🛑 Telegram bot stopped")
        except Exception:
            pass

async def start(settings: Settings) -> None:
    """Start Telegram bot (alias for start_telegram_bot)"""
    await start_telegram_bot(settings)
