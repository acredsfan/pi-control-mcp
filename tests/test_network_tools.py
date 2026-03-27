from pi_remote_mcp.tools.network_tools import scrape


def test_scrape_rejects_bad_url_gracefully() -> None:
    result = scrape("http://127.0.0.1:1")
    assert result["tool"] == "Scrape"
    assert "error" in result
