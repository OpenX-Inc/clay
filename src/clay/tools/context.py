"""ToolContext + the single ``dispatch`` chokepoint.

Every tool call — from the in-app agent or an MCP client — goes through
``dispatch``, so both surfaces get identical behavior. Exceptions are converted
to structured error envelopes; the model reacts to them instead of crashing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from clay.config import Config
from clay.tools.registry import REGISTRY
from clay.tools.result import error


@dataclass
class ToolContext:
    config: Config
    output_dir: Path

    @classmethod
    def from_config(cls, config: Config) -> ToolContext:
        out = Path(config.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        return cls(config=config, output_dir=out)


def dispatch(ctx: ToolContext, name: str, args: dict[str, Any]) -> dict:
    """Run a tool by name; convert any exception into a structured error."""
    spec = REGISTRY.get(name)
    if spec is None:
        return error("unknown_tool", f"no tool named {name!r}")
    try:
        return spec.fn(ctx, args or {})
    except Exception as err:  # noqa: BLE001 — surface as a value, never crash the loop
        return error("tool_failed", f"{name} raised {type(err).__name__}: {err}")
