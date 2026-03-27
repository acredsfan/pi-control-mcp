from __future__ import annotations

import platform
import socket
import subprocess

import psutil

from pi_remote_mcp.tools.desktop_tools import get_clipboard as desktop_get_clipboard
from pi_remote_mcp.tools.desktop_tools import lock_screen as desktop_lock_screen
from pi_remote_mcp.tools.desktop_tools import notification as desktop_notification
from pi_remote_mcp.tools.desktop_tools import set_clipboard as desktop_set_clipboard
from pi_remote_mcp.utils.command_runner import find_command, require_command, run_command


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


def kill_process(pid: int = 0, name: str = "") -> dict:
    if pid:
        process = psutil.Process(pid)
        process.kill()
        return {"tool": "KillProcess", "pid": pid, "name": process.name()}

    if name:
        killed = []
        for process in psutil.process_iter(attrs=["pid", "name"]):
            if process.info.get("name") == name:
                psutil.Process(process.info["pid"]).kill()
                killed.append(process.info)
        return {"tool": "KillProcess", "name": name, "killed": killed}

    return {"tool": "KillProcess", "error": "Provide pid or name"}


def get_clipboard() -> dict:
    return desktop_get_clipboard()


def set_clipboard(text: str) -> dict:
    return desktop_set_clipboard(text)


def notification(title: str = "Pi Control MCP", message: str = "") -> dict:
    return desktop_notification(title, message)


def lock_screen() -> dict:
    return desktop_lock_screen()


def service_list(filter_text: str = "") -> dict:
    binary = require_command("systemctl")
    result = run_command([binary, "list-units", "--type=service", "--all", "--no-pager"])
    lines = [line for line in result.stdout.splitlines() if filter_text.lower() in line.lower()]
    return {"tool": "ServiceList", "filter": filter_text, "services": lines}


def service_start(name: str) -> dict:
    binary = require_command("systemctl")
    result = run_command([binary, "start", name])
    return {"tool": "ServiceStart", "name": name, "stdout": result.stdout}


def service_stop(name: str) -> dict:
    binary = require_command("systemctl")
    result = run_command([binary, "stop", name])
    return {"tool": "ServiceStop", "name": name, "stdout": result.stdout}


def task_list(filter_text: str = "") -> dict:
    services = service_list(filter_text)
    timer_binary = require_command("systemctl")
    result = run_command([timer_binary, "list-timers", "--all", "--no-pager"])
    return {"tool": "TaskList", "timers": result.stdout.splitlines(), "services": services.get("services", [])}


def task_create(name: str, command: str, schedule: str) -> dict:
    return {
        "tool": "TaskCreate",
        "name": name,
        "command": command,
        "schedule": schedule,
        "note": "Task creation should be mapped to systemd timers or cron in a later implementation pass",
    }


def task_delete(name: str) -> dict:
    return {
        "tool": "TaskDelete",
        "name": name,
        "note": "Task deletion should remove the mapped systemd timer/cron entry in a later implementation pass",
    }


def event_log(log_name: str = "system", count: int = 20, level: str = "") -> dict:
    binary = find_command("journalctl")
    if not binary:
        return {"tool": "EventLog", "error": "journalctl not available"}
    command = [binary, "-n", str(count), "--no-pager"]
    if log_name.lower() != "system":
        command.extend(["-u", log_name])
    if level:
        command.extend(["-p", level])
    result = run_command(command)
    return {"tool": "EventLog", "entries": result.stdout.splitlines()}
