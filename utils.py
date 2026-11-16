from __future__ import annotations

import os
from typing import Dict, List


def _ensure_path(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


__all__ = ["_ensure_path"]
