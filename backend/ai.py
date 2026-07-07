from __future__ import annotations

import os
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv

load_dotenv()

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openrouter/free"


class OpenRouterError(RuntimeError):
    """Raised when an OpenRouter request cannot be completed."""


class OpenRouterClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.base_url = base_url or os.environ.get("OPENROUTER_BASE_URL", DEFAULT_BASE_URL)
        self.model = model or os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL)
        self.timeout = timeout

    def _build_headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise OpenRouterError("OPENROUTER_API_KEY is not set")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **extra_payload: Any,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        payload.update(extra_payload)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.base_url,
                    headers=self._build_headers(),
                    json=payload,
                )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:  # pragma: no cover - exercised via HTTPError branch
            raise OpenRouterError(f"OpenRouter request failed: {exc}") from exc
        except httpx.HTTPError as exc:
            raise OpenRouterError("Unable to reach OpenRouter") from exc

    async def math_connectivity_test(self) -> str:
        messages = [
            {"role": "system", "content": "You are a careful math assistant."},
            {"role": "user", "content": "What is 2 + 2? Respond with only the number."},
        ]
        data = await self.chat_completion(messages, max_tokens=8)
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise OpenRouterError("Malformed response from OpenRouter") from exc
