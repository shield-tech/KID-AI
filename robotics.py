from __future__ import annotations

from typing import Any, Dict, Optional

try:
    import serial
except ImportError:
    serial = None


class RoboticsController:
    """Safe disconnected-by-default serial boundary; no generic movement protocol is assumed."""

    def __init__(self, config: Optional[Any] = None) -> None:
        self.config = config
        self.connected = False
        self.authorized = False
        self.simulation = bool(getattr(config, "robot_simulation_mode", True)) if config else True
        self.serial_port = getattr(config, "robot_port", None) if config else None
        self._port = None
        self._estop_latched = False

    def status(self) -> Dict[str, Any]:
        return {"mode": "simulation" if self.simulation else "hardware", "connected": bool(self.connected and self._port and getattr(self._port, "is_open", False)), "authorized": self.authorized, "emergency_stop_latched": self._estop_latched, "port": self.serial_port or "not configured"}

    def authorize(self, confirmed: bool = False) -> bool:
        # Authorization must originate from an explicit human confirmation path.
        self.authorized = bool(confirmed)
        return self.authorized

    def connect(self) -> Dict[str, Any]:
        self.connected = False
        if self.simulation:
            return {"status": "simulation", "connected": False, "message": "Simulation mode; no physical device is connected."}
        if serial is None:
            return {"status": "disconnected", "connected": False, "message": "pyserial is not installed."}
        if not self.serial_port:
            return {"status": "disconnected", "connected": False, "message": "No serial port configured."}
        try:
            self._port = serial.Serial(self.serial_port, 115200, timeout=1, write_timeout=1)
            self.connected = bool(self._port.is_open)
            return {"status": "connected" if self.connected else "disconnected", "connected": self.connected, "message": "Serial port opened; device protocol/identity has not been verified."}
        except (OSError, serial.SerialException) as exc:
            self._port = None
            return {"status": "error", "connected": False, "message": str(exc)}

    def move(self, *, left_speed: float = 0.0, right_speed: float = 0.0) -> Dict[str, Any]:
        if self._estop_latched:
            return {"accepted": False, "message": "Emergency-stop latch is set; reset and inspect hardware before any motion."}
        if not self.authorized:
            return {"accepted": False, "message": "Explicit human authorization is required."}
        if not self.connected or self._port is None or not getattr(self._port, "is_open", False):
            return {"accepted": False, "message": "No verified physical connection; motion rejected."}
        # No device wire protocol is defined in this project; never emit generic motor bytes.
        return {"accepted": False, "message": "Motion is disabled until a device-specific validated protocol is configured."}

    def emergency_stop(self) -> Dict[str, Any]:
        self._estop_latched = True
        self.authorized = False
        # Closing serial is not represented as a hardware emergency stop.
        self.connected = False
        if self._port is not None:
            try:
                self._port.close()
            except Exception:
                pass
            self._port = None
        return {"status": "software latch set", "physical_stop_verified": False, "message": "Software motion lock set and serial closed if present; this is not a hardware safety-rated E-stop."}


__all__ = ["RoboticsController"]
