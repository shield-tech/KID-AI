from __future__ import annotations

import asyncio

from kid.core.errors import ProviderError
from kid.core.models import GenerationOptions, Message, ProviderResponse


class GeminiProvider:
    """Google Gemini adapter."""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._model_client = None
        self._import_error: Exception | None = None

        try:
            import google.generativeai as genai
        except ImportError as exc:  # pragma: no cover - import guard
            self._import_error = exc
            return

        genai.configure(api_key=self.api_key)
        self._model_client = genai.GenerativeModel(self.model)

    async def generate(
        self,
        messages: list[Message],
        options: GenerationOptions,
    ) -> ProviderResponse:
        if self._model_client is None:
            raise ProviderError(
                "Google Generative AI package is not installed. Install it with `pip install google-generativeai`."
            )

        prompt = "\n".join(f"{message.role}: {message.content}" for message in messages)

        try:
            response = await asyncio.to_thread(self._model_client.generate_content, prompt)
            text = getattr(response, "text", "") or ""
            return ProviderResponse(
                text=text,
                provider="gemini",
                usage={"input_tokens": getattr(response, "usage_metadata", {}).input_tokens, "output_tokens": getattr(response, "usage_metadata", {}).output_tokens} if getattr(response, "usage_metadata", None) else None,
                finish_reason=getattr(response, "finish_reason", None),
            )
        except Exception as exc:  # pragma: no cover - runtime/network path
            raise ProviderError(f"Gemini request failed: {exc}") from exc
