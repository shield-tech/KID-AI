from __future__ import annotations

import sqlite3
import threading
from typing import Any, Dict, Iterable, List, Optional, Tuple


class MemoryStore:
    def __init__(self, db_path: str = "kid_memory.sqlite3") -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def add_message(self, role: str, content: str) -> None:
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO conversations (role, content) VALUES (?, ?)",
                    (role, content),
                )
                conn.commit()

    def get_recent_history(self, limit: int = 20) -> List[Tuple[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [(role, content) for role, content in reversed(rows)]

    def add_memory(self, topic: str, content: str) -> None:
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO memories (topic, content) VALUES (?, ?)",
                    (topic.strip(), content.strip()),
                )
                conn.commit()

    def delete_memory(self, memory_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()

    def list_memories(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, topic, content, created_at FROM memories ORDER BY created_at DESC"
            ).fetchall()
        return [{"id": row[0], "topic": row[1], "content": row[2], "created_at": row[3]} for row in rows]

    def get_relevant_memories(self, topic: str, limit: int = 5) -> List[Dict[str, Any]]:
        query = f"%{topic.lower()}%"
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT id, topic, content, created_at
                FROM memories
                WHERE LOWER(topic) LIKE ? OR LOWER(content) LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (query, query, limit),
            ).fetchall()
        return [{"id": row[0], "topic": row[1], "content": row[2], "created_at": row[3]} for row in rows]


__all__ = ["MemoryStore"]
