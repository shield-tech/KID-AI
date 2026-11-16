from __future__ import annotations

import queue
import subprocess
import threading
import time
from typing import Any, Callable, Optional


class SpeechQueue:
    def __init__(self) -> None:
        self._queue: "queue.Queue[tuple[str, float, str]]" = queue.Queue()
        self._worker: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._active = False

    def start(self, callback: Callable[[str], None]) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._stop_event.clear()
        self._worker = threading.Thread(target=self._run_worker, args=(callback,), daemon=True)
        self._worker.start()

    def enqueue(self, text: str, volume: float = 1.0, voice: str = "default") -> None:
        self._queue.put((text, volume, voice))

    def stop(self) -> None:
        self._stop_event.set()

    def _run_worker(self, callback: Callable[[str], None]) -> None:
        while not self._stop_event.is_set():
            try:
                text, volume, voice = self._queue.get(timeout=0.25)
            except queue.Empty:
                continue
            try:
                callback(text)
            finally:
                self._queue.task_done()


__all__ = ["SpeechQueue"]
