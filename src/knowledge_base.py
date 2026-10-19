"""Knowledge-base loading and simple explainable retrieval."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KnowledgeEntry:
    id: str
    title: str
    text: str
    confidential: bool
    category: str


class KnowledgeBase:
    """Load public admissions facts and retrieve relevant entries."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        raw_entries = json.loads(self.path.read_text(encoding="utf-8"))
        self.entries = [
            KnowledgeEntry(
                id=item["id"],
                title=item["title"],
                text=item["text"],
                confidential=bool(item["confidential"]),
                category=item["category"],
            )
            for item in raw_entries
        ]
        self._by_id = {entry.id: entry for entry in self.entries}

    def get(self, entry_id: str) -> KnowledgeEntry:
        return self._by_id[entry_id]

    def public_entries(self) -> list[KnowledgeEntry]:
        return [entry for entry in self.entries if not entry.confidential]

    def retrieve(self, query: str, limit: int = 3) -> list[KnowledgeEntry]:
        """Return public entries ranked by simple content-word overlap."""
        query_words = self._words(query)
        scored: list[tuple[int, int, KnowledgeEntry]] = []
        for index, entry in enumerate(self.public_entries()):
            entry_words = self._words(f"{entry.title} {entry.text} {entry.category}")
            score = len(query_words & entry_words)
            if score:
                scored.append((score, -index, entry))
        scored.sort(reverse=True, key=lambda item: (item[0], item[1]))
        return [entry for _, _, entry in scored[:limit]]

    @staticmethod
    def _words(text: str) -> set[str]:
        return {
            word
            for word in re.findall(r"[a-z0-9]+", text.lower())
            if len(word) > 2
        }
