from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TaskRecord:
    id: int
    title: str
    notes: str = ""
    status: str = "open"
    created_at: str = ""


class TaskManager:
    """Simple local JSON task board for SHIELD work tracking."""

    def __init__(self, path: str = ".kid/tasks.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _load(self) -> List[Dict[str, Any]]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        return payload if isinstance(payload, list) else []

    def _save(self, tasks: List[Dict[str, Any]]) -> None:
        self.path.write_text(json.dumps(tasks, indent=2), encoding="utf-8")

    def add_task(self, title: str, notes: str = "") -> TaskRecord:
        title = title.strip()
        if not title:
            raise ValueError("A task title is required.")
        tasks = self._load()
        new_id = max((item.get("id", 0) for item in tasks), default=0) + 1
        item = {
            "id": new_id,
            "title": title,
            "notes": notes.strip(),
            "status": "open",
            "created_at": __import__("datetime").datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }
        tasks.append(item)
        self._save(tasks)
        return TaskRecord(**item)

    def list_tasks(self, *, include_completed: bool = True) -> List[TaskRecord]:
        tasks = self._load()
        records: List[TaskRecord] = [TaskRecord(**item) for item in tasks]
        if not include_completed:
            records = [item for item in records if item.status != "completed"]
        return sorted(records, key=lambda item: item.id)

    def complete_task(self, task_id: int) -> bool:
        tasks = self._load()
        for item in tasks:
            if int(item.get("id", -1)) == int(task_id):
                item["status"] = "completed"
                self._save(tasks)
                return True
        return False

    def remove_task(self, task_id: int) -> bool:
        tasks = self._load()
        filtered = [item for item in tasks if int(item.get("id", -1)) != int(task_id)]
        if len(filtered) == len(tasks):
            return False
        self._save(filtered)
        return True

    def summary(self) -> Dict[str, int]:
        tasks = self.list_tasks()
        return {
            "total": len(tasks),
            "open": sum(1 for task in tasks if task.status == "open"),
            "completed": sum(1 for task in tasks if task.status == "completed"),
        }


__all__ = ["TaskManager", "TaskRecord"]
