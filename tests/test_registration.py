from pi_remote_mcp.config import AppConfig
from pi_remote_mcp.server import create_server


def test_server_registers_expanded_default_toolset() -> None:
    server, enabled = create_server(AppConfig())
    assert "Snapshot" in enabled
    assert "GetClipboard" in enabled
    assert "Scroll" in enabled
    assert "FileSearch" in enabled
    assert "Ping" in enabled
    assert "Shell" not in enabled

    provider = getattr(server, "_local_provider", None)
    components = getattr(provider, "_components", {}) if provider else {}
    tool_names = {
        getattr(component, "name", key.split(":", 1)[1].split("@", 1)[0])
        for key, component in components.items()
        if isinstance(key, str) and key.startswith("tool:")
    }
    assert "Snapshot" in tool_names
    assert "GetClipboard" in tool_names
    assert "Ping" in tool_names
