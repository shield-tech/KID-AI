from __future__ import annotations

import asyncio

from terminal_ui import TerminalUI


def test_listen_command_submits_recognized_transcript(monkeypatch) -> None:
    class Engine:
        model = "test"
        memory = None
        knowledge = None
        voice_enabled = False
        config = type("Config", (), {"knowledge_root": "knowledge"})()
        class Ollama:
            last_stats = {}
        ollama = Ollama()
        class Voice:
            available_engine = None
        voice = Voice()
        class Robotics:
            def status(self): return {"mode": "simulation", "device_verified": False}
        robotics = Robotics()
        class Tasks:
            def summary(self): return {"open": 0, "completed": 0}
        tasks = Tasks()
        def __init__(self): self.submitted = []; self.shutdown_called = False
        async def handle_command(self, command):
            return "Recognized: inspect the motor controller\nSubmit the text above as a new prompt when ready."
        async def stream_response(self, text):
            self.submitted.append(text)
            yield "Answer"
        def shutdown(self): self.shutdown_called = True

    engine = Engine()
    ui = TerminalUI(engine)
    async def no_banner():
        return None
    ui.print_banner = no_banner
    inputs = iter(["/listen", "/exit"])
    async def fake_to_thread(func, *args, **kwargs):
        return next(inputs)
    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    asyncio.run(ui.run())
    assert engine.submitted == ["inspect the motor controller"]
    assert engine.shutdown_called
