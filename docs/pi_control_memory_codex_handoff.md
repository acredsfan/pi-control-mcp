# Codex Implementation Handoff: Pi Control MCP Memory + Headless Mower Diagnostics

## Copy/paste prompt for Codex

You are working in this repository:

```text
https://github.com/acredsfan/pi-control-mcp
```

Implement a local "Pi Memory" feature inspired by Auto Memory, but adapted for Pi Control MCP and headless Raspberry Pi workflows.

The goal is to give coding agents durable local recall of prior Pi Control MCP activity, errors, service logs, file changes, shell results, and explicit agent notes. This should help agents avoid repeating mistakes, rediscovering the same facts, or blindly debugging the mower project from scratch.

Use the existing architecture:
- FastMCP tool registration in `src/pi_remote_mcp/server.py`
- Tiered safety policy in `src/pi_remote_mcp/security/policy.py`
- Existing tool modules under `src/pi_remote_mcp/tools/`
- Existing command runner patterns where possible
- Python 3.11+
- No admin/root-only requirements unless a command naturally needs sudo and is only reported, not forced

Build this in phases.

### Phase 1 — Local memory store

Add a new package:

```text
src/pi_remote_mcp/memory/
  __init__.py
  db.py
  models.py
  redact.py
  service.py
  summarize.py
```

Use only Python stdlib for the core database layer:
- `sqlite3`
- `json`
- `datetime`
- `pathlib`
- `uuid`
- `re`
- `os`

Store the DB here by default:

```text
~/.local/share/pi-control-mcp/memory/pi_memory.sqlite3
```

Allow overriding with environment variable:

```text
PI_CONTROL_MEMORY_DB=/custom/path/pi_memory.sqlite3
```

Create these tables:

```sql
CREATE TABLE IF NOT EXISTS memory_items (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    source_type TEXT NOT NULL,
    project TEXT,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    body TEXT NOT NULL,
    tags_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    importance INTEGER NOT NULL DEFAULT 1,
    redacted INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_memory_created_at
ON memory_items(created_at);

CREATE INDEX IF NOT EXISTS idx_memory_source_type
ON memory_items(source_type);

CREATE INDEX IF NOT EXISTS idx_memory_project
ON memory_items(project);
```

Try to create an FTS5 table, but gracefully fall back to LIKE search if FTS5 is unavailable:

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
    title,
    summary,
    body,
    tags,
    content='memory_items',
    content_rowid='rowid'
);
```

Do not fail startup if FTS5 is unavailable. Return FTS availability from `MemoryHealth`.

### Phase 2 — Redaction

Add redaction before storage and before returning results.

Redact at least:
- GitHub PATs: `ghp_...`, `github_pat_...`
- OpenAI-style keys: `sk-...`
- Bearer tokens
- Cloudflare tokens
- AWS-style access keys
- NTRIP passwords if visible in `.env`-like text
- generic `PASSWORD=...`, `TOKEN=...`, `SECRET=...`, `API_KEY=...`
- private keys blocks
- email addresses may be left alone for now unless easy to redact

Use replacement strings like:

```text
[REDACTED_TOKEN]
[REDACTED_SECRET]
[REDACTED_PRIVATE_KEY]
```

Keep redaction conservative and transparent. Return `redacted: true` if anything was changed.

### Phase 3 — MCP memory tools

Add:

```text
src/pi_remote_mcp/tools/memory_tools.py
```

Implement these MCP-callable functions returning JSON-serializable dicts:

```python
def memory_recent(
    limit: int = 20,
    project: str | None = None,
    include_body: bool = False,
) -> dict: ...

def memory_search(
    query: str,
    project: str | None = None,
    source_types: list[str] | None = None,
    limit: int = 20,
) -> dict: ...

def memory_show(memory_id: str) -> dict: ...

def memory_files(
    project: str | None = None,
    limit: int = 50,
) -> dict: ...

def memory_errors(
    project: str | None = None,
    limit: int = 20,
) -> dict: ...

def memory_note_add(
    note: str,
    tags: list[str] | None = None,
    project: str | None = None,
    importance: int = 2,
) -> dict: ...

def memory_health() -> dict: ...

def memory_schema_check() -> dict: ...
```

Tool behavior:
- `MemoryRecent`: newest memory items, concise by default
- `MemorySearch`: FTS search when available, LIKE fallback
- `MemoryShow`: full body for a single ID
- `MemoryFiles`: items tagged/source-typed as file activity
- `MemoryErrors`: source types or tags related to errors, failed commands, exceptions, service failures
- `MemoryNoteAdd`: explicit agent/human note
- `MemoryHealth`: db path, item count, FTS available, schema version, last item date
- `MemorySchemaCheck`: validates required tables/indexes and returns repair suggestions

### Phase 4 — Register tools

Update `src/pi_remote_mcp/server.py`:
- import memory tool functions
- register them with FastMCP using names:
  - `MemoryRecent`
  - `MemorySearch`
  - `MemoryShow`
  - `MemoryFiles`
  - `MemoryErrors`
  - `MemoryNoteAdd`
  - `MemoryHealth`
  - `MemorySchemaCheck`

Update `src/pi_remote_mcp/security/policy.py`:
- Add these read-only tools to `TIER_1_TOOLS`:
  - `MemoryRecent`
  - `MemorySearch`
  - `MemoryShow`
  - `MemoryFiles`
  - `MemoryErrors`
  - `MemoryHealth`
  - `MemorySchemaCheck`
- Add `MemoryNoteAdd` to `TIER_2_TOOLS`, because it writes a local note.

### Phase 5 — Passive ingestion helper

Add a clean helper that other tools can call later:

```python
def record_memory(
    source_type: str,
    title: str,
    summary: str,
    body: str,
    project: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    importance: int = 1,
) -> dict:
    ...
```

Do not try to wrap every existing tool in this first pass unless it is easy and safe. The main deliverable is the memory tool surface and database.

However, add lightweight ingestion for:
- `MemoryNoteAdd`
- future use by system/mower diagnostic tools
- optionally failed shell commands if this can be done without destabilizing existing shell behavior

### Phase 6 — Headless mower diagnostics tools

Add:

```text
src/pi_remote_mcp/tools/mower_tools.py
```

Implement these MCP tools. They should be safe/read-only and work well on headless Raspberry Pi OS Lite.

```python
def service_health_report(
    services: list[str] | None = None,
    include_journal: bool = True,
    journal_lines: int = 80,
) -> dict: ...

def journal_search(
    unit: str | None = None,
    query: str | None = None,
    since: str = "1 hour ago",
    limit: int = 200,
) -> dict: ...

def mower_runtime_snapshot(
    api_url: str = "http://127.0.0.1:8081",
    frontend_url: str = "http://127.0.0.1:3000",
    include_services: bool = True,
    include_ports: bool = True,
    include_api_health: bool = True,
    include_recent_errors: bool = True,
) -> dict: ...

def hardware_probe(
    include_i2c: bool = True,
    include_uart: bool = True,
    include_usb: bool = True,
    include_gpio: bool = False,
) -> dict: ...

def network_failover_status() -> dict: ...

def git_project_state(
    root: str,
    include_recent_commits: bool = True,
    include_status: bool = True,
    include_untracked: bool = True,
) -> dict: ...
```

Recommended default services for mower diagnostics:

```python
DEFAULT_MOWER_SERVICES = [
    "lawnberry-backend",
    "lawnberry-frontend",
    "nginx",
    "NetworkManager",
    "cloudflared",
]
```

The tools should:
- never require sudo
- use `systemctl --user` only if appropriate, otherwise regular `systemctl` read-only status commands
- use `journalctl` read-only queries
- return clear errors when a command is unavailable
- never crash because a tool like `i2cdetect`, `lsusb`, `gpioinfo`, or `iw` is missing
- record useful summaries to memory via `record_memory(...)`

Register mower tools in `server.py` with names:
- `ServiceHealthReport`
- `JournalSearch`
- `MowerRuntimeSnapshot`
- `HardwareProbe`
- `NetworkFailoverStatus`
- `GitProjectState`

Add these to `TIER_1_TOOLS`.

### Phase 7 — Tests

Add unit tests for:
- database initialization
- insert/search/show/recent
- redaction
- FTS fallback behavior if possible
- `MemoryNoteAdd`
- `MemoryHealth`
- `MemorySchemaCheck`
- mower tools with mocked command runner responses

Prefer pytest and monkeypatch. Do not require actual Raspberry Pi hardware in tests.

### Phase 8 — Docs

Add:

```text
docs/pi-memory.md
```

Include:
- what Pi Memory is
- storage location
- privacy/redaction warning
- example MCP calls
- suggested agent workflow:
  1. `MemoryRecent`
  2. `MowerRuntimeSnapshot`
  3. `MemorySearch`
  4. `ServiceHealthReport`
  5. only then run shell/file changes

Update `README.md` with a short mention of Pi Memory and mower diagnostics.

## Important constraints

- Keep code PEP8-friendly.
- Do not add heavy dependencies for the first pass.
- Do not require a desktop session.
- Do not assume Wayland/X11 exists.
- Do not require root/admin.
- Do not store raw secrets.
- Do not invent APIs in the LawnBerry project. Use HTTP checks only when safe and generic.
- Keep every tool return value JSON-serializable.
- Use existing command runner helpers where possible.
- If a command is unavailable, return `{ "available": false, "error": "..." }` instead of failing.

## Definition of done

The implementation is complete when:

1. `pi-control-mcp run --tools MemoryRecent,MemorySearch,MemoryNoteAdd,MemoryHealth` starts successfully.
2. `MemoryNoteAdd` writes a note into SQLite.
3. `MemoryRecent` returns the note.
4. `MemorySearch` finds the note.
5. `MemoryHealth` reports DB path, item count, and FTS status.
6. `ServiceHealthReport` can run on a normal Linux/Pi system without crashing.
7. `MowerRuntimeSnapshot` returns useful status even when LawnBerry services are not installed.
8. Tests pass.
9. Docs explain how an agent should use memory before debugging.

---

## Implementation notes and design detail

### Why this is not a direct Auto Memory clone

Auto Memory reads another tool's local session database. Pi Control MCP should instead own its memory. That is better for Raspberry Pi use because the valuable context is not only chat history. It is:

- MCP tool calls
- command output
- systemd state
- journalctl logs
- file changes
- service failures
- hardware probe results
- explicit agent notes
- mower runtime snapshots

### Suggested source layout

```text
src/pi_remote_mcp/
  memory/
    __init__.py
    db.py
    models.py
    redact.py
    service.py
    summarize.py

  tools/
    memory_tools.py
    mower_tools.py
```

### Suggested memory item source types

Use consistent `source_type` values:

```text
note
tool_call
shell
file
service
journal
hardware
network
git
mower_snapshot
error
```

### Suggested tags

Examples:

```text
agent-note
mower
lawnberry
service-health
journal
hardware
network
git
error
file-change
```

### Example memory result shape

```json
{
  "id": "mem_20260501_abcdef",
  "created_at": "2026-05-01T15:00:00Z",
  "source_type": "note",
  "project": "lawnberry_pi",
  "title": "Agent note",
  "summary": "Backend telemetry broke after changing WebSocket startup.",
  "tags": ["agent-note", "backend", "telemetry"],
  "importance": 2,
  "redacted": false
}
```

### Example `MemoryHealth` output

```json
{
  "tool": "MemoryHealth",
  "ok": true,
  "db_path": "/home/pi/.local/share/pi-control-mcp/memory/pi_memory.sqlite3",
  "item_count": 42,
  "fts_available": true,
  "schema_version": 1,
  "latest_item_at": "2026-05-01T15:00:00Z"
}
```

### Example agent workflow for LawnBerry debugging

When debugging the headless mower, the agent should do this first:

```text
1. Call MemoryRecent(project="lawnberry_pi")
2. Call MowerRuntimeSnapshot()
3. Call MemorySearch(query="<current problem>", project="lawnberry_pi")
4. Call ServiceHealthReport()
5. Call JournalSearch(unit="lawnberry-backend", query="error")
6. Only then edit files or run commands
```

### Mower runtime assumptions

The LawnBerry project commonly uses:
- backend on `8081`
- frontend on `3000`
- preview/E2E on `4173`

The diagnostic tools should check `8081` and `3000` by default, but parameters should allow overrides.

### Safety posture

Memory and diagnostics should be safe by default:
- read-only except `MemoryNoteAdd`
- no destructive commands
- no service restarts
- no file writes outside the memory DB
- no secret leakage
- no sudo requirement

### Follow-up enhancements after MVP

Do not implement these in the first pass unless everything above is already clean:

- automatic wrapping of every tool call
- embeddings/vector search
- cloud sync
- browser/UI screenshot analysis
- live WebSocket telemetry sampling
- direct LawnBerry API schema integration
- memory export/import
- memory pruning/retention policy
- per-project memory namespaces configured in TOML
