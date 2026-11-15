"""Offline speech recognition adapter for K.I.D using Vosk."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_VOSK_MODEL_NAME = "vosk-model-cn-0.22"
DEFAULT_VOSK_MODEL_PATH = Path.home() / ".local" / "share" / "vosk" / DEFAULT_VOSK_MODEL_NAME


@dataclass
class VoiceConfig:
    model_name: str = DEFAULT_VOSK_MODEL_NAME
    model_path: str = str(DEFAULT_VOSK_MODEL_PATH)
    microphone_index: int | None = None
    continuous_listening: bool = False
    push_to_talk: bool = True

    @classmethod
    def from_env(cls) -> "VoiceConfig":
        return cls(
            model_name=os.getenv("KID_VOSK_MODEL_NAME", DEFAULT_VOSK_MODEL_NAME),
            model_path=os.getenv("KID_VOSK_MODEL_PATH", str(DEFAULT_VOSK_MODEL_PATH)),
            microphone_index=int(os.getenv("KID_MICROPHONE_INDEX", "0")) if os.getenv("KID_MICROPHONE_INDEX") else None,
            continuous_listening=os.getenv("KID_CONTINUOUS_LISTENING", "false").lower() in {"1", "true", "yes"},
            push_to_talk=os.getenv("KID_PUSH_TO_TALK", "true").lower() in {"1", "true", "yes"},
        )


class VoskRecognizer:
    """Thin abstraction around the local Vosk model and Python package."""

    def __init__(self, config: VoiceConfig | None = None):
        self.config = config or VoiceConfig.from_env()
        self._available = False
        self._error: str | None = None
        try:
            import vosk  # type: ignore
            from vosk import Model  # type: ignore
        except ImportError as exc:  # pragma: no cover - dependency not installed
            self._available = False
            self._error = f"vosk is not installed: {exc}"
            return

        model_path = Path(self.config.model_path).expanduser()
        if not model_path.exists():
            self._available = False
            self._error = f"Vosk model not found at {model_path}. Download the official model manually."
            return

        self._available = True
        self._model = Model(str(model_path))
        self._vosk = vosk

    @property
    def available(self) -> bool:
        return self._available

    @property
    def error(self) -> str | None:
        return self._error

    def recognize(self, audio_data: bytes) -> str:
        """Return a transcript for captured microphone data. Actual streaming is delegated to a real Vosk runtime."""
        if not self.available:
            raise RuntimeError(self._error or "Vosk is unavailable")
        from vosk import KaldiRecognizer

        recognizer = KaldiRecognizer(self._model, 16000)
        recognizer.AcceptWaveform(audio_data)
        result = recognizer.Result()
        try:
            import json

            return json.loads(result).get("text", "")
        except (TypeError, ValueError, json.JSONDecodeError):
            return result
