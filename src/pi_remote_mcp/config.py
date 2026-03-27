from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
import os
import tomllib


Transport = Literal["stdio", "streamable-http"]


@dataclass(slots=True)
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8090
    auth_key: str = ""
    transport: Transport = "stdio"


@dataclass(slots=True)
class SecurityConfig:
    enable_tier3: bool = False
    disable_tier2: bool = False
    ip_allowlist: list[str] = field(default_factory=lambda: ["127.0.0.1/32"])
    oauth_client_id: str = ""
    oauth_client_secret: str = ""


@dataclass(slots=True)
class ToolConfig:
    enable: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AppConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    tools: ToolConfig = field(default_factory=ToolConfig)


DEFAULT_CONFIG_PATHS = (
    Path("./pi-control.toml"),
    Path.home() / ".config" / "pi-control-mcp" / "pi-control.toml",
)


def _load_toml(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def load_config(config_path: str | None = None) -> AppConfig:
    cfg = AppConfig()

    if config_path:
        path = Path(config_path)
        if path.exists():
            _merge_config(cfg, _load_toml(path))
    else:
        for path in DEFAULT_CONFIG_PATHS:
            if path.exists():
                _merge_config(cfg, _load_toml(path))
                break

    auth_from_env = os.getenv("PI_CONTROL_AUTH_KEY")
    if auth_from_env:
        cfg.server.auth_key = auth_from_env

    return cfg


def _merge_config(cfg: AppConfig, raw: dict) -> None:
    server = raw.get("server", {})
    security = raw.get("security", {})
    tools = raw.get("tools", {})

    cfg.server.host = server.get("host", cfg.server.host)
    cfg.server.port = int(server.get("port", cfg.server.port))
    cfg.server.auth_key = server.get("auth_key", cfg.server.auth_key)
    cfg.server.transport = server.get("transport", cfg.server.transport)

    cfg.security.enable_tier3 = bool(security.get("enable_tier3", cfg.security.enable_tier3))
    cfg.security.disable_tier2 = bool(security.get("disable_tier2", cfg.security.disable_tier2))
    cfg.security.ip_allowlist = list(security.get("ip_allowlist", cfg.security.ip_allowlist))
    cfg.security.oauth_client_id = security.get("oauth_client_id", cfg.security.oauth_client_id)
    cfg.security.oauth_client_secret = security.get(
        "oauth_client_secret", cfg.security.oauth_client_secret
    )

    cfg.tools.enable = list(tools.get("enable", cfg.tools.enable))
    cfg.tools.exclude = list(tools.get("exclude", cfg.tools.exclude))
