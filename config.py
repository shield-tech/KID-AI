from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None


@dataclass
class AppConfig:
    ollama_base_url: str = "http://127.0.0.1:11434"
    default_model: str = "llama3.2"
    chat_model: str = "llama3.2"
    fallback_model: str = "llama3.1"
    keep_alive: str = "5m"
    num_ctx: int = 4096
    num_predict: int = 512
    temperature: float = 0.7
    num_thread: int = 4
    max_memory_items: int = 100
    memory_db_path: str = "kid_memory.sqlite3"
    knowledge_root: str = "knowledge"
    voice_output_enabled: bool = True
    voice_input_enabled: bool = False
    voice_model: str = "default"
    piper_voice: str = "en_US-lessac-medium"
    espeak_voice: str = "en-us"
    speech_volume: float = 1.0
    speech_speed: float = 1.0
    microphone_device: str = "default"
    wake_word_enabled: bool = False
    wake_word: str = "kid"
    enable_vision: bool = True
    memory_enabled: bool = True
    knowledge_enabled: bool = True
    audit_log_path: str = "kid_audit.log"
    robot_authorization_required: bool = True
    robot_simulation_mode: bool = True
    allow_external_network: bool = False
    voice_fallback_to_text: bool = True

    @classmethod
    def from_env(cls) -> "AppConfig":
        if load_dotenv is not None:
            load_dotenv(Path(".env"), override=False)

        cfg = cls()
        env_map = {
            "OLLAMA_BASE_URL": "ollama_base_url",
            "KID_DEFAULT_MODEL": "default_model",
            "KID_CHAT_MODEL": "chat_model",
            "KID_FALLBACK_MODEL": "fallback_model",
            "KID_KEEP_ALIVE": "keep_alive",
            "KID_NUM_CTX": "num_ctx",
            "KID_NUM_PREDICT": "num_predict",
            "KID_TEMPERATURE": "temperature",
            "KID_NUM_THREAD": "num_thread",
            "KID_MEMORY_DB_PATH": "memory_db_path",
            "KID_KNOWLEDGE_ROOT": "knowledge_root",
            "KID_VOICE_OUTPUT_ENABLED": "voice_output_enabled",
            "KID_VOICE_INPUT_ENABLED": "voice_input_enabled",
            "KID_PIPER_VOICE": "piper_voice",
            "KID_ESPEAK_VOICE": "espeak_voice",
            "KID_SPEECH_VOLUME": "speech_volume",
            "KID_SPEECH_SPEED": "speech_speed",
            "KID_MICROPHONE_DEVICE": "microphone_device",
            "KID_WAKE_WORD_ENABLED": "wake_word_enabled",
            "KID_WAKE_WORD": "wake_word",
            "KID_ENABLE_VISION": "enable_vision",
            "KID_MEMORY_ENABLED": "memory_enabled",
            "KID_KNOWLEDGE_ENABLED": "knowledge_enabled",
            "KID_AUDIT_LOG_PATH": "audit_log_path",
            "KID_ROBOT_AUTH_REQUIRED": "robot_authorization_required",
            "KID_ROBOT_SIMULATION": "robot_simulation_mode",
            "KID_ALLOW_EXTERNAL_NETWORK": "allow_external_network",
            "KID_VOICE_FALLBACK_TO_TEXT": "voice_fallback_to_text",
        }

        for env_name, attr_name in env_map.items():
            raw = os.getenv(env_name)
            if raw is None:
                continue
            setattr(cfg, attr_name, _coerce_value(raw, getattr(cfg, attr_name)))

        return cfg


def _coerce_value(raw: str, current: Any) -> Any:
    if isinstance(current, bool):
        val = raw.strip().lower()
        return val in {"1", "true", "yes", "on"}
    if isinstance(current, int):
        return int(raw)
    if isinstance(current, float):
        return float(raw)
    return raw


__all__ = ["AppConfig"]
