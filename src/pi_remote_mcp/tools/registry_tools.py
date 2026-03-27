from __future__ import annotations

from pi_remote_mcp.utils.command_runner import CommandUnavailableError, require_command, run_command


def reg_read(key: str, value_name: str = "") -> dict:
    try:
        gsettings = require_command("gsettings")
        command = [gsettings, "get", key, value_name] if value_name else [gsettings, "list-recursively", key]
        result = run_command(command)
        return {"tool": "RegRead", "key": key, "value_name": value_name, "value": result.stdout.strip()}
    except (CommandUnavailableError, RuntimeError) as exc:
        return {"tool": "RegRead", "key": key, "value_name": value_name, "error": str(exc)}


def reg_write(key: str, value_name: str, data: str, reg_type: str = "REG_SZ") -> dict:
    try:
        gsettings = require_command("gsettings")
        result = run_command([gsettings, "set", key, value_name, data])
        return {"tool": "RegWrite", "key": key, "value_name": value_name, "data": data, "reg_type": reg_type, "stdout": result.stdout}
    except (CommandUnavailableError, RuntimeError) as exc:
        return {"tool": "RegWrite", "key": key, "value_name": value_name, "data": data, "reg_type": reg_type, "error": str(exc)}
