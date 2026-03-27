# Usage

## Run in stdio mode

`pi-control-mcp run`

## Run in HTTP mode

`pi-control-mcp run --transport streamable-http --host 0.0.0.0 --port 8090`

## Safety tiers

- Default: Tier 1 + Tier 2
- Tier 3: disabled by default

Enable Tier 3:

`pi-control-mcp run --enable-tier3`

Disable Tier 2:

`pi-control-mcp run --disable-tier2`

## Explicit comfort controls

Allow only selected tools:

`pi-control-mcp run --tools Snapshot,FileList,GetSystemInfo`

Remove sensitive tools from resolved set:

`pi-control-mcp run --exclude-tools Shell,FileWrite,FileRead`
