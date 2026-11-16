from __future__ import annotations

import json
import queue
import time
from pathlib import Path
from typing import Any, Optional


class VoiceInput:
    """Explicit, one-shot offline Vosk capture; no microphone stream starts on import/init."""

    def __init__(self, config: Optional[object] = None) -> None:
        self.config = config
        self.enabled = bool(getattr(config, "voice_input_enabled", False)) if config else False
        self.vosk_model_dir = Path(getattr(config, "vosk_model_dir", "models/vosk") if config else "models/vosk").expanduser()
        self.mic_device = getattr(config, "microphone_device", "default") if config else "default"
        self._model = None
        self._vosk = None
        self._sounddevice = None

    def initialize(self) -> bool:
        if not self.enabled:
            return False
        if not self.vosk_model_dir.is_dir():
            return False
        try:
            import sounddevice
            import vosk
            self._vosk = vosk
            self._sounddevice = sounddevice
            self._model = vosk.Model(str(self.vosk_model_dir))
            return True
        except (ImportError, OSError, RuntimeError):
            self._model = None
            return False

    def available_devices(self) -> list[dict[str, Any]]:
        if self._sounddevice is None:
            try:
                import sounddevice
            except ImportError:
                return []
            self._sounddevice = sounddevice
        try:
            return [dict(item) for item in self._sounddevice.query_devices() if int(item.get("max_input_channels", 0)) > 0]
        except (OSError, RuntimeError):
            return []

    def listen_once(self, *, max_seconds: float = 20.0, silence_seconds: float = 1.2) -> Optional[str]:
        """Capture only during this call. Invocation is the push-to-talk activation."""
        if not self.enabled or self._model is None or self._sounddevice is None or self._vosk is None:
            return None
        audio_queue: queue.Queue[bytes] = queue.Queue()
        samplerate = 16000
        device: Any = None if str(self.mic_device).lower() in {"default", ""} else self.mic_device
        try:
            recognizer = self._vosk.KaldiRecognizer(self._model, samplerate)
            last_audio = time.monotonic()
            deadline = last_audio + max(1.0, max_seconds)

            def callback(indata, frames, timing, status):
                del frames, timing, status
                audio_queue.put(bytes(indata))

            # sounddevice opens the input stream only for this explicit one-shot call.
            with self._sounddevice.RawInputStream(samplerate=samplerate, blocksize=8000, dtype="int16", channels=1, device=device, callback=callback):
                while time.monotonic() < deadline:
                    try:
                        chunk = audio_queue.get(timeout=0.25)
                    except queue.Empty:
                        if time.monotonic() - last_audio >= silence_seconds:
                            break
                        continue
                    last_audio = time.monotonic()
                    if recognizer.AcceptWaveform(chunk):
                        result = json.loads(recognizer.Result())
                        text = str(result.get("text", "")).strip()
                        if text:
                            return text
                final = json.loads(recognizer.FinalResult())
                text = str(final.get("text", "")).strip()
                return text or None
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError):
            return None

    def is_available(self) -> bool:
        return bool(self.enabled and self._model is not None and self._sounddevice is not None)


__all__ = ["VoiceInput"]
