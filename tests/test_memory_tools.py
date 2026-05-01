from __future__ import annotations

from pi_remote_mcp.tools.memory_tools import (
    memory_health,
    memory_note_add,
    memory_recent,
    memory_schema_check,
    memory_search,
)


def test_memory_note_add_and_search(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PI_CONTROL_MEMORY_DB", str(tmp_path / "pi_memory.sqlite3"))
    added = memory_note_add("TOKEN=abc123 this is test note", tags=["agent-note"])
    assert added["ok"] is True
    assert added["redacted"] is True

    recent = memory_recent(limit=5)
    assert recent["items"]
    assert recent["items"][0]["source_type"] == "note"

    searched = memory_search("test note")
    assert len(searched["items"]) >= 1


def test_memory_health_and_schema(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PI_CONTROL_MEMORY_DB", str(tmp_path / "pi_memory.sqlite3"))
    memory_note_add("hello")
    health = memory_health()
    assert health["ok"] is True
    assert health["item_count"] >= 1
    assert health["db_path"].endswith("pi_memory.sqlite3")

    schema = memory_schema_check()
    assert schema["ok"] is True
