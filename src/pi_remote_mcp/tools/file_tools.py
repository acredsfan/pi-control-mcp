from __future__ import annotations

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
