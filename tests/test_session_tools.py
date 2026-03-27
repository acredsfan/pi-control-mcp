from pi_remote_mcp.tools.session_tools import detect_dialog, get_session_state, probe_capabilities


def test_probe_capabilities_has_backend() -> None:
    result = probe_capabilities()
    assert result["tool"] == "ProbeCapabilities"
    assert result["backend"] in {"wayland", "x11", "headless"}


def test_get_session_state_shape() -> None:
    result = get_session_state()
    assert result["tool"] == "GetSessionState"
    assert "session_type" in result


def test_detect_dialog_returns_boolean_flag() -> None:
    result = detect_dialog()
    assert result["tool"] == "DetectDialog"
    assert isinstance(result["detected"], bool)
