# Architecture

## Layers

1. **Transport layer**: stdio and streamable HTTP
2. **Security layer**: auth, policy and tier gating
3. **Tool layer**:
   - Desktop/UI tools
   - File/system/network tools
   - Session helpers
   - Pi Memory tools (SQLite-backed local memory)
   - Mower diagnostics/reporting tools
4. **Backend layer**: Wayland/X11 desktop capability abstraction

## Runtime entrypoints

- Package script: `pi-control-mcp = pi_remote_mcp.cli:main`
- Main command: `pi-control-mcp run`
- Server factory: `pi_remote_mcp.server.create_server`

## Configuration loading

Config is merged from the first existing path:

1. `./pi-control.toml`
2. `~/.config/pi-control-mcp/pi-control.toml`

`PI_CONTROL_AUTH_KEY` overrides `server.auth_key`.

## Policy resolution

Effective tools are resolved by:

1. Explicit include list (`tools.enable`) if present
2. Otherwise default tier set (Tier 1 + Tier 2, optional Tier 3)
3. Exclude list (`tools.exclude`)
4. Intersect with known registered tools
