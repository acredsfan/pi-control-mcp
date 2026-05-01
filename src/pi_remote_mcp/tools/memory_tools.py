from __future__ import annotations

from pi_remote_mcp.memory.db import MemoryDB
from pi_remote_mcp.memory.service import MemoryService, record_memory


def _service() -> MemoryService:
    return MemoryService()


def memory_recent(limit: int = 20, project: str | None = None, include_body: bool = False) -> dict:
    return {"tool": "MemoryRecent", "ok": True, "items": _service().recent(limit=limit, project=project, include_body=include_body)}


def memory_search(query: str, project: str | None = None, source_types: list[str] | None = None, limit: int = 20) -> dict:
    return {"tool": "MemorySearch", "ok": True, "items": _service().search(query=query, project=project, source_types=source_types, limit=limit)}


def memory_show(memory_id: str) -> dict:
    item = _service().show(memory_id)
    return {"tool": "MemoryShow", "ok": item is not None, "item": item}


def memory_files(project: str | None = None, limit: int = 50) -> dict:
    items = _service().search(query="file", project=project, source_types=["file"], limit=limit)
    return {"tool": "MemoryFiles", "ok": True, "items": items}


def memory_errors(project: str | None = None, limit: int = 20) -> dict:
    items = _service().search(query="error", project=project, source_types=["error", "shell", "service"], limit=limit)
    return {"tool": "MemoryErrors", "ok": True, "items": items}


def memory_note_add(note: str, tags: list[str] | None = None, project: str | None = None, importance: int = 2) -> dict:
    tags = tags or ["agent-note"]
    recorded = record_memory("note", "Agent note", note[:120], note, project, tags, importance=importance)
    return {"tool": "MemoryNoteAdd", "ok": True, **recorded}


def memory_health() -> dict:
    health = _service().health()
    return {"tool": "MemoryHealth", "ok": True, **health}


def memory_schema_check() -> dict:
    db = MemoryDB()
    required = {"memory_items", "idx_memory_created_at", "idx_memory_source_type", "idx_memory_project"}
    with db.connect() as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type in ('table','index')").fetchall()}
    missing = sorted(required - tables)
    return {"tool": "MemorySchemaCheck", "ok": len(missing) == 0, "missing": missing,
            "repair_suggestions": [] if not missing else ["Re-run tool initialization to rebuild schema."]}
