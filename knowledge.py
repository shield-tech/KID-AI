from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SUPPORTED = {".txt", ".md", ".pdf", ".docx"}


class KnowledgeBase:
    """A local SQLite-backed keyword index. Documents are read only from the configured root."""

    def __init__(self, root: str = "knowledge", db_path: str = ".kid/knowledge.sqlite3") -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS documents (path TEXT PRIMARY KEY, mtime REAL NOT NULL, size INTEGER NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS chunks (id INTEGER PRIMARY KEY, path TEXT NOT NULL, page INTEGER, text TEXT NOT NULL)")
            conn.execute("CREATE INDEX IF NOT EXISTS chunks_path_idx ON chunks(path)")

    def _extract(self, path: Path) -> List[Tuple[Optional[int], str]]:
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md"}:
            return [(None, path.read_text(encoding="utf-8", errors="replace"))]
        if suffix == ".pdf":
            try:
                import fitz
            except ImportError as exc:
                raise RuntimeError("PDF indexing requires pymupdf; install requirements.txt") from exc
            with fitz.open(path) as doc:
                return [(index + 1, page.get_text("text")) for index, page in enumerate(doc)]
        if suffix == ".docx":
            try:
                from docx import Document
            except ImportError as exc:
                raise RuntimeError("DOCX indexing requires python-docx; install requirements.txt") from exc
            document = Document(path)
            text = "\n".join(p.text for p in document.paragraphs)
            return [(None, text)]
        return []

    @staticmethod
    def _split(text: str, size: int = 900, overlap: int = 120) -> List[str]:
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized:
            return []
        chunks = []
        start = 0
        while start < len(normalized):
            end = min(len(normalized), start + size)
            if end < len(normalized):
                boundary = normalized.rfind(" ", start, end)
                if boundary > start + size // 2:
                    end = boundary
            chunks.append(normalized[start:end])
            if end == len(normalized):
                break
            start = max(start + 1, end - overlap)
        return chunks

    def index_directory(self, directory: str | None = None) -> List[str]:
        base = Path(directory).expanduser().resolve() if directory else self.root
        if not base.is_dir():
            raise NotADirectoryError(str(base))
        indexed: List[str] = []
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED:
                continue
            stat = path.stat()
            with self._connect() as conn:
                old = conn.execute("SELECT mtime, size FROM documents WHERE path=?", (str(path),)).fetchone()
                if old and old["mtime"] == stat.st_mtime and old["size"] == stat.st_size:
                    continue
            extracted = self._extract(path)
            pieces: List[Tuple[Optional[int], str]] = []
            for page, text in extracted:
                pieces.extend((page, chunk) for chunk in self._split(text))
            with self._connect() as conn:
                conn.execute("DELETE FROM chunks WHERE path=?", (str(path),))
                conn.execute("INSERT OR REPLACE INTO documents(path, mtime, size) VALUES (?, ?, ?)", (str(path), stat.st_mtime, stat.st_size))
                conn.executemany("INSERT INTO chunks(path, page, text) VALUES (?, ?, ?)", [(str(path), page, text) for page, text in pieces])
            indexed.append(str(path))
        return indexed

    def indexed_files(self) -> List[str]:
        with self._connect() as conn:
            return [row[0] for row in conn.execute("SELECT path FROM documents ORDER BY path").fetchall()]

    def search(self, query: str, directory: str | None = None, limit: int = 5) -> List[Dict[str, str]]:
        terms = list(dict.fromkeys(re.findall(r"[\w'-]+", query.lower())))
        if not terms:
            return []
        filters = ""
        params: List[object] = []
        if directory:
            root = str(Path(directory).expanduser().resolve())
            filters = " AND path LIKE ?"
            params.append(root.rstrip("/") + "%")
        with self._connect() as conn:
            rows = conn.execute("SELECT path, page, text FROM chunks WHERE 1=1" + filters, params).fetchall()
        scored = []
        for row in rows:
            text = row["text"]
            lowered = text.lower()
            score = sum(lowered.count(term) for term in terms)
            if score:
                excerpt = self._excerpt(text, terms)
                result = {"path": row["path"], "excerpt": excerpt, "score": str(score)}
                if row["page"] is not None:
                    result["page"] = str(row["page"])
                scored.append(result)
        scored.sort(key=lambda item: (-int(item["score"]), item["path"]))
        return scored[:max(0, limit)]

    @staticmethod
    def _excerpt(text: str, terms: List[str], window: int = 320) -> str:
        lowered = text.lower()
        positions = [lowered.find(term) for term in terms if lowered.find(term) >= 0]
        start_at = min(positions) if positions else 0
        start = max(0, start_at - window // 3)
        return text[start:start + window].strip()


__all__ = ["KnowledgeBase"]
