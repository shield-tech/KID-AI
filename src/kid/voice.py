"""Approved local tool execution and file-system guardrails."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


class PermissionDeniedError(RuntimeError):
    """Raised when a local tool request is not permitted."""


@dataclass(frozen=True)
class ToolPolicy:
    allowed_roots: tuple[str, ...] = ("/home", "/tmp", "/var/tmp")
    allowed_commands: tuple[str, ...] = ("ls", "pwd", "echo", "python -c", "ps")
    allow_shell: bool = False


@dataclass
class ActivityLog:
    action: str
    path: str | None = None
    command: str | None = None
    status: str = "ok"
    detail: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "action": self.action,
            "path": self.path,
            "command": self.command,
            "status": self.status,
            "detail": self.detail,
        }


class ToolExecutor:
    def __init__(self, policy: ToolPolicy | None = None):
        self.policy = policy or ToolPolicy()
        self.activity: list[ActivityLog] = []

    def _ensure_allowed_path(self, target: str | Path) -> Path:
        path = Path(target).expanduser().resolve()
        allowed = False
        for root in self.policy.allowed_roots:
            root_path = Path(root).resolve()
            try:
                path.relative_to(root_path)
                allowed = True
                break
            except ValueError:
                continue
        if not allowed:
            raise PermissionDeniedError(f"Path is outside the approved roots: {path}")
        return path

    def _ensure_allowed_command(self, command: str) -> str:
        if self.policy.allow_shell:
            return command
        normalized = command.strip()
        allowed_prefix = any(normalized.startswith(prefix) for prefix in self.policy.allowed_commands)
        if not allowed_prefix:
            raise PermissionDeniedError(f"Command is not approved for local execution: {command}")
        return command

    def read_text(self, path: str | Path) -> str:
        real = self._ensure_allowed_path(path)
        self.activity.append(ActivityLog("read_text", str(real), None, "ok"))
        return real.read_text(encoding="utf-8")

    def list_dir(self, path: str | Path) -> list[str]:
        real = self._ensure_allowed_path(path)
        self.activity.append(ActivityLog("list_dir", str(real), None, "ok"))
        return sorted(p.name for p in real.iterdir())

    def search_files(self, root: str | Path, pattern: str) -> list[str]:
        base = self._ensure_allowed_path(root)
        matches: list[str] = []
        for current, _, files in os.walk(base):
            for filename in files:
                if pattern.lower() in filename.lower():
                    matches.append(str(Path(current) / filename))
        self.activity.append(ActivityLog("search_files", str(base), None, "ok", pattern))
        return sorted(matches)

    def run_command(self, command: str, timeout: int = 15) -> str:
        validated = self._ensure_allowed_command(command)
        completed = subprocess.run(
            validated,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        self.activity.append(ActivityLog("run_command", None, validated, "ok" if completed.returncode == 0 else "error"))
        if completed.returncode != 0:
            raise PermissionDeniedError(completed.stderr or completed.stdout or "Command failed")
        return completed.stdout
