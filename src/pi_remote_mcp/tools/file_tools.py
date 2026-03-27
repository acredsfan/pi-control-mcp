from __future__ import annotations

import base64
from fnmatch import fnmatch
from pathlib import Path


def file_list(path: str = ".") -> dict:
    p = Path(path)
    items = []
    if p.exists() and p.is_dir():
        for child in sorted(p.iterdir()):
            items.append(
                {
                    "name": child.name,
                    "is_dir": child.is_dir(),
                }
            )
    return {"tool": "FileList", "path": str(p.resolve()), "items": items}


def file_read(path: str, max_chars: int = 2000) -> dict:
    p = Path(path)
    if not p.exists():
        return {"tool": "FileRead", "error": "not found", "path": path}
    text = p.read_text(encoding="utf-8", errors="replace")
    return {
        "tool": "FileRead",
        "path": str(p.resolve()),
        "truncated": len(text) > max_chars,
        "content": text[:max_chars],
    }


def file_write(path: str, content: str) -> dict:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return {"tool": "FileWrite", "path": str(p.resolve()), "written": len(content)}


def file_search(pattern: str, path: str = ".", recursive: bool = True, limit: int = 50) -> dict:
    root = Path(path)
    iterator = root.rglob("*") if recursive else root.glob("*")
    matches = []
    for item in iterator:
        if fnmatch(item.name, pattern):
            matches.append({"path": str(item.resolve()), "is_dir": item.is_dir()})
        if len(matches) >= limit:
            break
    return {
        "tool": "FileSearch",
        "pattern": pattern,
        "path": str(root.resolve()),
        "recursive": recursive,
        "matches": matches,
    }


def file_download(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"tool": "FileDownload", "error": "not found", "path": path}
    return {
        "tool": "FileDownload",
        "path": str(p.resolve()),
        "data_base64": base64.b64encode(p.read_bytes()).decode("ascii"),
    }


def file_upload(path: str, data_base64: str) -> dict:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    raw = base64.b64decode(data_base64.encode("ascii"))
    p.write_bytes(raw)
    return {"tool": "FileUpload", "path": str(p.resolve()), "written": len(raw)}
