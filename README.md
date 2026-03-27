# Pi Control MCP

A Raspberry Pi OS (Debian Trixie) MCP server for remote desktop automation, file operations, and system control with **tiered safety controls**.

This project is inspired by the design goals of `winremote-mcp`, adapted for Linux desktop stacks and Raspberry Pi workflows.

## Highlights

- MCP server powered by **FastMCP**
- Targets **Wayland + X11** with graceful fallback
- Implements the full `winremote-mcp` style tool surface with Linux/Raspberry Pi semantics
- Tiered security model:
  - **Tier 1**: read-only/low-risk
  - **Tier 2**: interactive UI controls
  - **Tier 3**: destructive/high-risk actions
- Explicit tool inclusion/exclusion for fine-grained comfort control
- Supports **stdio** and **HTTP** transport setup patterns
- OAuth support scaffold included for v1 security roadmap
- Adds Pi-native extras such as `ListWindows`, `GetActiveWindow`, `WindowProperties`, `ListWorkspaces`, `SwitchWorkspace`, `ListMonitors`, `ProbeCapabilities`, `DetectDialog`, `WatchClipboard`, `WatchWindow`, and `GetSessionState`

## Installation

```bash
pip install -e .
```

Optional extras:

```bash
pip install -e .[ocr,test]
```

## Quickstart

```bash
pi-control-mcp run
```

Default behavior:
- Tier 1 + Tier 2 enabled
- Tier 3 disabled
- Local-only safety defaults unless overridden

## Tier and tool controls

```bash
# Enable Tier 3 tools
pi-control-mcp run --enable-tier3

# Disable Tier 2 tools (Tier 1 only)
pi-control-mcp run --disable-tier2

# Include only specific tools
pi-control-mcp run --tools Snapshot,FileList,GetSystemInfo

# Exclude specific tools from resolved set
pi-control-mcp run --exclude-tools Shell,FileWrite
```

Precedence: **explicit tools > tier flags > defaults**.

## Configuration

Create `pi-control.toml`:

```toml
[server]
host = "127.0.0.1"
port = 8090
auth_key = ""
transport = "stdio"

[security]
enable_tier3 = false
disable_tier2 = false
ip_allowlist = ["127.0.0.1/32"]
oauth_client_id = ""
oauth_client_secret = ""

[tools]
enable = []
exclude = []
```

## Raspberry Pi dependencies

For practical automation on Trixie, you may need:
- `grim` / `slurp` / compositor-compatible screenshot path for Wayland
- `ydotool` (Wayland input injection)
- `xdotool` and `xwd`/`import` for X11 workflows
- `tesseract-ocr` for OCR
- `wmctrl`, `xclip` / `xsel`, `notify-send`, `systemctl`, `journalctl`, `loginctl`, `xrandr`, `wlr-randr`, `swaymsg`

## Tool categories

### Desktop and semantic UI

- `Snapshot`, `ObserveScreen`, `AnnotatedSnapshot`
- `OCR`, `ScreenRecord`
- `UIMap`, `UIMapJson`, `UIFind`, `UIClick`, `UIAct`, `UISequence`, `UIWatch`
- `Click`, `Type`, `Scroll`, `Move`, `Shortcut`, `Wait`
- `FocusWindow`, `MinimizeAll`, `App`

### File, system, and network

- `FileRead`, `FileWrite`, `FileList`, `FileSearch`, `FileDownload`, `FileUpload`
- `GetClipboard`, `SetClipboard`, `ListProcesses`, `KillProcess`, `GetSystemInfo`, `Notification`, `LockScreen`
- `ServiceList`, `ServiceStart`, `ServiceStop`, `TaskList`, `TaskCreate`, `TaskDelete`, `EventLog`
- `RegRead`, `RegWrite`
- `Ping`, `PortCheck`, `NetConnections`, `Scrape`

### Pi-native session helpers

- `ListWindows`, `GetActiveWindow`, `WindowProperties`
- `ListWorkspaces`, `SwitchWorkspace`, `ListMonitors`
- `GetBackendInfo`, `ProbeCapabilities`, `GetSessionState`
- `DetectDialog`, `WatchClipboard`, `WatchWindow`
- `ReconnectSession`, `GetTaskStatus`, `GetRunningTasks`, `CancelTask`

## Linux mappings for Windows-oriented names

- `Service*` tools use `systemctl`
- `Task*` tools are exposed with Linux-friendly semantics and can be mapped to systemd timers / cron workflows
- `EventLog` reads from `journalctl`
- `RegRead` / `RegWrite` map to desktop settings via `gsettings` when available

## Security

See [`SECURITY.md`](SECURITY.md) for deployment guidance and risk mitigations.
