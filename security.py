from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List


class AuditLogger:
    def __init__(self, path: str = "kid_audit.log") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def log(self, event: str, **fields: Any) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **fields,
        }
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


class SecurityManager:
    def __init__(self, audit_path: str = "kid_audit.log") -> None:
        self.audit = AuditLogger(audit_path)

    def require_confirmation(self, action: str, *, details: str = "") -> bool:
        print(f"[SECURITY] Required confirmation for: {action}")
        if details:
            print(details)
        decision = input("Proceed? [y/N]: ").strip().lower()
        self.audit.log("confirmation_requested", action=action, details=details, response=decision)
        return decision in {"y", "yes"}

    def guard_command(self, command: str) -> bool:
        if not command or command.startswith("http"):
            return False
        if any(token in command.lower() for token in ["rm -rf", "sudo", "chmod 777", "curl | bash", "wget | sh"]):
            return False
        return True

    def write_audit(self, event: str, **fields: Any) -> None:
        self.audit.log(event, **fields)


__all__ = ["SecurityManager", "AuditLogger"]
