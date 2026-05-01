# Pi Memory

Pi Memory adds local SQLite-backed durable memory for Pi Control MCP agents.

- Default DB: `~/.local/share/pi-control-mcp/memory/pi_memory.sqlite3`
- Override: `PI_CONTROL_MEMORY_DB=/custom/path/pi_memory.sqlite3`

## Privacy and redaction

Pi Memory redacts likely secrets (tokens, API keys, private keys, PASSWORD/TOKEN/SECRET style variables) before storage and before return.

## Tools

- `MemoryRecent`
- `MemorySearch`
- `MemoryShow`
- `MemoryFiles`
- `MemoryErrors`
- `MemoryNoteAdd`
- `MemoryHealth`
- `MemorySchemaCheck`

## Headless mower diagnostics tools

- `ServiceHealthReport`
- `JournalSearch`
- `MowerRuntimeSnapshot`
- `HardwareProbe`
- `NetworkFailoverStatus`
- `GitProjectState`

## Suggested workflow

1. `MemoryRecent`
2. `MowerRuntimeSnapshot`
3. `MemorySearch`
4. `ServiceHealthReport`
5. Then proceed to shell/file changes.
