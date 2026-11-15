"""Local diagnostics, health checks, and environment validation."""

from __future__ import annotations

import json
import os
import socket
from pathlib import Path


def is_loopback_port_open(host: str = "127.0.0.1", port: int = 11434, timeout: float = 1.5) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def collect_debug_report() -> dict[str, object]:
    env = {
        "KID_OLLAMA_URL": os.getenv("KID_OLLAMA_URL", "http://127.0.0.1:11434"),
        "KID_MODEL_PRIMARY": os.getenv("KID_MODEL_PRIMARY", "llama3.2:3b"),
        "KID_MODEL_LIGHTWEIGHT": os.getenv("KID_MODEL_LIGHTWEIGHT", "llama3.2:1b"),
        "KID_MODEL_VISION": os.getenv("KID_MODEL_VISION", "qwen2.5vl:3b"),
        "KID_MODEL_EXPERIMENTAL": os.getenv("KID_MODEL_EXPERIMENTAL", "llama3:8b"),
        "KID_VOSK_MODEL_NAME": os.getenv("KID_VOSK_MODEL_NAME", "vosk-model-cn-0.22"),
        "KID_PIPER_VOICE": os.getenv("KID_PIPER_VOICE", "en_US-lessac-medium"),
    }
    return {
        "ollama_loopback_open": is_loopback_port_open(),
        "environment": env,
    }


def write_debug_report(path: str | Path) -> Path:
    destination = Path(path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(collect_debug_report(), indent=2), encoding="utf-8")
    return destination
