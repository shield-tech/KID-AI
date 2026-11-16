from __future__ import annotations

import shutil
import subprocess
import threading
from pathlib import Path
from typing import Optional


class VoiceOutput:
    """Local Piper-first TTS. Playback executes on the speech worker, never the asyncio loop."""

    def __init__(self, config: Optional[object] = None) -> None:
        self.config = config
        self._enabled = bool(getattr(config, "voice_output_enabled", True)) if config else True
        self._muted = False
        self._lock = threading.RLock()
        self._voice = str(getattr(config, "piper_voice", "en_US-lessac-medium")) if config else "en_US-lessac-medium"
        self._voice_dir = Path(getattr(config, "piper_voice_dir", "voices")).expanduser() if config else Path("voices")
        self._fallback_voice = str(getattr(config, "espeak_voice", "en-us")) if config else "en-us"
        self._volume = float(getattr(config, "speech_volume", 1.0)) if config else 1.0
        self._speed = float(getattr(config, "speech_speed", 1.0)) if config else 1.0
        self._process: Optional[subprocess.Popen[bytes]] = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def muted(self) -> bool:
        return self._muted

    @property
    def available_engine(self) -> Optional[str]:
        if shutil.which("piper") and self._piper_model().is_file() and (shutil.which("paplay") or shutil.which("aplay")):
            return "piper"
        if shutil.which("espeak-ng"):
            return "espeak-ng"
        if shutil.which("espeak"):
            return "espeak"
        return None

    def _piper_model(self) -> Path:
        voice = Path(self._voice).expanduser()
        if voice.suffix == ".onnx" or voice.is_absolute() or voice.parent != Path("."):
            return voice
        return self._voice_dir / f"{self._voice}.onnx"

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        if not enabled:
            self.stop()

    def set_muted(self, muted: bool) -> None:
        self._muted = bool(muted)
        if muted:
            self.stop()

    def set_voice(self, voice: str) -> None:
        if not voice.strip():
            raise ValueError("Voice name/path cannot be empty")
        self._voice = voice.strip()

    def set_volume(self, volume: float) -> None:
        if not 0 <= float(volume) <= 1:
            raise ValueError("Volume must be between 0 and 1")
        self._volume = float(volume)

    def set_speed(self, speed: float) -> None:
        if not 0.5 <= float(speed) <= 2.0:
            raise ValueError("Speed must be between 0.5 and 2.0")
        self._speed = float(speed)

    def stop(self) -> None:
        with self._lock:
            proc = self._process
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=0.5)

    def speak(self, text: str) -> None:
        if not text.strip() or not self._enabled or self._muted or self._volume <= 0:
            return
        engine = self.available_engine
        if engine is None:
            return
        with self._lock:
            try:
                if engine == "piper":
                    command = ["piper", "--model", str(self._piper_model()), "--length_scale", str(1.0 / self._speed)]
                    piper = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                    self._process = piper
                    audio, _ = piper.communicate(text.encode("utf-8"), timeout=90)
                    if piper.returncode != 0:
                        raise RuntimeError("Piper synthesis failed")
                    if shutil.which("paplay"):
                        player_command = ["paplay", f"--volume={int(self._volume * 65536)}"]
                    else:
                        player_command = ["aplay", "-q"]
                    player = subprocess.Popen(player_command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self._process = player
                    player.communicate(audio, timeout=90)
                else:
                    executable = "espeak-ng" if engine == "espeak-ng" else "espeak"
                    self._process = subprocess.Popen(
                        [executable, "-v", self._fallback_voice, "-s", str(round(170 * self._speed)), "-a", str(round(200 * self._volume)), text],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                    self._process.wait(timeout=90)
            except (OSError, subprocess.SubprocessError, RuntimeError):
                self.stop()
            finally:
                self._process = None


__all__ = ["VoiceOutput"]
