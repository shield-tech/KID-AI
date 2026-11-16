from __future__ import annotations

import queue
import threading
from typing import Callable, Optional


class SpeechQueue:
    """Single-worker speech queue: serializes playback and supports flush/stop."""

    def __init__(self) -> None:
        self._queue: queue.Queue[Optional[str]] = queue.Queue()
        self._worker: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._callback: Optional[Callable[[str], None]] = None
        self._lock = threading.Lock()

    def start(self, callback: Callable[[str], None]) -> None:
        with self._lock:
            self._callback = callback
            if self._worker and self._worker.is_alive():
                return
            self._stop_event.clear()
            self._worker = threading.Thread(target=self._run, name="kid-speech", daemon=True)
            self._worker.start()

    def enqueue(self, text: str) -> None:
        value = text.strip()
        if value and not self._stop_event.is_set():
            self._queue.put(value)

    def stop(self) -> None:
        """Discard queued speech and interrupt current playback via callback hook."""
        self._stop_event.set()
        while True:
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break
        callback = self._callback
        stop_callback = getattr(callback, "stop", None)
        if callable(stop_callback):
            stop_callback()
        self._stop_event.clear()

    def close(self, timeout: float = 1.0) -> None:
        self._stop_event.set()
        self._queue.put(None)
        if self._worker:
            self._worker.join(timeout=timeout)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                text = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if text is None:
                self._queue.task_done()
                return
            try:
                if self._callback:
                    self._callback(text)
            finally:
                self._queue.task_done()


__all__ = ["SpeechQueue"]
