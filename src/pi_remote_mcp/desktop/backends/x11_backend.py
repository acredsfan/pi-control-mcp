from __future__ import annotations

import re
from pathlib import Path
from tempfile import NamedTemporaryFile

from pi_remote_mcp.utils.command_runner import CommandExecutionError, CommandUnavailableError, require_command, run_command


BUTTON_MAP = {"left": "1", "middle": "2", "right": "3"}


def click(x: int, y: int, button: str = "left", action: str = "click") -> dict:
    binary = require_command("xdotool")
    if action == "hover":
        run_command([binary, "mousemove", str(x), str(y)])
    elif action == "double":
        run_command([binary, "mousemove", str(x), str(y), "click", "--repeat", "2", BUTTON_MAP.get(button, "1")])
    else:
        run_command([binary, "mousemove", str(x), str(y), "click", BUTTON_MAP.get(button, "1")])
    return {"backend": "x11", "action": action, "x": x, "y": y, "button": button}


def type_text(text: str, clear: bool = False, press_enter: bool = False) -> dict:
    binary = require_command("xdotool")
    if clear:
        run_command([binary, "key", "ctrl+a", "BackSpace"])
    run_command([binary, "type", "--delay", "1", text])
    if press_enter:
        run_command([binary, "key", "Return"])
    return {
        "backend": "x11",
        "action": "type",
        "chars": len(text),
        "clear": clear,
        "press_enter": press_enter,
    }


def snapshot() -> dict:
    with NamedTemporaryFile(suffix=".png", delete=False) as handle:
        temp_path = Path(handle.name)

    # Try import (ImageMagick) or gnome-screenshot first
    try:
        binary = require_command("import", "gnome-screenshot")
        if Path(binary).name == "import":
            run_command([binary, "-window", "root", str(temp_path)])
        else:
            run_command([binary, "-f", str(temp_path)])
        return {"backend": "x11", "action": "snapshot", "path": str(temp_path), "exists": temp_path.exists()}
    except (CommandUnavailableError, CommandExecutionError):
        pass

    # Fall back to scrot
    try:
        scrot_bin = require_command("scrot")
        run_command([scrot_bin, str(temp_path)])
        return {"backend": "x11", "action": "snapshot", "path": str(temp_path), "exists": temp_path.exists()}
    except (CommandUnavailableError, CommandExecutionError) as exc:
        return {"backend": "x11", "action": "snapshot", "error": str(exc), "path": ""}


def scroll(amount: int, horizontal: bool = False) -> dict:
    binary = require_command("xdotool")
    button = "6" if horizontal and amount > 0 else "7" if horizontal else "4" if amount > 0 else "5"
    run_command([binary, "click", button])
    return {"backend": "x11", "action": "scroll", "amount": amount, "horizontal": horizontal}


def move(x: int, y: int) -> dict:
    binary = require_command("xdotool")
    run_command([binary, "mousemove", str(x), str(y)])
    return {"backend": "x11", "action": "move", "x": x, "y": y}


def shortcut(keys: list[str]) -> dict:
    binary = require_command("xdotool")
    run_command([binary, "key", "+".join(keys)])
    return {"backend": "x11", "action": "shortcut", "keys": keys}


def focus_window(title: str) -> dict:
    binary = require_command("wmctrl")
    run_command([binary, "-a", title])
    return {"backend": "x11", "action": "focus_window", "title": title}


def list_windows() -> dict:
    binary = require_command("wmctrl")
    result = run_command([binary, "-lpG"])
    windows = []
    pattern = re.compile(
        r"^(?P<id>0x[0-9a-fA-F]+)\s+(?P<desktop>-?\d+)\s+(?P<pid>\d+)\s+(?P<x>-?\d+)\s+(?P<y>-?\d+)\s+(?P<width>\d+)\s+(?P<height>\d+)\s+(?P<host>\S+)\s+(?P<title>.*)$"
    )
    for line in result.stdout.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        windows.append(
            {
                "id": match.group("id"),
                "desktop": int(match.group("desktop")),
                "pid": int(match.group("pid")),
                "x": int(match.group("x")),
                "y": int(match.group("y")),
                "width": int(match.group("width")),
                "height": int(match.group("height")),
                "host": match.group("host"),
                "title": match.group("title"),
                "focused": False,
            }
        )
    return {"backend": "x11", "action": "list_windows", "windows": windows}


def get_clipboard() -> dict:
    binary = require_command("xclip", "xsel")
    if Path(binary).name == "xclip":
        result = run_command([binary, "-selection", "clipboard", "-o"])
    else:
        result = run_command([binary, "--clipboard", "--output"])
    return {"backend": "x11", "action": "get_clipboard", "content": result.stdout}


def notify(title: str, message: str) -> dict:
    binary = require_command("notify-send")
    run_command([binary, title, message])
    return {"backend": "x11", "action": "notify", "title": title}
