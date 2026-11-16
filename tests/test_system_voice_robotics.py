from __future__ import annotations

from linux_monitor import LinuxMonitor


def test_system_summary_has_explicit_metrics_and_sections(monkeypatch) -> None:
    monitor = LinuxMonitor()
    monkeypatch.setattr(monitor, "collect", lambda: {
        "platform": {"distro": "Linux Mint test", "kernel": "6.0", "architecture": "x86_64"},
        "cpu": {"model": "Test CPU", "logical_cores": 4, "load_average_1_5_15": (0.2, 0.3, 0.4)},
        "cpu_percent": 12.5,
        "ram": {"used_gb": 2.0, "total_gb": 8.0, "available_gb": 6.0, "percent": 25.0},
        "swap": {"used_gb": 0.5, "total_gb": 2.0, "percent": 25.0},
        "disk": {"mount": "/home/test", "used_gb": 10.0, "total_gb": 100.0, "free_gb": 90.0, "percent": 10.0},
        "temperature": [{"sensor": "CPU", "celsius": 42.0}],
        "uptime": 90061.0,
        "network": {"status": "default route present", "interface": "wlan0"},
        "processes": [{"pid": 10, "name": "ollama", "cpu_percent": 2.5, "memory_percent": 1.0}],
    })
    output = monitor.summary()
    assert "Linux Mint test" in output
    assert "4 logical cores" in output
    assert "Swap:" in output and "Disk (/home/test)" in output
    assert "CPU 42.0 °C" in output
    assert "wlan0" in output and "1d 1h 1m" in output
    assert "ollama" in output
    assert "Usage:" in monitor.summary("invalid")


def test_system_missing_metrics_stay_unavailable(monkeypatch) -> None:
    monitor = LinuxMonitor()
    monkeypatch.setattr(monitor, "collect", lambda: {
        "platform": {"distro": "unknown", "kernel": "unknown", "architecture": "unknown"},
        "cpu": {"model": "unknown", "logical_cores": None, "load_average_1_5_15": ()},
        "cpu_percent": None,
        "ram": {"used_gb": None, "total_gb": None, "available_gb": None, "percent": None},
        "swap": {"used_gb": None, "total_gb": None, "percent": None},
        "disk": {"mount": "/tmp", "used_gb": None, "total_gb": None, "free_gb": None, "percent": None},
        "temperature": [], "uptime": None,
        "network": {"status": "unknown", "interface": "unknown"}, "processes": [],
    })
    assert "unavailable" in monitor.summary("ram")
    assert "no readable sensor" in monitor.summary("temperature")


def test_robotics_status_distinguishes_port_from_verified_device() -> None:
    from config import AppConfig
    from robotics import RoboticsController
    robot = RoboticsController(AppConfig(robot_simulation_mode=True))
    status = robot.status()
    assert status["mode"] == "simulation"
    assert not status["port_open"] and not status["connected"] and not status["device_verified"]
    assert not status["motion_enabled"]
    result = robot.connect()
    assert result["connected"] is False and result["device_verified"] is False
    assert robot.move(left_speed=0.1, right_speed=0.1)["accepted"] is False
