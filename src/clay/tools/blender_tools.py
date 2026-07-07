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


@tool(
    "retopo_asset",
    "Retopologize a mesh to clean quad-dominant topology (Quadriflow) with UVs "
    "re-unwrapped — for anything animated/deformable. Blender-backed.",
    {
        "input_path": "string",
        "target_faces": {"type": "integer", "minimum": 20, "optional": True},
        "quads": "boolean?",
        "output_path": "string?",
    },
)
def retopo_asset(ctx: ToolContext, args: dict) -> dict:
    from clay.blender import retopo as _retopo

    src = Path(args["input_path"])
    if not src.exists():
        return error("not_found", f"no mesh at {src}")
    out = (
        Path(args["output_path"])
        if args.get("output_path")
        else ctx.output_dir / f"{src.stem}_retopo.glb"
    )
    try:
        res = _retopo(
            src, out,
            target_faces=int(args.get("target_faces", 5000)),
            quads=bool(args.get("quads", True)),
            blender=ctx.config.blender.path or None,
        )
    except BlenderError as err:
        return error("blender_unavailable", str(err))
    return ok(path=str(out), faces=res.get("faces"), quads=res.get("quads"),
              quad_ratio=res.get("quad_ratio"))
