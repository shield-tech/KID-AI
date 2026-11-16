from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


@dataclass
class AppConfig:
    ollama_base_url: str = "http://127.0.0.1:11434"
    default_model: str = ""
    chat_model: str = ""
    keep_alive: str = "5m"
    num_ctx: int = 4096
    num_predict: int = 512
    temperature: float = 0.7
    num_thread: int = 4
    memory_db_path: str = "kid_memory.sqlite3"
    knowledge_root: str = "knowledge"
    task_db_path: str = ".kid/tasks.json"
    voice_output_enabled: bool = True
    voice_input_enabled: bool = False
    piper_voice: str = "en_US-lessac-medium"
    piper_voice_dir: str = "voices"
    espeak_voice: str = "en-us"
    speech_volume: float = 1.0
    speech_speed: float = 1.0
    vosk_model_dir: str = "models/vosk"
    microphone_device: str = "default"
    wake_word_enabled: bool = False
    wake_word: str = "kid"
    enable_vision: bool = True
    memory_enabled: bool = True
    knowledge_enabled: bool = True
    audit_log_path: str = "kid_audit.log"
    robot_authorization_required: bool = True
    robot_simulation_mode: bool = True
    robot_port: str = ""
    allow_external_network: bool = False
    warmup_model: bool = False
    request_timeout: float = 180.0

    @classmethod
    def from_env(cls) -> "AppConfig":
        if load_dotenv is not None:
            load_dotenv(Path(".env"), override=False)
        cfg = cls()
        mapping = {
            "OLLAMA_BASE_URL": ("ollama_base_url", str),
            "KID_DEFAULT_MODEL": ("default_model", str),
            "KID_CHAT_MODEL": ("chat_model", str),
            "KID_KEEP_ALIVE": ("keep_alive", str),
            "KID_NUM_CTX": ("num_ctx", int),
            "KID_NUM_PREDICT": ("num_predict", int),
            "KID_TEMPERATURE": ("temperature", float),
            "KID_NUM_THREAD": ("num_thread", int),
            "KID_MEMORY_DB_PATH": ("memory_db_path", str),
            "KID_KNOWLEDGE_ROOT": ("knowledge_root", str),
            "KID_TASK_DB_PATH": ("task_db_path", str),
            "KID_VOICE_OUTPUT_ENABLED": ("voice_output_enabled", _bool),
            "KID_VOICE_INPUT_ENABLED": ("voice_input_enabled", _bool),
            "KID_PIPER_VOICE": ("piper_voice", str),
            "KID_PIPER_VOICE_DIR": ("piper_voice_dir", str),
            "KID_ESPEAK_VOICE": ("espeak_voice", str),
            "KID_SPEECH_VOLUME": ("speech_volume", float),
            "KID_SPEECH_SPEED": ("speech_speed", float),
            "VOSK_MODEL_DIR": ("vosk_model_dir", str),
            "KID_MICROPHONE_DEVICE": ("microphone_device", str),
            "KID_WAKE_WORD_ENABLED": ("wake_word_enabled", _bool),
            "KID_WAKE_WORD": ("wake_word", str),
            "KID_ENABLE_VISION": ("enable_vision", _bool),
            "KID_MEMORY_ENABLED": ("memory_enabled", _bool),
            "KID_KNOWLEDGE_ENABLED": ("knowledge_enabled", _bool),
            "KID_AUDIT_LOG_PATH": ("audit_log_path", str),
            "KID_ROBOT_SIMULATION": ("robot_simulation_mode", _bool),
            "KID_ROBOT_PORT": ("robot_port", str),
            "KID_WARMUP_MODEL": ("warmup_model", _bool),
            "KID_REQUEST_TIMEOUT": ("request_timeout", float),
        }
        for env, (attr, caster) in mapping.items():
            raw = os.getenv(env)
            if raw is not None:
                setattr(cfg, attr, caster(raw))
        if cfg.num_ctx < 256 or cfg.num_predict < 1 or cfg.num_thread < 1:
            raise ValueError("num_ctx must be >=256; num_predict and num_thread must be positive")
        if not 0 <= cfg.temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")
        if not 0 <= cfg.speech_volume <= 1 or not 0.5 <= cfg.speech_speed <= 2:
            raise ValueError("speech volume must be 0..1 and speech speed must be 0.5..2")
        return cfg


def _bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


__all__ = ["AppConfig"]
