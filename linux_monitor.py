from __future__ import annotations

import os
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional

try:
    import psutil
except Exception:  # pragma: no cover
    psutil = None


class LinuxMonitor:
    def __init__(self) -> None:
        self.psutil = psutil

    def collect(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "cpu_percent": self._cpu_percent(),
            "ram": self._ram_usage(),
            "disk": self._disk_usage(),
            "temperature": self._temperature(),
            "uptime": self._uptime(),
            "processes": self._processes(),
            "network": self._network_status(),
        }
        return data

    def _cpu_percent(self) -> float:
        if self.psutil is not None:
            return float(self.psutil.cpu_percent(interval=None))
        return 0.0

    def _ram_usage(self) -> Dict[str, float]:
        if self.psutil is not None:
            mem = self.psutil.virtual_memory()
            return {
                "used_gb": round(mem.used / (1024 ** 3), 2),
                "total_gb": round(mem.total / (1024 ** 3), 2),
                "percent": float(mem.percent),
            }
        return {"used_gb": 0.0, "total_gb": 0.0, "percent": 0.0}

    def _disk_usage(self) -> Dict[str, float]:
        if self.psutil is not None:
            disk = self.psutil.disk_usage('/')
            return {
                "used_gb": round(disk.used / (1024 ** 3), 2),
                "total_gb": round(disk.total / (1024 ** 3), 2),
                "percent": float(disk.percent),
            }
        return {"used_gb": 0.0, "total_gb": 0.0, "percent": 0.0}

    def _temperature(self) -> Optional[float]:
        candidates = [
            "/sys/class/thermal/thermal_zone0/temp",
            "/sys/class/thermal/thermal_zone1/temp",
            "/sys/class/thermal/thermal_zone2/temp",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as handle:
                        value = float(handle.read().strip()) / 1000.0
                    return value
                except Exception:
                    pass
        return None

    def _uptime(self) -> float:
        try:
            with open("/proc/uptime", "r", encoding="utf-8") as handle:
                return float(handle.read().split()[0])
        except Exception:
            return 0.0

    def _processes(self) -> List[str]:
        try:
            if self.psutil is not None:
                return [proc.name() for proc in self.psutil.process_iter(attrs=['name'])][:20]
        except Exception:
            pass
        return []

    def _network_status(self) -> Dict[str, str]:
        status = {"interface": "unknown", "status": "unknown"}
        try:
            if shutil.which("ip"):
                result = subprocess.run(["ip", "route"], capture_output=True, text=True, check=False)
                if result.stdout:
                    status["interface"] = result.stdout.splitlines()[0].split()[0]
                    status["status"] = "online"
        except Exception:
            pass
        return status


__all__ = ["LinuxMonitor"]
