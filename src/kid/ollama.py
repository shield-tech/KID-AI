"""Local model client for Ollama (loopback only)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import requests

from kid.config import Settings


class OllamaError(RuntimeError):
    """Raised when a local Ollama request fails."""


@dataclass(frozen=True)
class OllamaStatus:
    connected: bool
    installed_models: list[str]
    loaded_models: list[str]
    error: str | None = None


class OllamaClient:
    """Small loopback-only client used to discover and query local Ollama models."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _request(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        url = self.settings.ollama_url.rstrip("/") + path
        response = self.session.post(url, json=payload, timeout=self.settings.request_timeout_seconds)
        if response.status_code >= 400:
            raise OllamaError(f"Ollama request failed: {response.status_code} {response.text}")
        return response.json()

    def status(self) -> OllamaStatus:
        try:
            tags = self._request("/api/tags")
            ps = self._request("/api/ps")
        except Exception as exc:  # pragma: no cover - runtime path, not unit test branch
            return OllamaStatus(False, [], [], str(exc))

        installed = []
        for item in tags.get("models", []):
            name = item.get("name")
            if name:
                installed.append(name)

        loaded = []
        for item in ps.get("models", []):
            name = item.get("name")
            if name:
                loaded.append(name)

        return OllamaStatus(True, installed, loaded)

    def generate(self, model: str, prompt: str, history: list[dict[str, str]] | None = None) -> str:
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        if history:
            payload["messages"] = [
                {"role": item["role"], "content": item["content"]}
                for item in history
            ] + [{"role": "user", "content": prompt}]

        response = self._request("/api/chat", payload)
        message = response.get("message", {})
        content = message.get("content")
        if not isinstance(content, str):
            raise OllamaError("Ollama response did not include text content.")
        return content
