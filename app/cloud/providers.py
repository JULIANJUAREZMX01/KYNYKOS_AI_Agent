"""
KynicOS — LLM Provider Chain
Cadena de fallback 100% pública y gratuita. SIN Anthropic/Claude.

Cadena de prioridad:
  1. Groq (Llama 3.3 70B / llama-3.1-8b-instant para prompts grandes)
  2. Together AI (gratis con API key pública)
  3. OpenRouter (modelos públicos gratuitos)
  4. Ollama local (si está configurado)

Estrategia anti-413:
  - Detecta prompts >8k tokens → cambia a modelo más pequeño (llama-3.1-8b-instant)
  - Si sigue fallando → trunca historial a últimos 4 mensajes + system
  - Retry con backoff exponencial
"""

import asyncio
import re
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import Settings
from app.utils import get_logger

logger = get_logger(__name__)

# Límites de tokens por modelo (estimado conservador)
MODEL_TOKEN_LIMITS = {
    "llama-3.3-70b-versatile": 8000,
    "llama-3.1-8b-instant": 7000,
    "llama3-8b-8192": 6000,
    "mixtral-8x7b-32768": 28000,
    "gemma2-9b-it": 7000,
    # Together AI
    "meta-llama/Llama-3.2-3B-Instruct-Turbo": 6000,
    "mistralai/Mistral-7B-Instruct-v0.2": 6000,
    # OpenRouter (gratuitos)
    "google/gemma-3-1b-it:free": 5000,
    "mistralai/mistral-7b-instruct:free": 6000,
}


def estimate_tokens(messages: List[Dict[str, str]]) -> int:
    """Estimación rápida de tokens (4 chars ≈ 1 token)"""
    total_chars = sum(len(m.get("content", "")) for m in messages)
    return total_chars // 4


def truncate_messages(messages: List[Dict[str, str]], max_tokens: int = 6000) -> List[Dict[str, str]]:
    """
    Trunca el historial de mensajes manteniendo:
    - El mensaje de sistema (siempre)
    - Los últimos N mensajes de conversación
    """
    if not messages:
        return messages

    system_msgs = [m for m in messages if m["role"] == "system"]
    conv_msgs = [m for m in messages if m["role"] != "system"]

    # Calcular tokens del sistema
    system_tokens = estimate_tokens(system_msgs)
    available = max_tokens - system_tokens - 500  # buffer

    # Agregar mensajes del más reciente al más antiguo hasta llenar
    selected_conv = []
    running_tokens = 0
    for msg in reversed(conv_msgs):
        msg_tokens = estimate_tokens([msg])
        if running_tokens + msg_tokens > available:
            break
        selected_conv.insert(0, msg)
        running_tokens += msg_tokens

    # Siempre incluir al menos el último mensaje del usuario
    if not selected_conv and conv_msgs:
        selected_conv = [conv_msgs[-1]]

    result = system_msgs + selected_conv
    logger.info(f"[Truncate] {len(messages)} → {len(result)} msgs (~{estimate_tokens(result)} tokens)")
    return result


# ── GROQ PROVIDER ────────────────────────────────────────────────────────────

class GroqProvider:
    """Groq LLM — primario. Gratis con límites generosos."""

    PRIMARY_MODEL = "llama-3.3-70b-versatile"
    FALLBACK_MODEL = "llama-3.1-8b-instant"  # más pequeño para prompts grandes

    def __init__(self, api_key: str):
        from groq import Groq
        self.client = Groq(api_key=api_key)
        self.name = "groq"

    async def call(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Llama a Groq con auto-downgrade de modelo si el prompt es muy grande."""
        
        estimated = estimate_tokens(messages)
        model = self.PRIMARY_MODEL

        # Si el prompt es demasiado grande → usar modelo más pequeño
        if estimated > MODEL_TOKEN_LIMITS[self.PRIMARY_MODEL]:
            logger.warning(f"[Groq] Prompt grande ({estimated} tokens) → usando {self.FALLBACK_MODEL}")
            model = self.FALLBACK_MODEL
            messages = truncate_messages(messages, max_tokens=MODEL_TOKEN_LIMITS[self.FALLBACK_MODEL])

        return await self._call_with_model(messages, model, max_tokens, temperature)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
    )
    async def _call_with_model(
        self, messages, model, max_tokens, temperature
    ) -> Dict[str, Any]:
        try:
            logger.info(f"[Groq] Calling {model} (~{estimate_tokens(messages)} tokens)")
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = response.choices[0].message.content
            logger.info(f"[Groq] ✅ {len(content)} chars")
            return {"text": content, "tool_calls": [], "model": model, "provider": "groq"}
        except Exception as e:
            error_str = str(e)
            # Si es 413 (demasiado grande), truncar y reintentar UNA vez
            if "413" in error_str or "tokens" in error_str.lower():
                logger.warning(f"[Groq] 413 en {model} — truncando a 4 mensajes")
                messages = truncate_messages(messages, max_tokens=4000)
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.FALLBACK_MODEL,
                    messages=messages,
                    max_tokens=1024,
                    temperature=temperature,
                )
                content = response.choices[0].message.content
                return {"text": content, "tool_calls": [], "model": self.FALLBACK_MODEL, "provider": "groq"}
            logger.error(f"[Groq] Error: {e}")
            raise


# ── TOGETHER AI PROVIDER ─────────────────────────────────────────────────────

class TogetherProvider:
    """Together AI — fallback gratuito con créditos mensuales."""

    MODEL = "meta-llama/Llama-3.2-3B-Instruct-Turbo"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.name = "together"
        self.base_url = "https://api.together.xyz/v1/chat/completions"

    async def call(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        import httpx
        messages = truncate_messages(messages, max_tokens=5000)
        logger.info(f"[Together] Calling {self.MODEL}")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.MODEL,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            logger.info(f"[Together] ✅ {len(content)} chars")
            return {"text": content, "tool_calls": [], "model": self.MODEL, "provider": "together"}


# ── OPENROUTER PROVIDER ───────────────────────────────────────────────────────

class OpenRouterProvider:
    """OpenRouter — acceso a modelos públicos gratuitos como fallback final."""

    MODEL = "mistralai/mistral-7b-instruct:free"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.name = "openrouter"
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    async def call(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        import httpx
        messages = truncate_messages(messages, max_tokens=5000)
        logger.info(f"[OpenRouter] Calling {self.MODEL}")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://kynicos.onrender.com",
                    "X-Title": "KynicOS",
                },
                json={
                    "model": self.MODEL,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            logger.info(f"[OpenRouter] ✅ {len(content)} chars")
            return {"text": content, "tool_calls": [], "model": self.MODEL, "provider": "openrouter"}


# ── OLLAMA PROVIDER (local) ───────────────────────────────────────────────────

class OllamaProvider:
    """Ollama local — opcional, sin costo, sin límites."""

    def __init__(self, url: str = "http://localhost:11434", model: str = "llama3"):
        self.url = url
        self.model = model
        self.name = "ollama"

    async def call(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        import httpx
        messages = truncate_messages(messages, max_tokens=6000)
        logger.info(f"[Ollama] Calling {self.model}")
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {"num_predict": max_tokens, "temperature": temperature},
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["message"]["content"]
            logger.info(f"[Ollama] ✅ {len(content)} chars")
            return {"text": content, "tool_calls": [], "model": self.model, "provider": "ollama"}


# ── PROVIDER MANAGER ─────────────────────────────────────────────────────────

class ProviderManager:
    """
    Gestiona la cadena de proveedores LLM.
    Cadena: Groq → Together → OpenRouter → Ollama
    SIN Anthropic/Claude.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._providers: List = []
        self._init_providers()

    def _init_providers(self):
        """Inicializa proveedores disponibles según las env vars configuradas."""
        # 1. Groq (primario)
        if getattr(self.settings, "groq_api_key", None):
            try:
                self._providers.append(GroqProvider(self.settings.groq_api_key))
                logger.info("✅ [Provider] Groq inicializado (primario)")
            except Exception as e:
                logger.warning(f"Groq init error: {e}")

        # 2. Together AI
        if getattr(self.settings, "together_api_key", None):
            try:
                self._providers.append(TogetherProvider(self.settings.together_api_key))
                logger.info("✅ [Provider] Together AI inicializado")
            except Exception as e:
                logger.warning(f"Together init error: {e}")

        # 3. OpenRouter
        if getattr(self.settings, "openrouter_api_key", None):
            try:
                self._providers.append(OpenRouterProvider(self.settings.openrouter_api_key))
                logger.info("✅ [Provider] OpenRouter inicializado")
            except Exception as e:
                logger.warning(f"OpenRouter init error: {e}")

        # 4. Ollama local
        ollama_url = getattr(self.settings, "ollama_url", None)
        if ollama_url:
            try:
                ollama_model = getattr(self.settings, "ollama_model", "llama3")
                self._providers.append(OllamaProvider(ollama_url, ollama_model))
                logger.info(f"✅ [Provider] Ollama inicializado ({ollama_model})")
            except Exception as e:
                logger.warning(f"Ollama init error: {e}")

        if not self._providers:
            logger.error("❌ NINGÚN proveedor LLM disponible. Configura GROQ_API_KEY como mínimo.")

        logger.info(f"📊 Cadena de proveedores: {[p.name for p in self._providers]}")

    def get_provider(self):
        """Obtiene el primer proveedor disponible."""
        if not self._providers:
            raise RuntimeError("No hay proveedores LLM disponibles")
        return self._providers[0]

    async def call(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Llama al LLM con fallback automático entre proveedores.
        Si un proveedor falla, intenta el siguiente.
        """
        last_error = None
        for provider in self._providers:
            try:
                return await provider.call(messages, max_tokens, temperature)
            except Exception as e:
                logger.warning(f"[{provider.name}] Falló: {str(e)[:100]} — intentando siguiente...")
                last_error = e
                continue

        # Todos fallaron
        logger.error(f"❌ Todos los proveedores fallaron. Último error: {last_error}")
        raise RuntimeError(f"Todos los proveedores LLM fallaron: {last_error}")
