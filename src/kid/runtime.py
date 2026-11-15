"""Runtime manager and local health diagnostics for K.I.D."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from kid.config import Settings
from kid.hardware import inspect_hardware, model_warning
from kid.ollama import OllamaClient, OllamaError, OllamaStatus


@dataclass
class RuntimeState:
    ollama_connected: bool
    active_model: str
    selected_mode: str
    installed_models: list[str] = field(default_factory=list)
    hardware_summary: dict[str, object] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    message: str = ""


class RuntimeManager:
    """Runtime coordinator for local Ollama availability, model selection, and warnings."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.from_env()
        self.ollama = OllamaClient(self.settings)

    def check_ollama(self) -> OllamaStatus:
        try:
            return self.ollama.status()
        except OllamaError as exc:  # pragma: no cover - defensive for runtime-only branch
            return OllamaStatus(False, error=str(exc))

    def choose_model(self, preferred: str | None = None, *, force_lightweight: bool = False) -> str:
        hardware = inspect_hardware(self.settings.data_dir)
        available_ram = hardware.available_ram_gib
        if force_lightweight or available_ram <= self.settings.memory_pressure_gib:
            return self.settings.lightweight_model
        if preferred:
            return preferred
        return self.settings.primary_model

    def build_runtime_state(self, preferred_model: str | None = None, *, force_lightweight: bool = False) -> RuntimeState:
        hardware = inspect_hardware(self.settings.data_dir)
        status = self.check_ollama()
        selected = self.choose_model(preferred_model, force_lightweight=force_lightweight)
        warnings: list[str] = []
        if not status.connected:
            warnings.append(status.error or "Ollama is unavailable")
        else:
            if selected not in status.installed_models:
                warnings.append(f"Selected model {selected!r} is not installed in Ollama.")
            warning = model_warning(
                selected,
                hardware.available_ram_gib,
                self.settings.model_ram_estimate(selected),
            )
            if warning:
                warnings.append(warning)

        runtime_state = RuntimeState(
            ollama_connected=status.connected,
            active_model=selected,
            selected_mode="Lightweight" if force_lightweight or hardware.available_ram_gib <= self.settings.memory_pressure_gib else "Standard",
            installed_models=list(status.installed_models),
            hardware_summary={
                "operating_system": hardware.operating_system,
                "cpu": hardware.cpu,
                "logical_cpus": hardware.logical_cpus,
                "ram_total_gib": hardware.total_ram_gib,
                "ram_available_gib": hardware.available_ram_gib,
                "gpu": hardware.gpu,
                "disk_free_gib": hardware.disk_free_gib,
            },
            warnings=warnings,
            message="Ollama is available locally." if status.connected else (status.error or "Ollama is unavailable."),
        )
        return runtime_state


def diagnose_environment() -> dict[str, object]:
    """Collect local runtime facts for diagnostics and release notes."""
    hardware = inspect_hardware()
    ollama_binary = shutil.which("ollama")
    return {
        "ollama_binary": ollama_binary,
        "python_version": "3.11+",
        "operating_system": hardware.operating_system,
        "cpu": hardware.cpu,
        "logical_cpus": hardware.logical_cpus,
        "ram_total_gib": round(hardware.total_ram_gib, 2),
        "ram_available_gib": round(hardware.available_ram_gib, 2),
        "gpu": hardware.gpu,
        "disk_free_gib": round(hardware.disk_free_gib, 2),
    }
