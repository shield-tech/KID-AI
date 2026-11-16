from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import docx  # type: ignore
except Exception:  # pragma: no cover
    docx = None

try:
    import fitz  # type: ignore
except Exception:  # pragma: no cover
    fitz = None


class KnowledgeBase:
    def __init__(self, root: str = "knowledge") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def index_directory(self, directory: str | None = None) -> List[str]:
        base = Path(directory) if directory else self.root
        indexed: List[str] = []
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".txt", ".md", ".pdf", ".docx"}:
                indexed.append(str(path))
        return indexed

    def read_text(self, path: str) -> str:
        p = Path(path)
        if p.suffix.lower() == ".pdf" and fitz is not None:
            try:
                doc = fitz.open(str(p))
                chunks = []
                for page in doc:
                    chunks.append(page.get_text())
                return "\n\n".join(chunks)
            except Exception:
                return ""
        if p.suffix.lower() == ".docx" and docx is not None:
            try:
                document = docx.Document(str(p))
                return "\n".join(paragraph.text for paragraph in document.paragraphs)
            except Exception:
                return ""
        if p.exists():
            try:
                return p.read_text(encoding="utf-8")
            except Exception:
                return p.read_text(encoding="utf-8", errors="ignore")
        return ""

    def search(self, query: str, directory: str | None = None, limit: int = 5) -> List[Dict[str, str]]:
        results: List[Dict[str, str]] = []
        for path in self.index_directory(directory):
            text = self.read_text(path)
            if not text:
                continue
            haystack = text.lower()
            if query.lower() in haystack:
                excerpt = self._excerpt(text, query)
                results.append({"path": path, "excerpt": excerpt})
                if len(results) >= limit:
                    break
        return results

    @staticmethod
    def _excerpt(text: str, query: str, window: int = 180) -> str:
        q = query.lower()
        match = re.search(re.escape(q), text.lower())
        if not match:
            return text[:window]
        start = max(0, match.start() - window // 2)
        end = min(len(text), match.end() + window // 2)
        snippet = text[start:end].strip().replace("\n", " ")
        return snippet


__all__ = ["KnowledgeBase"]
