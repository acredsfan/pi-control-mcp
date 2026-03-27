# Security Guide

`pi-control-mcp` exposes powerful desktop and system automation capabilities. Use least privilege and enable only the tools you need.

## Risk Tiers

### Tier 1 (Read-only, low risk) — default enabled
Examples: `Snapshot`, `ObserveScreen`, `AnnotatedSnapshot`, `UIMap`, `UIFind`, `UIWatch`, `OCR`, `ScreenRecord`, `FileList`, `FileSearch`, `GetSystemInfo`, `ListProcesses`, `ServiceList`, `TaskList`, `EventLog`, `Ping`, `PortCheck`, `NetConnections`, `GetClipboard`.

### Tier 2 (Interactive, medium risk) — default enabled
Examples: `Click`, `Type`, `Scroll`, `Move`, `Shortcut`, `FocusWindow`, `MinimizeAll`, `App`, `UIClick`, `UIAct`, `UISequence`, `Scrape`, `ReconnectSession`, `SwitchWorkspace`.

### Tier 3 (Destructive, high risk) — default disabled
Examples: `Shell`, `FileRead`, `FileWrite`, `FileUpload`, `FileDownload`, `KillProcess`, `ServiceStart`, `ServiceStop`, `TaskCreate`, `TaskDelete`, `SetClipboard`, `LockScreen`, `RegWrite`.

## Controls

- `--enable-tier3`
- `--disable-tier2`
- `--tools ...`
- `--exclude-tools ...`

Resolution order: explicit include list > tier flags > defaults, then apply excludes.

## Deployment profiles

### Safe (recommended baseline)
- Bind localhost only
- Tier 3 disabled
- Restrictive tool set

### Dev
- Localhost + optional auth
- Tier 1+2 enabled
- Tier 3 disabled

### Power
- Auth required
- Optional remote bind + IP allowlist
- Tier 3 selectively enabled

## Authentication

- Bearer token supported via `auth_key`
- OAuth fields are available for managed client flows (`oauth_client_id`, `oauth_client_secret`)

## Linux semantics and compatibility notes

- Some tool names are intentionally kept compatible with `winremote-mcp` even though they map to Linux/Raspberry Pi equivalents.
- `Service*` tools operate on `systemd` services.
- `Task*` tools currently expose Linux-friendly task management semantics rather than Windows scheduled tasks.
- `EventLog` reads from `journalctl` when available.
- `RegRead` and `RegWrite` use `gsettings` / desktop settings namespaces when supported.
- Advanced UI tools prefer accessibility/window metadata and fall back to screenshot/OCR-based heuristics when richer platform data is not available.

## Hardening checklist

- Use strong auth token (32+ chars)
- Restrict network exposure
- Configure firewall/VPN if remote
- Keep Tier 3 disabled unless required
- Audit logs for high-risk actions
