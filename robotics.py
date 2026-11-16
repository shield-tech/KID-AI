from __future__ import annotations

from typing import Any, Dict, Optional

try:
    import serial
except ImportError:
    serial = None


class RoboticsController:
    """Disconnected-by-default serial boundary. No device protocol or motion is assumed."""

    def __init__(self, config: Optional[Any] = None) -> None:
        self.config = config
        self.simulation = bool(getattr(config, "robot_simulation_mode", True)) if config else True
        self.serial_port = getattr(config, "robot_port", None) if config else None
        self.authorized = False
        self._port = None
        self._estop_latched = False

    def status(self) -> Dict[str, Any]:
        port_open = bool(self._port is not None and getattr(self._port, "is_open", False))
        return {
            "mode": "simulation" if self.simulation else "hardware",
            "port_configured": bool(self.serial_port),
            "port_open": port_open,
            "connected": False,  # no device identity/protocol handshake is implemented
            "device_verified": False,
            "authorized": self.authorized,
            "motion_enabled": False,
            "emergency_stop_latched": self._estop_latched,
            "port": self.serial_port or "not configured",
            "reason": "No device-specific identity handshake and safety-rated motion protocol are implemented.",
        }

    def authorize(self, confirmed: bool = False) -> bool:
        self.authorized = bool(confirmed) and not self._estop_latched
        return self.authorized

    def connect(self) -> Dict[str, Any]:
        self.close()
        if self.simulation:
            return {"status": "simulation", "port_open": False, "connected": False, "device_verified": False, "message": "Simulation mode only; no physical device is connected or simulated as connected."}
        if serial is None:
            return {"status": "disconnected", "port_open": False, "connected": False, "device_verified": False, "message": "pyserial is not installed."}
        if not self.serial_port:
            return {"status": "disconnected", "port_open": False, "connected": False, "device_verified": False, "message": "No serial port configured."}
        try:
            self._port = serial.Serial(self.serial_port, 115200, timeout=1, write_timeout=1)
            return {"status": "port opened; device unverified", "port_open": bool(self._port.is_open), "connected": False, "device_verified": False, "message": "Serial port opened only. Device identity and protocol are unverified; motion remains disabled."}
        except (OSError, serial.SerialException) as exc:
            self._port = None
            return {"status": "error", "port_open": False, "connected": False, "device_verified": False, "message": str(exc)}

    def move(self, *, left_speed: float = 0.0, right_speed: float = 0.0) -> Dict[str, Any]:
        if self._estop_latched:
            return {"accepted": False, "message": "Emergency-stop latch is set; manual inspection/reset is required."}
        if not self.authorized:
            return {"accepted": False, "message": "Explicit human authorization is required."}
        if not self.status()["device_verified"]:
            return {"accepted": False, "message": "No verified physical device connection; motion rejected."}
        return {"accepted": False, "message": "Motion is disabled until a device-specific validated protocol and safety interlocks exist."}

    def emergency_stop(self) -> Dict[str, Any]:
        self._estop_latched = True
        self.authorized = False
        self.close()
        return {"status": "software motion lock set", "physical_stop_verified": False, "message": "Software motion lock set. This is not a hardware safety-rated emergency stop."}

    def close(self) -> None:
        if self._port is not None:
            try:
                self._port.close()
            except Exception:
                pass
            self._port = None


__all__ = ["RoboticsController"]
