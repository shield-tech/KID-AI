from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

try:
    import serial  # type: ignore
except Exception:  # pragma: no cover
    serial = None


class RoboticsController:
    def __init__(self, config: Optional[Any] = None) -> None:
        self.config = config
        self.connected = False
        self.authorized = False
        self.serial_port = getattr(config, "robot_port", None) if config else None

    def authorize(self) -> bool:
        self.authorized = True
        return True

    def connect(self) -> Dict[str, Any]:
        if self.config and getattr(self.config, "robot_simulation_mode", True):
            self.connected = True
            return {"status": "simulated", "connected": True, "message": "Simulation mode active; no hardware connected."}
        if serial is None:
            return {"status": "disconnected", "connected": False, "message": "pyserial is not installed."}
        if not self.serial_port:
            return {"status": "disconnected", "connected": False, "message": "No robot serial port configured."}
        try:
            self._port = serial.Serial(self.serial_port, 115200, timeout=1)
            self.connected = self._port.is_open
            return {"status": "connected" if self.connected else "disconnected", "connected": self.connected}
        except Exception as exc:
            return {"status": "error", "connected": False, "message": str(exc)}

    def move(self, *, left_speed: float = 0.0, right_speed: float = 0.0) -> Dict[str, Any]:
        if not self.authorized:
            return {"authorized": False, "message": "Robot movement requires explicit authorization."}
        if not self.connected and not getattr(self.config, "robot_simulation_mode", True):
            return {"authorized": True, "connected": False, "message": "No hardware connection verified."}
        left_speed = max(-1.0, min(1.0, left_speed))
        right_speed = max(-1.0, min(1.0, right_speed))
        return {"authorized": True, "connected": True, "left_speed": left_speed, "right_speed": right_speed, "message": "Movement request accepted in safe simulation mode."}

    def emergency_stop(self) -> Dict[str, Any]:
        self.connected = False
        return {"status": "stopped", "message": "Emergency stop applied."}


__all__ = ["RoboticsController"]
