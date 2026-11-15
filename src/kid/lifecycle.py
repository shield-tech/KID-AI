"""K.I.D local application lifecycle helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppLifecycle:
    app_name: str = "K.I.D"
    data_dir: str = str(Path.home() / ".local" / "share" / "kid")
    logs_dir: str = str(Path.home() / ".local" / "share" / "kid" / "logs")
    safe_mode: bool = False

    def ensure_dirs(self) -> None:
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.logs_dir).mkdir(parents=True, exist_ok=True)
