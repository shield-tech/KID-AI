from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Tuple


class MemoryStore:
    def __init__(self, db_path: str = "kid_memory.sqlite3") -> None:
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS conversations (id INTEGER PRIMARY KEY, role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
            conn.execute("CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY, topic TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")

    def add_message(self, role: str, content: str) -> None:
        if role not in {"user", "assistant"} or not content.strip():
            return
        with self._lock, self._connect() as conn:
            conn.execute("INSERT INTO conversations(role, content) VALUES (?, ?)", (role, content.strip()))

    def get_recent_history(self, limit: int = 12) -> List[Tuple[str, str]]:
        limit = max(0, min(int(limit), 100))
        with self._connect() as conn:
            rows = conn.execute("SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [(row["role"], row["content"]) for row in reversed(rows)]

    def clear_history(self) -> int:
        with self._lock, self._connect() as conn:
            cursor = conn.execute("DELETE FROM conversations")
            return cursor.rowcount

    def add_memory(self, topic: str, content: str) -> int:
        topic, content = topic.strip(), content.strip()
        if not topic or not content:
            raise ValueError("Both a topic and memory text are required.")
        with self._lock, self._connect() as conn:
            cur = conn.execute("INSERT INTO memories(topic, content) VALUES (?, ?)", (topic, content))
            return int(cur.lastrowid)

    def edit_memory(self, memory_id: int, topic: str, content: str) -> bool:
        if not topic.strip() or not content.strip():
            raise ValueError("Both a topic and memory text are required.")
        with self._lock, self._connect() as conn:
            cur = conn.execute("UPDATE memories SET topic=?, content=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (topic.strip(), content.strip(), int(memory_id)))
            return cur.rowcount > 0

    def delete_memory(self, memory_id: int) -> bool:
        with self._lock, self._connect() as conn:
            cur = conn.execute("DELETE FROM memories WHERE id=?", (int(memory_id),))
            return cur.rowcount > 0

    def list_memories(self, query: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if query.strip():
                term = f"%{query.strip()}%"
                rows = conn.execute("SELECT id, topic, content, created_at, updated_at FROM memories WHERE topic LIKE ? OR content LIKE ? ORDER BY updated_at DESC LIMIT ?", (term, term, min(limit, 500))).fetchall()
            else:
                rows = conn.execute("SELECT id, topic, content, created_at, updated_at FROM memories ORDER BY updated_at DESC LIMIT ?", (min(limit, 500),)).fetchall()
        return [dict(row) for row in rows]

    def get_relevant_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        terms = [term for term in query.lower().split() if len(term) > 2][:8]
        if not terms:
            return []
        clauses = " OR ".join("LOWER(topic || ' ' || content) LIKE ?" for _ in terms)
        params = [f"%{term}%" for term in terms] + [max(1, min(limit, 20))]
        with self._connect() as conn:
            rows = conn.execute(f"SELECT id, topic, content, created_at FROM memories WHERE {clauses} ORDER BY updated_at DESC LIMIT ?", params).fetchall()
        return [dict(row) for row in rows]


__all__ = ["MemoryStore"]
