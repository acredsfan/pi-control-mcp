from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

BackendKind = Literal["wayland", "x11", "headless"]


@dataclass(slots=True)
class BackendCapabilities:
    backend: BackendKind
    supports_pointer: bool
    supports_keyboard: bool
    supports_screenshot: bool
    notes: str = ""


def detect_backend() -> BackendCapabilities:
    wayland = os.getenv("WAYLAND_DISPLAY")
    x11 = os.getenv("DISPLAY")

    if wayland:
        return BackendCapabilities(
            backend="wayland",
            supports_pointer=True,
            supports_keyboard=True,
            supports_screenshot=True,
            notes="Wayland session detected. Some compositors may require external helpers.",
        )

    if x11:
        return BackendCapabilities(
            backend="x11",
            supports_pointer=True,
            supports_keyboard=True,
            supports_screenshot=True,
            notes="X11 session detected.",
        )

    return BackendCapabilities(
        backend="headless",
        supports_pointer=False,
        supports_keyboard=False,
        supports_screenshot=False,
        notes="No desktop session detected. GUI tools will be unavailable.",
    )
