import json

from pi_remote_mcp.tools.ui_tools import ui_map, ui_sequence, ui_watch


def test_ui_map_returns_elements_key() -> None:
    result = ui_map()
    assert result["tool"] == "UIMap"
    assert "elements" in result


def test_ui_watch_returns_change_marker() -> None:
    result = ui_watch(reset=True)
    assert result["tool"] == "UIWatch"
    assert "changed" in result


def test_ui_sequence_handles_wait_step() -> None:
    result = ui_sequence(json.dumps([{"action": "wait", "seconds": 0}]))
    assert result["tool"] == "UISequence"
    assert len(result["results"]) == 1
