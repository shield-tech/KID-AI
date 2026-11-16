from __future__ import annotations

import subprocess
from typing import Any, Dict

from security import SecurityManager


class LinuxController:
    def __init__(self, security: SecurityManager) -> None:
        self.security = security

    def safe_command(self, args: list[str], *, require_confirmation: bool = True, timeout: int = 15) -> Dict[str, Any]:
        if require_confirmation:
            confirmed = self.security.require_confirmation("run a shell command", details=f"Command: {' '.join(args)}")
            if not confirmed:
                return {"allowed": False, "reason": "User rejected command execution."}
        try:
            proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
            return {
                "allowed": True,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
        except Exception as exc:
            return {"allowed": False, "reason": str(exc)}

    def read_only_status(self) -> Dict[str, Any]:
        return self.safe_command(["uname", "-a"], require_confirmation=False)


__all__ = ["LinuxController"]
