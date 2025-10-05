"""Factory for AI service providers."""

from __future__ import annotations

from fastapi import HTTPException, status

from .anthropic_service import AnthropicService
from .base import BaseAIService
from .openai_service import OpenAIService

__all__ = [
    "AnthropicService",
    "BaseAIService",
    "OpenAIService",
    "get_ai_service",
]


def get_ai_service(provider: str) -> BaseAIService:
    """Return the AI service implementation for the given provider."""
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conversation does not define an AI provider",
        )

    normalized_provider = provider.lower()

    if normalized_provider == "openai":
        return OpenAIService()
    if normalized_provider == "anthropic":
        return AnthropicService()

    raise ValueError(f"Unknown provider: {provider}")
