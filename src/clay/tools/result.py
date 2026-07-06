"""Tool result envelope — errors are *values*, never exceptions.

Every tool returns one of these dicts. Feeding structured failures back to the
model (instead of raising) lets it self-correct.
"""

from __future__ import annotations

from typing import Any


def ok(**fields: Any) -> dict:
    """Success envelope: ``{"ok": True, ...fields}``."""
    return {"ok": True, **fields}


def error(code: str, message: str, hint: str = "") -> dict:
    """Recoverable error the model can react to (e.g. ``not_found``, ``invalid``)."""
    err: dict[str, Any] = {"code": code, "message": message}
    if hint:
        err["hint"] = hint
    return {"ok": False, "error": err}
