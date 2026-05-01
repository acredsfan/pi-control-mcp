from __future__ import annotations

import re

REDACT_PATTERNS = [
    (re.compile(r"ghp_[A-Za-z0-9]{20,}"), "[REDACTED_TOKEN]"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "[REDACTED_TOKEN]"),
    (re.compile(r"sk-[A-Za-z0-9_-]{16,}"), "[REDACTED_TOKEN]"),
    (re.compile(r"Bearer\s+[A-Za-z0-9._-]{10,}", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED_TOKEN]"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"(?im)\b(PASSWORD|TOKEN|SECRET|API_KEY|NTRIP_PASSWORD)\s*=\s*[^\s\n]+"), r"\1=[REDACTED_SECRET]"),
]


def redact_text(text: str) -> tuple[str, bool]:
    redacted = text
    changed = False
    for pattern, replacement in REDACT_PATTERNS:
        updated = pattern.sub(replacement, redacted)
        if updated != redacted:
            changed = True
            redacted = updated
    return redacted, changed
