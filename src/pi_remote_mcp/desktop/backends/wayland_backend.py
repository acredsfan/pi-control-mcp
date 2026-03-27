from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from pi_remote_mcp.utils.command_runner import (
    CommandExecutionError,
    CommandUnavailableError,
    require_command,
    run_command,
)


BUTTON_MAP = {"left": "0xC0", "middle": "0xC1", "right": "0xC2"}


def _run_ydotool(*args: str) -> dict:
    binary = require_command("ydotool")
    result = run_command([binary, *args])
    return {"command": result.command, "stdout": result.stdout, "stderr": result.stderr}


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
    swaymsg = require_command("swaymsg")
    result = run_command([swaymsg, f'[title="{title}"]', "focus"])
    return {"backend": "wayland", "action": "focus_window", "title": title, "stdout": result.stdout}


def list_windows() -> dict:
    swaymsg = require_command("swaymsg")
    result = run_command([swaymsg, "-t", "get_tree"])
    return {"backend": "wayland", "action": "list_windows", "tree": result.stdout}


def get_clipboard() -> dict:
    binary = require_command("wl-paste")
    result = run_command([binary, "--no-newline"])
    return {"backend": "wayland", "action": "get_clipboard", "content": result.stdout}


def set_clipboard(text: str) -> dict:
    binary = require_command("wl-copy")
    result = run_command([binary], check=False, text=True)
    return {
        "backend": "wayland",
        "action": "set_clipboard",
        "content_length": len(text),
        "note": "wl-copy invocation requires stdin plumbing; use desktop tool wrapper for direct subprocess handling",
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def notify(title: str, message: str) -> dict:
    binary = require_command("notify-send")
    run_command([binary, title, message])
    return {"backend": "wayland", "action": "notify", "title": title}
