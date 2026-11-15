"""Offline text-to-speech adapter for K.I.D using Piper."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PIPER_VOICE = "en_US-lessac-medium"
DEFAULT_PIPER_MODEL = Path.home() / ".local" / "share" / "piper" / "en_US-lessac-medium.onnx"


@dataclass
class TTSConfig:
    voice: str = DEFAULT_PIPER_VOICE
    model_path: str = str(DEFAULT_PIPER_MODEL)
    speed: float = 1.0
    output_dir: str = str(Path.home() / ".local" / "share" / "kid" / "tts")

    @classmethod
    def from_env(cls) -> "TTSConfig":
        return cls(
            voice=os.getenv("KID_PIPER_VOICE", DEFAULT_PIPER_VOICE),
            model_path=os.getenv("KID_PIPER_MODEL", str(DEFAULT_PIPER_MODEL)),
            speed=float(os.getenv("KID_TTS_SPEED", "1.0")),
            output_dir=os.getenv("KID_TTS_OUTPUT_DIR", str(Path.home() / ".local" / "share" / "kid" / "tts")),
        )


class PiperTTS:
    def __init__(self, config: TTSConfig | None = None):
        self.config = config or TTSConfig.from_env()
        self._binary = shutil.which("piper")
        self._ready = self._binary is not None and Path(self.config.model_path).expanduser().exists()

    @property
    def ready(self) -> bool:
        return self._ready

    def speak(self, text: str, output_path: str | None = None) -> str:
        if not self._binary:
            raise RuntimeError("Piper is not installed and available on PATH.")
        if not Path(self.config.model_path).expanduser().exists():
            raise RuntimeError(f"Piper voice model not found at {self.config.model_path}.")

        target = Path(output_path or self.config.output_dir).expanduser()
        target.mkdir(parents=True, exist_ok=True)
        output_file = target / "response.wav"
        cmd = [
            self._binary,
            "--model",
            str(Path(self.config.model_path).expanduser()),
            "--output_file",
            str(output_file),
            "--sentence_silence",
            "0.1",
        ]
        subprocess.run(cmd, input=text, text=True, check=False)
        return str(output_file)
