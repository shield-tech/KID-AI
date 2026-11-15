"""Strictly local Ollama client. This module never downloads models."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from kid.config import Settings


class OllamaError(RuntimeError):
    """Ollama is unavailable or returned an invalid response."""


@dataclass(frozen=True)
class OllamaStatus:
    connected: bool
    installed_models: tuple[str, ...] = ()
    loaded_models: tuple[str, ...] = ()
    error: str | None = None


class OllamaClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        if settings.ollama_url not in {"http://127.0.0.1:11434", "http://localhost:11434"}:
            raise ValueError("Only the loopback Ollama endpoint is allowed.")

    def _get_json(self, path: str) -> dict:
        request = Request(self.settings.ollama_url + path, headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=3) as response:
                return json.loads(response.read().decode("utf-8"))
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise OllamaError(f"Ollama is unavailable at {self.settings.ollama_url}: {exc}") from exc

    def status(self) -> OllamaStatus:
        try:
            tags = self._get_json("/api/tags")
            running = self._get_json("/api/ps")
            installed = tuple(
                str(item.get("name", "")) for item in tags.get("models", []) if item.get("name")
            )
            loaded = tuple(
                str(item.get("name", "")) for item in running.get("models", []) if item.get("name")
            )
            return OllamaStatus(True, installed, loaded)
        except OllamaError as exc:
            return OllamaStatus(False, error=str(exc))

    def generate(self, model: str, prompt: str, history: list[dict[str, str]] | None = None) -> str:
        """Generate a response from an already-installed model; never pulls."""
        if model not in self.status().installed_models:
            raise OllamaError(f"Model {model!r} is not installed. K.I.D will not download it automatically.")
        messages = list(history or [])
        messages.append({"role": "user", "content": prompt})
        payload = json.dumps({"model": model, "messages": messages, "stream": False}).encode("utf-8")
        request = Request(
            self.settings.ollama_url + "/api/chat",
            data=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.settings.request_timeout_seconds) as response:
                result = json.loads(response.read().decode("utf-8"))
            text = result.get("message", {}).get("content")
            if not isinstance(text, str):
                raise OllamaError("Ollama returned no message text.")
            return text
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise OllamaError(f"Local Ollama inference failed: {exc}") from exc

    async def agenerate(self, model: str, prompt: str, history: list[dict[str, str]] | None = None) -> str:
        return await asyncio.to_thread(self.generate, model, prompt, history)
