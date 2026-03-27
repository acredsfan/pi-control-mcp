from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AuthConfig:
    auth_key: str = ""
    oauth_client_id: str = ""
    oauth_client_secret: str = ""


def is_authorized(auth_header: str | None, expected_key: str) -> bool:
    if not expected_key:
        return True
    if not auth_header:
        return False
    if not auth_header.lower().startswith("bearer "):
        return False
    token = auth_header.split(" ", 1)[1].strip()
    return token == expected_key


def oauth_enabled(cfg: AuthConfig) -> bool:
    return bool(cfg.oauth_client_id and cfg.oauth_client_secret)
