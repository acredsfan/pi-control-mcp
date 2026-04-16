from pi_remote_mcp.tools.network_tools import port_check, scrape


def test_scrape_rejects_bad_url_gracefully() -> None:
    result = scrape("http://127.0.0.1:1")
    assert result["tool"] == "Scrape"
    assert "error" in result


def test_port_check_closed_port_returns_error_dict() -> None:
    """port_check on a closed port must return a dict, never raise."""
    result = port_check("127.0.0.1", 19999, timeout=0.5)
    assert result["tool"] == "PortCheck"
    assert result["open"] is False
    assert "error" in result


def test_port_check_open_port_returns_open_true() -> None:
    """port_check on an open port (SSH :22) must return open=True."""
    result = port_check("127.0.0.1", 22, timeout=2.0)
    assert result["tool"] == "PortCheck"
    assert result["open"] is True
