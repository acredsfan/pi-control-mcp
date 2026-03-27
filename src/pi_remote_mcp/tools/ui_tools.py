from __future__ import annotations

import hashlib
import importlib
import json
import time
from pathlib import Path
from typing import Any

from pi_remote_mcp.runtime_tasks import registry
from pi_remote_mcp.tools.desktop_tools import click, snapshot, type_text
from pi_remote_mcp.tools.session_tools import window_properties

_BASELINES: dict[str, str] = {}


def _import_pillow():
    try:
        image_module = importlib.import_module("PIL.Image")
        draw_module = importlib.import_module("PIL.ImageDraw")
    except ImportError:  # pragma: no cover - optional dependency
        return None, None
    return image_module, draw_module


def _import_tesseract():
    try:
        pytesseract = importlib.import_module("pytesseract")
    except ImportError:  # pragma: no cover - optional dependency
        return None
    return pytesseract


def _snapshot_path() -> str | None:
    snap = snapshot()
    return snap.get("path") if isinstance(snap, dict) else None


def _load_image(path: str):
    Image, _ = _import_pillow()
    if Image is None:
        return None
    return Image.open(path)


def _window_elements(window_title: str = "") -> list[dict[str, Any]]:
    payload = window_properties(window_title)
    windows = payload.get("windows") or []
    single = payload.get("window")
    if single:
        windows = [single]
    elements: list[dict[str, Any]] = []
    for index, window in enumerate(windows):
        if not isinstance(window, dict):
            continue
        x = int(window.get("x", 0))
        y = int(window.get("y", 0))
        width = int(window.get("width", 0))
        height = int(window.get("height", 0))
        elements.append(
            {
                "element_id": f"window-{index}",
                "label": window.get("title", "window"),
                "class": "window",
                "rect": {"left": x, "top": y, "width": width, "height": height},
                "center": {"x": x + max(width // 2, 0), "y": y + max(height // 2, 0)},
                "window": window,
            }
        )
    return elements


def ocr(left: int = 0, top: int = 0, right: int = 0, bottom: int = 0, lang: str = "eng") -> dict:
    pytesseract = _import_tesseract()
    path = _snapshot_path()
    if pytesseract is None or not path:
        return {"tool": "OCR", "error": "OCR dependencies or screenshot support unavailable"}
    image = _load_image(path)
    if image is None:
        return {"tool": "OCR", "error": "Pillow is not installed"}
    if right > left and bottom > top:
        image = image.crop((left, top, right, bottom))
    text = pytesseract.image_to_string(image, lang=lang)
    return {"tool": "OCR", "path": path, "text": text}


def annotated_snapshot(max_elements: int = 30, quality: int = 75, max_width: int = 0) -> dict:
    path = _snapshot_path()
    Image, ImageDraw = _import_pillow()
    if not path or Image is None or ImageDraw is None:
        return {"tool": "AnnotatedSnapshot", "error": "Screenshot or Pillow support unavailable"}
    image = Image.open(path)
    draw = ImageDraw.Draw(image)
    elements = _window_elements()[:max_elements]
    for index, element in enumerate(elements, start=1):
        rect = element["rect"]
        left = rect["left"]
        top = rect["top"]
        right = left + rect["width"]
        bottom = top + rect["height"]
        draw.rectangle((left, top, right, bottom), outline="red", width=2)
        draw.text((left + 4, top + 4), str(index), fill="white")
    annotated_path = str(Path(path).with_name(Path(path).stem + "-annotated.png"))
    image.save(annotated_path, quality=quality)
    return {"tool": "AnnotatedSnapshot", "path": annotated_path, "elements": elements, "max_width": max_width}


def screen_record(
    duration: float = 3.0,
    fps: int = 5,
    left: int = 0,
    top: int = 0,
    right: int = 0,
    bottom: int = 0,
    max_width: int = 800,
) -> dict:
    Image, _ = _import_pillow()
    path = _snapshot_path()
    if not path or Image is None:
        return {"tool": "ScreenRecord", "error": "Screenshot or Pillow support unavailable"}
    frame_paths: list[str] = []
    frame_count = max(1, int(max(duration, 0.2) * max(fps, 1)))
    interval = 1 / max(fps, 1)
    for _index in range(frame_count):
        current = _snapshot_path()
        if current:
            frame_paths.append(current)
        time.sleep(interval)
    images = [Image.open(frame) for frame in frame_paths if Path(frame).exists()]
    if not images:
        return {"tool": "ScreenRecord", "error": "No frames were captured"}
    gif_path = str(Path(frame_paths[-1]).with_name(Path(frame_paths[-1]).stem + "-recording.gif"))
    images[0].save(
        gif_path,
        save_all=True,
        append_images=images[1:],
        duration=max(int(interval * 1000), 1),
        loop=0,
    )
    return {
        "tool": "ScreenRecord",
        "path": gif_path,
        "frame_count": len(images),
        "duration": duration,
        "bounds": {"left": left, "top": top, "right": right, "bottom": bottom, "max_width": max_width},
    }


def ui_map(window_title: str = "", include_text: bool = False, max_elements: int = 100, min_width: int = 4, min_height: int = 4) -> dict:
    elements = []
    for element in _window_elements(window_title):
        rect = element["rect"]
        if rect["width"] >= min_width and rect["height"] >= min_height:
            elements.append(element)
    if include_text:
        ocr_result = ocr()
        if "text" in ocr_result:
            elements.append({"element_id": "ocr-fullscreen", "label": ocr_result["text"][:500], "class": "ocr"})
    return {"tool": "UIMap", "window_title": window_title, "elements": elements[:max_elements]}


def ui_map_json(window_title: str = "", include_text: bool = False, max_elements: int = 100, min_width: int = 4, min_height: int = 4) -> dict:
    result = ui_map(window_title, include_text, max_elements, min_width, min_height)
    result["tool"] = "UIMapJson"
    return result


def ui_find(query: str, window_title: str = "", include_text: bool = False, max_results: int = 5, match_mode: str = "auto", max_elements: int = 100, min_width: int = 4, min_height: int = 4) -> dict:
    mapping = ui_map(window_title, include_text, max_elements, min_width, min_height)
    q = query.lower()
    matches = []
    for element in mapping["elements"]:
        haystack = f"{element.get('label', '')} {element.get('class', '')}".lower()
        if q in haystack:
            matches.append({**element, "match": {"mode": match_mode, "score": 1.0 if q == haystack.strip() else 0.7}})
    return {"tool": "UIFind", "query": query, "results": matches[:max_results]}


def ui_click(query: str, window_title: str = "", include_text: bool = False, match_mode: str = "auto", button: str = "left", action: str = "click", max_elements: int = 100, min_width: int = 4, min_height: int = 4) -> dict:
    found = ui_find(query, window_title, include_text, 1, match_mode, max_elements, min_width, min_height)
    results = found.get("results", [])
    if not results:
        return {"tool": "UIClick", "query": query, "error": "No matching UI element found"}
    target = results[0]
    center = target.get("center", {"x": 0, "y": 0})
    click_result = click(center.get("x", 0), center.get("y", 0), button=button, action=action)
    return {"tool": "UIClick", "query": query, "target": target, "click_result": click_result}


def observe_screen_tool(window_title: str = "", include_text: bool = False, monitor: int = 0, left: int = 0, top: int = 0, right: int = 0, bottom: int = 0, max_elements: int = 40, min_width: int = 4, min_height: int = 4, grid_size: int = 6, reset: bool = False, update_baseline: bool = True) -> dict:
    mapping = ui_map(window_title, include_text, max_elements, min_width, min_height)
    digest = hashlib.sha256(json.dumps(mapping, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    baseline_key = f"{window_title}:{monitor}:{left}:{top}:{right}:{bottom}:{grid_size}"
    previous = None if reset else _BASELINES.get(baseline_key)
    changed = previous != digest
    if update_baseline:
        _BASELINES[baseline_key] = digest
    return {
        "tool": "ObserveScreen",
        "window_title": window_title,
        "changed": changed,
        "baseline": previous,
        "current": digest,
        "elements": mapping["elements"],
    }


def ui_watch(window_title: str = "", include_text: bool = False, max_elements: int = 100, min_width: int = 4, min_height: int = 4, reset: bool = False, update_baseline: bool = True) -> dict:
    result = observe_screen_tool(window_title, include_text, 0, 0, 0, 0, 0, max_elements, min_width, min_height, 6, reset, update_baseline)
    result["tool"] = "UIWatch"
    return result


def ui_act(query: str, window_title: str = "", include_text: bool = False, match_mode: str = "auto", button: str = "left", action: str = "click", text: str = "", clear: bool = False, press_enter: bool = False, wait_for_change: bool = True, wait_for_query: str = "", wait_match_mode: str = "auto", wait_until: str = "appear", timeout_seconds: float = 2.0, poll_interval: float = 0.25, focus_window: bool = True, max_elements: int = 100, min_width: int = 4, min_height: int = 4, grid_size: int = 6) -> dict:
    task_id = registry.start("UIAct", {"query": query})
    try:
        if text:
            action_result = type_text(text, clear=clear, press_enter=press_enter)
        else:
            action_result = ui_click(query, window_title, include_text, match_mode, button, action, max_elements, min_width, min_height)
        wait_result: dict[str, Any] | None = None
        if wait_for_query:
            start = time.time()
            while time.time() - start < timeout_seconds:
                found = ui_find(wait_for_query, window_title, include_text, 1, wait_match_mode, max_elements, min_width, min_height)
                condition_met = bool(found.get("results")) if wait_until == "appear" else not bool(found.get("results"))
                if condition_met:
                    wait_result = found
                    break
                time.sleep(poll_interval)
        elif wait_for_change:
            wait_result = ui_watch(window_title, include_text, max_elements, min_width, min_height, False, False)
        registry.finish(task_id, details={"query": query})
        return {"tool": "UIAct", "task_id": task_id, "action_result": action_result, "wait_result": wait_result, "focused": focus_window}
    except Exception as exc:
        registry.fail(task_id, str(exc))
        return {"tool": "UIAct", "task_id": task_id, "error": str(exc)}


def ui_sequence(steps_json: str, default_poll_interval: float = 0.25, max_steps: int = 8, max_elements: int = 100, min_width: int = 4, min_height: int = 4, grid_size: int = 6) -> dict:
    task_id = registry.start("UISequence", {"steps_json": steps_json})
    try:
        steps = json.loads(steps_json)
        if not isinstance(steps, list):
            raise ValueError("steps_json must decode to a list")
        results = []
        for step in steps[:max_steps]:
            action = step.get("action", "click")
            if action == "type":
                results.append(type_text(step.get("text", ""), clear=bool(step.get("clear", False)), press_enter=bool(step.get("press_enter", False))))
            elif action == "wait":
                time.sleep(float(step.get("seconds", default_poll_interval)))
                results.append({"tool": "Wait", "waited_seconds": float(step.get("seconds", default_poll_interval))})
            else:
                results.append(
                    ui_click(
                        step.get("query", ""),
                        step.get("window_title", ""),
                        bool(step.get("include_text", False)),
                        step.get("match_mode", "auto"),
                        step.get("button", "left"),
                        step.get("action", "click"),
                        max_elements,
                        min_width,
                        min_height,
                    )
                )
        registry.finish(task_id, details={"steps": len(results)})
        return {"tool": "UISequence", "task_id": task_id, "results": results}
    except Exception as exc:
        registry.fail(task_id, str(exc))
        return {"tool": "UISequence", "task_id": task_id, "error": str(exc)}
