from __future__ import annotations

import asyncio
import inspect
import json
from typing import Any, Dict, List, Optional

import httpx


class OllamaEngine:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.base_url = getattr(config, "ollama_base_url", "http://127.0.0.1:11434")
        self.headers = {"Content-Type": "application/json"}

    async def available_models(self) -> List[str]:
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                payload = response.json()
                models = payload.get("models", [])
                return [entry.get("name", "") for entry in models if entry.get("name")]
        except Exception:
            return []

    async def discover_model(self, preferred: Optional[str] = None) -> Optional[str]:
        models = await self.available_models()
        if not models:
            return None
        if preferred and preferred in models:
            return preferred
        return models[0]

    async def warmup(self, model_name: Optional[str] = None) -> None:
        model = model_name or self.config.chat_model
        await self.generate(model, "Warm up.", max_tokens=10, stream=False)

    async def generate(
        self,
        model_name: str,
        prompt: str,
        *,
        max_tokens: Optional[int] = None,
        stream: bool = True,
        stop: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
    ) -> Any:
        payload: Dict[str, Any] = {
            "model": model_name,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": getattr(self.config, "temperature", 0.7),
                "num_ctx": getattr(self.config, "num_ctx", 4096),
                "num_predict": max_tokens or getattr(self.config, "num_predict", 512),
                "num_thread": getattr(self.config, "num_thread", 4),
            },
            "keep_alive": getattr(self.config, "keep_alive", "5m"),
        }
        if system_prompt:
            payload["system"] = system_prompt
        if stop:
            payload["stop"] = stop

        async with httpx.AsyncClient(timeout=120.0) as client:
            if stream:
                async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as resp:
                    await resp.raise_for_status()
                    async for chunk in resp.aiter_lines():
                        if not chunk:
                            continue
                        try:
                            decoded = json.loads(chunk)
                        except Exception:
                            continue
                        if decoded.get("done"):
                            return decoded
                        token = decoded.get("response")
                        if token:
                            yield token
            else:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                resp.raise_for_status()
                return resp.json()

    async def model_info(self, model_name: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/show"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json={"name": model_name})
                resp.raise_for_status()
                return resp.json()
        except Exception:
            return {}


__all__ = ["OllamaEngine"]
