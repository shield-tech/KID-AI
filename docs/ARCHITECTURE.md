from __future__ import annotations

from kid.core.errors import ProviderError
from kid.core.models import GenerationOptions, Message, ProviderResponse


class OpenAIProvider:
    """OpenAI adapter."""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = base_url
        self._client = None

        try:
            from openai import AsyncOpenAI
        except ImportError:  # pragma: no cover - import guard
            self._client = None
            return

        self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def generate(
        self,
        messages: list[Message],
        options: GenerationOptions,
    ) -> ProviderResponse:
        if self._client is None:
            raise ProviderError(
                "OpenAI package is not installed. Install it with `pip install openai`."
            )

        payload = [
            {"role": message.role, "content": message.content}
            for message in messages
        ]

        try:
            response = await self._client.chat.completions.create(
                model=options.model,
                messages=payload,
                temperature=options.temperature,
                max_tokens=options.max_tokens,
            )
            text = response.choices[0].message.content or ""
            usage = getattr(response, "usage", None)
            usage_dict = None
            if usage is not None:
                usage_dict = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(usage, "completion_tokens", 0),
                    "total_tokens": getattr(usage, "total_tokens", 0),
                }
            return ProviderResponse(
                text=text,
                provider="openai",
                usage=usage_dict,
                finish_reason=getattr(response.choices[0], "finish_reason", None),
            )
        except Exception as exc:  # pragma: no cover - runtime/network path
            raise ProviderError(f"OpenAI request failed: {exc}") from exc
