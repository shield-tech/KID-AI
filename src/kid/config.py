"""Local Ollama and hardware configuration for K.I.D."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModelProfile:
    key: str
    env_name: str
    default: str
    estimated_ram_gib: float
    purpose: str


MODEL_PROFILES = (
    ModelProfile("primary", "KID_MODEL_PRIMARY", "llama3.2:3b", 3.0, "Conversation"),
    ModelProfile("lightweight", "KID_MODEL_LIGHTWEIGHT", "llama3.2:1b", 1.5, "Lightweight conversation"),
    ModelProfile("vision", "KID_MODEL_VISION", "qwen2.5vl:3b", 4.0, "Image understanding"),
    ModelProfile("experimental", "KID_MODEL_EXPERIMENTAL", "llama3:8b", 6.0, "Experimental"),
)


@dataclass(frozen=True)
class Settings:
    ollama_url: str = "http://127.0.0.1:11434"
    primary_model: str = "llama3.2:3b"
    lightweight_model: str = "llama3.2:1b"
    vision_model: str = "qwen2.5vl:3b"
    experimental_model: str = "llama3:8b"
    data_dir: Path = Path.home() / ".local" / "share" / "kid"
    request_timeout_seconds: float = 120.0
    memory_pressure_gib: float = 2.0

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings, rejecting non-loopback Ollama endpoints."""
        url = os.getenv("KID_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
        if url not in {"http://127.0.0.1:11434", "http://localhost:11434"}:
            raise ValueError("K.I.D only permits the local Ollama endpoint at 127.0.0.1:11434.")
        return cls(
            ollama_url=url,
            primary_model=os.getenv("KID_MODEL_PRIMARY", "llama3.2:3b"),
            lightweight_model=os.getenv("KID_MODEL_LIGHTWEIGHT", "llama3.2:1b"),
            vision_model=os.getenv("KID_MODEL_VISION", "qwen2.5vl:3b"),
            experimental_model=os.getenv("KID_MODEL_EXPERIMENTAL", "llama3:8b"),
            data_dir=Path(os.getenv("KID_DATA_DIR", str(Path.home() / ".local/share/kid"))).expanduser(),
            request_timeout_seconds=float(os.getenv("KID_OLLAMA_TIMEOUT", "120")),
            memory_pressure_gib=float(os.getenv("KID_MEMORY_PRESSURE_GIB", "2.0")),
        )

    def models(self) -> dict[str, str]:
        return {
            "Conversation": self.primary_model,
            "Lightweight": self.lightweight_model,
            "Vision (load only when requested)": self.vision_model,
            "Experimental": self.experimental_model,
        }

    def model_ram_estimate(self, model: str) -> float:
        configured = {
            self.primary_model: 3.0,
            self.lightweight_model: 1.5,
            self.vision_model: 4.0,
            self.experimental_model: 6.0,
        }
        return configured.get(model, 3.0)
