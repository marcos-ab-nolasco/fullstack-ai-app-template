"""OpenAI chat completion service."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from openai import AsyncOpenAI
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.core.config import get_settings

from .base import BaseAIService


class OpenAIService(BaseAIService):
    """Implementation of the AI service using OpenAI's chat completions API."""

    def __init__(self) -> None:
        settings = get_settings()
        api_key = settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else None
        self._client = AsyncOpenAI(api_key=api_key) if api_key else None

    async def generate_response(
        self,
        messages: list[dict[str, Any]],
        model: str,
        system_prompt: str | None = None,
    ) -> str:
        """Generate a completion using OpenAI with retry logic."""
        if self._client is None:
            return "OpenAI não está configurado. Defina OPENAI_API_KEY para habilitar respostas automáticas."

        client = self._client
        payload = self._build_payload(messages, system_prompt)

        try:
            async for attempt in AsyncRetrying(
                reraise=True,
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=4),
                retry=retry_if_exception_type(Exception),
            ):
                with attempt:
                    response = await client.chat.completions.create(
                        model=model,
                        messages=payload,  # type: ignore[arg-type]
                    )
        except Exception as exc:  # noqa: BLE001 - upstream errors vary
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to generate response from OpenAI: {exc}",
            ) from exc

        message = response.choices[0].message

        if isinstance(message.content, str):
            content = message.content
        else:
            parts: list[str] = []
            for part in message.content or []:  # type: ignore[var-annotated]
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict):
                    text = part.get("text")
                    if isinstance(text, str):
                        parts.append(text)
                else:
                    text_value = getattr(part, "text", None)
                    if isinstance(text_value, str):
                        parts.append(text_value)
            content = "".join(parts)

        if not content:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenAI returned an empty response",
            )

        return content

    @staticmethod
    def _build_payload(
        messages: list[dict[str, Any]], system_prompt: str | None
    ) -> list[dict[str, Any]]:
        """Prepare message payload including optional system prompt."""
        payload: list[dict[str, Any]] = []

        if system_prompt:
            payload.append({"role": "system", "content": system_prompt})

        payload.extend({"role": msg["role"], "content": msg["content"]} for msg in messages)

        return payload
