from __future__ import annotations

import subprocess
import time

from pi_remote_mcp.desktop.backend_selector import detect_backend, get_backend_module
from pi_remote_mcp.utils.command_runner import CommandUnavailableError, require_command, run_command


def _backend_call(name: str, *args, **kwargs) -> dict:
    module, capabilities = get_backend_module()
    if capabilities.backend == "headless":
        return {"tool": name, "error": "No GUI session detected", "backend": capabilities.backend}
    if not hasattr(module, name):
        return {
            "tool": name,
            "error": f"Backend '{capabilities.backend}' does not implement '{name}'",
            "backend": capabilities.backend,
        }
    try:
        result = getattr(module, name)(*args, **kwargs)
        if isinstance(result, dict):
            result.setdefault("capabilities_note", capabilities.notes)
        return result
    except (CommandUnavailableError, subprocess.SubprocessError, RuntimeError) as exc:
        return {
            "tool": name,
            "backend": capabilities.backend,
            "error": str(exc),
            "capabilities_note": capabilities.notes,
        }


def snapshot() -> dict:
    backend = detect_backend()
    if not backend.supports_screenshot:
        return {"tool": "Snapshot", "backend": backend.backend, "error": backend.notes}
    result = _backend_call("snapshot")
    result["tool"] = "Snapshot"
    result["commands"] = backend.commands
    return result


def click(x: int, y: int, button: str = "left", action: str = "click") -> dict:
    result = _backend_call("click", x, y, button=button, action=action)
    result["tool"] = "Click"
    return result


def type_text(
    text: str,
    x: int = 0,
    y: int = 0,
    clear: bool = False,
    press_enter: bool = False,
) -> dict:
    if x and y:
        click(x, y)
    result = _backend_call("type_text", text, clear=clear, press_enter=press_enter)
    result["tool"] = "Type"
    return result


def scroll(amount: int, x: int = 0, y: int = 0, horizontal: bool = False) -> dict:
    if x and y:
        move(x, y)
    result = _backend_call("scroll", amount, horizontal=horizontal)
    result["tool"] = "Scroll"
    return result


def move(
    x: int,
    y: int,
    drag: bool = False,
    start_x: int = 0,
    start_y: int = 0,
    duration: float = 0.3,
) -> dict:
    if drag and start_x and start_y:
        _backend_call("move", start_x, start_y)
    time.sleep(max(duration, 0.0))
    result = _backend_call("move", x, y)
    result["tool"] = "Move"
    result["drag"] = drag
    return result


def shortcut(keys: str) -> dict:
    parts = [part.strip() for part in keys.replace("+", ",").split(",") if part.strip()]
    result = _backend_call("shortcut", parts)
    result["tool"] = "Shortcut"
    return result


def wait(seconds: float = 1.0) -> dict:
    time.sleep(max(seconds, 0.0))
    return {"tool": "Wait", "waited_seconds": max(seconds, 0.0)}


def focus_window(title: str) -> dict:
    result = _backend_call("focus_window", title)
    result["tool"] = "FocusWindow"
    return result


def minimize_all() -> dict:
    result = shortcut("super+d")
    result["tool"] = "MinimizeAll"
    return result


def app(command: str, args: str = "", cwd: str = "") -> dict:
    command_parts = [command, *[part for part in args.split(" ") if part]]
    process = subprocess.Popen(command_parts, cwd=cwd or None)  # noqa: S603
    return {
        "tool": "App",
        "command": command_parts,
        "cwd": cwd or None,
        "pid": process.pid,
    }


def get_clipboard() -> dict:
    result = _backend_call("get_clipboard")
    result["tool"] = "GetClipboard"
    return result


def set_clipboard(text: str) -> dict:
    backend = detect_backend()
    try:
        if backend.backend == "wayland":
            binary = require_command("wl-copy")
            completed = subprocess.run([binary], input=text, text=True, capture_output=True, check=False)
        elif backend.backend == "x11":
            binary = require_command("xclip", "xsel")
            if binary.endswith("xclip"):
                completed = subprocess.run(
                    [binary, "-selection", "clipboard"],
                    input=text,
                    text=True,
                    capture_output=True,
                    check=False,
                )
            else:
                completed = subprocess.run(
                    [binary, "--clipboard", "--input"],
                    input=text,
                    text=True,
                    capture_output=True,
                    check=False,
                )
        else:
            return {"tool": "SetClipboard", "error": backend.notes, "backend": backend.backend}
        return {
            "tool": "SetClipboard",
            "backend": backend.backend,
            "content_length": len(text),
            "exit_code": completed.returncode,
            "stderr": completed.stderr,
        }
    except (CommandUnavailableError, subprocess.SubprocessError) as exc:
        return {"tool": "SetClipboard", "backend": backend.backend, "error": str(exc)}


def notification(title: str = "Pi Control MCP", message: str = "") -> dict:
    result = _backend_call("notify", title, message)
    result["tool"] = "Notification"
    return result


def lock_screen() -> dict:
    for cmd in (("loginctl", "lock-session"), ("xdg-screensaver", "lock"), ("dm-tool", "lock")):
        try:
            binary = require_command(cmd[0])
            run_command([binary, *cmd[1:]], check=True)
            return {"tool": "LockScreen", "command": [binary, *cmd[1:]]}
        except (CommandUnavailableError, RuntimeError):
            continue
    return {"tool": "LockScreen", "error": "No supported screen-lock command was found"}


def list_windows() -> dict:
    result = _backend_call("list_windows")
    result["tool"] = "ListWindows"
    return result


def get_backend_info() -> dict:
    backend = detect_backend()
    return {
        "tool": "GetBackendInfo",
        "backend": backend.backend,
        "supports_pointer": backend.supports_pointer,
        "supports_keyboard": backend.supports_keyboard,
        "supports_screenshot": backend.supports_screenshot,
        "supports_clipboard": backend.supports_clipboard,
        "supports_window_management": backend.supports_window_management,
        "supports_notifications": backend.supports_notifications,
        "commands": backend.commands,
        "note": backend.notes,
    }


def annotated_snapshot(max_elements: int = 30, quality: int = 75, max_width: int = 0) -> dict:
    from pi_remote_mcp.tools.ui_tools import annotated_snapshot as ui_annotated_snapshot

    return ui_annotated_snapshot(max_elements=max_elements, quality=quality, max_width=max_width)


def observe_screen() -> dict:
    backend = detect_backend()
    return {
        "tool": "ObserveScreen",
        "backend": backend.backend,
        "summary": "Screen observation scaffold active",
        "note": backend.notes,
    }
