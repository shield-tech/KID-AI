from __future__ import annotations

import asyncio
from pathlib import Path

from config import AppConfig
from conversation import ConversationEngine
from knowledge import KnowledgeBase
from memory import MemoryStore
from robotics import RoboticsController
from speech_queue import SpeechQueue
from voice_output import VoiceOutput


def test_voice_output_controls_and_unavailable_engine(monkeypatch, tmp_path: Path) -> None:
    from voice_output import VoiceOutput
    monkeypatch.setattr("shutil.which", lambda _name: None)
    voice = VoiceOutput(AppConfig())
    assert voice.available_engine is None
    voice.set_volume(0.5)
    voice.set_speed(1.5)
    voice.set_voice("custom")
    assert voice._volume == 0.5 and voice._speed == 1.5 and voice._voice == "custom"
    try:
        voice.set_volume(2)
    except ValueError:
        pass
    else:
        raise AssertionError("out of range volume should fail")


def test_speech_queue_serializes_and_stop_flushes() -> None:
    import threading
    from speech_queue import SpeechQueue
    spoken = []
    event = threading.Event()
    queue = SpeechQueue()
    def callback(text):
        spoken.append(text)
        event.set()
    queue.start(callback)
    queue.enqueue("sentence")
    assert event.wait(1)
    queue.close()
    assert spoken == ["sentence"]


def test_robotics_stays_disconnected_and_rejects_motion() -> None:
    from robotics import RoboticsController
    robot = RoboticsController(AppConfig(robot_simulation_mode=True))
    assert robot.connect()["connected"] is False
    assert robot.status()["connected"] is False
    robot.authorize(confirmed=True)
    result = robot.move(left_speed=0.2, right_speed=0.2)
    assert result["accepted"] is False
    assert "No verified physical connection" in result["message"]
    stopped = robot.emergency_stop()
    assert stopped["physical_stop_verified"] is False
    assert robot.status()["emergency_stop_latched"] is True


def test_linux_monitor_reports_missing_metrics_without_fake_zero(monkeypatch) -> None:
    from linux_monitor import LinuxMonitor
    monitor = LinuxMonitor()
    monkeypatch.setattr("linux_monitor.psutil", None)
    data = monitor.collect()
    assert data["cpu_percent"] is None
    assert data["ram"]["percent"] is None
    assert "unavailable" in monitor.summary("ram")


def test_memory_inspection_and_credential_rejection(tmp_path: Path) -> None:
    config = AppConfig(memory_db_path=str(tmp_path / "mem.db"), knowledge_enabled=False)
    memory = MemoryStore(config.memory_db_path)
    engine = ConversationEngine(config, memory=memory, knowledge=None)
    async def exercise():
        assert "Credential" in await engine.handle_command("/remember account | api key ABC")
        assert "none" in await engine.handle_command("/memory")
        assert "Recent conversation history" in await engine.handle_command("/memory history")
        item = await engine.handle_command("/remember lab | uses local models")
        assert "Saved explicitly" in item
        assert "lab" in await engine.handle_command("/memory search local")
        assert "deleted" in await engine.handle_command("/forget 1")
    asyncio.run(exercise())


def test_voice_controls_are_wired_to_engine(tmp_path: Path, monkeypatch) -> None:
    class Voice:
        available_engine = "test"
        _voice = "test"
        _volume = 1.0
        _speed = 1.0
        def __init__(self): self.enabled = True; self.muted = False
        def set_enabled(self, value): self.enabled = value
        def set_muted(self, value): self.muted = value
        def set_volume(self, value): self._volume = value
        def set_speed(self, value): self._speed = value
        def set_voice(self, value): self._voice = value
        def stop(self): pass
        def speak(self, text): pass
    class Queue:
        def start(self, callback): self.callback = callback
        def stop(self): pass
        def close(self): pass
        def enqueue(self, text): pass
    config = AppConfig(memory_db_path=str(tmp_path / "v.db"), knowledge_enabled=False)
    engine = ConversationEngine(config, memory=MemoryStore(config.memory_db_path), knowledge=None, voice_output=Voice(), speech_queue=Queue())
    async def exercise():
        assert "set to 0.4" in await engine.handle_command("/voice volume 0.4")
        assert "1.4x" in await engine.handle_command("/voice speed 1.4")
        assert "muted" in await engine.handle_command("/mute")
        assert engine.voice.muted
        assert "disabled" in await engine.handle_command("/voice off")
    asyncio.run(exercise())
