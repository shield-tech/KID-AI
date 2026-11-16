from __future__ import annotations

import os
from typing import Any, Dict, List, Optional


class VisionManager:
    def __init__(self, ollama_engine: Any) -> None:
        self.ollama = ollama_engine

    async def supports_vision(self, model_name: str) -> bool:
        info = await self.ollama.model_info(model_name)
        if not info:
            return False
        capabilities = info.get("details", {}).get("capabilities", [])
        return "vision" in capabilities or "visual" in str(info).lower()

    async def analyze(self, model_name: str, image_path: str, prompt: str = "Describe this image.") -> str:
        if not os.path.exists(image_path):
            return "Image path does not exist."
        if not await self.supports_vision(model_name):
            return f"Model '{model_name}' does not advertise vision support."
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_path],
                }
            ],
            "stream": False,
        }
        try:
            return "Vision analysis is not available because the Ollama client in this prototype does not expose the chat API for images."
        except Exception:
            return "Vision request failed."


__all__ = ["VisionManager"]
