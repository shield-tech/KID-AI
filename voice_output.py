from __future__ import annotations

import os
import shutil
import subprocess
import threading
from typing import Optional


class VoiceOutput:
    def __init__(self, config: Optional[object] = None) -> None:
        self.config = config
        self._enabled = True
        self._muted = False
        self._lock = threading.Lock()
        self._voice = getattr(config, "piper_voice", "default") if config else "default"
        self._volume = getattr(config, "speech_volume", 1.0) if config else 1.0
        self._speed = getattr(config, "speech_speed", 1.0) if config else 1.0

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def set_muted(self, muted: bool) -> None:
        self._muted = muted

    def set_voice(self, voice: str) -> None:
        self._voice = voice

    def set_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(2.0, volume))

    def set_speed(self, speed: float) -> None:
        self._speed = max(0.5, min(2.0, speed))

    def stop(self) -> None:
        for proc_name in ("piper", "espeak-ng", "espeak"):
            try:
                subprocess.run(["pkill", "-f", proc_name], check=False)
            except Exception:
                pass

    def speak(self, text: str) -> None:
        if not self._enabled or self._muted or not text.strip():
            return
        with self._lock:
            if shutil.which("piper"):
                self._speak_with_piper(text)
            elif shutil.which("espeak-ng"):
                self._speak_with_espeak(text)
            else:
                print(f"[VOICE] {text}")

    def _speak_with_piper(self, text: str) -> None:
        try:
            voice = self._voice
            cmd = ["piper", "--model", f"{voice}.onnx", "--output-raw", "--voice", voice]
            subprocess.run(cmd, input=text.encode("utf-8"), check=False)
        except Exception:
            self._speak_with_espeak(text)

    def _speak_with_espeak(self, text: str) -> None:
        try:
            cmd = ["espeak-ng", "-v", self._voice, "-s", str(int(140 * self._speed)), "-a", str(int(200 * self._volume)), text]
            subprocess.run(cmd, check=False)
        except Exception:
            print(f"[VOICE] {text}")


__all__ = ["VoiceOutput"]
