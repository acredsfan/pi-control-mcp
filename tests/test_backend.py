from unittest.mock import patch

from pi_remote_mcp.desktop.backend_selector import detect_backend
from pi_remote_mcp.desktop.backends.x11_backend import snapshot as x11_snapshot
from pi_remote_mcp.utils.command_runner import CommandUnavailableError


def test_backend_detector_returns_known_kind() -> None:
    caps = detect_backend()
    assert caps.backend in {"wayland", "x11", "headless"}


def test_x11_snapshot_uses_scrot_when_import_missing() -> None:
    """snapshot() should succeed with scrot if import/gnome-screenshot absent."""

    def side_effect(*names):
        if set(names) <= {"import", "gnome-screenshot"}:
            raise CommandUnavailableError("not found")
        if "scrot" in names:
            return "/usr/bin/scrot"
        raise CommandUnavailableError("not found")

    fake_result = type(
        "R", (), {"stdout": "", "stderr": "", "exit_code": 0, "ok": True, "command": []}
    )()

    with patch("pi_remote_mcp.desktop.backends.x11_backend.require_command", side_effect=side_effect), \
         patch("pi_remote_mcp.desktop.backends.x11_backend.run_command", return_value=fake_result):
        result = x11_snapshot()

    assert result["backend"] == "x11"
    assert "path" in result
