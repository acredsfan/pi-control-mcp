from __future__ import annotations

from datetime import datetime, timezone
import json
import uuid
from typing import Any

from .db import MemoryDB
from .redact import redact_text
from .summarize import summarize_text


class MemoryService:
    def __init__(self, db: MemoryDB | None = None):
        self.db = db or MemoryDB()

    def add_item(self, source_type: str, title: str, summary: str, body: str, project: str | None = None,
                 tags: list[str] | None = None, metadata: dict[str, Any] | None = None, importance: int = 1) -> dict:
        tags = tags or []
        metadata = metadata or {}
        merged = "\n".join([title, summary, body])
        _, changed = redact_text(merged)
        title_r, _ = redact_text(title)
        summary_r, _ = redact_text(summary)
        body_r, _ = redact_text(body)
        mid = f"mem_{uuid.uuid4().hex[:12]}"
        created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        with self.db.connect() as conn:
            conn.execute(
                """INSERT INTO memory_items (id,created_at,source_type,project,title,summary,body,tags_json,metadata_json,importance,redacted)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (mid, created_at, source_type, project, title_r, summary_r, body_r,
                 json.dumps(tags), json.dumps(metadata), importance, 1 if changed else 0),
            )
            if self.db.fts_available:
                conn.execute(
                    "INSERT INTO memory_fts(rowid,title,summary,body,tags) VALUES (last_insert_rowid(),?,?,?,?)",
                    (title_r, summary_r, body_r, " ".join(tags)),
                )
        return {"id": mid, "redacted": changed}

    def recent(self, limit: int, project: str | None = None, include_body: bool = False) -> list[dict]:
        query = "SELECT id,created_at,source_type,project,title,summary,body,tags_json,importance,redacted FROM memory_items"
        params: list[Any] = []
        if project:
            query += " WHERE project=?"
            params.append(project)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self.db.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_item(r, include_body=include_body) for r in rows]

    def _row_to_item(self, row: tuple, include_body: bool = False) -> dict:
        body = row[6] if include_body else ""
        return {"id": row[0], "created_at": row[1], "source_type": row[2], "project": row[3], "title": row[4],
                "summary": row[5], "body": body, "tags": json.loads(row[7]), "importance": row[8], "redacted": bool(row[9])}

    def show(self, memory_id: str) -> dict | None:
        with self.db.connect() as conn:
            row = conn.execute("SELECT id,created_at,source_type,project,title,summary,body,tags_json,importance,redacted FROM memory_items WHERE id=?", (memory_id,)).fetchone()
        return self._row_to_item(row, include_body=True) if row else None

    def search(self, query: str, project: str | None, source_types: list[str] | None, limit: int) -> list[dict]:
        with self.db.connect() as conn:
            if self.db.fts_available:
                rows = conn.execute(
                    """SELECT m.id,m.created_at,m.source_type,m.project,m.title,m.summary,m.body,m.tags_json,m.importance,m.redacted
                    FROM memory_fts f JOIN memory_items m ON m.rowid=f.rowid WHERE memory_fts MATCH ? ORDER BY m.created_at DESC LIMIT ?""",
                    (query, limit),
                ).fetchall()
            else:
                like = f"%{query}%"
                rows = conn.execute(
                    "SELECT id,created_at,source_type,project,title,summary,body,tags_json,importance,redacted FROM memory_items WHERE title LIKE ? OR summary LIKE ? OR body LIKE ? ORDER BY created_at DESC LIMIT ?",
                    (like, like, like, limit),
                ).fetchall()
        items = [self._row_to_item(r) for r in rows]
        if project:
            items = [i for i in items if i["project"] == project]
        if source_types:
            allowed = set(source_types)
            items = [i for i in items if i["source_type"] in allowed]
        return items[:limit]

    def health(self) -> dict:
        with self.db.connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM memory_items").fetchone()[0]
            latest = conn.execute("SELECT created_at FROM memory_items ORDER BY created_at DESC LIMIT 1").fetchone()
        return {"db_path": self.db.db_path, "item_count": count, "fts_available": self.db.fts_available,
                "schema_version": 1, "latest_item_at": latest[0] if latest else None}


def record_memory(source_type: str, title: str, summary: str, body: str, project: str | None = None,
                  tags: list[str] | None = None, metadata: dict[str, Any] | None = None, importance: int = 1) -> dict:
    service = MemoryService()
    if not summary:
        summary = summarize_text(body)
    return service.add_item(source_type, title, summary, body, project, tags, metadata, importance)
