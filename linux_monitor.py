from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional

try:
    import psutil
except ImportError:  # telemetry remains partially available without psutil
    psutil = None


class LinuxMonitor:
    def collect(self) -> Dict[str, Any]:
        memory = self._memory()
        disk = self._disk()
        return {
            "cpu_percent": self._cpu_percent(), "ram": memory, "disk": disk,
            "temperature": self._temperature(), "uptime": self._uptime(),
            "processes": self._processes(), "network": self._network_status(),
        }

    def _cpu_percent(self) -> Optional[float]:
        return float(psutil.cpu_percent(interval=0.1)) if psutil else None

    def _memory(self) -> Dict[str, Optional[float]]:
        if not psutil:
            return {"used_gb": None, "total_gb": None, "percent": None}
        mem = psutil.virtual_memory()
        return {"used_gb": round(mem.used / 1024**3, 2), "total_gb": round(mem.total / 1024**3, 2), "percent": float(mem.percent)}

    def _disk(self) -> Dict[str, Optional[float]]:
        if not psutil:
            return {"used_gb": None, "total_gb": None, "percent": None}
        disk = psutil.disk_usage(os.path.expanduser("~"))
        return {"used_gb": round(disk.used / 1024**3, 2), "total_gb": round(disk.total / 1024**3, 2), "percent": float(disk.percent)}

    def _temperature(self) -> Optional[float]:
        if psutil:
            try:
                for sensors in psutil.sensors_temperatures().values():
                    for sensor in sensors:
                        if sensor.current is not None:
                            return float(sensor.current)
            except (AttributeError, OSError):
                pass
        for path in ("/sys/class/thermal/thermal_zone0/temp", "/sys/class/thermal/thermal_zone1/temp"):
            try:
                with open(path, encoding="ascii") as handle:
                    return float(handle.read().strip()) / 1000
            except (OSError, ValueError):
                continue
        return None

    @staticmethod
    def _uptime() -> Optional[float]:
        try:
            with open("/proc/uptime", encoding="ascii") as handle:
                return float(handle.read().split()[0])
        except (OSError, ValueError, IndexError):
            return None

    @staticmethod
    def _processes(limit: int = 8) -> List[str]:
        if not psutil:
            return []
        processes = []
        try:
            for proc in psutil.process_iter(attrs=["pid", "name", "cpu_percent", "memory_percent"]):
                info = proc.info
                processes.append((float(info.get("cpu_percent") or 0), f"{info['pid']} {info.get('name') or 'unknown'}"))
        except (psutil.Error, OSError):
            pass
        return [name for _, name in sorted(processes, reverse=True)[:limit]]

    @staticmethod
    def _network_status() -> Dict[str, str]:
        if not shutil.which("ip"):
            return {"status": "unavailable", "interface": "unknown"}
        try:
            result = subprocess.run(["ip", "-o", "route", "show", "default"], capture_output=True, text=True, timeout=2, check=False)
            if result.returncode == 0 and result.stdout.strip():
                fields = result.stdout.split()
                interface = fields[fields.index("dev") + 1] if "dev" in fields else "unknown"
                return {"status": "online", "interface": interface}
            return {"status": "no default route", "interface": "unknown"}
        except (OSError, subprocess.TimeoutExpired):
            return {"status": "unknown", "interface": "unknown"}

    def summary(self, section: str = "all") -> str:
        data = self.collect()
        section = section.lower()
        if section == "processes":
            return "Top processes (PID name):\n" + ("\n".join(data["processes"]) or "Unavailable (psutil not installed).")
        if section == "network":
            return f"Network: {data['network']['status']} (interface: {data['network']['interface']})"
        if section == "disk":
            return self._format_percent("Disk", data["disk"])
        if section not in {"all", "cpu", "ram", "temperature", "uptime"}:
            return "Usage: /system [all|cpu|ram|disk|temperature|network|processes|uptime]"
        if section == "cpu":
            return f"CPU: {self._fmt(data['cpu_percent'], '%')}"
        if section == "ram":
            return self._format_percent("RAM", data["ram"])
        if section == "temperature":
            return f"Temperature: {self._fmt(data['temperature'], ' °C')}"
        if section == "uptime":
            return f"Uptime: {self._fmt(data['uptime'] / 3600 if data['uptime'] is not None else None, ' hours')}"
        return (f"CPU: {self._fmt(data['cpu_percent'], '%')} | " + self._format_percent("RAM", data["ram"]) + " | " + self._format_percent("Disk", data["disk"]) + "\n" +
                f"Temperature: {self._fmt(data['temperature'], ' °C')} | Network: {data['network']['status']} ({data['network']['interface']}) | " +
                f"Uptime: {self._fmt(data['uptime'] / 3600 if data['uptime'] is not None else None, ' h')}\n" +
                "Top processes:\n" + ("\n".join(data["processes"]) or "Unavailable (psutil not installed)."))

    @staticmethod
    def _fmt(value: Optional[float], suffix: str) -> str:
        return "unavailable" if value is None else f"{value:.1f}{suffix}"

    @classmethod
    def _format_percent(cls, name: str, values: Dict[str, Optional[float]]) -> str:
        percent = cls._fmt(values.get("percent"), "%")
        used, total = values.get("used_gb"), values.get("total_gb")
        capacity = "unavailable" if used is None or total is None else f"{used:.1f}/{total:.1f} GB"
        return f"{name}: {percent} ({capacity})"


__all__ = ["LinuxMonitor"]
