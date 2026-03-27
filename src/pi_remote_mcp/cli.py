from __future__ import annotations

from typing import Optional

import typer

from pi_remote_mcp.config import load_config
from pi_remote_mcp.server import create_server

app = typer.Typer(help="Pi Control MCP server for Raspberry Pi OS Trixie")


@app.command()
def run(
    config: Optional[str] = typer.Option(None, help="Path to pi-control.toml"),
    host: Optional[str] = typer.Option(None, help="Bind host"),
    port: Optional[int] = typer.Option(None, help="Bind port"),
    transport: Optional[str] = typer.Option(None, help="stdio|streamable-http"),
    auth_key: Optional[str] = typer.Option(None, help="Bearer auth key"),
    enable_tier3: bool = typer.Option(False, help="Enable high-risk Tier 3 tools"),
    disable_tier2: bool = typer.Option(False, help="Disable interactive Tier 2 tools"),
    tools: Optional[str] = typer.Option(None, help="Comma-separated tool include list"),
    exclude_tools: Optional[str] = typer.Option(None, help="Comma-separated tool exclude list"),
) -> None:
    cfg = load_config(config)

    if host is not None:
        cfg.server.host = host
    if port is not None:
        cfg.server.port = port
    if transport is not None:
        cfg.server.transport = transport  # type: ignore[assignment]
    if auth_key is not None:
        cfg.server.auth_key = auth_key

    if enable_tier3:
        cfg.security.enable_tier3 = True
    if disable_tier2:
        cfg.security.disable_tier2 = True

    if tools:
        cfg.tools.enable = [t.strip() for t in tools.split(",") if t.strip()]
    if exclude_tools:
        cfg.tools.exclude = [t.strip() for t in exclude_tools.split(",") if t.strip()]

    server, enabled_tools = create_server(cfg)

    typer.echo(
        f"Pi Control MCP starting | transport={cfg.server.transport} | host={cfg.server.host}:{cfg.server.port}"
    )
    typer.echo(f"Enabled tools ({len(enabled_tools)}): {', '.join(sorted(enabled_tools))}")

    if cfg.server.transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(transport="streamable-http", host=cfg.server.host, port=cfg.server.port)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
