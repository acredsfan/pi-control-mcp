from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pi_remote_mcp.desktop.backends import wayland_backend


# ---------------------------------------------------------------------------
# set_clipboard — must actually pipe text via stdin
# ---------------------------------------------------------------------------

def test_set_clipboard_pipes_text_to_wl_copy() -> None:
    mock_result = MagicMock()
    mock_result.returncode = 0

    with (
        patch("pi_remote_mcp.desktop.backends.wayland_backend.require_command", return_value="/usr/bin/wl-copy"),
        patch("pi_remote_mcp.desktop.backends.wayland_backend.subprocess.run", return_value=mock_result) as mock_run,
    ):
        result = wayland_backend.set_clipboard("hello wayland")

    mock_run.assert_called_once()
    call_kwargs = mock_run.call_args
    assert call_kwargs.kwargs.get("input") == "hello wayland", "text must be piped via stdin"
    assert result["action"] == "set_clipboard"
    assert result["content_length"] == len("hello wayland")


def test_set_clipboard_returns_error_on_failure() -> None:
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "wl-copy: no compositor"

    with (
        patch("pi_remote_mcp.desktop.backends.wayland_backend.require_command", return_value="/usr/bin/wl-copy"),
        patch("pi_remote_mcp.desktop.backends.wayland_backend.subprocess.run", return_value=mock_result),
    ):
        result = wayland_backend.set_clipboard("text")

    assert "error" in result


# ---------------------------------------------------------------------------
# focus_window / list_windows — graceful fallback when no IPC tool
# ---------------------------------------------------------------------------

def test_focus_window_returns_error_when_no_compositor_ipc() -> None:
    with patch("pi_remote_mcp.desktop.backends.wayland_backend.find_command", return_value=None):
        result = wayland_backend.focus_window("some-title")

    assert "error" in result
    assert result.get("action") == "focus_window"


def test_list_windows_returns_empty_list_when_no_compositor_ipc() -> None:
    with patch("pi_remote_mcp.desktop.backends.wayland_backend.find_command", return_value=None):
        result = wayland_backend.list_windows()

    assert result.get("windows") == []
    assert "error" in result


# ---------------------------------------------------------------------------
# snapshot — grim must be used
# ---------------------------------------------------------------------------

def test_snapshot_uses_grim() -> None:
    fake_result = MagicMock()
    fake_result.ok = True
    fake_result.stdout = ""
    fake_result.stderr = ""
    fake_result.exit_code = 0

    with (
        patch("pi_remote_mcp.desktop.backends.wayland_backend.require_command", return_value="/usr/bin/grim"),
        patch("pi_remote_mcp.desktop.backends.wayland_backend.run_command", return_value=fake_result),
    ):
        result = wayland_backend.snapshot()

    assert result["backend"] == "wayland"
    assert result["action"] == "snapshot"
