from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile

from pi_remote_mcp.utils.command_runner import (
    CommandExecutionError,
    CommandUnavailableError,
    find_command,
    require_command,
    run_command,
)


BUTTON_MAP = {"left": "0xC0", "middle": "0xC1", "right": "0xC2"}
_YDOTOOL_SOCKET = os.getenv("YDOTOOL_SOCKET", "/run/user/1000/.ydotool_socket")


def _run_ydotool(*args: str) -> dict:
    binary = require_command("ydotool")
    env = {**os.environ, "YDOTOOL_SOCKET": _YDOTOOL_SOCKET}
    result = subprocess.run(  # noqa: S603
        [binary, *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    return {"command": [binary, *args], "stdout": result.stdout, "stderr": result.stderr}


def click(x: int, y: int, button: str = "left", action: str = "click") -> dict:
    _run_ydotool("mousemove", str(x), str(y))
    if action == "hover":
        return {"backend": "wayland", "action": action, "x": x, "y": y, "button": button}

    button_code = BUTTON_MAP.get(button, BUTTON_MAP["left"])
    if action == "double":
        _run_ydotool("click", button_code)
        _run_ydotool("click", button_code)
    else:
        _run_ydotool("click", button_code)
    return {"backend": "wayland", "action": action, "x": x, "y": y, "button": button}


def type_text(text: str, clear: bool = False, press_enter: bool = False) -> dict:
    if clear:
        _run_ydotool("key", "29:1", "30:1", "30:0", "29:0")
        _run_ydotool("key", "111:1", "111:0")
    _run_ydotool("type", text)
    if press_enter:
        _run_ydotool("key", "28:1", "28:0")
    return {
        "backend": "wayland",
        "action": "type",
        "chars": len(text),
        "clear": clear,
        "press_enter": press_enter,
    }


def snapshot() -> dict:
    binary = require_command("grim")
    with NamedTemporaryFile(suffix=".png", delete=False) as handle:
        temp_path = Path(handle.name)
    run_command([binary, str(temp_path)])
    return {
        "backend": "wayland",
        "action": "snapshot",
        "path": str(temp_path),
        "exists": temp_path.exists(),
    }


def scroll(amount: int, horizontal: bool = False) -> dict:
    if horizontal:
        raise CommandExecutionError("Horizontal scrolling is not currently supported on Wayland")
    _run_ydotool("click", "0xC4" if amount > 0 else "0xC5")
    return {"backend": "wayland", "action": "scroll", "amount": amount, "horizontal": horizontal}


def move(x: int, y: int) -> dict:
    _run_ydotool("mousemove", str(x), str(y))
    return {"backend": "wayland", "action": "move", "x": x, "y": y}


def shortcut(keys: list[str]) -> dict:
    raise CommandUnavailableError(
        "Wayland shortcut support requires compositor-specific keycode mapping; not yet implemented"
    )


def focus_window(title: str) -> dict:
    swaymsg = find_command("swaymsg")
    if swaymsg:
        result = run_command([swaymsg, f'[title="{title}"]', "focus"])
        return {"backend": "wayland", "action": "focus_window", "title": title, "stdout": result.stdout}
    hyprctl = find_command("hyprctl")
    if hyprctl:
        result = run_command([hyprctl, "dispatch", "focuswindow", f"title:{title}"])
        return {"backend": "wayland", "action": "focus_window", "title": title, "stdout": result.stdout}
    return {
        "backend": "wayland",
        "action": "focus_window",
        "error": "No compositor IPC tool available (swaymsg, hyprctl). Window management requires Sway or Hyprland.",
    }


def list_windows() -> dict:
    swaymsg = find_command("swaymsg")
    if swaymsg:
        result = run_command([swaymsg, "-t", "get_tree"])
        parsed = json.loads(result.stdout)
        windows: list[dict] = []

        def visit(node: dict) -> None:
            name = node.get("name")
            rect = node.get("rect") or {}
            if name:
                windows.append(
                    {
                        "id": node.get("id"),
                        "title": name,
                        "focused": bool(node.get("focused", False)),
                        "x": int(rect.get("x", 0)),
                        "y": int(rect.get("y", 0)),
                        "width": int(rect.get("width", 0)),
                        "height": int(rect.get("height", 0)),
                        "app_id": node.get("app_id", ""),
                    }
                )
            for child in node.get("nodes", []):
                if isinstance(child, dict):
                    visit(child)
            for child in node.get("floating_nodes", []):
                if isinstance(child, dict):
                    visit(child)

        visit(parsed)
        return {"backend": "wayland", "action": "list_windows", "windows": windows}

    hyprctl = find_command("hyprctl")
    if hyprctl:
        result = run_command([hyprctl, "-j", "clients"])
        clients = json.loads(result.stdout)
        windows = [
            {
                "id": c.get("address"),
                "title": c.get("title", ""),
                "focused": bool(c.get("focusHistoryID", 1) == 0),
                "x": int(c.get("at", [0, 0])[0]),
                "y": int(c.get("at", [0, 0])[1]),
                "width": int(c.get("size", [0, 0])[0]),
                "height": int(c.get("size", [0, 0])[1]),
                "app_id": c.get("class", ""),
            }
            for c in clients
        ]
        return {"backend": "wayland", "action": "list_windows", "windows": windows}

    return {
        "backend": "wayland",
        "action": "list_windows",
        "error": "No compositor IPC tool available (swaymsg, hyprctl). Window listing requires Sway or Hyprland.",
        "windows": [],
    }


def get_clipboard() -> dict:
    binary = require_command("wl-paste")
    result = run_command([binary, "--no-newline"])
    return {"backend": "wayland", "action": "get_clipboard", "content": result.stdout}


def set_clipboard(text: str) -> dict:
    binary = require_command("wl-copy")
    result = subprocess.run(  # noqa: S603
        [binary],
        input=text,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return {"backend": "wayland", "action": "set_clipboard", "error": result.stderr.strip()}
    return {"backend": "wayland", "action": "set_clipboard", "content_length": len(text)}


def notify(title: str, message: str) -> dict:
    binary = require_command("notify-send")
    run_command([binary, title, message])
    return {"backend": "wayland", "action": "notify", "title": title}
