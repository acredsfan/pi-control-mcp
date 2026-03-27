from __future__ import annotations

from pi_remote_mcp.desktop.backend_selector import detect_backend


def snapshot() -> dict:
    backend = detect_backend()
    return {
        "tool": "Snapshot",
        "backend": backend.backend,
        "supports_screenshot": backend.supports_screenshot,
        "note": backend.notes,
    }


def click(x: int, y: int, button: str = "left") -> dict:
    backend = detect_backend()
    return {
        "tool": "Click",
        "backend": backend.backend,
        "x": x,
        "y": y,
        "button": button,
        "accepted": backend.supports_pointer,
        "note": backend.notes,
    }


def type_text(text: str) -> dict:
    backend = detect_backend()
    return {
        "tool": "Type",
        "backend": backend.backend,
        "length": len(text),
        "accepted": backend.supports_keyboard,
        "note": backend.notes,
    }


def observe_screen() -> dict:
    backend = detect_backend()
    return {
        "tool": "ObserveScreen",
        "backend": backend.backend,
        "summary": "Screen observation scaffold active",
        "note": backend.notes,
    }
