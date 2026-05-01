from __future__ import annotations

from pi_remote_mcp.tools.mower_tools import hardware_probe, journal_search, service_health_report


def test_mower_tools_handle_missing_commands() -> None:
    report = service_health_report(services=["definitely-not-real-service"], include_journal=False)
    assert report["ok"] is True

    journal = journal_search(query="error")
    assert "ok" in journal

    hw = hardware_probe(include_gpio=True)
    assert hw["ok"] is True
