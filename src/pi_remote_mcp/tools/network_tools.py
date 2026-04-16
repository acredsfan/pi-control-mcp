from __future__ import annotations

import socket
import urllib.error
import urllib.request

import psutil

from pi_remote_mcp.utils.command_runner import require_command, run_command


def ping(host: str, count: int = 4) -> dict:
    binary = require_command("ping")
    flag = "-n" if host.startswith("windows:") else "-c"
    normalized_host = host.removeprefix("windows:")
    result = run_command([binary, flag, str(count), normalized_host])
    return {"tool": "Ping", "host": normalized_host, "stdout": result.stdout, "stderr": result.stderr}


def port_check(host: str, port: int, timeout: float = 5.0) -> dict:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
        return {"tool": "PortCheck", "host": host, "port": port, "open": True, "timeout": timeout}
    except OSError as exc:
        return {"tool": "PortCheck", "host": host, "port": port, "open": False, "timeout": timeout, "error": str(exc)}


def net_connections(filter_text: str = "", limit: int = 50) -> dict:
    connections = []
    for conn in psutil.net_connections():
        local_addr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
        remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ""
        rendered = f"{conn.type} {local_addr} -> {remote_addr} {conn.status}"
        if filter_text.lower() in rendered.lower():
            connections.append(
                {
                    "fd": conn.fd,
                    "family": str(conn.family),
                    "type": str(conn.type),
                    "local": local_addr,
                    "remote": remote_addr,
                    "status": conn.status,
                    "pid": conn.pid,
                }
            )
        if len(connections) >= limit:
            break
    return {"tool": "NetConnections", "filter": filter_text, "connections": connections}


def scrape(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            content = response.read().decode("utf-8", errors="replace")
        return {"tool": "Scrape", "url": url, "content": content[:10000], "truncated": len(content) > 10000}
    except urllib.error.URLError as exc:
        return {"tool": "Scrape", "url": url, "error": str(exc)}
