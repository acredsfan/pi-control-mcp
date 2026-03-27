from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from typing import Sequence


@dataclass(slots=True)
class CommandResult:
    ok: bool
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str


class CommandUnavailableError(RuntimeError):
    """Raised when a required system command is not available."""


class CommandExecutionError(RuntimeError):
    """Raised when a system command exits unsuccessfully."""


def find_command(*names: str) -> str | None:
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def require_command(*names: str) -> str:
    found = find_command(*names)
    if found is None:
        joined = ", ".join(names)
        raise CommandUnavailableError(f"Required command not found: {joined}")
    return found


def run_command(
    command: Sequence[str],
    *,
    cwd: str | None = None,
    timeout: float = 15.0,
    check: bool = True,
    text: bool = True,
) -> CommandResult:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        timeout=timeout,
        capture_output=True,
        text=text,
        check=False,
    )
    result = CommandResult(
        ok=completed.returncode == 0,
        command=list(command),
        exit_code=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )
    if check and not result.ok:
        raise CommandExecutionError(
            f"Command failed ({result.exit_code}): {' '.join(result.command)}\n{result.stderr.strip()}"
        )
    return result


def ensure_parent_dir(path: str | Path) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved
