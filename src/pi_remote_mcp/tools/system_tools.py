from __future__ import annotations

import platform
import socket
import subprocess
import psutil


def get_system_info() -> dict:
    return {
        "tool": "GetSystemInfo",
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
    }


def list_processes(limit: int = 50) -> dict:
    result = []
    for p in psutil.process_iter(attrs=["pid", "name", "cpu_percent", "memory_percent"]):
        info = p.info
        result.append(info)
        if len(result) >= limit:
            break
    return {"tool": "ListProcesses", "processes": result}


def shell(command: str, cwd: str | None = None) -> dict:
    completed = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
    )
    return {
        "tool": "Shell",
        "exit_code": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }
