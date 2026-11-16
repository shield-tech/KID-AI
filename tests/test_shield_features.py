from __future__ import annotations

import asyncio
from pathlib import Path

from config import AppConfig
from conversation import ConversationEngine
from knowledge import KnowledgeBase
from memory import MemoryStore
from robotics import RoboticsController
from speech_queue import SpeechQueue
from task_manager import TaskManager
from vision import VisionManager
from voice_output import VoiceOutput


def test_task_management_and_vision_status(tmp_path: Path) -> None:
    config = AppConfig(memory_db_path=str(tmp_path / "m.db"), knowledge_root=str(tmp_path / "docs"), enable_vision=True)
    task_store = TaskManager(str(tmp_path / "tasks.json"))
    task = task_store.add_task("Calibrate rover", "Check wheel alignment")
    assert task.title == "Calibrate rover"
    assert task_store.summary()["open"] == 1
    assert task_store.complete_task(task.id)
    assert task_store.summary()["completed"] == 1

    async def exercise():
        class FakeOllama:
            async def available_models(self):
                return ["llava:latest", "llama3.2"]
        engine = ConversationEngine(config, ollama=FakeOllama(), memory=MemoryStore(config.memory_db_path), knowledge=KnowledgeBase(config.knowledge_root, str(tmp_path / "k.db")), tasks=task_store, vision=VisionManager(FakeOllama(), config), speech_queue=SpeechQueue(), voice_output=VoiceOutput(config))
        status = await engine.handle_command("/vision status")
        assert "Vision:" in status
        assert "llava:latest" in status
        summary = await engine.handle_command("/tasks summary")
        assert "total=" in summary
    asyncio.run(exercise())


def test_knowledge_and_tasks_commands(tmp_path: Path) -> None:
    config = AppConfig(memory_db_path=str(tmp_path / "m.db"), knowledge_root=str(tmp_path / "docs"), knowledge_enabled=True)
    docs = Path(config.knowledge_root)
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "robotics.md").write_text("Helicopter rotor test safety is required before flight.", encoding="utf-8")
    memory = MemoryStore(config.memory_db_path)
    knowledge = KnowledgeBase(config.knowledge_root, str(tmp_path / "k.db"))
    engine = ConversationEngine(config, memory=memory, knowledge=knowledge, tasks=TaskManager(str(tmp_path / "tasks.json")))

    async def exercise():
        assert "Indexed" in await engine.handle_command("/knowledge index")
        result = await engine.handle_command("/knowledge search test safety")
        assert "Helicopter" in result
        task_message = await engine.handle_command("/tasks add Deploy test rig | run preflight")
        assert "Created task" in task_message
    asyncio.run(exercise())
