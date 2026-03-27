from pi_remote_mcp.desktop.backend_selector import detect_backend


def test_backend_detector_returns_known_kind() -> None:
    caps = detect_backend()
    assert caps.backend in {"wayland", "x11", "headless"}
