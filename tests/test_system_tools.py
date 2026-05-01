from __future__ import annotations

from unittest.mock import patch

import pytest

from pi_remote_mcp.tools.system_tools import task_create, task_delete


def _mock_crontab(existing_lines: list[str]):
    """Return a pair of mock patches for _crontab_lines and _write_crontab."""
    written: list[list[str]] = []

    def fake_write(lines: list[str]) -> None:
        written.append(list(lines))

    return existing_lines[:], written, fake_write


def test_task_create_adds_cron_entry() -> None:
    existing: list[str] = []
    written: list[list[str]] = []

    with (
        patch("pi_remote_mcp.tools.system_tools._crontab_lines", return_value=existing),
        patch("pi_remote_mcp.tools.system_tools._write_crontab", side_effect=lambda lines: written.append(list(lines))),
    ):
        result = task_create("test-task", "echo hello", "*/5 * * * *")

    assert result["status"] == "created"
    assert len(written) == 1
    added = written[0][-1]
    assert "echo hello" in added
    assert "pi-control-mcp:test-task" in added


def test_task_create_refuses_duplicate() -> None:
    existing = ["*/5 * * * * echo hello  # pi-control-mcp:test-task"]
    with (
        patch("pi_remote_mcp.tools.system_tools._crontab_lines", return_value=existing),
        patch("pi_remote_mcp.tools.system_tools._write_crontab") as mock_write,
    ):
        result = task_create("test-task", "echo hello", "*/5 * * * *")

    assert result["status"] == "exists"
    mock_write.assert_not_called()


def test_task_delete_removes_entry() -> None:
    existing = ["*/5 * * * * echo hello  # pi-control-mcp:test-task", "0 * * * * other  # pi-control-mcp:other"]
    written: list[list[str]] = []

    with (
        patch("pi_remote_mcp.tools.system_tools._crontab_lines", return_value=existing),
        patch("pi_remote_mcp.tools.system_tools._write_crontab", side_effect=lambda lines: written.append(list(lines))),
    ):
        result = task_delete("test-task")

    assert result["status"] == "deleted"
    assert len(written) == 1
    remaining = written[0]
    assert all("pi-control-mcp:test-task" not in l for l in remaining)
    assert any("pi-control-mcp:other" in l for l in remaining)


def test_task_delete_not_found() -> None:
    existing: list[str] = []
    with (
        patch("pi_remote_mcp.tools.system_tools._crontab_lines", return_value=existing),
        patch("pi_remote_mcp.tools.system_tools._write_crontab") as mock_write,
    ):
        result = task_delete("nonexistent")

    assert result["status"] == "not_found"
    mock_write.assert_not_called()
