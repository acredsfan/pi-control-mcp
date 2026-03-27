from __future__ import annotations

import json
import os
import time
from typing import Any

from pi_remote_mcp.desktop.backend_selector import detect_backend
from pi_remote_mcp.tools.desktop_tools import get_backend_info, list_windows
from pi_remote_mcp.utils.command_runner import CommandUnavailableError, require_command, run_command


def _parse_windows_payload() -> list[dict[str, Any]]:
    result = list_windows()
    windows = result.get("windows")
    if isinstance(windows, list):
        return windows
    tree = result.get("tree")
    if isinstance(tree, list):
        return tree
    return []


def get_active_window() -> dict:
    backend = detect_backend()
    try:
        if backend.backend == "x11":
            xdotool = require_command("xdotool")
            result = run_command([xdotool, "getactivewindow", "getwindowname"])
            return {"tool": "GetActiveWindow", "backend": backend.backend, "title": result.stdout.strip()}
        windows = _parse_windows_payload()
        focused = next((window for window in windows if window.get("focused")), None)
        return {"tool": "GetActiveWindow", "backend": backend.backend, "window": focused}
    except (CommandUnavailableError, RuntimeError) as exc:
        return {"tool": "GetActiveWindow", "backend": backend.backend, "error": str(exc)}


def window_properties(title: str = "") -> dict:
    windows = _parse_windows_payload()
    if title:
        match = next((window for window in windows if title.lower() in str(window).lower()), None)
        return {"tool": "WindowProperties", "title": title, "window": match}
    return {"tool": "WindowProperties", "windows": windows[:25]}


def list_monitors() -> dict:
    backend = detect_backend()
    commands = [("xrandr", ["--listmonitors"]), ("wlr-randr", []), ("swaymsg", ["-t", "get_outputs"])]
    for name, args in commands:
        try:
            binary = require_command(name)
            result = run_command([binary, *args])
            payload = result.stdout.strip()
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                parsed = payload.splitlines()
            return {"tool": "ListMonitors", "backend": backend.backend, "monitors": parsed}
        except (CommandUnavailableError, RuntimeError):
            continue
    return {"tool": "ListMonitors", "backend": backend.backend, "error": "No supported monitor command found"}


def list_workspaces() -> dict:
    backend = detect_backend()
    for name, args in (("wmctrl", ["-d"]), ("swaymsg", ["-t", "get_workspaces"])):
        try:
            binary = require_command(name)
            result = run_command([binary, *args])
            payload = result.stdout.strip()
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                parsed = payload.splitlines()
            return {"tool": "ListWorkspaces", "backend": backend.backend, "workspaces": parsed}
        except (CommandUnavailableError, RuntimeError):
            continue
    return {"tool": "ListWorkspaces", "backend": backend.backend, "error": "No supported workspace command found"}


def switch_workspace(target: str) -> dict:
    backend = detect_backend()
    try:
        if backend.backend == "x11":
            wmctrl = require_command("wmctrl")
            run_command([wmctrl, "-s", target])
        else:
            swaymsg = require_command("swaymsg")
            run_command([swaymsg, "workspace", target])
        return {"tool": "SwitchWorkspace", "backend": backend.backend, "target": target}
    except (CommandUnavailableError, RuntimeError) as exc:
        return {"tool": "SwitchWorkspace", "backend": backend.backend, "target": target, "error": str(exc)}


def probe_capabilities() -> dict:
    info = get_backend_info()
    info["tool"] = "ProbeCapabilities"
    info["session_type"] = os.getenv("XDG_SESSION_TYPE", "")
    return info


def get_session_state() -> dict:
    backend = detect_backend()
    return {
        "tool": "GetSessionState",
        "backend": backend.backend,
        "session_type": os.getenv("XDG_SESSION_TYPE", ""),
        "wayland_display": os.getenv("WAYLAND_DISPLAY", ""),
        "display": os.getenv("DISPLAY", ""),
        "idle_hint": False,
    }


def reconnect_session(force: bool = False) -> dict:
    try:
        loginctl = require_command("loginctl")
        result = run_command([loginctl, "activate", os.getenv("XDG_SESSION_ID", "")], check=False)
        return {
            "tool": "ReconnectSession",
            "force": force,
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except (CommandUnavailableError, RuntimeError) as exc:
        return {"tool": "ReconnectSession", "force": force, "error": str(exc)}


def watch_clipboard(timeout: float = 5.0, poll_interval: float = 0.25) -> dict:
    from pi_remote_mcp.tools.desktop_tools import get_clipboard

    start = time.time()
    first = get_clipboard().get("content", "")
    while time.time() - start < timeout:
        current = get_clipboard().get("content", "")
        if current != first:
            return {"tool": "WatchClipboard", "changed": True, "content": current}
        time.sleep(poll_interval)
    return {"tool": "WatchClipboard", "changed": False, "content": first}


def watch_window(title: str, timeout: float = 5.0, poll_interval: float = 0.25) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        match = window_properties(title).get("window")
        if match:
            return {"tool": "WatchWindow", "found": True, "window": match}
        time.sleep(poll_interval)
    return {"tool": "WatchWindow", "found": False, "title": title}


def detect_dialog() -> dict:
    windows = _parse_windows_payload()
    keywords = ("dialog", "confirm", "warning", "error", "save", "open")
    matches = [window for window in windows if any(keyword in str(window).lower() for keyword in keywords)]
    return {"tool": "DetectDialog", "dialogs": matches, "detected": bool(matches)}
