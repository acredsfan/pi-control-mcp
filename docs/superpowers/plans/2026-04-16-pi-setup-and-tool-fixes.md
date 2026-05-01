# Pi Control MCP — Setup, Boot Service & Tool Fixes

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install the server, fix broken tools, create a persistent HTTP service (systemd), and wire up Copilot CLI, VS Code Insiders, and Open WebUI as clients.

**Architecture:** The server runs in two modes concurrently — a persistent `streamable-http` daemon (systemd, port 8090) used by Open WebUI, and stdio processes spawned on demand by Copilot CLI and VS Code Insiders. All three clients can reach every tool; the HTTP daemon exposes the same tools without spawning additional processes.

**Tech Stack:** Python 3.13, FastMCP 3.x, systemd, X11 (Xorg :0 + Openbox), cron, `scrot`, `libnotify-bin`

---

## Environment Facts (do not re-detect)

- Desktop session: **X11** — `DISPLAY=:0`, `XAUTHORITY=/home/pi/.Xauthority`
- `DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus`
- `XDG_RUNTIME_DIR=/run/user/1000`
- Venv: `/home/pi/pi-control-mcp/.venv`
- Binary: `/home/pi/pi-control-mcp/.venv/bin/pi-control-mcp`
- Missing system tools: `notify-send` (need `libnotify-bin`); `scrot` is present but not in X11 snapshot code
- VS Code Insiders user config dir: `~/.config/Code - Insiders/User/`

---

## Task 1: Install missing system packages

**Files:** none (system packages)

- [ ] **Step 1: Install libnotify-bin**

```bash
sudo apt-get install -y libnotify-bin
```

Expected: `notify-send` appears at `/usr/bin/notify-send`

- [ ] **Step 2: Verify**

```bash
which notify-send && notify-send --version
```

Expected: version line printed, exit 0.

- [ ] **Step 3: Commit** *(skip — no source files changed)*

---

## Task 2: Fix X11 snapshot — add scrot support

`x11_backend.snapshot()` tries `import` (ImageMagick) then `gnome-screenshot`. Neither is installed. `scrot` is available and must be added.

**Files:**
- Modify: `src/pi_remote_mcp/desktop/backends/x11_backend.py`
- Test: `tests/test_backend.py`

- [ ] **Step 1: Write a failing test**

Add to `tests/test_backend.py`:

```python
import os
from unittest.mock import patch
from pi_remote_mcp.desktop.backends.x11_backend import snapshot as x11_snapshot


def test_x11_snapshot_uses_scrot_when_import_missing() -> None:
    """snapshot() should succeed with scrot if import/gnome-screenshot absent."""
    with patch("pi_remote_mcp.desktop.backends.x11_backend.require_command") as mock_req, \
         patch("pi_remote_mcp.desktop.backends.x11_backend.run_command") as mock_run:
        # Simulate: import not found, gnome-screenshot not found, scrot found
        def side_effect(*names):
            if set(names) == {"import", "gnome-screenshot"}:
                from pi_remote_mcp.utils.command_runner import CommandUnavailableError
                raise CommandUnavailableError("not found")
            if "scrot" in names:
                return "/usr/bin/scrot"
            from pi_remote_mcp.utils.command_runner import CommandUnavailableError
            raise CommandUnavailableError("not found")
        mock_req.side_effect = side_effect
        mock_run.return_value = type("R", (), {"stdout": "", "stderr": "", "exit_code": 0, "ok": True, "command": []})()
        result = x11_snapshot()
    assert result["backend"] == "x11"
    assert "path" in result
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd /home/pi/pi-control-mcp && .venv/bin/pytest tests/test_backend.py -v
```

Expected: `test_x11_snapshot_uses_scrot_when_import_missing` FAILS (function doesn't try scrot).

- [ ] **Step 3: Fix `x11_backend.snapshot()`**

Replace the `snapshot` function in `src/pi_remote_mcp/desktop/backends/x11_backend.py`:

```python
def snapshot() -> dict:
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(suffix=".png", delete=False) as handle:
        temp_path = Path(handle.name)

    # Try import (ImageMagick), gnome-screenshot, then scrot
    try:
        binary = require_command("import", "gnome-screenshot")
        if Path(binary).name == "import":
            run_command([binary, "-window", "root", str(temp_path)])
        else:
            run_command([binary, "-f", str(temp_path)])
        return {"backend": "x11", "action": "snapshot", "path": str(temp_path), "exists": temp_path.exists()}
    except (CommandUnavailableError, CommandExecutionError):
        pass

    try:
        scrot_bin = require_command("scrot")
        run_command([scrot_bin, str(temp_path)])
        return {"backend": "x11", "action": "snapshot", "path": str(temp_path), "exists": temp_path.exists()}
    except (CommandUnavailableError, CommandExecutionError) as exc:
        return {"backend": "x11", "action": "snapshot", "error": str(exc), "path": ""}
```

Also add `CommandExecutionError` to the import line at the top of `x11_backend.py`:

```python
from pi_remote_mcp.utils.command_runner import CommandExecutionError, CommandUnavailableError, require_command, run_command
```

- [ ] **Step 4: Run tests**

```bash
cd /home/pi/pi-control-mcp && .venv/bin/pytest tests/test_backend.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/pi/pi-control-mcp && git add src/pi_remote_mcp/desktop/backends/x11_backend.py tests/test_backend.py
git commit -m "fix: add scrot fallback to x11 snapshot"
```

---

## Task 3: Fix port_check error handling

`network_tools.port_check()` raises `ConnectionRefusedError` / `OSError` unhandled when the port is closed.

**Files:**
- Modify: `src/pi_remote_mcp/tools/network_tools.py`
- Test: `tests/test_network_tools.py`

- [ ] **Step 1: Write a failing test**

Replace the contents of `tests/test_network_tools.py`:

```python
from pi_remote_mcp.tools.network_tools import ping, port_check


def test_ping_returns_tool_key() -> None:
    result = ping("127.0.0.1", count=1)
    assert result["tool"] == "Ping"


def test_port_check_closed_port_returns_error_dict() -> None:
    """port_check on a closed port must return a dict, never raise."""
    result = port_check("127.0.0.1", 19999, timeout=0.5)
    assert result["tool"] == "PortCheck"
    assert result["open"] is False
    assert "error" in result


def test_port_check_open_port_returns_open_true() -> None:
    """port_check on an open port (SSH :22) must return open=True."""
    result = port_check("127.0.0.1", 22, timeout=2.0)
    assert result["tool"] == "PortCheck"
    assert result["open"] is True
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd /home/pi/pi-control-mcp && .venv/bin/pytest tests/test_network_tools.py -v
```

Expected: `test_port_check_closed_port_returns_error_dict` FAILS with an unhandled exception.

- [ ] **Step 3: Fix `port_check`**

Replace the `port_check` function in `src/pi_remote_mcp/tools/network_tools.py`:

```python
def port_check(host: str, port: int, timeout: float = 5.0) -> dict:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
        return {"tool": "PortCheck", "host": host, "port": port, "open": True, "timeout": timeout}
    except OSError as exc:
        return {"tool": "PortCheck", "host": host, "port": port, "open": False, "timeout": timeout, "error": str(exc)}
```

- [ ] **Step 4: Run tests**

```bash
cd /home/pi/pi-control-mcp && .venv/bin/pytest tests/test_network_tools.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/pi/pi-control-mcp && git add src/pi_remote_mcp/tools/network_tools.py tests/test_network_tools.py
git commit -m "fix: handle closed-port OSError in port_check"
```

---

## Task 4: Implement task_create and task_delete via cron

`task_create` and `task_delete` are stubs that return notes. Implement them using the user's crontab.

**Files:**
- Modify: `src/pi_remote_mcp/tools/system_tools.py`
- Test: `tests/test_system_tools.py` (create new)

- [ ] **Step 1: Write failing tests**

Create `tests/test_system_tools.py`:

```python
from unittest.mock import patch
from pi_remote_mcp.tools.system_tools import task_create, task_delete


def test_task_create_adds_cron_line() -> None:
    """task_create should write a cron entry and return success."""
    with patch("pi_remote_mcp.tools.system_tools._crontab_lines", return_value=[]) as _mock_read, \
         patch("pi_remote_mcp.tools.system_tools._write_crontab") as mock_write:
        result = task_create("test-job", "/usr/bin/echo hello", "*/5 * * * *")
    assert result["tool"] == "TaskCreate"
    assert result.get("error") is None
    mock_write.assert_called_once()
    written = mock_write.call_args[0][0]
    assert any("test-job" in line for line in written)
    assert any("/usr/bin/echo hello" in line for line in written)


def test_task_delete_removes_cron_line() -> None:
    """task_delete should remove the named cron entry."""
    existing = ["*/5 * * * * /usr/bin/echo hello  # pi-mcp:test-job\n"]
    with patch("pi_remote_mcp.tools.system_tools._crontab_lines", return_value=existing), \
         patch("pi_remote_mcp.tools.system_tools._write_crontab") as mock_write:
        result = task_delete("test-job")
    assert result["tool"] == "TaskDelete"
    written = mock_write.call_args[0][0]
    assert not any("test-job" in line for line in written)


def test_task_delete_missing_returns_not_found() -> None:
    with patch("pi_remote_mcp.tools.system_tools._crontab_lines", return_value=[]), \
         patch("pi_remote_mcp.tools.system_tools._write_crontab"):
        result = task_delete("no-such-job")
    assert result["tool"] == "TaskDelete"
    assert result.get("found") is False
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd /home/pi/pi-control-mcp && .venv/bin/pytest tests/test_system_tools.py -v
```

Expected: all 3 tests FAIL (missing `_crontab_lines` and `_write_crontab` helpers).

- [ ] **Step 3: Implement cron helpers and replace stubs**

In `src/pi_remote_mcp/tools/system_tools.py`, add helper functions after the imports block and replace `task_create` / `task_delete`:

```python
# ---- cron helpers -------------------------------------------------------

def _crontab_lines() -> list[str]:
    """Return current crontab lines for the running user, or [] if none."""
    completed = subprocess.run(
        ["crontab", "-l"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return completed.stdout.splitlines(keepends=True)


def _write_crontab(lines: list[str]) -> None:
    """Write lines back as the current user's crontab."""
    content = "".join(lines)
    subprocess.run(
        ["crontab", "-"],
        input=content,
        text=True,
        check=True,
    )


_CRON_TAG_PREFIX = "# pi-mcp:"


def task_create(name: str, command: str, schedule: str) -> dict:
    """Add a cron job tagged with name.  schedule is a standard cron expression."""
    tag = f"{_CRON_TAG_PREFIX}{name}"
    lines = _crontab_lines()
    # Remove any existing entry with the same name first
    lines = [line for line in lines if tag not in line]
    lines.append(f"{schedule} {command}  {tag}\n")
    try:
        _write_crontab(lines)
        return {"tool": "TaskCreate", "name": name, "schedule": schedule, "command": command}
    except subprocess.CalledProcessError as exc:
        return {"tool": "TaskCreate", "name": name, "error": str(exc)}


def task_delete(name: str) -> dict:
    """Remove a cron job previously created by task_create."""
    tag = f"{_CRON_TAG_PREFIX}{name}"
    lines = _crontab_lines()
    new_lines = [line for line in lines if tag not in line]
    if len(new_lines) == len(lines):
        return {"tool": "TaskDelete", "name": name, "found": False}
    try:
        _write_crontab(new_lines)
        return {"tool": "TaskDelete", "name": name, "found": True}
    except subprocess.CalledProcessError as exc:
        return {"tool": "TaskDelete", "name": name, "found": True, "error": str(exc)}
```

- [ ] **Step 4: Run tests**

```bash
cd /home/pi/pi-control-mcp && .venv/bin/pytest tests/test_system_tools.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Run full test suite**

```bash
cd /home/pi/pi-control-mcp && .venv/bin/pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/pi/pi-control-mcp && git add src/pi_remote_mcp/tools/system_tools.py tests/test_system_tools.py
git commit -m "feat: implement task_create/task_delete via cron"
```

---

## Task 5: Create pi-control.toml

Creates the production config for the HTTP daemon.

**Files:**
- Create: `/home/pi/pi-control-mcp/pi-control.toml`

- [ ] **Step 1: Create config**

```bash
cat > /home/pi/pi-control-mcp/pi-control.toml << 'EOF'
[server]
host = "0.0.0.0"
port = 8090
auth_key = ""
transport = "streamable-http"

[security]
enable_tier3 = true
disable_tier2 = false
ip_allowlist = ["0.0.0.0/0"]

[tools]
enable = []
exclude = []
EOF
```

- [ ] **Step 2: Verify the server starts**

```bash
cd /home/pi/pi-control-mcp && DISPLAY=:0 XAUTHORITY=/home/pi/.Xauthority .venv/bin/pi-control-mcp run --config /home/pi/pi-control-mcp/pi-control.toml &
sleep 3 && curl -s -o /dev/null -w "%{http_code}" http://localhost:8090/mcp && echo ""
kill %1 2>/dev/null
```

Expected: HTTP 200 (or 404/405 — any response means the server is up).

- [ ] **Step 3: Commit**

```bash
cd /home/pi/pi-control-mcp && git add pi-control.toml
git commit -m "chore: add production pi-control.toml for HTTP transport"
```

---

## Task 6: Create systemd service

**Files:**
- Create: `/etc/systemd/system/pi-control-mcp.service`

- [ ] **Step 1: Write service file**

```bash
sudo tee /etc/systemd/system/pi-control-mcp.service > /dev/null << 'EOF'
[Unit]
Description=Pi Control MCP Server
After=network.target graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/pi-control-mcp
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
Environment=XDG_SESSION_TYPE=x11
ExecStart=/home/pi/pi-control-mcp/.venv/bin/pi-control-mcp run --config /home/pi/pi-control-mcp/pi-control.toml
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

- [ ] **Step 2: Enable and start**

```bash
sudo systemctl daemon-reload
sudo systemctl enable pi-control-mcp
sudo systemctl start pi-control-mcp
```

- [ ] **Step 3: Verify running**

```bash
sudo systemctl status pi-control-mcp --no-pager
sleep 3 && curl -s -o /dev/null -w "%{http_code}" http://localhost:8090/mcp && echo ""
```

Expected: service shows `active (running)`, curl returns non-error HTTP code.

---

## Task 7: Fix VS Code Insiders mcp.json

The existing config sets Wayland env vars but the session is X11. Fix to use the correct env.

**Files:**
- Modify: `/home/pi/.config/Code - Insiders/User/mcp.json`

- [ ] **Step 1: Write correct mcp.json**

```bash
cat > "/home/pi/.config/Code - Insiders/User/mcp.json" << 'EOF'
{
  "servers": {
    "pi-control": {
      "type": "stdio",
      "command": "/usr/bin/env",
      "args": [
        "DISPLAY=:0",
        "XAUTHORITY=/home/pi/.Xauthority",
        "XDG_RUNTIME_DIR=/run/user/1000",
        "XDG_SESSION_TYPE=x11",
        "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus",
        "/home/pi/pi-control-mcp/.venv/bin/pi-control-mcp",
        "run",
        "--enable-tier3"
      ]
    }
  },
  "inputs": []
}
EOF
```

- [ ] **Step 2: Verify JSON is valid**

```bash
python3 -c "import json; json.load(open('/home/pi/.config/Code - Insiders/User/mcp.json')); print('JSON valid')"
```

Expected: `JSON valid`

---

## Task 8: Create Copilot CLI mcp.json

**Files:**
- Create: `/home/pi/.config/github-copilot/mcp.json`

- [ ] **Step 1: Create config**

```bash
mkdir -p /home/pi/.config/github-copilot
cat > /home/pi/.config/github-copilot/mcp.json << 'EOF'
{
  "servers": {
    "pi-control": {
      "type": "stdio",
      "command": "/usr/bin/env",
      "args": [
        "DISPLAY=:0",
        "XAUTHORITY=/home/pi/.Xauthority",
        "XDG_RUNTIME_DIR=/run/user/1000",
        "XDG_SESSION_TYPE=x11",
        "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus",
        "/home/pi/pi-control-mcp/.venv/bin/pi-control-mcp",
        "run",
        "--enable-tier3"
      ]
    }
  }
}
EOF
```

- [ ] **Step 2: Verify JSON**

```bash
python3 -c "import json; json.load(open('/home/pi/.config/github-copilot/mcp.json')); print('JSON valid')"
```

Expected: `JSON valid`

---

## Task 9: Configure Open WebUI MCP tool

Open WebUI connects to MCP servers via its Admin Panel HTTP tool configuration.

- [ ] **Step 1: Confirm HTTP service is reachable**

```bash
curl -s http://localhost:8090/mcp -o /dev/null -w "HTTP %{http_code}\n"
```

Expected: HTTP 200 or 405 (service is up and responding).

- [ ] **Step 2: Configure in Open WebUI Admin Panel**

In a browser, go to `http://<pi-ip>:8080` → log in as admin → **Admin Panel** → **Settings** → **Tools**.

Add a new tool server with URL:
```
http://localhost:8090/mcp
```

Leave auth blank (no bearer token configured).

Click Save / Test connection.

- [ ] **Step 3: Verify tools appear**

In Open WebUI, start a new chat. Click the **Tools** icon (wrench) and confirm Pi Control tools appear in the list (e.g., `GetSystemInfo`, `FileList`, `Snapshot`).

---

## Task 10: Full regression test

- [ ] **Step 1: Run full test suite**

```bash
cd /home/pi/pi-control-mcp && .venv/bin/pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 2: Verify service survives reboot** *(optional, skip if rebooting is disruptive)*

```bash
sudo systemctl is-enabled pi-control-mcp
```

Expected: `enabled`
