from __future__ import annotations


def click(x: int, y: int, button: str = "left") -> dict:
    return {
        "backend": "wayland",
        "action": "click",
        "x": x,
        "y": y,
        "button": button,
        "status": "queued",
    }


def type_text(text: str) -> dict:
    return {"backend": "wayland", "action": "type", "chars": len(text), "status": "queued"}


def snapshot() -> dict:
    return {"backend": "wayland", "action": "snapshot", "status": "not-implemented"}
