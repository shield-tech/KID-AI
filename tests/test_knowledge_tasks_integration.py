from __future__ import annotations

import asyncio
from pathlib import Path

from config import AppConfig
from conversation import ConversationEngine
from knowledge import KnowledgeBase
from memory import MemoryStore
from task_manager import TaskManager


def test_knowledge_index_search_and_tasks_end_to_end(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    root.mkdir()
    (root / "spec.md").write_text("Motor controller commissioning requires a current limit and emergency stop test.", encoding="utf-8")
    config = AppConfig(memory_db_path=str(tmp_path / "memory.db"), knowledge_root=str(root), task_db_path=str(tmp_path / "tasks.json"))
    kb = KnowledgeBase(str(root), str(tmp_path / "knowledge.db"))
    tasks = TaskManager(config.task_db_path)
    engine = ConversationEngine(config, memory=MemoryStore(config.memory_db_path), knowledge=kb, tasks=tasks)

    async def run_commands():
        indexed = await engine.handle_command("/knowledge index")
        assert "Indexed" in indexed
        matches = await engine.handle_command("/knowledge search current limit")
        assert "spec.md" in matches
        assert "emergency stop" in matches
        created = await engine.handle_command("/tasks add Verify controller | inspect current limit")
        assert "Created task [1]" in created
        assert "Verify controller" in await engine.handle_command("/tasks list")
        assert "complete" in await engine.handle_command("/tasks done 1")
        assert "completed=1" in await engine.handle_command("/tasks summary")
    asyncio.run(run_commands())
