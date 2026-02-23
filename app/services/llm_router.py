from typing import Optional, Dict
from enum import Enum
from loguru import logger


class ProviderName(str, Enum):
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    OPENAI = "openai"


class LLMRouter:
    PRIORITY_ORDER = [
        ProviderName.OLLAMA,
        ProviderName.ANTHROPIC,
        ProviderName.GROQ,
        ProviderName.OPENAI,
    ]

    def __init__(self):
        self.providers: Dict[str, Dict] = {}
        self.current_provider: Optional[str] = None
        self.logger = logger

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
        """Select best available provider based on priority"""
        for provider_name in self.PRIORITY_ORDER:
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                if provider.get("status") == "available":
                    self.current_provider = provider_name
                    return provider_name

        return "ollama"

    async def call_llm(self, prompt: str) -> str:
        """Route LLM call to selected provider"""
        provider = await self.select_provider()
        self.logger.info(f"Routing to {provider}: {prompt[:50]}...")
        return f"Response from {provider}"
