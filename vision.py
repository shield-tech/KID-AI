from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import httpx


class VisionManager:
    """Local Ollama vision checks and image analysis; never assumes capability from a name."""

    IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

    def __init__(self, ollama: Any = None, config: Any = None) -> None:
        self.ollama = ollama
        self.config = config

    async def vision_capabilities(self) -> Dict[str, bool]:
        if self.ollama is None:
            return {}
        try:
            models = await self.ollama.available_models()
        except Exception:
            return {}
        capabilities: Dict[str, bool] = {}
        for model in models:
            try:
                info = await self.ollama.model_info(model)
            except Exception:
                capabilities[model] = False
                continue
            caps = info.get("capabilities", [])
            if not isinstance(caps, list):
                caps = []
            capabilities[model] = "vision" in {str(item).lower() for item in caps}
        return capabilities

    async def available_models(self) -> List[str]:
        return [model for model, supports in (await self.vision_capabilities()).items() if supports]

    async def status(self) -> Dict[str, Any]:
        caps = await self.vision_capabilities()
        return {
            "enabled": bool(getattr(self.config, "enable_vision", True) if self.config else True),
            "models": [name for name, supports in caps.items() if supports],
            "unverified_models": [name for name, supports in caps.items() if not supports],
            "camera_connected": False,
            "message": "Image-path analysis only; no camera is configured or verified.",
        }

    async def describe_status(self) -> str:
        info = await self.status()
        models = ", ".join(info["models"]) if info["models"] else "none verified"
        return f"Vision: {'enabled' if info['enabled'] else 'disabled'} | verified models={models} | camera_connected=false | {info['message']}"

    async def analyze(self, model_name: str, image_path: str, prompt: str = "Describe this image accurately.") -> str:
        if not bool(getattr(self.config, "enable_vision", True) if self.config else True):
            return "Vision is disabled in configuration."
        capabilities = await self.vision_capabilities()
        if not capabilities.get(model_name, False):
            return f"Model {model_name!r} is not verified as vision-capable via Ollama /api/show."
        path = Path(image_path).expanduser().resolve()
        if path.suffix.lower() not in self.IMAGE_SUFFIXES:
            return "Unsupported image type. Use PNG, JPEG, WEBP, or BMP."
        try:
            if not path.is_file():
                return "Image file does not exist or is not a regular file."
            if path.stat().st_size > 20 * 1024 * 1024:
                return "Image exceeds K.I.D's 20 MiB safety limit."
            import base64
            image_b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        except OSError as exc:
            return f"Could not read image: {exc}"

        base_url = str(getattr(self.ollama, "base_url", "http://127.0.0.1:11434")).rstrip("/")
        config = self.config
        payload = {
            "model": model_name,
            "stream": False,
            "keep_alive": getattr(config, "keep_alive", "5m"),
            "messages": [{"role": "user", "content": prompt.strip() or "Describe this image accurately.", "images": [image_b64]}],
            "options": {
                "temperature": getattr(config, "temperature", 0.2),
                "num_ctx": getattr(config, "num_ctx", 4096),
                "num_predict": getattr(config, "num_predict", 512),
            },
        }
        timeout = httpx.Timeout(float(getattr(config, "request_timeout", 180.0)), connect=5.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(f"{base_url}/api/chat", json=payload)
                response.raise_for_status()
                message = response.json().get("message", {})
                content = message.get("content", "")
                return str(content).strip() if content else "Ollama returned no image-analysis text."
        except httpx.HTTPStatusError as exc:
            return f"Ollama vision request failed ({exc.response.status_code}): {exc.response.text[:300]}"
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            return f"Ollama vision request failed: {exc}"


__all__ = ["VisionManager"]
