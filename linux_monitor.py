from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import psutil
except ImportError:  # telemetry remains partially available without psutil
    psutil = None


class LinuxMonitor:
    """Read-only host telemetry. Missing metrics are reported as unavailable, never as zero."""

    def collect(self) -> Dict[str, Any]:
        return {
            "platform": self._platform(),
            "cpu": self._cpu(),
            "cpu_percent": self._cpu_percent(),
            "ram": self._memory(),
            "swap": self._swap(),
            "disk": self._disk(),
            "temperature": self._temperatures(),
            "uptime": self._uptime(),
            "processes": self._processes(),
            "network": self._network_status(),
        }

    @staticmethod
    def _platform() -> Dict[str, str]:
        distro = "unknown Linux distribution"
        try:
            for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
                if line.startswith("PRETTY_NAME="):
                    distro = line.split("=", 1)[1].strip().strip('"')
                    break
        except OSError:
            pass
        return {"distro": distro, "kernel": platform.release(), "architecture": platform.machine()}

    @staticmethod
    def _cpu() -> Dict[str, Any]:
        model = "unknown"
        try:
            for line in Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace").splitlines():
                if line.lower().startswith(("model name", "hardware")) and ":" in line:
                    model = line.split(":", 1)[1].strip()
                    break
        except OSError:
            pass
        try:
            load = tuple(float(value) for value in os.getloadavg())
        except (AttributeError, OSError):
            load = ()
        return {"model": model, "logical_cores": os.cpu_count(), "load_average_1_5_15": load}

    @staticmethod
    def _cpu_percent() -> Optional[float]:
        try:
            return float(psutil.cpu_percent(interval=0.1)) if psutil else None
        except (OSError, RuntimeError):
            return None

    @staticmethod
    def _memory() -> Dict[str, Optional[float]]:
        if not psutil:
            return {"used_gb": None, "total_gb": None, "available_gb": None, "percent": None}
        try:
            mem = psutil.virtual_memory()
            return {"used_gb": round(mem.used / 1024**3, 2), "total_gb": round(mem.total / 1024**3, 2), "available_gb": round(mem.available / 1024**3, 2), "percent": float(mem.percent)}
        except (OSError, AttributeError):
            return {"used_gb": None, "total_gb": None, "available_gb": None, "percent": None}

    @staticmethod
    def _swap() -> Dict[str, Optional[float]]:
        if not psutil:
            return {"used_gb": None, "total_gb": None, "percent": None}
        try:
            swap = psutil.swap_memory()
            return {"used_gb": round(swap.used / 1024**3, 2), "total_gb": round(swap.total / 1024**3, 2), "percent": float(swap.percent)}
        except (OSError, AttributeError):
            return {"used_gb": None, "total_gb": None, "percent": None}

    @staticmethod
    def _disk() -> Dict[str, Optional[float] | str]:
        target = str(Path.home())
        if not psutil:
            return {"mount": target, "used_gb": None, "total_gb": None, "free_gb": None, "percent": None}
        try:
            disk = psutil.disk_usage(target)
            return {"mount": target, "used_gb": round(disk.used / 1024**3, 2), "total_gb": round(disk.total / 1024**3, 2), "free_gb": round(disk.free / 1024**3, 2), "percent": float(disk.percent)}
        except (OSError, AttributeError):
            return {"mount": target, "used_gb": None, "total_gb": None, "free_gb": None, "percent": None}

    @staticmethod
    def _temperatures() -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        if psutil:
            try:
                for name, entries in psutil.sensors_temperatures().items():
                    for entry in entries:
                        if entry.current is not None:
                            result.append({"sensor": entry.label or name, "celsius": float(entry.current)})
            except (AttributeError, OSError):
                pass
        if result:
            return result
        for zone in sorted(Path("/sys/class/thermal").glob("thermal_zone*/temp")):
            try:
                value = float(zone.read_text(encoding="ascii").strip())
                result.append({"sensor": zone.parent.name, "celsius": value / 1000 if value > 1000 else value})
            except (OSError, ValueError):
                continue
        return result

    @staticmethod
    def _uptime() -> Optional[float]:
        try:
            return float(Path("/proc/uptime").read_text(encoding="ascii").split()[0])
        except (OSError, ValueError, IndexError):
            return None

    @staticmethod
    def _processes(limit: int = 8) -> List[Dict[str, Any]]:
        if not psutil:
            return []
        found = []
        try:
            for proc in psutil.process_iter(attrs=["pid", "name", "cpu_percent", "memory_percent"]):
                item = proc.info
                found.append({"pid": item.get("pid"), "name": item.get("name") or "unknown", "cpu_percent": float(item.get("cpu_percent") or 0), "memory_percent": float(item.get("memory_percent") or 0)})
        except (psutil.Error, OSError):
            pass
        return sorted(found, key=lambda item: (item["cpu_percent"], item["memory_percent"]), reverse=True)[:limit]

    @staticmethod
    def _network_status() -> Dict[str, str]:
        if not shutil.which("ip"):
            return {"status": "unavailable (ip command missing)", "interface": "unknown"}
        try:
            result = subprocess.run(["ip", "-o", "route", "show", "default"], capture_output=True, text=True, timeout=2, check=False)
            if result.returncode == 0 and result.stdout.strip():
                fields = result.stdout.split()
                interface = fields[fields.index("dev") + 1] if "dev" in fields else "unknown"
                return {"status": "default route present", "interface": interface}
            return {"status": "no default route", "interface": "unknown"}
        except (OSError, subprocess.TimeoutExpired):
            return {"status": "unknown", "interface": "unknown"}

    def summary(self, section: str = "all") -> str:
        section = (section or "all").lower()
        allowed = {"all", "cpu", "ram", "swap", "disk", "temperature", "network", "processes", "uptime", "platform"}
        if section not in allowed:
            return "Usage: /system [all|cpu|ram|swap|disk|temperature|network|processes|uptime|platform]"
        data = self.collect()
        if section == "platform":
            p = data["platform"]
            return f"System: {p['distro']} | kernel {p['kernel']} | {p['architecture']}"
        if section == "cpu":
            return self._cpu_summary(data)
        if section == "ram":
            return self._capacity_summary("RAM", data["ram"], available=True)
        if section == "swap":
            return self._capacity_summary("Swap", data["swap"])
        if section == "disk":
            return self._capacity_summary(f"Disk ({data['disk']['mount']})", data["disk"], free=True)
        if section == "temperature":
            return self._temperature_summary(data["temperature"])
        if section == "network":
            return f"Network: {data['network']['status']} | interface: {data['network']['interface']}"
        if section == "uptime":
            return f"Uptime: {self._duration(data['uptime'])}"
        if section == "processes":
            return self._process_summary(data["processes"])
        return "\n".join([
            f"System: {data['platform']['distro']} | kernel {data['platform']['kernel']} | {data['platform']['architecture']}",
            self._cpu_summary(data),
            self._capacity_summary("RAM", data["ram"], available=True),
            self._capacity_summary("Swap", data["swap"]),
            self._capacity_summary(f"Disk ({data['disk']['mount']})", data["disk"], free=True),
            self._temperature_summary(data["temperature"]),
            f"Network: {data['network']['status']} | interface: {data['network']['interface']}",
            f"Uptime: {self._duration(data['uptime'])}",
            self._process_summary(data["processes"]),
        ])

    @staticmethod
    def _cpu_summary(data: Dict[str, Any]) -> str:
        cpu = data["cpu"]
        loads = cpu["load_average_1_5_15"]
        load_text = ", ".join(f"{value:.2f}" for value in loads) if loads else "unavailable"
        return f"CPU: {LinuxMonitor._fmt(data['cpu_percent'], '%')} | {cpu['model']} | {cpu['logical_cores'] or 'unknown'} logical cores | load 1/5/15m: {load_text}"

    @staticmethod
    def _capacity_summary(name: str, values: Dict[str, Any], *, available: bool = False, free: bool = False) -> str:
        percent = LinuxMonitor._fmt(values.get("percent"), "%")
        used, total = values.get("used_gb"), values.get("total_gb")
        capacity = "unavailable" if used is None or total is None else f"{used:.1f}/{total:.1f} GB used"
        extra_key = "available_gb" if available else "free_gb" if free else None
        extra = values.get(extra_key) if extra_key else None
        if extra is not None:
            capacity += f", {extra:.1f} GB {'available' if available else 'free'}"
        return f"{name}: {percent} ({capacity})"

    @staticmethod
    def _temperature_summary(items: List[Dict[str, Any]]) -> str:
        if not items:
            return "Temperature: unavailable (no readable sensor found)"
        return "Temperature: " + ", ".join(f"{item['sensor']} {item['celsius']:.1f} °C" for item in items[:6])

    @staticmethod
    def _process_summary(items: List[Dict[str, Any]]) -> str:
        if not items:
            return "Top processes: unavailable (psutil not installed or access denied)"
        return "Top processes (PID name CPU% RAM%):\n" + "\n".join(f"{item['pid']} {item['name']} {item['cpu_percent']:.1f}% {item['memory_percent']:.1f}%" for item in items)

    @staticmethod
    def _duration(value: Optional[float]) -> str:
        if value is None:
            return "unavailable"
        days, remainder = divmod(int(value), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes = remainder // 60
        return f"{days}d {hours}h {minutes}m"

    @staticmethod
    def _fmt(value: Optional[float], suffix: str) -> str:
        return "unavailable" if value is None else f"{value:.1f}{suffix}"


__all__ = ["LinuxMonitor"]
