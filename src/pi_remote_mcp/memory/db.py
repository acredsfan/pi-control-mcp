from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from pi_remote_mcp.utils.command_runner import ensure_parent_dir

DEFAULT_DB_PATH = "~/.local/share/pi-control-mcp/memory/pi_memory.sqlite3"


class MemoryDB:
    def __init__(self, db_path: str | None = None):
        raw = db_path or os.getenv("PI_CONTROL_MEMORY_DB") or DEFAULT_DB_PATH
        self.db_path = str(Path(raw).expanduser())
        ensure_parent_dir(self.db_path)
        self.fts_available = False
        self._init_schema()

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_items (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    project TEXT,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    body TEXT NOT NULL,
                    tags_json TEXT NOT NULL DEFAULT '[]',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    importance INTEGER NOT NULL DEFAULT 1,
                    redacted INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_created_at ON memory_items(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_source_type ON memory_items(source_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_project ON memory_items(project)")
            try:
                conn.execute(
                    """CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                    title, summary, body, tags, content='memory_items', content_rowid='rowid')"""
                )
                self.fts_available = True
            except sqlite3.OperationalError:
                self.fts_available = False

    @staticmethod
    def dumps(value: object) -> str:
        return json.dumps(value, ensure_ascii=False)
