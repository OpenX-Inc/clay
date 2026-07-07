"""Blender-backed tools (FBX export now; rig / retopo / bake later).

All fail *visibly* when Blender isn't available — Clay never fakes output.
"""

from __future__ import annotations

from pathlib import Path

from clay.blender import BlenderError
from clay.blender import export_fbx as _export_fbx
from clay.tools.context import ToolContext
from clay.tools.registry import tool
from clay.tools.result import error, ok


@tool(
    "export_fbx",
    "Convert an existing mesh (glb/obj/ply/stl/fbx) to FBX via headless Blender, "
    "preserving meshes + UVs (+ skeleton later).",
    {"input_path": "string", "output_path": "string?"},
)
def export_fbx(ctx: ToolContext, args: dict) -> dict:
    src = Path(args["input_path"])
    if not src.exists():
        return error("not_found", f"no mesh at {src}")
    out = (
        Path(args["output_path"])
        if args.get("output_path")
        else ctx.output_dir / f"{src.stem}.fbx"
    )
    try:
        res = _export_fbx(src, out, blender=ctx.config.blender.path or None)
    except BlenderError as err:
        return error("blender_unavailable", str(err))
    return ok(path=str(out), faces=res.get("faces"), mesh_count=res.get("mesh_count"))
