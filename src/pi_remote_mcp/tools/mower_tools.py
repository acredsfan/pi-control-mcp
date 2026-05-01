from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

from pi_remote_mcp.memory.service import record_memory
from pi_remote_mcp.utils.command_runner import CommandExecutionError, CommandUnavailableError, require_command, run_command

DEFAULT_MOWER_SERVICES = ["lawnberry-backend", "lawnberry-frontend", "nginx", "NetworkManager", "cloudflared"]


def _run_optional(command: list[str]) -> dict:
    try:
        require_command(command[0])
        result = run_command(command, check=False)
        return {"available": True, "ok": result.ok, "stdout": result.stdout, "stderr": result.stderr, "exit_code": result.exit_code}
    except CommandUnavailableError as exc:
        return {"available": False, "error": str(exc)}


def service_health_report(services: list[str] | None = None, include_journal: bool = True, journal_lines: int = 80) -> dict:
    services = services or DEFAULT_MOWER_SERVICES
    status = {name: _run_optional(["systemctl", "status", name, "--no-pager"]) for name in services}
    journal = {}
    if include_journal:
        for name in services:
            journal[name] = _run_optional(["journalctl", "-u", name, "-n", str(journal_lines), "--no-pager"])
    record_memory("service", "Service health report", f"Checked {len(services)} services", json.dumps({"services": services}), tags=["service-health", "mower"])
    return {"tool": "ServiceHealthReport", "ok": True, "services": status, "journal": journal}


def journal_search(unit: str | None = None, query: str | None = None, since: str = "1 hour ago", limit: int = 200) -> dict:
    cmd = ["journalctl", "--since", since, "-n", str(limit), "--no-pager"]
    if unit:
        cmd += ["-u", unit]
    data = _run_optional(cmd)
    lines = data.get("stdout", "").splitlines()
    if query:
        lines = [ln for ln in lines if query.lower() in ln.lower()]
    return {"tool": "JournalSearch", "ok": data.get("available", False), "available": data.get("available", False), "lines": lines[:limit], "error": data.get("error")}


def mower_runtime_snapshot(api_url: str = "http://127.0.0.1:8081", frontend_url: str = "http://127.0.0.1:3000", include_services: bool = True,
                           include_ports: bool = True, include_api_health: bool = True, include_recent_errors: bool = True) -> dict:
    result = {"tool": "MowerRuntimeSnapshot", "ok": True}
    if include_services:
        result["services"] = service_health_report(include_journal=False)["services"]
    if include_ports:
        result["ports"] = _run_optional(["ss", "-lntup"])
    if include_api_health:
        result["api_health"] = _http_probe(api_url)
        result["frontend_health"] = _http_probe(frontend_url)
    if include_recent_errors:
        result["recent_errors"] = journal_search(query="error", limit=80)
    record_memory("mower_snapshot", "Mower runtime snapshot", "Collected mower runtime snapshot", json.dumps(result), tags=["mower", "snapshot"])
    return result


def _http_probe(url: str) -> dict:
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=3) as response:  # nosec B310
            return {"available": True, "status": response.status}
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def hardware_probe(include_i2c: bool = True, include_uart: bool = True, include_usb: bool = True, include_gpio: bool = False) -> dict:
    out = {"tool": "HardwareProbe", "ok": True}
    if include_i2c:
        out["i2c"] = _run_optional(["i2cdetect", "-l"])
    if include_uart:
        out["uart"] = _run_optional(["bash", "-lc", "ls /dev/tty* 2>/dev/null | head -n 40"])
    if include_usb:
        out["usb"] = _run_optional(["lsusb"])
    if include_gpio:
        out["gpio"] = _run_optional(["gpioinfo"])
    return out


def network_failover_status() -> dict:
    return {"tool": "NetworkFailoverStatus", "ok": True, "nmcli": _run_optional(["nmcli", "device", "status"]), "ip_route": _run_optional(["ip", "route"]), "iw": _run_optional(["iw", "dev"])}


def git_project_state(root: str, include_recent_commits: bool = True, include_status: bool = True, include_untracked: bool = True) -> dict:
    git_dir = Path(root)
    if not git_dir.exists():
        return {"tool": "GitProjectState", "ok": False, "error": f"Path not found: {root}"}
    data: dict = {"tool": "GitProjectState", "ok": True, "root": str(git_dir)}
    if include_status:
        args = ["git", "status", "--short"]
        if not include_untracked:
            args.append("--untracked-files=no")
        data["status"] = _run_optional(args + ["--branch"])
    if include_recent_commits:
        data["commits"] = _run_optional(["git", "log", "--oneline", "-n", "10"])
    record_memory("git", "Git project state", f"Checked git state for {root}", json.dumps({"root": root}), tags=["git"])
    return data
