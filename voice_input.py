from __future__ import annotations

import os
import shutil
import subprocess
from typing import Optional


class VoiceInput:
    def __init__(self, config: Optional[object] = None) -> None:
        self.config = config
        self.enabled = bool(getattr(config, "voice_input_enabled", False)) if config else False
        self.vosk_model_dir = getattr(config, "vosk_model_dir", "models/vosk") if config else "models/vosk"
        self.mic_device = getattr(config, "microphone_device", "default") if config else "default"
        self._vosk_ready = False

    def initialize(self) -> bool:
        if not self.enabled:
            return False
        try:
            import vosk  # type: ignore
        except Exception:
            print("[VOICE INPUT] Vosk is not installed. Voice input will remain unavailable.")
            return False
        if not os.path.isdir(self.vosk_model_dir):
            print(f"[VOICE INPUT] Vosk model directory not found: {self.vosk_model_dir}")
            return False
        self._vosk_ready = True
        return True

    def listen_once(self) -> Optional[str]:
        if not self._vosk_ready:
            return None
        print("[VOICE INPUT] Push-to-talk not active in this prototype; manual text input is supported.")
        return None

    def is_available(self) -> bool:
        return self._vosk_ready


__all__ = ["VoiceInput"]
