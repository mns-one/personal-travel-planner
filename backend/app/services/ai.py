"""Provider-based async language model integration."""

import logging
import os
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AIGenerationError(RuntimeError):
    """Raised when a configured AI provider cannot generate a response."""


class LLMProvider(ABC):
    """Shared interface implemented by language model providers."""

    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text from system and user instructions."""


class GroqProvider(LLMProvider):
    """Groq API provider using its asynchronous client."""

    def __init__(self, api_key: str, model: str | None = None):
        try:
            from groq import AsyncGroq

            self.client = AsyncGroq(api_key=api_key)
            self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            logger.info("Groq async client initialized")
        except Exception as error:
            logger.exception("Failed to initialize Groq provider")
            raise AIGenerationError("Groq initialization failed") from error

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.4,
            )
            content = response.choices[0].message.content
            if not content:
                raise AIGenerationError("Groq returned an empty response")
            return content
        except AIGenerationError:
            raise
        except Exception as error:
            logger.exception("Groq itinerary generation failed")
            raise AIGenerationError("Groq itinerary generation failed") from error


def get_llm_provider() -> LLMProvider | None:
    """Return the configured provider, or None when no API key is set."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return GroqProvider(api_key)
