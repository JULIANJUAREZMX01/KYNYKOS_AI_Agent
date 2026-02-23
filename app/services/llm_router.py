from typing import Optional, Dict
from enum import Enum
from loguru import logger
from app.services.token_tracker import TokenTracker


class ProviderName(str, Enum):
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    OPENAI = "openai"


class LLMRouter:
    # Priority order: External providers first, then Ollama as fallback
    PRIORITY_ORDER = [
        ProviderName.ANTHROPIC,
        ProviderName.GROQ,
        ProviderName.OPENAI,
        ProviderName.OLLAMA,
    ]

    def __init__(self):
        self.providers: Dict[str, Dict] = {}
        self.current_provider: Optional[str] = None
        self.logger = logger
        self.token_tracker = TokenTracker()

    async def initialize(self):
        """Initialize all providers"""
        self.providers = {
            "ollama": {"status": "available", "url": "http://localhost:11434"},
            "anthropic": {"status": "available", "url": "https://api.anthropic.com"},
            "groq": {"status": "available", "url": "https://api.groq.com"},
            "openai": {"status": "available", "url": "https://api.openai.com"},
        }
        self.logger.info("LLMRouter initialized")

    async def select_provider(self) -> str:
        """Select best available provider based on priority and rate limits"""
        for provider_name in self.PRIORITY_ORDER:
            if provider_name in self.providers:
                # Check if provider is available
                provider = self.providers[provider_name]
                if provider.get("status") != "available":
                    continue

                # Check rate limits (skip check for Ollama generally, but TokenTracker handles it)
                if self.token_tracker.is_rate_limited(provider_name):
                    self.logger.warning(f"Provider {provider_name} is rate limited (>90%). Skipping.")
                    continue

                self.current_provider = provider_name
                return provider_name

        # Fallback to Ollama if everything else fails or is limited
        self.logger.warning("All primary providers unavailable or limited. Forcing fallback to Ollama.")
        return ProviderName.OLLAMA.value

    async def call_llm(self, prompt: str) -> str:
        """Route LLM call to selected provider"""
        provider = await self.select_provider()
        self.logger.info(f"Routing to {provider}: {prompt[:50]}...")

        # Note: In a real implementation, usage should be recorded after the call.
        # self.token_tracker.add_usage(provider, tokens_used)

        return f"Response from {provider}"
