from __future__ import annotations

from typing import Any, Dict, List


class VisionManager:
    """Safe, honest vision-capability detection for local Ollama models."""

    def __init__(self, ollama: Any = None, config: Any = None) -> None:
        self.ollama = ollama
        self.config = config

    async def available_models(self) -> List[str]:
        if self.ollama is None:
            return []
        try:
            models = await self.ollama.available_models()
        except Exception:
            return []
        keywords = ("vision", "llava", "bakllava", "qwen2.5-vl", "llama3.2-vision", "gemma3")
        return [name for name in models if any(token in name.lower() for token in keywords)]

    async def status(self) -> Dict[str, Any]:
        models = await self.available_models()
        return {
            "enabled": bool(getattr(self.config, "enable_vision", True) if self.config else True),
            "models": models,
            "camera_connected": False,
            "message": "No camera is confirmed connected; vision support is limited to locally installed Ollama vision-capable models.",
        }

    async def describe_status(self) -> str:
        info = await self.status()
        model_text = ", ".join(info["models"]) if info["models"] else "none detected"
        return f"Vision: {'enabled' if info['enabled'] else 'disabled'} | models={model_text} | camera_connected={str(info['camera_connected']).lower()} | {info['message']}"


__all__ = ["VisionManager"]
