"""CPU geometry tools (trimesh) — collision now; LODs/variations later."""

from __future__ import annotations

from pathlib import Path

from clay.tools.context import ToolContext
from clay.tools.registry import tool
from clay.tools.result import error, ok


@tool(
    "make_collision",
    "Build a physics collider for a mesh — convex hull / box / simplified / VHACD "
    "compound. CPU-only. Emits a separate *_collision file for the game engine.",
    {
        "input_path": "string",
        "kind": {
            "type": "string",
            "enum": ["convex", "box", "simplified", "compound"],
            "optional": True,
        },
        "max_hulls": {"type": "integer", "minimum": 1, "optional": True},
    },
)
def make_collision(ctx: ToolContext, args: dict) -> dict:
    from clay.collision import make_collision as _make

    src = Path(args["input_path"])
    if not src.exists():
        return error("not_found", f"no mesh at {src}")
    res = _make(
        src,
        kind=args.get("kind", "convex"),
        max_hulls=int(args.get("max_hulls", 32)),
        out_dir=ctx.output_dir,
    )
    return ok(**res)


@tool(
    "make_lods",
    "Build an LOD chain (decimated copies at descending ratios) for a mesh. CPU-only.",
    {
        "input_path": "string",
        "ratios": {"type": "array", "items": "number", "optional": True},
    },
)
def make_lods(ctx: ToolContext, args: dict) -> dict:
    from clay.lods import DEFAULT_RATIOS
    from clay.lods import make_lods as _make

    src = Path(args["input_path"])
    if not src.exists():
        return error("not_found", f"no mesh at {src}")
    ratios = args.get("ratios") or list(DEFAULT_RATIOS)
    try:
        res = _make(src, ratios=ratios, out_dir=ctx.output_dir)
    except ValueError as err:
        return error("invalid", str(err))
    return ok(**res)
