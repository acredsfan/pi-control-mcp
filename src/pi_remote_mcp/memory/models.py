from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MemoryItem:
    id: str
    created_at: str
    source_type: str
    project: str | None
    title: str
    summary: str
    body: str
    tags: list[str]
    metadata: dict
    importance: int
    redacted: bool
