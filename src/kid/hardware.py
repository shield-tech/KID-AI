"""Hardware discovery and conservative local-model recommendations."""

from __future__ import annotations

import os
import platform
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HardwareInfo:
    operating_system: str
    cpu: str
    logical_cpus: int
    total_ram_gib: float
    available_ram_gib: float
    gpu: str
    disk_free_gib: float


def _memory_gib(field: str) -> float:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith(field + ":"):
                return int(line.split()[1]) / 1024 / 1024
    except (OSError, ValueError, IndexError):
        pass
    return 0.0


def _gpu_description() -> str:
    drm = Path("/sys/class/drm")
    if drm.exists():
        for device in drm.glob("card[0-9]/device"):
            try:
                vendor = (device / "vendor").read_text().strip()
                if vendor == "0x8086":
                    return "Intel integrated graphics (detected via DRM)"
                return f"GPU vendor {vendor} (DRM)"
            except OSError:
                continue
    return "No GPU information available"


def inspect_hardware(data_path: Path | None = None) -> HardwareInfo:
    """Read system information without optional hardware packages."""
    cpu = platform.processor() or "Unknown CPU"
    if platform.system() == "Linux":
        try:
            for line in Path("/proc/cpuinfo").read_text().splitlines():
                if line.lower().startswith("model name"):
                    cpu = line.split(":", 1)[1].strip()
                    break
        except OSError:
            pass
    total = _memory_gib("MemTotal")
    available = _memory_gib("MemAvailable") or _memory_gib("MemFree")
    path = data_path or Path.home()
    try:
        disk_free = shutil.disk_usage(path if path.exists() else path.parent).free / 1024**3
    except OSError:
        disk_free = 0.0
    return HardwareInfo(
        operating_system=f"{platform.system()} {platform.release()}",
        cpu=cpu,
        logical_cpus=os.cpu_count() or 1,
        total_ram_gib=total,
        available_ram_gib=available,
        gpu=_gpu_description(),
        disk_free_gib=disk_free,
    )


def model_warning(model: str, available_ram_gib: float, estimated_ram_gib: float) -> str | None:
    """Return a warning when a model's estimated RAM leaves little headroom."""
    if available_ram_gib <= 0:
        return "Available RAM could not be detected; model fit is unknown."
    if estimated_ram_gib > available_ram_gib * 0.8:
        return (
            f"{model} may exceed safe memory headroom: estimated model RAM "
            f"{estimated_ram_gib:.1f} GiB vs {available_ram_gib:.1f} GiB currently available."
        )
    return None
