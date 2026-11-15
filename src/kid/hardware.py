"""Hardware inspection for K.I.D."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass


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
    value = os.getenv(field)
    if value:
        try:
            return float(value)
        except ValueError:
            pass
    return 0.0


def _gpu_description() -> str:
    if shutil.which("nvidia-smi"):
        try:
            output = subprocess.check_output(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], text=True, stderr=subprocess.DEVNULL)
            return output.strip().splitlines()[0] if output.strip() else "No GPU detected"
        except Exception:
            pass
    return "No NVIDIA GPU detected"


def inspect_hardware(data_dir: str | None = None) -> HardwareInfo:
    cpu = os.getenv("KID_CPU_MODEL", "Unknown CPU")
    logical_cpus = int(os.getenv("KID_CPU_CORES", "1"))
    total_ram = _memory_gib("KID_TOTAL_RAM_GIB")
    available_ram = _memory_gib("KID_AVAILABLE_RAM_GIB")
    if total_ram <= 0 or available_ram <= 0:
        try:
            meminfo = open("/proc/meminfo", "r", encoding="utf-8").read()
            total_kib = 0
            available_kib = 0
            for line in meminfo.splitlines():
                if line.startswith("MemTotal:"):
                    total_kib = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    available_kib = int(line.split()[1])
            if total_kib:
                total_ram = total_kib / 1024 / 1024
            if available_kib:
                available_ram = available_kib / 1024 / 1024
        except OSError:
            total_ram = 8.0
            available_ram = 4.0
    disk_free = 0.0
    try:
        stat = os.statvfs("/")
        disk_free = (stat.f_bavail * stat.f_frsize) / (1024**3)
    except OSError:
        disk_free = 0.0

    return HardwareInfo(
        operating_system=os.getenv("KID_OS", "Linux"),
        cpu=cpu,
        logical_cpus=logical_cpus,
        total_ram_gib=total_ram,
        available_ram_gib=available_ram,
        gpu=_gpu_description(),
        disk_free_gib=disk_free,
    )


def model_warning(model: str, available_ram_gib: float, required_ram_gib: float) -> str | None:
    if available_ram_gib <= 0:
        return None
    if required_ram_gib > available_ram_gib:
        return f"Warning: {model} requires roughly {required_ram_gib:.1f} GiB but only {available_ram_gib:.1f} GiB is available. Use lightweight mode."
    return None
