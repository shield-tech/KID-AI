from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx


class OllamaError(RuntimeError):
    """A clear, user-facing local Ollama API error."""


class OllamaEngine:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.base_url = str(getattr(config, "ollama_base_url", "http://127.0.0.1:11434")).rstrip("/")
        self.last_stats: Dict[str, Any] = {}

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(self.base_url)
                return response.is_success
        except httpx.HTTPError:
            return False

    async def available_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                entries = response.json().get("models", [])
                return [str(item["name"]) for item in entries if item.get("name")]
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            raise OllamaError(f"Could not list local Ollama models: {exc}") from exc

    async def discover_model(self, preferred: Optional[str] = None) -> Optional[str]:
        models = await self.available_models()
        if preferred and preferred in models:
            return preferred
        return models[0] if models else None

    async def model_info(self, model_name: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{self.base_url}/api/show", json={"name": model_name})
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OllamaError(f"Could not inspect model {model_name!r}: {exc}") from exc

    async def generate(
        self,
        model_name: str,
        prompt: str,
        *,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        images: Optional[List[str]] = None,
    ) -> AsyncIterator[str]:
        if not model_name.strip():
            raise OllamaError("Select an installed model before sending a prompt.")
        payload: Dict[str, Any] = {
            "model": model_name,
            "prompt": prompt,
            "stream": True,
            "keep_alive": getattr(self.config, "keep_alive", "5m"),
            "options": {
                "temperature": getattr(self.config, "temperature", 0.7),
                "num_ctx": getattr(self.config, "num_ctx", 4096),
                "num_predict": max_tokens or getattr(self.config, "num_predict", 512),
                "num_thread": getattr(self.config, "num_thread", 4),
            },
        }
        if system_prompt:
            payload["system"] = system_prompt
        if images:
            payload["images"] = images
        self.last_stats = {}
        timeout = httpx.Timeout(float(getattr(self.config, "request_timeout", 180.0)), connect=5.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            item = json.loads(line)
                        except json.JSONDecodeError as exc:
                            raise OllamaError("Ollama returned malformed streaming data.") from exc
                        token = item.get("response")
                        if token:
                            yield str(token)
                        if item.get("done"):
                            self.last_stats = item
                            break
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            raise OllamaError(f"Ollama request failed ({exc.response.status_code}): {detail}") from exc
        except httpx.TimeoutException as exc:
            raise OllamaError("Ollama request timed out.") from exc
        except httpx.HTTPError as exc:
            raise OllamaError(f"Could not connect to Ollama at {self.base_url}: {exc}") from exc

    async def warmup(self, model_name: str) -> None:
        async for _ in self.generate(model_name, "Reply with OK.", max_tokens=2):
            pass


__all__ = ["OllamaEngine", "OllamaError"]
