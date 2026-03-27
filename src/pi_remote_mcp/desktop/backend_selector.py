from __future__ import annotations

import os
from dataclasses import dataclass
from importlib import import_module
from typing import Literal

from pi_remote_mcp.utils.command_runner import find_command

BackendKind = Literal["wayland", "x11", "headless"]


@dataclass(slots=True)
class BackendCapabilities:
    backend: BackendKind
    supports_pointer: bool
    supports_keyboard: bool
    supports_screenshot: bool
    supports_clipboard: bool
    supports_window_management: bool
    supports_notifications: bool
    commands: dict[str, str | None]
    notes: str = ""


def detect_backend() -> BackendCapabilities:
    wayland = os.getenv("WAYLAND_DISPLAY")
    x11 = os.getenv("DISPLAY")

    if wayland:
        commands = {
            "pointer": find_command("ydotool"),
            "screenshot": find_command("grim", "gnome-screenshot", "spectacle"),
            "clipboard_read": find_command("wl-paste"),
            "clipboard_write": find_command("wl-copy"),
            "window": find_command("swaymsg", "hyprctl", "wlr-randr"),
            "notify": find_command("notify-send"),
        }
        return BackendCapabilities(
            backend="wayland",
            supports_pointer=commands["pointer"] is not None,
            supports_keyboard=commands["pointer"] is not None,
            supports_screenshot=commands["screenshot"] is not None,
            supports_clipboard=commands["clipboard_read"] is not None
            and commands["clipboard_write"] is not None,
            supports_window_management=commands["window"] is not None,
            supports_notifications=commands["notify"] is not None,
            commands=commands,
            notes="Wayland session detected. Some actions depend on compositor helpers such as grim, ydotool, or swaymsg.",
        )

    if x11:
        commands = {
            "pointer": find_command("xdotool"),
            "screenshot": find_command("import", "xwd", "gnome-screenshot"),
            "clipboard_read": find_command("xclip", "xsel"),
            "clipboard_write": find_command("xclip", "xsel"),
            "window": find_command("wmctrl", "xdotool"),
            "notify": find_command("notify-send"),
        }
        return BackendCapabilities(
            backend="x11",
            supports_pointer=commands["pointer"] is not None,
            supports_keyboard=commands["pointer"] is not None,
            supports_screenshot=commands["screenshot"] is not None,
            supports_clipboard=commands["clipboard_read"] is not None
            and commands["clipboard_write"] is not None,
            supports_window_management=commands["window"] is not None,
            supports_notifications=commands["notify"] is not None,
            commands=commands,
            notes="X11 session detected.",
        )

    return BackendCapabilities(
        backend="headless",
        supports_pointer=False,
        supports_keyboard=False,
        supports_screenshot=False,
        supports_clipboard=False,
        supports_window_management=False,
        supports_notifications=False,
        commands={},
        notes="No desktop session detected. GUI tools will be unavailable.",
    )


def get_backend_module():
    capabilities = detect_backend()
    module_name = {
        "wayland": "pi_remote_mcp.desktop.backends.wayland_backend",
        "x11": "pi_remote_mcp.desktop.backends.x11_backend",
        "headless": "pi_remote_mcp.desktop.backends.x11_backend",
    }[capabilities.backend]
    return import_module(module_name), capabilities
